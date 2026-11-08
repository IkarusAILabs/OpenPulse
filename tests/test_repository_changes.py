"""Repository changes become findings (v0.20.0 item C2).

Exit criterion: a license change, an archive and a move to a new owner
are reported from two comparable records of the repository history, with
both records as evidence and a first-detection date only when the history
is keyed. "No license detected" and NOASSERTION are never a relicense;
unarchived, missing and restored are changes, not findings; the snapshot
rules' restatement of the same fact is replaced, not duplicated.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from analyzers.change_analyst import (
    DETECTION_REPOSITORY_HISTORY,
    analyze_github_meta,
    analyze_repository_changes,
    replace_snapshot_duplicates,
)
from core.observations.base import GitHubRepositoryObservation
from core.observations.repository import (
    diff_repository_observations,
    first_detected_at_for,
    license_evidence,
    observe_github_repository,
)
from core.risk.impact import evaluate_impact
from tests.history_keys import TEST_KEY

T0 = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
REPO = "example/widget"


def _record(day=0, **facts):
    values = {
        "namespace": "example",
        "repository": "widget",
        "full_name": "example/widget",
        "archived": False,
        "license": "MIT",
        "observed_at": T0 + timedelta(days=day),
    }
    values.update(facts)
    return GitHubRepositoryObservation(**values).seal()


def _types(before, after):
    return [c["type"] for c in diff_repository_observations(before, after)]


def _meta(**overrides):
    meta = {
        "collector": "github",
        "kind": "repo_meta",
        "repo": REPO,
        "full_name": REPO,
        "archived": False,
        "pushed_at": "2026-11-01T00:00:00Z",
        "default_branch": "main",
        "license": "MIT",
    }
    meta.update(overrides)
    return meta


# --- what counts as a change ------------------------------------------------------------


def test_no_previous_record_is_no_change():
    assert diff_repository_observations(None, _record()) == []


def test_a_new_license_id_is_a_license_change():
    changes = diff_repository_observations(_record(), _record(1, license="BUSL-1.1"))
    assert [(c["type"], c["previous"], c["current"]) for c in changes] == [
        ("license_changed", "MIT", "BUSL-1.1")
    ]
    change = changes[0]
    assert change["previous_observed_at"].startswith("2026-11-08")
    assert change["observed_at"].startswith("2026-11-09")
    assert change["current_hash"] and change["previous_hash"]
    assert change["first_detected_at"] is None


@pytest.mark.parametrize("unknown", [None, "NOASSERTION", "other", ""])
def test_losing_license_evidence_is_never_a_relicense(unknown):
    assert _types(_record(), _record(1, license=unknown)) == ["license_evidence_lost"]
    assert _types(_record(license=unknown), _record(1)) == ["license_detected"]
    assert license_evidence(unknown) is None


def test_the_same_license_in_another_case_is_no_change():
    assert _types(_record(license="mit"), _record(1, license="MIT")) == []


def test_archive_transitions():
    assert _types(_record(), _record(1, archived=True)) == ["archived"]
    assert _types(_record(archived=True), _record(1)) == ["unarchived"]
    assert _types(_record(archived=True), _record(1, archived=True)) == []


def test_a_new_owner_is_a_move_and_a_same_owner_rename_is_not():
    moved = diff_repository_observations(_record(), _record(1, full_name="newco/widget"))
    assert [(c["type"], c["previous"], c["current"]) for c in moved] == [
        ("moved", "example/widget", "newco/widget")
    ]
    assert _types(_record(), _record(1, full_name="example/gadget")) == []
    assert _types(_record(), _record(1, full_name="Example/Widget")) == []


def test_a_404_says_only_that_it_went_missing():
    gone = _record(1, missing=True, license=None, full_name=None)
    assert _types(_record(), gone) == ["repo_missing"]
    assert _types(gone, _record(2, license="Apache-2.0")) == ["repo_restored"]
    assert _types(gone, _record(2, missing=True, license=None, full_name=None)) == []


def test_several_changes_at_once():
    after = _record(1, license="Apache-2.0", archived=True, full_name="newco/widget")
    assert _types(_record(), after) == ["license_changed", "archived", "moved"]


# --- first detection --------------------------------------------------------------------


def _chain(*records):
    linked, previous = [], None
    for record in records:
        record = record.link(previous)
        linked.append(record)
        previous = record
    return linked


def test_first_detection_is_the_start_of_the_current_episode():
    history = _chain(
        _record(0),
        _record(1, archived=True),
        _record(2),
        _record(3, archived=True),
        _record(4, archived=True),
    )
    target = diff_repository_observations(history[2], history[3])[0]
    assert first_detected_at_for(target, history) == T0 + timedelta(days=3)


def test_a_license_change_to_another_value_starts_a_new_episode():
    history = _chain(
        _record(0),
        _record(1, license="Apache-2.0"),
        _record(2),
        _record(3, license="Apache-2.0"),
    )
    target = diff_repository_observations(history[2], history[3])[0]
    assert first_detected_at_for(target, history) == T0 + timedelta(days=3)


def test_a_record_that_does_not_verify_proves_no_date():
    history = _chain(_record(0), _record(1, archived=True))
    tampered = history[0].model_copy(update={"license": "Apache-2.0"})
    target = diff_repository_observations(history[0], history[1])[0]
    assert first_detected_at_for(target, [tampered, history[1]]) is None


# --- through the observation cycle ------------------------------------------------------


def _observe(root, day, meta, **kwargs):
    return observe_github_repository(
        REPO, meta, store_root=str(root), observed_at=T0 + timedelta(days=day), **kwargs
    )


def test_an_unkeyed_history_reports_changes_without_a_date(tmp_path):
    assert _observe(tmp_path, 0, _meta())["changes"] == []
    result = _observe(tmp_path, 1, _meta(license="BUSL-1.1"))
    assert [c["type"] for c in result["changes"]] == ["license_changed"]
    assert result["changes"][0]["first_detected_at"] is None  # B3c: unkeyed proves no date


def test_a_keyed_history_dates_each_change(tmp_path):
    _observe(tmp_path, 0, _meta(), history_key=TEST_KEY)
    assert _observe(tmp_path, 1, _meta(), history_key=TEST_KEY)["changes"] == []
    result = _observe(tmp_path, 2, _meta(archived=True), history_key=TEST_KEY)
    assert [c["type"] for c in result["changes"]] == ["archived"]
    assert result["changes"][0]["first_detected_at"].startswith("2026-11-10")
    assert _observe(tmp_path, 3, _meta(archived=True), history_key=TEST_KEY)["changes"] == []


def test_no_changes_across_a_rebaseline(tmp_path):
    _observe(tmp_path, 0, _meta())
    _observe(tmp_path, 1, _meta())
    files = sorted((tmp_path / "github.com" / "example" / "widget").glob("2026*.json"))
    files[-1].unlink()  # roll back
    result = _observe(tmp_path, 2, _meta(license="BUSL-1.1"), rebaseline_reason="restored backup")
    assert result["history_status"] == "REBASELINED"
    assert result["changes"] == []


# --- findings ---------------------------------------------------------------------------


def _changes(before, after):
    return diff_repository_observations(before, after)


def test_license_archive_and_move_become_findings_with_both_records_as_evidence():
    changes = _changes(
        _record(), _record(1, license="BUSL-1.1", archived=True, full_name="newco/widget")
    )
    findings = analyze_repository_changes(changes, today=date(2026, 11, 9))
    assert [f["event_type"] for f in findings] == [
        "LICENSE_CHANGE",
        "PROJECT_ARCHIVED",
        "OWNERSHIP_CHANGE",
    ]
    for finding in findings:
        assert finding["detection_method"] == DETECTION_REPOSITORY_HISTORY
        assert finding["evidence_strength"] == "moderate"
        assert finding["impact"] == "REVIEW"
        assert finding["effective_at"].startswith("2026-11-09")  # when first seen
        evidence = finding["observation_evidence"]
        assert evidence["content_hash"] and evidence["previous_content_hash"]
        assert evidence["previous_observed_at"].startswith("2026-11-08")
    license_change, archived, moved = findings
    assert license_change["observation_evidence"]["fact"]["previous"] == "MIT"
    assert license_change["observation_evidence"]["fact"]["current"] == "BUSL-1.1"
    assert "from MIT to BUSL-1.1" in license_change["title"]
    assert archived["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/example/widget"}
    ]
    # A move names the old path: the references that now redirect.
    assert moved["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/example/widget"}
    ]
    assert moved["references"] == ["https://github.com/newco/widget"]


@pytest.mark.parametrize(
    "after",
    [
        _record(1, license=None),
        _record(1, license="NOASSERTION"),
        _record(1, missing=True, license=None, full_name=None),
    ],
)
def test_lost_evidence_and_a_404_are_not_findings(after):
    changes = _changes(_record(), after)
    assert changes and analyze_repository_changes(changes) == []


def test_unarchived_is_not_a_finding():
    changes = _changes(_record(archived=True), _record(1))
    assert analyze_repository_changes(changes) == []


def test_a_license_change_is_placed_for_review():
    finding = analyze_repository_changes(_changes(_record(), _record(1, license="BUSL-1.1")))[0]
    assessed = evaluate_impact(finding, today=date(2026, 11, 9))
    assert assessed["eligibility"] == "REVIEW"
    assert any("license change" in reason for reason in assessed["reasons"])


def test_the_history_finding_replaces_the_snapshot_restatement():
    snapshot = analyze_github_meta(
        [
            {
                "kind": "repo_meta",
                "repo": REPO,
                "full_name": REPO,
                "archived": True,
                "pushed_at": "2026-01-01",
            }
        ]
    )
    other = {"event_type": "EOL", "affected_artifacts": [], "title": "unrelated"}
    items = [{"project": "widget", "findings": [*snapshot, other]}]
    history = analyze_repository_changes(_changes(_record(), _record(1, archived=True)))

    kept = replace_snapshot_duplicates(items, history)
    assert [f["event_type"] for f in kept[0]["findings"]] == ["EOL"]
    assert [f["event_type"] for f in items[0]["findings"]] == ["PROJECT_ARCHIVED", "EOL"]
    assert replace_snapshot_duplicates(items, []) is items


def test_a_snapshot_for_another_repository_is_kept():
    snapshot = analyze_github_meta(
        [{"kind": "repo_meta", "repo": "other/thing", "full_name": "other/thing", "archived": True}]
    )
    items = [{"project": "thing", "findings": snapshot}]
    history = analyze_repository_changes(_changes(_record(), _record(1, archived=True)))
    assert replace_snapshot_duplicates(items, history)[0]["findings"] == snapshot


# --- the commands -----------------------------------------------------------------------


def _patch_meta(monkeypatch, metas):
    from collectors.github import collector

    queue = list(metas)
    monkeypatch.setattr(
        collector.GitHubCollector, "fetch_repo_meta", lambda self, slug: queue.pop(0)
    )
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)


def test_observe_github_reports_a_license_change(tmp_path, monkeypatch):
    from cli.main import cli

    _patch_meta(monkeypatch, [_meta(), _meta(), _meta(license="BUSL-1.1")])
    store = str(tmp_path / "store")
    runner = CliRunner()
    for _ in range(2):
        result = runner.invoke(cli, ["observe-github", "--repo", REPO, "--store", store])
        assert result.exit_code == 0, result.output
    assert "no changes since the last observation" in result.output

    result = runner.invoke(cli, ["observe-github", "--repo", REPO, "--store", store])
    assert result.exit_code == 0, result.output
    assert "- license_changed: MIT -> BUSL-1.1" in result.output
    assert "not proven (history is not keyed)" in result.output
    assert "LICENSE_CHANGE" in result.output


def test_report_sweep_observes_catalog_repositories(tmp_path, monkeypatch):
    from cli.main import _observe_catalog_repositories

    _patch_meta(monkeypatch, [_meta(), _meta(archived=True)])
    catalog = [{"slug": "widget", "github": REPO}, {"slug": "no-repo"}]
    store = str(tmp_path / "store")
    assert _observe_catalog_repositories(catalog, store, None, ()) == []
    findings = _observe_catalog_repositories(catalog, store, None, ())
    assert [f["event_type"] for f in findings] == ["PROJECT_ARCHIVED"]


def test_report_sweep_skips_a_repository_it_cannot_observe(tmp_path, monkeypatch, capsys):
    from cli.main import _observe_catalog_repositories

    _patch_meta(
        monkeypatch, [{"collector": "github", "error": True, "status_code": 403, "repo": REPO}]
    )
    findings = _observe_catalog_repositories(
        [{"slug": "widget", "github": REPO}], str(tmp_path), None, ()
    )
    assert findings == []
    assert "repository history skipped for example/widget" in capsys.readouterr().out
