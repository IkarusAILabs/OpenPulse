"""Warning deadline tests: bands, ranking, window, CLI e2e (issue #66)."""

import json
from datetime import date

from click.testing import CliRunner

from core.detections import ledger
from core.risk.check import check_dependency
from core.schema.models import OSSEvent
from core.warnings import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_OVERDUE,
    build_warnings,
    deadline_severity,
    recommended_action,
    render_warnings_md,
)


def _future_django_eol(
    effective: str = "2026-12-31",
    announced: str = "2026-09-30",
    event_id: str = "evt-django-future-eol",
):
    """Django 4.2 EOL with shifted dates so it lands inside the window."""
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = event_id
    data["title"] = "Django 4.2 LTS end of extended support"
    for e in data["evidences"]:
        e["effective_date"] = effective
        e["announcement_date"] = announced
    return OSSEvent(**data)


_WL = (
    "version: 1\n"
    "dependencies:\n"
    "  - package: django\n"
    "    ecosystem: PyPI\n"
    '    version: "4.2"\n'
    "  - ref: docker.io/bitnami/redis:7.2\n"
)


def _write_watchlist(tmp_path, deps_yaml: str) -> str:
    path = tmp_path / "watchlist.yaml"
    path.write_text(deps_yaml, encoding="utf-8")
    return str(path)


def _future_event_file(tmp_path, effective="2026-12-31", event_id="evt-django-future-eol"):
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = event_id
    for e in data["evidences"]:
        e["effective_date"] = effective
    path = tmp_path / f"{event_id}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def _django_dep():
    return {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}


class _FrozenDate(date):
    """Wall-clock stand-in pinned to 2026-10-06, the day the comment
    fixtures and pinned countdowns in this file were written against.
    The CLI tests below exercise the full command path, which has no
    `--today` flag to pass explicitly like the pure-function tests do,
    so the calendar is frozen here instead (same pattern as the
    stepped datetime in test_attestation.py). A real calendar ticking
    past 2026-10-06 shifts every countdown by one day per day and
    turns these asserts red within 24h of landing.
    """

    @classmethod
    def today(cls):
        return cls(2026, 10, 6)


def _freeze_warnings_clock(monkeypatch):
    import core.digest as digest_module

    monkeypatch.setattr(digest_module, "date", _FrozenDate)


# ---------------------------------------------------------------------------
# Pure deadline calculator (issue #66: pure-function deadline calc)
# ---------------------------------------------------------------------------


def test_deadline_severity_bands():
    """Every band boundary, both sides, plus the exact horizon edges."""
    assert deadline_severity(-30) == SEVERITY_OVERDUE
    assert deadline_severity(-1) == SEVERITY_OVERDUE
    assert deadline_severity(0) == SEVERITY_CRITICAL
    assert deadline_severity(7) == SEVERITY_CRITICAL
    assert deadline_severity(8) == SEVERITY_HIGH
    assert deadline_severity(30) == SEVERITY_HIGH
    assert deadline_severity(31) == SEVERITY_MEDIUM
    assert deadline_severity(90) == SEVERITY_MEDIUM
    assert deadline_severity(91) == SEVERITY_LOW
    assert deadline_severity(3650) == SEVERITY_LOW


def test_recommended_action_gates_on_impact():
    """Severity drives urgency, impact gates it: WATCH/INFO never becomes
    migration work however close the deadline."""
    passive = recommended_action(SEVERITY_CRITICAL, "WATCH")
    assert "No migration action" in passive
    assert passive == recommended_action(SEVERITY_OVERDUE, "INFORMATIONAL")
    assert "Act now" in recommended_action(SEVERITY_CRITICAL, "ACTION")
    assert "Deadline passed" in recommended_action(SEVERITY_OVERDUE, "ACTION")
    assert "planning cycle" in recommended_action(SEVERITY_MEDIUM, "REVIEW")


# ---------------------------------------------------------------------------
# build_warnings: the projection over the digest join
# ---------------------------------------------------------------------------


def test_warning_object_shape_matches_issue(tmp_path):
    """Every field issue #66 names is present with the right value."""
    event = _future_django_eol()
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django",
        "lifecycle",
        "EOL",
        ["4.2"],
        detected_at="2026-07-01T00:00:00+00:00",
        root=root,
    )
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings([verdict], [event], ledger_root=str(root), today=date(2026, 10, 6))
    assert len(built["warnings"]) == 1
    w = built["warnings"][0]
    assert w["project"] == "django"
    assert w["ref"] == "django==4.2"
    assert w["event_type"] == "EOL"
    assert w["effective_date"] == "2026-12-31"
    assert w["days_until_effective"] == 86
    assert w["severity"] == SEVERITY_MEDIUM
    assert w["first_detected"] == "2026-07-01"
    assert w["lead_time_days"] == 183
    assert "Plan the upgrade" in w["recommended_action"]
    assert built["window_days"] == 90
    assert built["generated_at"] == "2026-10-06"


def test_not_affected_and_related_never_become_warnings():
    """Public intelligence never implies customer impact: only affected
    verdicts for declared dependencies produce warnings."""
    event = _future_django_eol()
    deps = [
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.2"},
        {"kind": "package", "package": "flask", "ecosystem": "PyPI", "version": "3.0"},
    ]
    verdicts = [check_dependency(d, [event]) for d in deps]
    built = build_warnings(verdicts, [event], today=date(2026, 10, 6))
    assert built["warnings"] == []


def test_event_without_effective_date_yields_no_warning():
    """No evidence-declared deadline means nothing to count down to."""
    data = json.load(open("data/fixtures/django-eol/event.json"))
    for e in data["evidences"]:
        e["effective_date"] = None
    event = OSSEvent(**data)
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings([verdict], [event], today=date(2026, 10, 6))
    assert built["warnings"] == []


def _future_event(
    event_type: str,
    effective: str,
    event_id: str,
    project: str = "django",
    versions: list | None = None,
):
    """Fixture-derived event with a chosen type/date/scope."""
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = event_id
    data["event_type"] = event_type
    data["scope"] = {"kind": "version", "versions": versions or ["4.2"]}
    data["affected_versions"] = versions or ["4.2"]
    for e in data["evidences"]:
        e["effective_date"] = effective
        e["announcement_date"] = "2026-09-30"
    return OSSEvent(**data)


def test_overdue_change_keeps_its_overdue_severity(tmp_path):
    """A newly-effective change inside the lookback stays as OVERDUE -
    the digest's symmetric window keeps it, and warnings surface the
    passed deadline as its own band, first in the briefing."""
    event = _future_django_eol(effective="2026-10-01")
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django",
        "lifecycle",
        "EOL",
        ["4.2"],
        detected_at="2026-04-01T00:00:00+00:00",
        root=root,
    )
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings([verdict], [event], ledger_root=str(root), today=date(2026, 10, 6))
    assert len(built["warnings"]) == 1
    w = built["warnings"][0]
    assert w["days_until_effective"] == -5
    assert w["severity"] == SEVERITY_OVERDUE
    assert "Deadline passed" in w["recommended_action"]
    assert w["lead_time_days"] == 183


def test_ranking_soonest_effective_first():
    """The closer deadline leads the list."""
    e_far = _future_django_eol(effective="2026-12-31", event_id="evt-far")
    e_near = _future_django_eol(effective="2026-11-05", event_id="evt-near")
    deps = [
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"},
    ]
    verdicts = [check_dependency(d, [e_far, e_near]) for d in deps]
    built = build_warnings(verdicts, [e_far, e_near], today=date(2026, 10, 6))
    assert [w["days_until_effective"] for w in built["warnings"]] == [30, 86]


def test_ranking_shortest_lead_time_breaks_ties(tmp_path):
    """At equal distance, the least-warned dependency (shortest known
    lead time) ranks first; an unknown lead time sorts last. Three
    distinct lifecycle facts (EOL, DEPRECATION, SUPPORT_CHANGE) give
    three distinct ledger identities at the same deadline."""
    e_eol = _future_event("EOL", "2026-11-05", "evt-eol-early-warn")
    e_depr = _future_event("DEPRECATION", "2026-11-05", "evt-depr-late-warn")
    e_sup = _future_event("SUPPORT_CHANGE", "2026-11-05", "evt-sup-never-warn")
    root = tmp_path / "ledger"
    # EOL detected early: long lead time.
    ledger.record_detection(
        "django",
        "lifecycle",
        "EOL",
        ["4.2"],
        detected_at="2026-04-01T00:00:00+00:00",
        root=root,
    )
    # DEPRECATION detected late: short lead time, least warned.
    ledger.record_detection(
        "django",
        "lifecycle",
        "DEPRECATION",
        ["4.2"],
        detected_at="2026-11-01T00:00:00+00:00",
        root=root,
    )
    # SUPPORT_CHANGE never recorded: unknown lead time.
    deps = [{"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}]
    events = [e_eol, e_depr, e_sup]
    verdicts = [check_dependency(d, events) for d in deps]
    built = build_warnings(verdicts, events, ledger_root=str(root), today=date(2026, 10, 6))
    assert len(built["warnings"]) == 3
    assert [w["event_id"] for w in built["warnings"]] == [
        "evt-depr-late-warn",  # 4d lead - least warned, first
        "evt-eol-early-warn",  # 218d lead
        "evt-sup-never-warn",  # unknown lead, last
    ]
    leads = [w["lead_time_days"] for w in built["warnings"]]
    assert leads == [4, 218, None]


def test_window_filters_beyond_n_days():
    """--window-days bounds the countdown on both sides."""
    event = _future_django_eol(effective="2026-12-31")
    verdict = check_dependency(_django_dep(), [event])
    in_window = build_warnings([verdict], [event], today=date(2026, 10, 6), window_days=90)
    out_window = build_warnings([verdict], [event], today=date(2026, 10, 6), window_days=30)
    assert len(in_window["warnings"]) == 1
    assert out_window["warnings"] == []
    assert out_window["window_days"] == 30


def test_window_edge_today_is_included():
    """A change effective exactly today is the most urgent line."""
    event = _future_django_eol(effective="2026-10-06")
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings([verdict], [event], today=date(2026, 10, 6))
    assert built["warnings"][0]["days_until_effective"] == 0
    assert built["warnings"][0]["severity"] == SEVERITY_CRITICAL


def test_no_ledger_record_means_no_lead_time_claim(tmp_path):
    """Absent detection -> no lead time, and the entry still renders."""
    event = _future_django_eol()
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings(
        [verdict], [event], ledger_root=str(tmp_path / "nope"), today=date(2026, 10, 6)
    )
    w = built["warnings"][0]
    assert w["first_detected"] is None
    assert w["lead_time_days"] is None
    assert "no first-detection record" in render_warnings_md(built)


def test_ledger_disabled_makes_no_claims():
    """ledger_root=None (the CLI's --ledger '') means no claims."""
    event = _future_django_eol()
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    assert built["warnings"][0]["first_detected"] is None


def test_security_causes_have_no_deadline_to_count(tmp_path, monkeypatch):
    """Security findings carry CVE fixes, not effective dates - the
    digest excludes them from deadlines and so do warnings."""

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    (bundle_dir / "django.json").write_text(
        json.dumps(
            {
                "osv": [
                    {
                        "id": "GHSA-test-django",
                        "summary": "django 4.2 RCE",
                        "affected": [
                            {
                                "package": {"ecosystem": "PyPI", "name": "django"},
                                "ranges": [
                                    {"type": "ECOSYSTEM", "events": [{"introduced": "4.2"}]}
                                ],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    from pathlib import Path

    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    event = _future_django_eol()
    dep = _django_dep()
    bundle = json.load(open(bundle_dir / "django.json"))
    verdict = check_dependency(dep, [event], {"django": bundle})
    built = build_warnings([verdict], [event], today=date(2026, 10, 6))
    # The lifecycle warning stands; the security cause contributed no
    # deadline (its event-less finding has no effective-date evidence).
    assert all(w["event_type"] != "vulnerability" for w in built["warnings"])


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def test_render_bands_and_rows(tmp_path):
    """Each present band gets its own table; OVERDUE leads; the counts
    line names every present band."""
    e_overdue = _future_event("EOL", "2026-10-01", "evt-overdue")
    e_critical = _future_event("DEPRECATION", "2026-10-10", "evt-crit")
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django",
        "lifecycle",
        "EOL",
        ["4.2"],
        detected_at="2026-04-01T00:00:00+00:00",
        root=root,
    )
    deps = [{"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}]
    events = [e_overdue, e_critical]
    verdicts = [check_dependency(d, events) for d in deps]
    built = build_warnings(verdicts, events, ledger_root=str(root), today=date(2026, 10, 6))
    md = render_warnings_md(built)
    assert "# OpenPulse warning deadlines" in md
    assert "## OVERDUE - passed deadlines (1)" in md
    assert "## CRITICAL - effective within 7 days (1)" in md
    assert "| django | django==4.2 | EOL | 2026-10-01 | 5d ago |" in md
    assert "2 warning(s): 1 overdue, 1 critical." in md
    assert "no claim is made" in md
    # Band order in the output follows SEVERITY_ORDER.
    assert md.index("OVERDUE") < md.index("CRITICAL")


def test_render_empty_is_clean_not_error():
    built = {"generated_at": "2026-10-06", "window_days": 90, "warnings": []}
    md = render_warnings_md(built)
    assert "No warning deadlines within the 90-day window." in md
    assert "openpulse check" in md


def test_render_overdue_band_label():
    """Renderer labels negative countdowns as time past, not distance."""
    event = _future_django_eol(effective="2026-09-06")
    verdict = check_dependency(_django_dep(), [event])
    built = build_warnings([verdict], [event], today=date(2026, 10, 6))
    md = render_warnings_md(built)
    assert "| 30d ago |" in md


# ---------------------------------------------------------------------------
# CLI end to end (issue #66: `openpulse warnings`)
# ---------------------------------------------------------------------------


def test_cli_warnings_end_to_end_two_runs(tmp_path, monkeypatch):
    """Acceptance: check records the detection; warnings, run later,
    reports the ORIGINAL first-seen date with a countdown and a band."""
    from cli.main import cli

    _freeze_warnings_clock(monkeypatch)

    watchlist = _write_watchlist(tmp_path, _WL)
    event_file = _future_event_file(tmp_path)
    ledger_root = tmp_path / "ledger"

    monkeypatch.setattr("core.detections.ledger.now_iso", lambda: "2026-07-01T00:00:00+00:00")
    check_run = CliRunner().invoke(
        cli,
        [
            "check",
            "--watchlist",
            watchlist,
            "--event",
            event_file,
            "--ledger",
            str(ledger_root),
        ],
    )
    assert check_run.exit_code == 0, check_run.output
    assert "first detected 2026-07-01" in check_run.output

    out = CliRunner().invoke(
        cli,
        [
            "warnings",
            "--watchlist",
            watchlist,
            "--event",
            event_file,
            "--ledger",
            str(ledger_root),
        ],
    )
    assert out.exit_code == 0, out.output
    assert "django==4.2" in out.output
    assert "first detected 2026-07-01" in out.output
    assert "EOL" in out.output
    # Effective 2026-12-31 vs today 2026-10-06: 86 days, MEDIUM band.
    assert "2026-12-31" in out.output
    assert "MEDIUM" in out.output


def test_cli_warnings_json_output(tmp_path, monkeypatch):
    from cli.main import cli

    _freeze_warnings_clock(monkeypatch)
    watchlist = _write_watchlist(tmp_path, _WL)
    event_file = _future_event_file(tmp_path)
    out = CliRunner().invoke(
        cli,
        [
            "warnings",
            "--watchlist",
            watchlist,
            "--event",
            event_file,
            "--ledger",
            str(tmp_path / "ledger"),
            "--output",
            "json",
        ],
    )
    assert out.exit_code == 0, out.output
    payload = json.loads(out.output)
    assert payload["warnings"][0]["ref"] == "django==4.2"
    assert payload["warnings"][0]["severity"] == "MEDIUM"
    assert payload["warnings"][0]["days_until_effective"] == 86
    assert payload["window_days"] == 90


def test_cli_warnings_needs_an_event(tmp_path):
    from cli.main import cli

    watchlist = _write_watchlist(tmp_path, _WL)
    out = CliRunner().invoke(cli, ["warnings", "--watchlist", watchlist])
    assert out.exit_code != 0
    assert "needs at least one --event" in out.output


def test_cli_warnings_empty_result_renders_clean(tmp_path):
    """No affected deps -> clean empty output, not an error."""
    from cli.main import cli

    watchlist = _write_watchlist(
        tmp_path,
        'version: 1\ndependencies:\n  - package: flask\n    ecosystem: PyPI\n    version: "3.0"\n',
    )
    event_file = _future_event_file(tmp_path)
    out = CliRunner().invoke(cli, ["warnings", "--watchlist", watchlist, "--event", event_file])
    assert out.exit_code == 0, out.output
    assert "No warning deadlines within the 90-day window." in out.output


def test_cli_warnings_composable_with_images(tmp_path, monkeypatch):
    """--images is one of the composable inputs: image refs get
    deadlines through artifact matching."""
    from cli.main import cli

    _freeze_warnings_clock(monkeypatch)

    event = json.load(open("data/fixtures/bitnami/event.json"))
    # Shift the effective date inside the window so the countdown is
    # exercised (the real 2025-08-28 date sits far in the past).
    for e in event["evidences"]:
        e["effective_date"] = "2026-11-15"
    event_file = tmp_path / "bitnami.json"
    event_file.write_text(json.dumps(event), encoding="utf-8")
    images_file = tmp_path / "images.txt"
    images_file.write_text(
        "docker.io/bitnami/redis:7.2\ndocker.io/library/redis:7.2\n",
        encoding="utf-8",
    )
    out = CliRunner().invoke(
        cli, ["warnings", "--images", str(images_file), "--event", str(event_file)]
    )
    assert out.exit_code == 0, out.output
    assert "docker.io/bitnami/redis:7.2" in out.output
    assert "2026-11-15" in out.output
    assert "in 40d" in out.output
    assert "MEDIUM" in out.output  # 40 days: inside the 31-90 band


def test_cli_warnings_window_days_flag(tmp_path, monkeypatch):
    from cli.main import cli

    _freeze_warnings_clock(monkeypatch)

    watchlist = _write_watchlist(tmp_path, _WL)
    event_file = _future_event_file(tmp_path, effective="2026-12-31")
    wide = CliRunner().invoke(
        cli,
        [
            "warnings",
            "--watchlist",
            watchlist,
            "--event",
            event_file,
            "--window-days",
            "30",
        ],
    )
    assert wide.exit_code == 0, wide.output
    assert "No warning deadlines within the 30-day window." in wide.output


# ---------------------------------------------------------------------------
# Lead-time case studies (docs/LEAD_TIME_CASES.md) - pinned, replayable
# ---------------------------------------------------------------------------

#: Live-verified 2026-10-06 via https://endoflife.date/api/{postgresql,redis}.json
#: and the official versioning pages (see LEAD_TIME_CASES.md Cases 2 and 3).
_PG14_CYCLE = {
    "collector": "endoflife",
    "product": "postgresql",
    "cycle": "14",
    "eol": "2026-11-12",
    "latest": "14.24",
    "latestReleaseDate": "2026-08-10",
    "releaseDate": "2021-09-30",
}

_REDIS80_CYCLE = {
    "collector": "endoflife",
    "product": "redis",
    "cycle": "8.0",
    "eol": "2026-12-01",
    "latest": "8.0.6",
    "latestReleaseDate": "2026-02-22",
    "releaseDate": "2025-05-02",
    "support": "2025-08-04",
}


def _warnings_for_cycle(cycle_entry, dep, today, detected_at=None, ledger_root=None):
    """Producer pipeline end to end: live cycle entry -> UPCOMING finding
    -> bridged event -> check verdict -> warning deadline."""
    from analyzers.change_analyst import analyze_endoflife
    from analyzers.lifecycle_events import finding_to_event
    from core.risk.check import check_dependency

    findings = [
        f
        for f in analyze_endoflife([cycle_entry], today=today)
        if f["lifecycle_state"] == "UPCOMING" and f["event_type"] == "EOL"
    ]
    assert findings, "producer pipeline must fire the UPCOMING EOL finding"
    event = finding_to_event(findings[0], cycle_entry["product"], today=today)
    verdict = check_dependency(dep, [event])
    return build_warnings([verdict], [event], ledger_root=ledger_root, today=today), event


def test_case_postgresql_14_lead_time(tmp_path):
    """LEAD_TIME_CASES.md Case 2, replayed: PostgreSQL 14 EOL detected
    2026-10-06, 37 days before its 2026-11-12 effective date."""
    today = date(2026, 10, 6)
    root = tmp_path / "ledger"
    # The ledger records the first detection on the day it ran.
    ledger.record_detection(
        "postgresql",
        "lifecycle",
        "EOL",
        ["14"],
        detected_at="2026-10-06T00:00:00+00:00",
        root=root,
    )
    dep = {"kind": "image", "ref": "docker.io/postgres:14"}
    built, event = _warnings_for_cycle(_PG14_CYCLE, dep, today, ledger_root=str(root))
    assert len(built["warnings"]) == 1
    w = built["warnings"][0]
    assert w["project"] == "postgresql"
    assert w["ref"] == "docker.io/postgres:14"
    assert w["effective_date"] == "2026-11-12"
    assert w["days_until_effective"] == 37
    assert w["severity"] == SEVERITY_MEDIUM  # 31-90 days: one planning cycle
    assert w["first_detected"] == "2026-10-06"
    assert w["lead_time_days"] == 37


def test_case_redis_80_lead_time(tmp_path):
    """LEAD_TIME_CASES.md Case 3, replayed: Redis 8.0 EOL detected
    2026-10-06, 56 days before its 2026-12-01 effective date."""
    today = date(2026, 10, 6)
    root = tmp_path / "ledger"
    ledger.record_detection(
        "redis",
        "lifecycle",
        "EOL",
        ["8.0"],
        detected_at="2026-10-06T00:00:00+00:00",
        root=root,
    )
    dep = {"kind": "package", "package": "redis", "ecosystem": "generic", "version": "8.0"}
    built, event = _warnings_for_cycle(_REDIS80_CYCLE, dep, today, ledger_root=str(root))
    assert len(built["warnings"]) == 1
    w = built["warnings"][0]
    assert w["project"] == "redis"
    assert w["ref"] == "redis==8.0"
    assert w["effective_date"] == "2026-12-01"
    assert w["days_until_effective"] == 56
    assert w["severity"] == SEVERITY_MEDIUM
    assert w["first_detected"] == "2026-10-06"
    assert w["lead_time_days"] == 56


def test_case_pg14_outside_180d_horizon_fires_nothing():
    """The producer gate is honest: a cycle ending beyond EOL_WARN_DAYS
    (180) yields no finding, so no warning can be manufactured for it."""
    today = date(2026, 10, 6)
    far = dict(_PG14_CYCLE, cycle="18", eol="2030-11-14")
    from analyzers.change_analyst import analyze_endoflife

    findings = [
        f for f in analyze_endoflife([far], today=today) if f["lifecycle_state"] == "UPCOMING"
    ]
    assert findings == []
