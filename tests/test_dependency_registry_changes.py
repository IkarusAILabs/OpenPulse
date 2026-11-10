"""Your dependencies get the v0.20 registry checks (v0.21.0 item W1).

Exit criterion: with ``--registry-changes`` (``check``, ``attest``, the
Action's ``registry-changes`` input) and in the agent tools, a package you
use that its publisher deprecated, yanked or declared inactive, or whose
later releases change its license, is a REVIEW result with its evidence.
A flag on one release reaches that release only. What was not read is
said, never dropped. Nothing changes without the flag, and the results
fail a run only under ``--fail-on review`` or ``affected``.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from analyzers.change_analyst import analyze_deprecations, analyze_release_license_changes
from analyzers.registry_events import event_id, registry_finding_to_event
from cli.main import cli
from core import agent_tools
from core.agent_tools import REGISTRY_CHANGES_SOURCE, Lookups, registry_change_events
from core.risk.check import check_dependency, detections_from_verdicts

ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")
TODAY = date(2026, 11, 9)
NPM = "https://registry.npmjs.org/"
PYPI = "https://pypi.org/pypi/"

UUID_MESSAGE = "uuid@10 and below is no longer supported."


def _packument(licenses):
    return {
        "versions": {v: {"version": v, "license": lic} for v, lic in licenses.items()},
        "time": {v: f"202{i}-01-02T03:04:05.000Z" for i, v in enumerate(licenses)},
    }


def _files(yanked=False, reason=None):
    return [
        {"yanked": yanked, "yanked_reason": reason, "upload_time_iso_8601": "2023-04-26T00:00:00Z"}
    ]


REGISTRY = {
    # uuid: release 3.4.0 deprecated, 9.0.1 and the latest are not.
    NPM + "uuid/latest": {"name": "uuid", "version": "14.0.3"},
    NPM + "uuid/3.4.0": {"name": "uuid", "version": "3.4.0", "deprecated": UUID_MESSAGE},
    NPM + "uuid/9.0.1": {"name": "uuid", "version": "9.0.1"},
    NPM + "uuid": _packument({"3.4.0": "MIT", "9.0.1": "MIT", "14.0.3": "MIT"}),
    # relic: a license change after the release you use.
    NPM + "relic/latest": {"name": "relic", "version": "2.0.0"},
    NPM + "relic/1.0.0": {"name": "relic", "version": "1.0.0"},
    NPM + "relic": _packument({"1.0.0": "MIT", "2.0.0": "BUSL-1.1"}),
    # quiet: nothing to report.
    NPM + "quiet/latest": {"name": "quiet", "version": "1.0.0"},
    NPM + "quiet": _packument({"1.0.0": "MIT"}),
    # urllib3: 2.0.0 yanked.
    PYPI + "urllib3/json": {
        "info": {"version": "2.0.7", "license": "MIT", "classifiers": []},
        "releases": {
            "2.0.0": _files(True, "Truncated response bodies. Upgrade to at least 2.0.2"),
            "2.0.7": _files(),
        },
    },
    PYPI + "urllib3/2.0.0/json": {"info": {"version": "2.0.0", "license": "MIT"}},
}


class Registry:
    """Stub registry: recorded URL -> (200, document); anything else is unreachable."""

    def __init__(self, answers=None):
        self.answers = REGISTRY if answers is None else answers
        self.asked: list[str] = []

    def __call__(self, url):
        self.asked.append(url)
        if url in self.answers:
            return 200, json.loads(json.dumps(self.answers[url]))
        return 0, None


@pytest.fixture
def registry(monkeypatch):
    stub = Registry()
    monkeypatch.setattr("core.digest_integrity.default_fetch", stub)
    return stub


def _dep(name, version, ecosystem="npm"):
    return {"kind": "package", "package": name, "version": version, "ecosystem": ecosystem}


def _watchlist(tmp_path, *deps):
    path = tmp_path / "watchlist.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "dependencies": [
                    {"package": d["package"], "version": d["version"], "ecosystem": d["ecosystem"]}
                    for d in deps
                ]
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def _run(*args):
    return CliRunner().invoke(cli, list(args))


# --- The bridge ------------------------------------------------------------------------------


def _uuid_finding():
    from core import registry_deprecation

    record = registry_deprecation.check("npm", "uuid", "3.4.0", fetch_json=Registry())
    [finding] = analyze_deprecations(record, today=TODAY)
    return finding


def test_a_registry_finding_becomes_an_event_about_that_package_only():
    finding = _uuid_finding()
    event = registry_finding_to_event(finding, "uuid", today=TODAY)
    assert event.id == "evt-registry-npm_deprecated-pkg_npm_uuid-3.4.0" == event_id(finding)
    assert event.event_type.value == "DEPRECATION"
    assert event.impact.value == "REVIEW"
    assert event.confidence.value == "CONFIRMED"  # the publisher's own flag (C5)
    assert event.scope.kind == "package" and event.scope.packages == ["pkg:npm/uuid"]
    [evidence] = event.evidences
    assert evidence.source.name == "registry.npmjs.org"
    assert evidence.source.authority == "primary"
    assert str(evidence.source.url) == "https://www.npmjs.com/package/uuid/v/3.4.0"
    assert UUID_MESSAGE in evidence.excerpt


def test_a_registry_event_is_not_a_lifecycle_fact_in_the_ledger():
    event = registry_finding_to_event(_uuid_finding(), "uuid", today=TODAY)
    verdict = check_dependency(_dep("uuid", "3.4.0"), [event])
    assert verdict.affected and verdict.relationship == "AFFECTS_PACKAGE"
    # No release-cycle identity: never a lifecycle fact (so never a lead time).
    # It is remembered as a change, under its own event id (W4).
    assert event.scope.versions == []
    assert detections_from_verdicts([verdict], [event]) == [
        {"project": "uuid", "finding_class": "change", "subject": event.id, "scope": []}
    ]


def test_a_license_change_event_names_both_releases():
    from core import release_license

    record = release_license.check("npm", "relic", "1.0.0", fetch_json=Registry())
    [finding] = analyze_release_license_changes(record, today=TODAY)
    event = registry_finding_to_event(finding, "relic", today=TODAY)
    assert event.id == "evt-registry-license-pkg_npm_relic-1.0.0-2.0.0"
    assert event.event_type.value == "LICENSE_CHANGE"
    assert event.confidence.value == "EMERGING"  # an observed difference (C5)
    assert event.evidences[0].effective_date == date(2021, 1, 2)


def test_a_finding_without_registry_evidence_is_refused():
    with pytest.raises(ValueError):
        registry_finding_to_event({"event_type": "DEPRECATION", "title": "x"}, "x")


# --- One dependency's events --------------------------------------------------------------


def test_a_version_flag_reaches_that_release_and_not_another(registry):
    lookups = Lookups(budget=20)
    old, status = registry_change_events(_dep("uuid", "3.4.0"), lookups, TODAY)
    new, status_new = registry_change_events(_dep("uuid", "9.0.1"), lookups, TODAY)
    assert [e.title for e in old] == ["uuid 3.4.0 (npm) is deprecated by its publisher"]
    assert new == []
    assert status == {"source": REGISTRY_CHANGES_SOURCE, "status": "ok", "records": 1}
    assert status_new["status"] == "ok"


def test_an_unreadable_registry_is_said_never_a_clean_result(registry):
    events, status = registry_change_events(_dep("gone", "1.0.0"), Lookups(budget=20), TODAY)
    assert events == []
    assert status["status"] == "error"
    assert "deprecation:" in status["detail"] and "release license:" in status["detail"]


def test_a_spent_budget_is_said(registry):
    lookups = Lookups(budget=1)
    events, status = registry_change_events(_dep("uuid", "3.4.0"), lookups, TODAY)
    assert status["status"] == "budget-exhausted"
    assert [e.event_type.value for e in events] == ["DEPRECATION"]  # what was read is kept


def test_other_ecosystems_and_offline_are_not_read(registry):
    assert (
        registry_change_events(_dep("serde", "1.0.0", "cargo"), Lookups(), TODAY)[1]["status"]
        == "unsupported"
    )
    assert registry_change_events(_dep("uuid", "3.4.0"), None, TODAY)[1]["status"] == "disabled"
    assert registry.asked == []


def test_without_a_version_only_package_flags_are_read(registry):
    events, status = registry_change_events(_dep("uuid", None), Lookups(), TODAY)
    assert events == [] and status["status"] == "ok"
    assert "license changes not compared" in status["detail"]
    assert registry.asked == [NPM + "uuid/latest"]


def test_answers_are_cached_and_failures_are_not(registry):
    lookups = Lookups(budget=20)
    registry_change_events(_dep("uuid", "3.4.0"), lookups, TODAY)
    used = lookups.used
    registry_change_events(_dep("uuid", "3.4.0"), lookups, TODAY)
    assert lookups.used == used
    registry_change_events(_dep("gone", "1.0.0"), lookups, TODAY)
    registry_change_events(_dep("gone", "1.0.0"), lookups, TODAY)
    assert lookups.used == used + 4


# --- check ------------------------------------------------------------------------------------


def test_check_reports_each_change_with_what_changed(tmp_path, registry):
    watchlist = _watchlist(
        tmp_path,
        _dep("uuid", "3.4.0"),
        _dep("uuid", "9.0.1"),
        _dep("relic", "1.0.0"),
        _dep("quiet", "1.0.0"),
        _dep("urllib3", "2.0.0", "PyPI"),
    )
    result = _run("check", "--watchlist", watchlist, "--registry-changes", "--ledger", "")
    assert result.exit_code == 0, result.output
    out = result.output
    assert "uuid 3.4.0 (npm) is deprecated by its publisher" in out
    assert "relic (npm) changed its license from MIT to BUSL-1.1 in 2.0.0" in out
    assert "urllib3 2.0.0 (PyPI) was yanked by its publisher" in out
    assert "uuid==9.0.1: AFFECTED" not in out
    assert "quiet==1.0.0: AFFECTED" not in out
    assert "registry changes: 5 of 5 npm and PyPI dependencies read, 3 change(s) found" in out
    assert "3/5 dependencies affected" in out


def test_without_the_flag_nothing_is_read(tmp_path, registry):
    watchlist = _watchlist(tmp_path, _dep("uuid", "3.4.0"))
    result = _run("check", "--watchlist", watchlist, "--ledger", "")
    assert result.exit_code == 0, result.output
    assert registry.asked == []
    assert "0/1 dependencies affected" in result.output


@pytest.mark.parametrize(
    ("gate", "code"),
    [
        ((), 0),
        (("--strict",), 0),
        (("--fail-on", "action"), 0),
        (("--fail-on", "review"), 1),
        (("--fail-on", "affected"), 1),
    ],
)
def test_a_registry_change_fails_only_review_and_affected(tmp_path, registry, gate, code):
    watchlist = _watchlist(tmp_path, _dep("uuid", "3.4.0"))
    result = _run("check", "--watchlist", watchlist, "--registry-changes", "--ledger", "", *gate)
    assert result.exit_code == code, result.output


def test_what_was_not_read_is_named_and_counted(tmp_path, registry):
    watchlist = _watchlist(tmp_path, _dep("gone", "1.0.0"), _dep("serde", "1.0.0", "cargo"))
    result = _run("check", "--watchlist", watchlist, "--registry-changes", "--ledger", "")
    assert result.exit_code == 0, result.output
    assert "registry changes: 0 of 1 npm and PyPI dependencies read" in result.output
    assert "1 dependency(s) of other ecosystems not read (npm and PyPI only)" in result.output
    assert "! registry changes not fully read for gone==1.0.0" in result.output


def test_the_digest_carries_registry_changes(tmp_path, registry):
    watchlist = _watchlist(tmp_path, _dep("uuid", "3.4.0"))
    result = _run(
        "check", "--watchlist", watchlist, "--registry-changes", "--ledger", "", "--digest"
    )
    assert result.exit_code == 0, result.output
    assert "1/1 dependencies affected" in result.output


# --- attest, SARIF, the Action ---------------------------------------------------------------


def test_attest_emits_valid_contracts_and_sarif_for_registry_changes(tmp_path, registry):
    watchlist = _watchlist(tmp_path, _dep("uuid", "3.4.0"), _dep("relic", "1.0.0"))
    out, sarif = tmp_path / "c.jsonl", tmp_path / "r.sarif"
    result = _run(
        "attest",
        "--watchlist",
        watchlist,
        "--event",
        EVENT,
        "--registry-changes",
        "--output",
        str(out),
        "--sarif",
        str(sarif),
        "--fail-on",
        "review",
    )
    # Contracts are written (and schema-checked) before the gate fails.
    assert result.exit_code == 1, result.output
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    events = {d["provenance"]["event_id"] for d in docs}
    assert "evt-registry-npm_deprecated-pkg_npm_uuid-3.4.0" in events
    assert "evt-registry-license-pkg_npm_relic-1.0.0-2.0.0" in events
    rules = {
        r["ruleId"] for r in json.loads(sarif.read_text(encoding="utf-8"))["runs"][0]["results"]
    }
    assert {"openpulse/deprecation", "openpulse/license-change"} <= rules


def test_attest_without_the_flag_is_unchanged(tmp_path, registry):
    watchlist = _watchlist(tmp_path, _dep("uuid", "3.4.0"))
    out = tmp_path / "c.jsonl"
    result = _run("attest", "--watchlist", watchlist, "--event", EVENT, "--output", str(out))
    assert result.exit_code == 0, result.output
    assert len(out.read_text(encoding="utf-8").splitlines()) == 1
    assert registry.asked == []


def test_the_action_input_is_opt_in_and_passed_as_an_argument():
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert action["inputs"]["registry-changes"]["default"] == "off"
    step = next(s for s in action["runs"]["steps"] if s.get("id") == "run")
    assert step["env"]["IN_REGISTRY_CHANGES"] == "${{ inputs.registry-changes }}"
    script = step["run"]
    # Threat: script injection - the input reaches the shell only as an env var.
    assert "inputs.registry-changes" not in script
    assert "all) changes=(--registry-changes) ;;" in script
    assert "unknown registry-changes" in script
    assert '${changes[@]+"${changes[@]}"}' in script


# --- The agent tools -------------------------------------------------------------------------


def test_dependency_status_names_the_change_and_its_evidence(registry):
    out = agent_tools.dependency_status(
        "uuid", "3.4.0", "npm", lookups=Lookups(fetch=lambda slug: {}), today=TODAY
    )
    [cause] = [c for c in out["causes"] if c["type"] == "DEPRECATION"]
    assert cause["affected"] is True and cause["relationship"] == "AFFECTS_PACKAGE"
    assert cause["evidence_urls"] == ["https://www.npmjs.com/package/uuid/v/3.4.0"]
    assert out["verdict"]["affected"] is True
    [source] = [s for s in out["sources"] if s["source"] == REGISTRY_CHANGES_SOURCE]
    assert source == {"source": REGISTRY_CHANGES_SOURCE, "status": "ok", "records": 1}


def test_dependency_status_says_when_the_registry_was_not_read(registry):
    out = agent_tools.dependency_status(
        "gone", "1.0.0", "npm", lookups=Lookups(fetch=lambda slug: {}), today=TODAY
    )
    assert REGISTRY_CHANGES_SOURCE in out["not_established"]


def test_dependency_status_offline_reads_nothing(registry):
    out = agent_tools.dependency_status("uuid", "3.4.0", "npm", live=False, today=TODAY)
    assert not [c for c in out["causes"] if c["type"] == "DEPRECATION"]
    assert registry.asked == []
