"""Only what is new (v0.21.0 item W4).

Exit criterion: a run records its detections in the ledger and says which
ones the ledger had not seen. A first run is a starting point, not a list
of news. A registry or repository change is remembered under its own
class, so it is reported once and never given a lead time. ``check
--new-only`` lists only the new ones while every gate still covers all of
them; ``attest --ledger --new-findings`` writes them for the Action.
"""

from __future__ import annotations

import base64
import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from analyzers.registry_events import registry_finding_to_event
from cli.main import cli
from core.detections import ledger
from core.digest import build_digest
from core.history_key import keyring, parse_key
from core.new_detections import ledger_is_empty, record_new_detections, render_new_md
from core.risk.check import check_dependency
from core.schema.models import OSSEvent

ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")
DJANGO_EOL = OSSEvent(**json.loads(Path(EVENT).read_text(encoding="utf-8")))
KEY = parse_key(base64.b64encode(b"a" * 32).decode())
TODAY = date.today()
NPM = "https://registry.npmjs.org/"


def _dep(name, version, ecosystem="npm"):
    return {"kind": "package", "package": name, "version": version, "ecosystem": ecosystem}


def _deprecation_event(name, version=None):
    """A registry deprecation event for one dependency, as W1 builds it."""
    level = "version" if version else "package"
    finding = {
        "event_type": "DEPRECATION",
        "title": f"{name} is deprecated by its publisher",
        "summary": "The publisher deprecated it.",
        "confidence": "CONFIRMED",
        "affected_versions": [version] if version else ["*"],
        "references": [f"https://www.npmjs.com/package/{name}"],
        "registry_evidence": {
            "source": "registry.npmjs.org",
            "package": f"pkg:npm/{name}",
            "flag": "npm_deprecated",
            "level": level,
            "version": version,
        },
    }
    return registry_finding_to_event(finding, name, today=TODAY)


def _verdicts(pairs):
    """[(dep, [events])] -> (verdicts, every event)."""
    verdicts = [check_dependency(dep, events) for dep, events in pairs]
    return verdicts, [e for _, events in pairs for e in events]


def _record(tmp_path, pairs, key=KEY):
    verdicts, events = _verdicts(pairs)
    return record_new_detections(
        verdicts, events, ledger_root=tmp_path / "detections", history_key=key
    )


OLD = (_dep("oldpkg", "1.0.0"), [_deprecation_event("oldpkg")])
UUID = (_dep("uuid", "3.4.0"), [_deprecation_event("uuid", "3.4.0")])


# --- Recording and what is new -------------------------------------------------------------


def test_a_first_run_is_a_starting_point(tmp_path):
    assert ledger_is_empty(tmp_path / "detections")
    report = _record(tmp_path, [OLD])
    assert report["baseline"] is True
    assert (report["facts"], report["new_facts"]) == (1, 1)
    assert not ledger_is_empty(tmp_path / "detections")


def test_a_second_run_reports_only_what_the_ledger_had_not_seen(tmp_path):
    _record(tmp_path, [OLD])
    same = _record(tmp_path, [OLD])
    assert same["baseline"] is False and same["new"] == [] and same["facts"] == 1
    grown = _record(tmp_path, [OLD, UUID])
    assert (grown["facts"], grown["new_facts"]) == (2, 1)
    [item] = grown["new"]
    assert item["dependency"] == "uuid==3.4.0"
    assert item["event_type"] == "DEPRECATION" and item["finding_class"] == ledger.CHANGE
    assert item["title"] == "uuid is deprecated by its publisher"
    assert item["evidence_urls"] == ["https://www.npmjs.com/package/uuid"]
    assert item["impact"] == "REVIEW"


def test_first_seen_is_given_only_under_a_history_key(tmp_path):
    keyed = _record(tmp_path / "a", [OLD])
    unkeyed = _record(tmp_path / "b", [OLD], key=None)
    assert keyed["new"][0]["first_seen"].startswith(str(TODAY)[:4])
    assert unkeyed["new"][0]["first_seen"] is None


def test_a_fact_shared_by_two_dependencies_is_one_fact_reported_for_both(tmp_path):
    pairs = [
        (_dep("django", "4.2.1", "PyPI"), [DJANGO_EOL]),
        (_dep("django", "4.2.5", "PyPI"), [DJANGO_EOL]),
    ]
    report = _record(tmp_path, pairs)
    assert (report["facts"], report["new_facts"]) == (1, 1)
    assert [i["dependency"] for i in report["new"]] == ["django==4.2.1", "django==4.2.5"]
    assert {i["finding_class"] for i in report["new"]} == {ledger.LIFECYCLE}


def test_a_dependency_with_nothing_durable_adds_no_fact(tmp_path):
    report = _record(tmp_path, [(_dep("quiet", "1.0.0"), [])])
    assert report == {"baseline": True, "new": [], "facts": 0, "new_facts": 0}


def test_a_registry_change_never_gets_a_lead_time(tmp_path):
    """C5 holds through the ledger: remembered, but not a lifecycle claim."""
    finding = {
        "event_type": "LICENSE_CHANGE",
        "title": "relic changed its license",
        "summary": "x",
        "confidence": "EMERGING",
        "effective_at": f"{TODAY.isoformat()}T00:00:00Z",
        "references": ["https://www.npmjs.com/package/relic"],
        "registry_evidence": {
            "source": "registry.npmjs.org",
            "package": "pkg:npm/relic",
            "from_version": "1.0.0",
            "to_version": "2.0.0",
        },
    }
    event = registry_finding_to_event(finding, "relic", today=TODAY)
    verdicts, events = _verdicts([(_dep("relic", "1.0.0"), [event])])
    root = tmp_path / "detections"
    record_new_detections(verdicts, events, ledger_root=root, history_key=KEY)
    digest = build_digest(
        verdicts, events, ledger_root=str(root), today=TODAY, history_keys=keyring(KEY)
    )
    [entry] = digest["entries"]
    assert entry["first_detected"] is None and entry["lead_time_days"] is None


def test_the_summary_section_escapes_upstream_text():
    report = {
        "baseline": False,
        "facts": 2,
        "new_facts": 1,
        "new": [
            {
                "dependency": "a|b==1",
                "event_type": "DEPRECATION",
                "title": "bad | title\nsecond line",
                "impact": "REVIEW",
                "evidence_urls": ["https://example.org/x"],
            }
        ],
    }
    text = render_new_md(report)
    assert "### New since the last run" in text and "1 new of 2 detection(s)." in text
    assert "a\\|b==1" in text and "bad \\| title second line" in text
    assert "First run" in render_new_md({**report, "baseline": True})
    assert "Nothing new" in render_new_md({**report, "new": []})


# --- check ------------------------------------------------------------------------------------

REGISTRY = {
    NPM + "oldpkg/latest": {"name": "oldpkg", "version": "1.0.0", "deprecated": "use newpkg"},
    NPM + "uuid/latest": {"name": "uuid", "version": "14.0.3"},
    NPM + "uuid/3.4.0": {"name": "uuid", "version": "3.4.0", "deprecated": "old line"},
}


@pytest.fixture
def registry(monkeypatch):
    def fetch(url):
        return (200, json.loads(json.dumps(REGISTRY[url]))) if url in REGISTRY else (0, None)

    monkeypatch.setattr("core.digest_integrity.default_fetch", fetch)
    monkeypatch.delenv("OPENPULSE_HISTORY_KEY", raising=False)


def _watchlist(tmp_path, *deps):
    path = tmp_path / "watchlist.yml"
    path.write_text(yaml.safe_dump({"dependencies": list(deps)}), encoding="utf-8")
    return str(path)


def _check(tmp_path, deps, *extra):
    args = ["check", "--watchlist", _watchlist(tmp_path, *deps), "--registry-changes"]
    if "--no-ledger" in extra:
        extra = tuple(a for a in extra if a != "--no-ledger")
        args += ["--ledger", ""]
    else:
        args += ["--ledger", str(tmp_path / "detections")]
    return CliRunner().invoke(cli, [*args, *extra])


def test_check_says_what_is_new_run_after_run(tmp_path, registry):
    first = _check(tmp_path, [OLD[0]])
    assert first.exit_code == 0, first.output
    assert "first run with this ledger: 1 detection(s) recorded" in first.output

    second = _check(tmp_path, [OLD[0]])
    assert "new since the last run: none (1 detection(s) already known)" in second.output

    third = _check(tmp_path, [OLD[0], UUID[0]])
    assert "new since the last run: 1 of 2 detection(s)" in third.output
    assert "  + uuid==3.4.0: uuid 3.4.0 (npm) is deprecated by its publisher [REVIEW]" in (
        third.output
    )


def test_new_only_lists_the_new_and_still_gates_on_everything(tmp_path, registry):
    _check(tmp_path, [OLD[0]])
    result = _check(tmp_path, [OLD[0], UUID[0]], "--new-only")
    assert result.exit_code == 0, result.output
    assert "uuid==3.4.0: AFFECTED" in result.output
    assert "oldpkg==1.0.0: AFFECTED" not in result.output
    assert "2/2 dependencies affected" in result.output  # the count covers every dependency

    # Nothing is new now, but the known deprecations still fail a review gate.
    quiet = _check(tmp_path, [OLD[0], UUID[0]], "--new-only", "--fail-on", "review")
    assert quiet.exit_code == 1
    assert "AFFECTED" not in quiet.output.replace("dependencies affected", "")


def test_new_only_needs_the_ledger(tmp_path, registry):
    result = _check(tmp_path, [OLD[0]], "--no-ledger", "--new-only")
    assert result.exit_code != 0 and "--new-only needs the ledger" in result.output


def test_without_a_ledger_nothing_is_said_about_new(tmp_path, registry):
    result = _check(tmp_path, [OLD[0]], "--no-ledger")
    assert result.exit_code == 0, result.output
    assert "new since" not in result.output and "first run" not in result.output


# --- attest and the Action ---------------------------------------------------------------------


def _attest(tmp_path, deps, *extra):
    args = [
        "attest",
        "--watchlist",
        _watchlist(tmp_path, *deps),
        "--event",
        EVENT,
        "--registry-changes",
        "--output",
        str(tmp_path / "c.jsonl"),
        "--sarif",
        str(tmp_path / "r.sarif"),
        "--summary",
        str(tmp_path / "s.md"),
        *extra,
    ]
    return CliRunner().invoke(cli, args)


def test_attest_records_and_writes_the_new_findings(tmp_path, registry):
    led, new = str(tmp_path / "detections"), tmp_path / "new.json"
    first = _attest(tmp_path, [OLD[0]], "--ledger", led, "--new-findings", str(new))
    assert first.exit_code == 0, first.output
    assert json.loads(new.read_text(encoding="utf-8"))["baseline"] is True
    assert "First run with this history" in (tmp_path / "s.md").read_text(encoding="utf-8")

    second = _attest(tmp_path, [OLD[0], UUID[0]], "--ledger", led, "--new-findings", str(new))
    assert second.exit_code == 0, second.output
    payload = json.loads(new.read_text(encoding="utf-8"))
    assert payload["recorded"] is True and payload["new_facts"] == 1
    assert [i["dependency"] for i in payload["new"]] == ["uuid==3.4.0"]
    summary = (tmp_path / "s.md").read_text(encoding="utf-8")
    assert "1 new of 2 detection(s)." in summary
    assert "| `uuid==3.4.0` | DEPRECATION |" in summary


def test_attest_records_before_a_failed_gate(tmp_path, registry):
    led, new = str(tmp_path / "detections"), tmp_path / "new.json"
    result = _attest(
        tmp_path, [OLD[0]], "--ledger", led, "--new-findings", str(new), "--fail-on", "review"
    )
    assert result.exit_code == 1
    assert json.loads(new.read_text(encoding="utf-8"))["new_facts"] == 1


def test_attest_without_a_ledger_keeps_none(tmp_path, registry, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = _attest(tmp_path, [OLD[0]])
    assert result.exit_code == 0, result.output
    assert not (tmp_path / ".openpulse").exists()
    assert "New since the last run" not in (tmp_path / "s.md").read_text(encoding="utf-8")
    refused = _attest(tmp_path, [OLD[0]], "--new-findings", str(tmp_path / "n.json"))
    assert refused.exit_code != 0 and "--new-findings needs --ledger" in refused.output


def test_the_action_records_only_with_a_kept_history():
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert set(action["outputs"]) >= {"new-findings", "new-findings-file"}
    script = next(s for s in action["runs"]["steps"] if s.get("id") == "run")["run"]
    guarded = script.split('if [ "$HISTORY_ENABLED" = "true" ]; then')[1]
    guarded = guarded.split("gate=()")[0]
    assert 'ledger=(--ledger .openpulse/detections --new-findings "$new_file")' in guarded
    assert script.count("--ledger .openpulse/detections") == 1
    assert '${ledger[@]+"${ledger[@]}"}' in script


def test_a_run_that_finds_nothing_still_ends_the_first_run(tmp_path):
    """A project that begins clean: its first finding later is news, not a starting point."""
    root = tmp_path / "detections"
    clean = record_new_detections([], [], ledger_root=root, history_key=KEY)
    assert clean == {"baseline": True, "new": [], "facts": 0, "new_facts": 0}
    assert not ledger_is_empty(root)

    report = _record(tmp_path, [OLD])
    assert report["baseline"] is False and report["new_facts"] == 1
