"""GitHub repository observation history (v0.20.0 item C1).

Exit criterion: repository facts are kept as a history with the registry
history's guarantees: hash-chained and verified on every append, a
tampered or rolled-back history refused until an explicit, reasoned
re-baseline, keyed when a history key is set, and covered by anchors. A
404 is a recorded fact (missing); any other failure records nothing.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from core.anchor import build_anchor, verify_anchor
from core.observations.registry import RegistryObservation
from core.observations.repository import (
    observe_github_repository,
    split_repo,
    to_repository_observation,
    verify_repository_history,
)
from core.observations.store import (
    list_observations,
    load_all,
    read_rebaselines,
    read_tip,
    repo_dir,
    save_observation,
)
from tests.history_keys import TEST_KEY

T0 = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
REPO = "Example/Widget"


def _meta(**overrides):
    meta = {
        "collector": "github",
        "kind": "repo_meta",
        "repo": REPO,
        "full_name": "example/widget",
        "archived": False,
        "pushed_at": "2026-11-01T00:00:00Z",
        "default_branch": "main",
        "license": "MIT",
        "stargazers": 10,
        "url": "https://github.com/example/widget",
    }
    meta.update(overrides)
    return meta


def _observe(root, meta=None, days=0, **kwargs):
    return observe_github_repository(
        REPO, meta or _meta(), store_root=str(root), observed_at=T0 + timedelta(days=days), **kwargs
    )


def _files(root):
    return list_observations("github.com", "example", "widget", root=str(root))


# --- building one observation ---------------------------------------------------------


def test_metadata_becomes_a_sealed_observation_with_every_fact_hashed():
    obs = to_repository_observation(_meta(), REPO, observed_at=T0)
    assert (obs.registry, obs.namespace, obs.repository) == ("github.com", "example", "widget")
    assert obs.full_name == "example/widget"  # GitHub's spelling kept
    assert obs.license == "MIT" and obs.archived is False and obs.missing is False
    assert obs.verify_record() == "UNKNOWN"  # sealed, not yet chained
    body = obs.integrity_body()
    for fact in ("full_name", "archived", "missing", "license", "pushed_at", "default_branch"):
        assert fact in body
    assert "stargazers" not in body  # a count, not a repository fact


def test_a_404_is_recorded_as_missing():
    obs = to_repository_observation(
        {"collector": "github", "error": True, "status_code": 404, "repo": REPO}, REPO
    )
    assert obs.missing is True and obs.license is None and obs.full_name is None


@pytest.mark.parametrize(
    "meta",
    [
        {"collector": "github", "error": True, "status_code": 403, "repo": REPO},
        {"collector": "github", "error": True, "status_code": None, "repo": REPO},
        {"collector": "github", "project": "x", "skipped": "no repo mapping for x"},
        _meta(kind="release"),
        _meta(repo="other/widget"),
        _meta(archived="yes"),
        _meta(license="M" * 65),
        _meta(default_branch="main\nfake"),
        _meta(full_name="../../etc"),
        "not a mapping",
    ],
)
def test_anything_else_records_nothing(meta):
    with pytest.raises(ValueError):
        to_repository_observation(meta, REPO)


@pytest.mark.parametrize("repo", ["widget", "a/b/c", "../widget", "./..", "a/", "own er/x", ""])
def test_malformed_repository_paths_are_refused(repo):
    with pytest.raises(ValueError):
        split_repo(repo)


# --- the history ------------------------------------------------------------------------


def test_first_observation_is_a_baseline_and_the_next_one_follows_it(tmp_path):
    first = _observe(tmp_path)
    assert first["error"] is None
    assert first["history_status"] == "GENESIS" and first["previous"] is None
    assert first["history_integrity"] == "VALID_UNKEYED"

    second = _observe(tmp_path, _meta(license="Apache-2.0"), days=1)
    assert second["history_status"] == "VALID"
    assert second["previous"]["license"] == "MIT"
    assert second["observation"]["license"] == "Apache-2.0"
    assert second["observation"]["previous_observation_hash"] == first["observation"]["chain_hash"]
    assert second["observation"]["first_detected_at"].startswith("2026-11-08")
    assert len(_files(tmp_path)) == 2
    ordered = load_all("github.com", "example", "widget", root=str(tmp_path))
    assert verify_repository_history(ordered)["status"] == "VALID"


def test_paths_are_case_insensitive(tmp_path):
    _observe(tmp_path)
    result = observe_github_repository(
        "example/WIDGET",
        _meta(repo="example/WIDGET"),
        store_root=str(tmp_path),
        observed_at=T0 + timedelta(days=1),
    )
    assert result["history_status"] == "VALID"  # one history, not two
    assert len(_files(tmp_path)) == 2


def test_a_missing_repository_extends_the_history(tmp_path):
    _observe(tmp_path)
    gone = _observe(
        tmp_path, {"collector": "github", "error": True, "status_code": 404, "repo": REPO}, days=1
    )
    assert gone["history_status"] == "VALID"
    assert gone["observation"]["missing"] is True and gone["previous"]["missing"] is False


def test_a_failed_fetch_writes_nothing(tmp_path):
    _observe(tmp_path)
    tip = read_tip(repo_dir(tmp_path, "github.com", "example", "widget"))
    failed = _observe(
        tmp_path,
        {"collector": "github", "error": True, "status_code": 429, "repo": REPO},
        days=1,
    )
    assert failed["history_status"] == "NOT_OBSERVED"
    assert failed["error"]["collector"] == "github"
    assert len(_files(tmp_path)) == 1
    assert read_tip(repo_dir(tmp_path, "github.com", "example", "widget")) == tip


def test_an_edited_fact_breaks_the_history_and_is_refused(tmp_path):
    _observe(tmp_path)
    _observe(tmp_path, days=1)
    oldest = _files(tmp_path)[0]
    record = json.loads(oldest.read_text(encoding="utf-8"))
    record["license"] = "Apache-2.0"  # rewrite what the repository said
    oldest.write_text(json.dumps(record), encoding="utf-8")

    refused = _observe(tmp_path, days=2)
    assert refused["history_status"] == "BROKEN"
    assert refused["error"]["category"] == "integrity"
    assert (
        "openpulse observe-github --repo example/widget --rebaseline"
        in (refused["error"]["safe_message"])
    )
    assert len(_files(tmp_path)) == 2  # nothing appended


def test_a_registry_record_in_a_repository_history_is_broken(tmp_path):
    _observe(tmp_path)
    stray = RegistryObservation(namespace="example", repository="widget", tags={}).seal()
    record = stray.link(load_all("github.com", "example", "widget", root=str(tmp_path))[-1])
    save_observation(
        {**record.model_dump(mode="json"), "registry": "github.com", "observed_at": "2026-11-09"},
        root=str(tmp_path),
    )
    assert _observe(tmp_path, days=2)["history_status"] == "BROKEN"


def test_deleting_the_newest_record_is_a_rollback(tmp_path):
    _observe(tmp_path)
    _observe(tmp_path, days=1)
    _files(tmp_path)[-1].unlink()
    refused = _observe(tmp_path, days=2)
    assert refused["history_status"] == "ROLLBACK"
    assert refused["observation"] is None


def test_a_reasoned_rebaseline_quarantines_a_broken_history(tmp_path):
    _observe(tmp_path)
    oldest = _files(tmp_path)[0]
    record = json.loads(oldest.read_text(encoding="utf-8"))
    record["archived"] = True
    oldest.write_text(json.dumps(record), encoding="utf-8")

    accepted = _observe(tmp_path, days=1, rebaseline_reason="restored from a bad backup")
    assert accepted["error"] is None
    assert accepted["history_status"] == "REBASELINED"
    assert accepted["previous"] is None  # no comparison across a re-baseline
    directory = repo_dir(tmp_path, "github.com", "example", "widget")
    assert [e["previous_status"] for e in read_rebaselines(directory)] == ["BROKEN"]
    assert any(p.name.startswith("quarantine-") for p in directory.iterdir())


def test_a_keyed_history_needs_its_key(tmp_path):
    first = _observe(tmp_path, history_key=TEST_KEY)
    assert first["history_integrity"] == "VALID_KEYED"
    assert first["observation"]["key_id"] == TEST_KEY.key_id
    assert _observe(tmp_path, days=1, history_key=TEST_KEY)["history_integrity"] == "VALID_KEYED"

    refused = _observe(tmp_path, days=2)
    assert refused["history_status"] == "KEY_REQUIRED"
    assert refused["error"]["collector"] == "github"
    assert len(_files(tmp_path)) == 2


def test_anchors_cover_repository_histories(tmp_path):
    store, ledger = tmp_path / "observations", tmp_path / "ledger"
    _observe(store)
    _observe(store, days=1)
    anchor = build_anchor(store, ledger)
    assert anchor["observations"]["github.com/example/widget"]["records"] == 2
    assert verify_anchor(anchor, store, ledger)["status"] == "OK"

    _files(store)[-1].unlink()
    assert verify_anchor(anchor, store, ledger)["status"] == "VIOLATED"


def test_registry_histories_are_unchanged_by_the_refactor(tmp_path):
    from core.observations.sweep import observe_repository

    probe = {"registry": "docker.io", "namespace": "demo", "repo": "app", "digests": {"1": []}}
    first = observe_repository("docker.io", "demo", "app", probe, store_root=str(tmp_path))
    assert first["history_status"] == "GENESIS"
    path = list_observations("docker.io", "demo", "app", root=str(tmp_path))[0]
    record = json.loads(path.read_text(encoding="utf-8"))
    record["tags"] = {"2": []}
    path.write_text(json.dumps(record), encoding="utf-8")
    refused = observe_repository("docker.io", "demo", "app", probe, store_root=str(tmp_path))
    assert refused["history_status"] == "BROKEN"
    assert refused["error"]["collector"] == "registries"
    assert (
        "openpulse observe --namespace demo --repo app --rebaseline"
        in (refused["error"]["safe_message"])
    )


# --- the command ------------------------------------------------------------------------


def test_observe_github_records_and_reports(tmp_path, monkeypatch):
    from cli.main import cli
    from collectors.github import collector

    monkeypatch.setattr(collector.GitHubCollector, "fetch_repo_meta", lambda self, slug: _meta())
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    store = str(tmp_path / "store")
    runner = CliRunner()

    first = runner.invoke(cli, ["observe-github", "--repo", REPO, "--store", store])
    assert first.exit_code == 0, first.output
    assert "license MIT, archived false" in first.output
    assert "baseline recorded" in first.output

    second = runner.invoke(cli, ["observe-github", "--repo", REPO, "--store", store])
    assert second.exit_code == 0, second.output
    assert "appended to the history" in second.output
    assert len(list_observations("github.com", "example", "widget", root=store)) == 2


def test_observe_github_refuses_a_malformed_path(tmp_path):
    from cli.main import cli

    result = CliRunner().invoke(
        cli, ["observe-github", "--repo", "../etc", "--store", str(tmp_path / "s")]
    )
    assert result.exit_code == 2
    assert "owner/name" in result.output
