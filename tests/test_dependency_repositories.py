"""Observing the repositories your dependencies name (v0.21.0 item W3).

Exit criterion: with ``--observe-repositories`` (``check``, ``attest``, the
Action's ``observe-repositories`` input), the GitHub repository each npm and
PyPI dependency names is recorded in the kept history. A first observation
is a baseline and reports only what the repository already is (archived,
answering under another owner). After that, a license change, an archive or
a move to a new owner between two runs is a REVIEW result for every
dependency naming the repository, once. What was not observed is said.
"""

from __future__ import annotations

import base64
import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli
from core.dependency_repositories import observe_dependency_repositories
from core.history_audit import OK, audit_history
from core.history_key import keyring, parse_key
from core.observations.store import list_observations
from core.risk.check import check_dependency

ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")
TODAY = date(2026, 11, 10)
KEY = parse_key(base64.b64encode(b"a" * 32).decode())
NPM = "https://registry.npmjs.org/"
PYPI = "https://pypi.org/pypi/"


def _npm(name, version, repo, license="MIT"):
    doc = {"name": name, "version": version, "license": license}
    if repo:
        doc["repository"] = {"type": "git", "url": f"git+https://github.com/{repo}.git"}
    return doc


def _registry():
    return {
        NPM + "widget/1.0.0": _npm("widget", "1.0.0", "acme/widget"),
        NPM + "widget-cli/2.0.0": _npm("widget-cli", "2.0.0", "acme/widget"),
        NPM + "loner/1.0.0": _npm("loner", "1.0.0", None),
        PYPI + "gadget/3.0/json": {
            "info": {
                "name": "gadget",
                "version": "3.0",
                "project_urls": {"Source": "https://github.com/acme/gadget"},
            }
        },
    }


class Registry:
    def __init__(self, answers=None):
        self.answers = _registry() if answers is None else answers
        self.asked: list[str] = []

    def __call__(self, url):
        self.asked.append(url)
        if url in self.answers:
            return 200, json.loads(json.dumps(self.answers[url]))
        return 0, None


class GitHub:
    """Stub GitHub: repo -> the fields of its repository document; records what was asked."""

    def __init__(self, **repos):
        self.repos = {
            "acme/widget": {"license": "MIT"},
            "acme/gadget": {"license": "Apache-2.0"},
            **{k.replace("__", "/"): v for k, v in repos.items()},
        }
        self.asked: list[str] = []

    def __call__(self, repo):
        self.asked.append(repo)
        facts = self.repos.get(repo)
        if facts is None or facts.get("error"):
            return {
                "collector": "github",
                "error": True,
                "category": "rate_limit",
                "retryable": True,
                "status_code": 403,
                "safe_message": "github: rate limited",
                "repo": repo,
            }
        return {
            "collector": "github",
            "kind": "repo_meta",
            "repo": repo,
            "full_name": facts.get("full_name", repo),
            "archived": bool(facts.get("archived")),
            "pushed_at": "2026-11-01T00:00:00Z",
            "default_branch": "main",
            "license": facts.get("license"),
        }


def _dep(name, version, ecosystem="npm"):
    return {"kind": "package", "package": name, "version": version, "ecosystem": ecosystem}


WIDGET, CLI_DEP, GADGET = (
    _dep("widget", "1.0.0"),
    _dep("widget-cli", "2.0.0"),
    _dep("gadget", "3.0", "PyPI"),
)


def _observe(tmp_path, deps, github, registry=None, key=KEY, **kwargs):
    return observe_dependency_repositories(
        deps,
        store_root=str(tmp_path / "observations"),
        history_key=key,
        fetch_json=registry or Registry(),
        fetch_meta=github,
        today=TODAY,
        **kwargs,
    )


def _types(result, index=0):
    return [e.event_type.value for e in result["events"].get(index, [])]


# --- Baseline, then changes --------------------------------------------------------------------


def test_a_first_observation_is_a_baseline_with_nothing_to_report(tmp_path):
    result = _observe(tmp_path, [WIDGET, GADGET], GitHub())
    assert result["events"] == {}
    assert result["summary"]["observed"] == 2 and result["summary"]["baselines"] == 2
    audit = audit_history(
        tmp_path / "observations", tmp_path / "none", keyring(KEY), require_keyed=True
    )
    assert audit["status"] == OK and audit["histories"] == 2


def test_an_archive_between_two_runs_is_reported_once(tmp_path):
    _observe(tmp_path, [WIDGET], GitHub())
    result = _observe(tmp_path, [WIDGET], GitHub(acme__widget={"license": "MIT", "archived": 1}))
    [event] = result["events"][0]
    assert event.event_type.value == "PROJECT_ARCHIVED"
    assert event.title == "acme/widget was archived on GitHub"
    assert event.impact.value == "REVIEW" and event.confidence.value == "EMERGING"
    assert event.scope.packages == ["pkg:npm/widget"]
    assert str(event.evidences[0].source.url) == "https://github.com/acme/widget"
    # The package-to-repository link is the publisher's claim; the class is experimental.
    assert "names acme/widget as its source repository" in event.summary
    assert "not verified here" in event.summary and "Experimental" in event.summary
    verdict = check_dependency(WIDGET, [event])
    assert verdict.affected and verdict.relationship == "AFFECTS_PACKAGE"
    # The next run sees no difference: nothing is repeated.
    again = _observe(tmp_path, [WIDGET], GitHub(acme__widget={"license": "MIT", "archived": 1}))
    assert again["events"] == {} and again["summary"]["changes"] == 0


def test_a_move_to_a_new_owner_is_reported(tmp_path):
    _observe(tmp_path, [WIDGET], GitHub())
    moved = GitHub(acme__widget={"license": "MIT", "full_name": "newco/widget"})
    result = _observe(tmp_path, [WIDGET], moved)
    assert _types(result) == ["OWNERSHIP_CHANGE"]
    assert result["events"][0][0].title == "acme/widget moved to newco/widget on GitHub"


def test_a_license_change_is_corroborated_only_when_the_registry_agrees(tmp_path):
    _observe(tmp_path, [WIDGET], GitHub())
    relicensed = GitHub(acme__widget={"license": "BUSL-1.1"})
    lagging = _observe(tmp_path, [WIDGET], relicensed)
    [event] = lagging["events"][0]
    assert event.event_type.value == "LICENSE_CHANGE"
    assert event.confidence.value == "EMERGING"  # GitHub's detection alone is a heuristic

    other = tmp_path / "second"
    other.mkdir()
    _observe(other, [WIDGET], GitHub())
    answers = _registry()
    answers[NPM + "widget"] = {
        "versions": {"1.0.0": {"version": "1.0.0", "license": "BUSL-1.1"}},
        "time": {"1.0.0": "2026-01-02T03:04:05.000Z"},
    }
    agreeing = _observe(other, [WIDGET], relicensed, registry=Registry(answers))
    assert agreeing["events"][0][0].confidence.value == "CORROBORATED"


def test_packages_sharing_a_repository_observe_it_once_and_both_hear(tmp_path):
    github = GitHub()
    _observe(tmp_path, [WIDGET, CLI_DEP], github)
    assert github.asked == ["acme/widget"]
    result = _observe(
        tmp_path, [WIDGET, CLI_DEP], GitHub(acme__widget={"license": "MIT", "archived": 1})
    )
    assert _types(result, 0) == _types(result, 1) == ["PROJECT_ARCHIVED"]
    assert result["events"][1][0].scope.packages == ["pkg:npm/widget-cli"]
    assert result["events"][0][0].id != result["events"][1][0].id


def test_a_repository_already_archived_is_reported_at_the_baseline_only(tmp_path):
    archived = GitHub(acme__widget={"license": "MIT", "archived": 1})
    first = _observe(tmp_path, [WIDGET], archived)
    [event] = first["events"][0]
    assert event.event_type.value == "PROJECT_ARCHIVED"
    assert event.title == "acme/widget is archived on GitHub"
    assert "Experimental" not in event.summary  # the snapshot rule is a verified case
    assert _observe(tmp_path, [WIDGET], archived)["events"] == {}


def test_a_repository_answering_under_another_owner_is_reported_at_the_baseline(tmp_path):
    moved = GitHub(acme__widget={"license": "MIT", "full_name": "newco/widget"})
    assert _types(_observe(tmp_path, [WIDGET], moved)) == ["OWNERSHIP_CHANGE"]


# --- What was not observed is said -------------------------------------------------------------


def test_a_github_failure_records_nothing_and_is_named(tmp_path):
    result = _observe(tmp_path, [WIDGET, GADGET], GitHub(acme__widget={"error": True}))
    assert result["summary"]["observed"] == 1 and result["summary"]["failed"] == 1
    [failure] = result["failures"]
    assert failure["repository"] == "acme/widget"
    assert list_observations("github.com", "acme", "widget", root=tmp_path / "observations") == []
    # The next successful run is the baseline: a failure is never a change.
    assert _observe(tmp_path, [WIDGET], GitHub())["summary"]["baselines"] == 1


def test_a_collector_that_raises_is_a_failure_not_a_crash(tmp_path):
    def broken(repo):
        raise RuntimeError("boom")

    result = _observe(tmp_path, [WIDGET], broken)
    assert result["summary"]["failed"] == 1 and result["events"] == {}


def test_packages_without_a_repository_and_other_ecosystems_are_counted(tmp_path):
    deps = [_dep("loner", "1.0.0"), _dep("ghost", "1.0.0"), _dep("serde", "1.0.0", "cargo")]
    summary = _observe(tmp_path, deps, GitHub())["summary"]
    assert summary["no_repository"] == 1
    assert summary["registry_unanswered"] == 1
    assert summary["unsupported"] == 1
    assert summary["repositories"] == 0


def test_repositories_past_the_limit_are_counted(tmp_path):
    github = GitHub()
    summary = _observe(tmp_path, [WIDGET, GADGET], github, max_repositories=1)["summary"]
    assert summary["observed"] == 1 and summary["not_observed"] == 1
    assert github.asked == ["acme/gadget"]  # sorted: deterministic which ones


def test_a_keyed_history_refuses_a_run_without_its_key(tmp_path):
    _observe(tmp_path, [WIDGET], GitHub())
    result = _observe(tmp_path, [WIDGET], GitHub(), key=None)
    assert result["summary"]["failed"] == 1
    assert "keyed" in result["failures"][0]["reason"]


# --- check and attest --------------------------------------------------------------------------


@pytest.fixture
def world(monkeypatch, tmp_path):
    """A stub registry and GitHub behind the CLI; returns (github, watchlist, store)."""
    github = GitHub()
    monkeypatch.setattr("core.digest_integrity.default_fetch", Registry())
    monkeypatch.setattr(
        "core.dependency_repositories.default_fetch_meta", lambda repo: github(repo)
    )
    monkeypatch.delenv("OPENPULSE_HISTORY_KEY", raising=False)
    watchlist = tmp_path / "watchlist.yml"
    watchlist.write_text(
        yaml.safe_dump({"dependencies": [WIDGET, GADGET, _dep("serde", "1.0.0", "cargo")]}),
        encoding="utf-8",
    )
    return github, str(watchlist), str(tmp_path / "observations")


def _check(world, *extra):
    _, watchlist, store = world
    return CliRunner().invoke(
        cli,
        ["check", "--watchlist", watchlist, "--ledger", "", "--observe-repositories",
         "--observation-store", store, *extra],
    )  # fmt: skip


def test_check_baselines_then_reports_the_change(world):
    github = world[0]
    first = _check(world)
    assert first.exit_code == 0, first.output
    assert "repositories: 2 of 2 observed (2 for the first time), 0 change(s)" in first.output
    assert "1 dependency(s) of other ecosystems not read" in first.output
    assert "no history key" in first.output
    assert "0/3 dependencies affected" in first.output

    github.repos["acme/widget"] = {"license": "MIT", "archived": 1}
    second = _check(world)
    assert second.exit_code == 0, second.output
    assert "repositories: 2 of 2 observed (0 for the first time), 1 change(s), 1 finding(s)" in (
        second.output
    )
    assert "acme/widget was archived on GitHub" in second.output
    assert "1/3 dependencies affected" in second.output

    third = _check(world, "--fail-on", "review")
    assert third.exit_code == 0, third.output  # reported once: nothing left to fail on


def test_a_repository_change_fails_only_review_and_affected(world):
    github = world[0]
    for gate, code in ((("--fail-on", "action"), 0), (("--fail-on", "review"), 1)):
        github.repos["acme/widget"] = {"license": "MIT"}
        _check(world)
        github.repos["acme/widget"] = {"license": "MIT", "archived": 1}
        assert _check(world, *gate).exit_code == code


def test_check_names_a_repository_it_could_not_observe(world):
    world[0].repos["acme/widget"] = {"error": True}
    result = _check(world)
    assert result.exit_code == 0, result.output
    assert "repositories: 1 of 2 observed" in result.output
    assert "! repository not observed: acme/widget:" in result.output


def test_without_the_flag_github_is_never_asked(world):
    github, watchlist, _ = world
    result = CliRunner().invoke(cli, ["check", "--watchlist", watchlist, "--ledger", ""])
    assert result.exit_code == 0, result.output
    assert github.asked == []


def test_attest_emits_contracts_and_sarif_for_a_repository_change(world, tmp_path):
    github, watchlist, store = world
    out, sarif = tmp_path / "c.jsonl", tmp_path / "r.sarif"
    args = ["attest", "--watchlist", watchlist, "--event", EVENT, "--observe-repositories",
            "--observation-store", store, "--output", str(out), "--sarif", str(sarif)]  # fmt: skip
    assert CliRunner().invoke(cli, args).exit_code == 0
    github.repos["acme/widget"] = {"license": "MIT", "archived": 1}
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    [event_id] = [
        d["provenance"]["event_id"]
        for d in docs
        if d["provenance"]["event_id"].startswith("evt-repository-")
    ]
    assert event_id.startswith("evt-repository-project_archived-acme_widget-pkg_npm_widget-")
    run = json.loads(sarif.read_text(encoding="utf-8"))["runs"][0]
    assert "openpulse/project-archived" in {r["ruleId"] for r in run["results"]}


# --- The Action --------------------------------------------------------------------------------


def test_the_action_input_is_opt_in_needs_history_and_keeps_the_token_to_this_case():
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert action["inputs"]["observe-repositories"]["default"] == "off"
    step = next(s for s in action["runs"]["steps"] if s.get("id") == "run")
    assert step["env"]["IN_OBSERVE"] == "${{ inputs.observe-repositories }}"
    assert step["env"]["OPENPULSE_HISTORY_KEY"] == "${{ inputs.history-key }}"
    script = step["run"]
    assert "inputs.observe-repositories" not in script and "inputs.history-key" not in script
    assert "observe-repositories: on needs history: on" in script
    assert "observe=(--observe-repositories)" in script
    assert '${observe[@]+"${observe[@]}"}' in script
    # The job token is exported for attest only inside the `on` branch.
    on_branch = script.split("observe=(--observe-repositories)")[1].split(";;")[0]
    assert 'export GITHUB_TOKEN="$IN_TOKEN"' in on_branch
    assert script.count('export GITHUB_TOKEN="$IN_TOKEN"') == 1
