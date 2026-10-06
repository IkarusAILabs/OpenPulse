"""Alert digest tests: builder, ranking, window, CLI e2e (issue #63)."""

import json
from datetime import date

import pytest
from click.testing import CliRunner

from core.detections import ledger
from core.digest import (
    build_digest,
    render_digest_md,
)
from core.risk.check import check_dependency, check_watchlist
from core.schema.models import OSSEvent


@pytest.fixture(scope="module")
def django_eol():
    return OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))


@pytest.fixture(scope="module")
def bitnami_event():
    return OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))


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


def _write_watchlist(tmp_path, deps_yaml: str) -> str:
    path = tmp_path / "watchlist.yaml"
    path.write_text(f"version: 1\ndependencies:\n{deps_yaml}", encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Builder: entries only with customer evidence + a real deadline
# ---------------------------------------------------------------------------


def test_affected_dependency_with_ledger_gets_deadline_and_lead_time(tmp_path):
    event = _future_django_eol()
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], detected_at="2026-07-01T00:00:00+00:00", root=root
    )
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=str(root), today=date(2026, 10, 6))
    assert len(digest["entries"]) == 1
    entry = digest["entries"][0]
    assert entry["dependency"] == "django==4.2"
    assert entry["event_id"] == "evt-django-future-eol"
    assert entry["effective_date"] == "2026-12-31"
    assert entry["days_until_effective"] == 86
    assert entry["first_detected"] == "2026-07-01"
    assert entry["lead_time_days"] == 183
    assert entry["impact"] == "ACTION"
    assert entry["advice"] == "Schedule the upgrade before the effective date."


def test_not_affected_and_related_never_appear(django_eol):
    """Public intelligence never implies customer impact: only impact-asserting
    verdicts for declared dependencies make it into the digest."""
    event = _future_django_eol()
    deps = [
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.2"},
        {"kind": "image", "ref": "docker.io/redis:7.2"},
    ]
    verdicts = check_watchlist(deps, [event])
    digest = build_digest(verdicts, [event], ledger_root=None, today=date(2026, 10, 6))
    assert digest["entries"] == []


def test_event_without_effective_date_has_no_deadline():
    """No evidence-declared effective date -> nothing to count down to;
    the dependency stays in `check` output, out of the digest."""
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = "evt-django-undated"
    for e in data["evidences"]:
        e["effective_date"] = None
    event = OSSEvent(**data)
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    assert digest["entries"] == []


def test_aged_out_history_is_outside_the_lookback():
    """The 159-day-old django EOL is newly-effective only for a while: past
    the window's lookback it is history the monthly report narrates, not a
    deadline a customer can still act on."""
    event = _as_event(json.load(open("data/fixtures/django-eol/event.json")))
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    assert digest["entries"] == []
    wide = build_digest(
        [verdict], [event], ledger_root=None, today=date(2026, 10, 6), window_days=300
    )
    # 159 days past effective still counts as newly-effective at 300.
    entry = wide["entries"][0]
    assert entry["days_until_effective"] == -159
    md = render_digest_md(wide)
    assert "effective 159 days ago - OVERDUE" in md


def test_newly_effective_change_is_in_the_digest():
    """The issue says "upcoming and newly-effective": a change that became
    effective 5 days ago is the digest's most urgent line, not dropped the
    day it crossed zero. Negative days_until_effective, OVERDUE render."""
    event = _future_django_eol(effective="2026-10-01")  # 5 days ago
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    assert len(digest["entries"]) == 1
    entry = digest["entries"][0]
    assert entry["days_until_effective"] == -5
    md = render_digest_md(digest)
    assert "effective 5 days ago - OVERDUE" in md


def test_overdue_sorts_before_upcoming():
    """Most overdue first: the entry whose deadline already passed leads
    the briefing over one still counting down."""
    overdue = _future_django_eol(effective="2026-10-01", event_id="evt-django-overdue")
    upcoming = _future_django_eol(effective="2026-12-01", event_id="evt-django-upcoming")
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdicts = [check_dependency(dep, [overdue, upcoming])]
    digest = build_digest(verdicts, [overdue, upcoming], ledger_root=None, today=date(2026, 10, 6))
    assert [e["event_id"] for e in digest["entries"]] == [
        "evt-django-overdue",
        "evt-django-upcoming",
    ]


def _as_event(data):
    return OSSEvent(**data)


# ---------------------------------------------------------------------------
# Ranking and window semantics
# ---------------------------------------------------------------------------


def test_ranking_soonest_deadline_first():
    event_a = _future_django_eol(effective="2026-12-01")
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = "evt-django-later"
    for e in data["evidences"]:
        e["effective_date"] = "2026-12-20"
    event_b = OSSEvent(**data)
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdicts = [check_dependency(dep, [event_a, event_b])]
    digest = build_digest(verdicts, [event_a, event_b], ledger_root=None, today=date(2026, 10, 6))
    assert [e["effective_date"] for e in digest["entries"]] == ["2026-12-01", "2026-12-20"]
    assert [e["days_until_effective"] for e in digest["entries"]] == [56, 75]


def test_window_excludes_beyond_n_days():
    event = _future_django_eol(effective="2027-06-01")  # 238 days out
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    today = date(2026, 10, 6)
    assert build_digest([verdict], [event], ledger_root=None, today=today)["entries"] == []
    wide = build_digest([verdict], [event], ledger_root=None, today=today, window_days=300)
    assert len(wide["entries"]) == 1


def test_window_edge_today_is_included():
    event = _future_django_eol(effective="2026-10-06")  # effective today
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    assert len(digest["entries"]) == 1
    assert digest["entries"][0]["days_until_effective"] == 0


# ---------------------------------------------------------------------------
# Ledger semantics: no record -> no claim; tampered -> no claim
# ---------------------------------------------------------------------------


def test_no_ledger_record_means_no_lead_time_claim(tmp_path):
    event = _future_django_eol()
    root = tmp_path / "ledger"  # never written
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=str(root), today=date(2026, 10, 6))
    entry = digest["entries"][0]
    assert entry["first_detected"] is None
    assert entry["lead_time_days"] is None
    md = render_digest_md(digest)
    assert "no first-detection record in the ledger" in md


def test_tampered_ledger_entry_degrades_to_no_claim(tmp_path):
    event = _future_django_eol()
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], detected_at="2026-07-01T00:00:00+00:00", root=root
    )
    entry_path = root / "django" / f"{ledger.fact_key('django', 'lifecycle', 'EOL', ['4.2'])}.json"
    entry = json.loads(entry_path.read_text(encoding="utf-8"))
    entry["first_seen"] = "2025-01-01T00:00:00+00:00"
    entry_path.write_text(json.dumps(entry), encoding="utf-8")
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=str(root), today=date(2026, 10, 6))
    entry_out = digest["entries"][0]
    assert entry_out["first_detected"] is None
    assert entry_out["lead_time_days"] is None


def test_ledger_root_none_disables_first_detection_claims():
    event = _future_django_eol()
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    assert digest["entries"][0]["first_detected"] is None


def test_earliest_detection_survives_across_events(tmp_path):
    event_a = _future_django_eol(effective="2026-12-31")
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = "evt-django-same-fact-different-source"
    for e in data["evidences"]:
        e["effective_date"] = "2026-12-31"
    event_b = OSSEvent(**data)
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], detected_at="2026-06-15T00:00:00+00:00", root=root
    )
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdicts = [check_dependency(dep, [event_a, event_b])]
    digest = build_digest(
        verdicts, [event_a, event_b], ledger_root=str(root), today=date(2026, 10, 6)
    )
    assert len(digest["entries"]) == 2
    for entry in digest["entries"]:
        assert entry["first_detected"] == "2026-06-15"


# ---------------------------------------------------------------------------
# Security causes: no event join, no deadline, excluded by design
# ---------------------------------------------------------------------------


def test_security_cause_is_excluded_no_event_deadline(django_eol):
    bundle = {
        "django": {
            "osv": [
                {
                    "collector": "osv",
                    "package": "django",
                    "ecosystem": "PyPI",
                    "id": "CVE-2026-0100",
                    "severity": [{"score": 8.0}],
                    "affected": [
                        {
                            "package": "django",
                            "ecosystem": "PyPI",
                            "ranges": [
                                {
                                    "type": "ECOSYSTEM",
                                    "events": [{"introduced": "0"}, {"fixed": "5.1.1"}],
                                }
                            ],
                            "fixed": ["5.1.1"],
                            "versions": [],
                        }
                    ],
                    "references": [],
                }
            ]
        }
    }
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [django_eol], bundle)
    assert verdict.affected  # the CVE does affect 4.2
    digest = build_digest([verdict], [django_eol], ledger_root=None, today=date(2026, 10, 6))
    assert digest["entries"] == []


# ---------------------------------------------------------------------------
# Rendering: bands, empty digest, counts
# ---------------------------------------------------------------------------


def test_render_bands_and_lines(tmp_path):
    event = _future_django_eol()
    root = tmp_path / "ledger"
    ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], detected_at="2026-07-01T00:00:00+00:00", root=root
    )
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=str(root), today=date(2026, 10, 6))
    md = render_digest_md(digest)
    assert "## Act this cycle" in md
    assert "**django==4.2**" in md
    assert "effective in 86 days" in md
    assert "lead time 183 days (first detected 2026-07-01)" in md
    assert "1 action / 0 watch entries" in md


def test_render_watch_band_for_lower_impact():
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = "evt-django-watch-level"
    data["impact"] = "WATCH"
    for e in data["evidences"]:
        e["effective_date"] = "2026-12-31"
    event = OSSEvent(**data)
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [event])
    digest = build_digest([verdict], [event], ledger_root=None, today=date(2026, 10, 6))
    md = render_digest_md(digest)
    assert "## Watch (no confirmed deadline)" in md
    assert "0 action / 1 watch entries" in md


def test_empty_digest_renders_clean_message():
    md = render_digest_md({"generated_at": "2026-10-06", "entries": []})
    assert "Nothing upcoming or newly-effective within the warning window." in md
    assert "Act this cycle" not in md


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------

_WL = (
    "version: 1\n"
    "dependencies:\n"
    "  - package: django\n"
    "    ecosystem: PyPI\n"
    '    version: "4.2"\n'
    "  - ref: docker.io/bitnami/redis:7.2\n"
)


def _future_event_file(tmp_path, effective="2026-12-31", event_id="evt-django-future-eol"):
    data = json.load(open("data/fixtures/django-eol/event.json"))
    data["id"] = event_id
    for e in data["evidences"]:
        e["effective_date"] = effective
    path = tmp_path / f"{event_id}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_cli_digest_end_to_end_two_runs(tmp_path, monkeypatch):
    """Acceptance: check records the detection; digest, run later, reports
    the ORIGINAL first-seen date with a countdown from today."""
    from cli.main import cli

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
            "digest",
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
    # Countdown moves with today, first detection never does.
    assert "first detected 2026-07-01" in out.output


def test_cli_digest_json_output(tmp_path):
    from cli.main import cli

    watchlist = _write_watchlist(tmp_path, _WL)
    event_file = _future_event_file(tmp_path)
    out = CliRunner().invoke(
        cli,
        [
            "digest",
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
    assert payload["entries"][0]["dependency"] == "django==4.2"
    assert payload["entries"][0]["effective_date"] == "2026-12-31"
    assert payload["generated_at"]


def test_cli_digest_empty_ledger_still_renders(tmp_path):
    from cli.main import cli

    watchlist = _write_watchlist(tmp_path, _WL)
    event_file = _future_event_file(tmp_path)
    out = CliRunner().invoke(
        cli,
        [
            "digest",
            "--watchlist",
            watchlist,
            "--event",
            event_file,
            "--ledger",
            str(tmp_path / "nonexistent"),
        ],
    )
    assert out.exit_code == 0, out.output
    assert "django==4.2" in out.output
    assert "no first-detection record in the ledger" in out.output


def test_cli_digest_needs_an_event(tmp_path):
    from cli.main import cli

    watchlist = _write_watchlist(tmp_path, _WL)
    out = CliRunner().invoke(cli, ["digest", "--watchlist", watchlist])
    assert out.exit_code != 0
    assert "needs at least one --event" in out.output


def test_cli_digest_ledger_disabled_makes_no_claims(tmp_path):
    from cli.main import cli

    watchlist = _write_watchlist(tmp_path, _WL)
    event_file = _future_event_file(tmp_path)
    out = CliRunner().invoke(
        cli,
        [
            "digest",
            "--watchlist",
            watchlist,
            "--event",
            event_file,
            "--ledger",
            "",
        ],
    )
    assert out.exit_code == 0, out.output
    assert "django==4.2" in out.output
    assert "no first-detection record in the ledger" in out.output


def test_cli_digest_composable_with_sbom(tmp_path):
    """--sbom composes through the shared loader: same echo and skip-reason
    discipline as `check`, and a clean empty digest when the mapped
    components (django 5.0) fall outside the event's version scope."""
    from cli.main import cli

    event_file = _future_event_file(tmp_path)
    out = CliRunner().invoke(
        cli,
        [
            "digest",
            "--sbom",
            "data/fixtures/sbom/cyclonedx.json",
            "--event",
            event_file,
            "--ledger",
            str(tmp_path / "ledger"),
        ],
    )
    assert out.exit_code == 0, out.output
    assert "sbom: 3 mapped component(s), 1 skipped" in out.output
    assert "skipped: component `pkg:composer/symfony/http-foundation@7.0`" in out.output
    # SBOM django is 5.0; the event scope is 4.2 -> no deadline, clean exit.
    assert "Nothing upcoming or newly-effective within the warning window." in out.output
