"""Inventory-driven discovery (core/discovery.py, `openpulse discover`).

The retrospective study found 0 of 15 relocation, archival and
distribution events with catalog-driven discovery; these tests pin the
dependency -> target mapping, the offline probe-to-event path, and the
matching that lets a discovered event reach the dependency it came from.
"""

import json
from datetime import date

import pytest

from core.discovery import discover, go_module_repository, plan, target_for
from core.risk.check import check_dependency


def _go(module):
    return {"kind": "package", "package": module, "ecosystem": "Go", "version": "v1.0.0"}


def _image(ref):
    return {"kind": "image", "ref": ref}


@pytest.mark.parametrize(
    "module,repo",
    [
        ("github.com/docker/docker", "docker/docker"),
        ("github.com/docker/docker/client", "docker/docker"),
        ("github.com/docker/distribution/v3", "docker/distribution"),
        ("gopkg.in/yaml.v3", "go-yaml/yaml"),
        ("gopkg.in/user/pkg.v2/sub", "user/pkg"),
        ("golang.org/x/lint", "golang/lint"),
        ("go.uber.org/zap", None),  # vanity path: never guessed
        ("sigs.k8s.io/yaml", None),
        ("github.com/onlyowner", None),
    ],
)
def test_go_module_repository_conventions(module, repo):
    assert go_module_repository(module) == repo


@pytest.mark.parametrize(
    "ref,name",
    [
        ("openjdk:11", "library/openjdk"),
        ("centos:8@sha256:" + "a" * 64, "library/centos"),
        ("bitnami/redis:7", "bitnami/redis"),
        ("docker.io/library/java:8", "library/java"),
        ("github.com/coreos/prometheus-operator", "coreos/prometheus-operator"),
    ],
)
def test_image_and_repository_refs_map_to_targets(ref, name):
    target, reason = target_for(_image(ref))
    assert target is not None and target.name == name and reason == ""


@pytest.mark.parametrize(
    "dep,reason",
    [
        (_image("k8s.gcr.io/pause:3.2"), "no collector for registry k8s.gcr.io"),
        (_image("ghcr.io/opentofu/opentofu:1"), "no collector for registry ghcr.io"),
        (_image("localhost:5000/team/app:1"), "no collector for registry localhost:5000"),
        ({"kind": "package", "package": "colors", "ecosystem": "npm"}, "npm packages"),
        (_go("go.uber.org/zap"), "not on github.com"),
    ],
)
def test_unmappable_dependencies_carry_a_reason(dep, reason):
    target, why = target_for(dep)
    assert target is None and reason in why


def test_plan_deduplicates_and_caps_targets():
    deps = [_go("github.com/a/x"), _go("github.com/a/x/sub"), _go("github.com/b/y"), _image("z")]
    result = plan(deps, max_targets=2)
    assert len(result.targets) == 2
    assert len(result.skipped_targets) == 1
    assert sum(len(v) for v in result.targets.values()) <= 3


# --- the probe-to-event path, with fake collectors (no network) ----------

META = {
    "docker/docker": {"full_name": "moby/moby", "archived": False},
    "go-yaml/yaml": {"full_name": "go-yaml/yaml", "archived": True},
    "golang/dep": {"full_name": "golang/dep", "archived": True},
    "uber-go/zap": {"full_name": "uber-go/zap", "archived": False},
}


class FakeGitHub:
    def __init__(self, repo_map, token=None):
        self.repo_map = repo_map
        self.token = token

    def fetch_repo_meta(self, slug):
        repo = self.repo_map[slug]
        if repo not in META:
            return {"collector": "github", "error": True, "safe_message": "HTTP 404"}
        return {"collector": "github", "kind": "repo_meta", "repo": repo, **META[repo]}


class FakeHub:
    def check_image(self, namespace, repo):
        return {"collector": "registries", "namespace": namespace, "repo": repo, "tags": ["1"]}


@pytest.fixture(scope="module")
def found():
    deps = [
        _go("github.com/docker/docker"),
        _go("gopkg.in/yaml.v3"),
        _go("github.com/golang/dep"),
        _go("github.com/gone/away"),
        _image("openjdk:11"),
        _image("k8s.gcr.io/pause:3.2"),
    ]
    result = discover(deps, today=date(2026, 10, 30), github=FakeGitHub, registries=FakeHub)
    return deps, result


def test_discover_turns_observed_changes_into_gated_events(found):
    _, result = found
    kinds = sorted((e.event_type.value, e.affected_artifacts[0].ref) for e in result.events)
    assert kinds == [
        ("OWNERSHIP_CHANGE", "github.com/docker/docker"),
        ("PROJECT_ARCHIVED", "github.com/go-yaml/yaml"),
        ("PROJECT_ARCHIVED", "github.com/golang/dep"),
    ]
    assert [(t.name, m) for t, m in result.errors] == [("gone/away", "HTTP 404")]
    assert [label for label, _ in result.unmapped] == ["k8s.gcr.io/pause:3.2"]


def test_discovered_events_reach_the_dependencies_they_came_from(found):
    deps, result = found
    verdicts = {d.get("package") or d.get("ref"): check_dependency(d, result.events) for d in deps}
    for name in ("github.com/docker/docker", "gopkg.in/yaml.v3", "github.com/golang/dep"):
        assert (verdicts[name].affected, verdicts[name].relationship) == (True, "AFFECTS_ARTIFACT")
    assert not verdicts["github.com/gone/away"].affected
    assert not verdicts["openjdk:11"].affected


def test_destination_of_a_move_is_not_affected(found):
    _, result = found
    v = check_dependency(_go("github.com/moby/moby"), result.events)
    assert v.relationship not in ("AFFECTS_ARTIFACT", "NOT_AFFECTED")


def test_archived_finding_names_its_repository():
    from analyzers.change_analyst import analyze_github_meta

    (finding,) = analyze_github_meta(
        [{"collector": "github", "kind": "repo_meta", "repo": "golang/dep", "archived": True}]
    )
    assert finding["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/golang/dep"}
    ]


def test_cli_discover_writes_events_check_can_load(tmp_path, monkeypatch):
    from click.testing import CliRunner

    import collectors.github.collector as gh
    import collectors.registries.docker as hub
    from cli.main import cli

    monkeypatch.setattr(gh, "GitHubCollector", FakeGitHub)
    monkeypatch.setattr(hub, "RegistryCollector", FakeHub)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    gomod = tmp_path / "go.mod"
    gomod.write_text(
        "module example.com/demo\n\ngo 1.21\n\nrequire (\n"
        "\tgithub.com/golang/dep v0.5.4\n\tgo.uber.org/zap v1.27.0\n)\n",
        encoding="utf-8",
    )
    out = tmp_path / "events"
    res = CliRunner().invoke(cli, ["discover", "--manifest", str(gomod), "--out", str(out)])
    assert res.exit_code == 0, res.output
    assert "unmapped: go.uber.org/zap" in res.output
    (written,) = sorted(out.glob("*.json"))
    assert json.loads(written.read_text("utf-8"))["event_type"] == "PROJECT_ARCHIVED"
    res = CliRunner().invoke(
        cli, ["check", "--manifest", str(gomod), "--event", str(written), "--strict"]
    )
    assert "github.com/golang/dep==v0.5.4: AFFECTED" in res.output
