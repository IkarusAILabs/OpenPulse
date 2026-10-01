"""Lifecycle posture report tests: planning view, not an EOL export."""

from datetime import date

from reports.lifecycle import build_lifecycle_report, collect_lifecycle_status

TODAY = date(2026, 9, 26)


def _entry(cycle, eol=None, support=None, product="db"):
    return {
        "collector": "endoflife",
        "product": product,
        "cycle": cycle,
        "eol": eol,
        "support": support,
        "link": f"https://endoflife.date/{product}",
    }


def _status(slug, entries, today=TODAY):
    return collect_lifecycle_status(slug, {"endoflife": entries}, today=today)


def test_upcoming_deadlines_sorted_soonest_first():
    statuses = [
        _status(
            "db",
            [_entry("6.0", eol="2026-12-01"), _entry("5.0", eol="2026-10-05")],
        )
    ]
    md = build_lifecycle_report("2026-09", statuses, today=TODAY)
    table = md.split("## Upcoming Deadlines")[1].split("## Recently Ended")[0]
    assert table.index("2026-10-05") < table.index("2026-12-01")
    assert "| db | 5.0 | 2026-10-05 | 9 |" in table
    assert "| db | 6.0 | 2026-12-01 | 66 |" in table


def test_no_data_handling():
    statuses = [
        _status("ghost", [{"collector": "endoflife", "skipped": "not on endoflife.date"}]),
        _status("db", [_entry("5.0", eol="2026-01-01")]),
    ]
    md = build_lifecycle_report("2026-09", statuses, today=TODAY)
    assert "- Projects with no lifecycle data: 1" in md
    gaps = md.split("## Lifecycle Coverage Gaps")[1].split("## Top Lifecycle")[0]
    assert "ghost" in gaps
    assert "not on endoflife.date" in gaps
    assert "never read it as safe" in md
    # NO-DATA is counted only as a gap — never as OK or concern.
    assert "- Projects with current lifecycle concern (effective EOL): 1" in md


def test_appendix_preserves_all_project_detail():
    statuses = [
        _status("db", [_entry("5.0", eol="2026-01-01")]),
        _status("ghost", [{"collector": "endoflife", "skipped": "not on endoflife.date"}]),
    ]
    md = build_lifecycle_report("2026-09", statuses, today=TODAY)
    appendix = md.split("## Appendix — Full Lifecycle Coverage Matrix")[1]
    assert "| db | EOL | db 5.0 is end-of-life (2026-01-01) |" in appendix
    assert "| ghost | NO-DATA | not on endoflife.date |" in appendix


def test_executive_summary_counts():
    statuses = [
        _status("eol-proj", [_entry("1.0", eol="2026-01-01")]),
        _status("soon-proj", [_entry("2.0", eol="2026-12-01")]),
        _status("eos-proj", [_entry("3.0", support="2026-01-01")]),
        _status("ghost", [{"collector": "endoflife", "skipped": "not on endoflife.date"}]),
        _status("ok-proj", [_entry("4.0", eol="2027-06-01")]),
    ]
    md = build_lifecycle_report("2026-09", statuses, today=TODAY)
    summary = md.split("## Executive Summary")[1].split("## Upcoming Deadlines")[0]
    assert "- Projects checked: 5" in summary
    assert "- Projects with current lifecycle concern (effective EOL): 1" in summary
    assert "- Projects with an upcoming lifecycle deadline: 2" in summary
    assert "- Projects with ended support: 1" in summary
    assert "- Projects with no lifecycle data: 1" in summary


def test_no_customer_impact_claims():
    statuses = [
        _status("db", [_entry("5.0", eol="2026-01-01"), _entry("6.0", eol="2026-12-01")]),
    ]
    md = build_lifecycle_report("2026-09", statuses, today=TODAY).lower()
    for phrase in (
        "you are affected",
        "your environment is affected",
        "will affect your",
        "action_required",
        "your software is",
    ):
        assert phrase not in md


def test_stable_rendering_and_explicit_today():
    statuses = [_status("db", [_entry("5.0", eol="2026-12-01")])]
    assert build_lifecycle_report("2026-09", statuses, today=TODAY) == build_lifecycle_report(
        "2026-09", statuses, today=TODAY
    )
    later = build_lifecycle_report("2026-09", statuses, today=date(2026, 10, 26))
    assert "| db | 5.0 | 2026-12-01 | 36 |" in later


def test_top_planning_items_prioritized():
    statuses = [
        _status("far", [_entry("9.0", eol="2027-01-01")]),
        _status("near", [_entry("8.0", eol="2026-10-05")]),
        _status("old", [_entry("7.0", eol="2024-01-01")]),
    ]
    md = build_lifecycle_report("2026-09", statuses, today=TODAY)
    planning = md.split("## Top Lifecycle Planning Items")[1].split("## Appendix")[0]
    assert planning.index("**near** 8.0 EOL in 9 days") < planning.index("**far** 9.0 EOL")
    assert "confirmed end-of-life version(s) (7.0)" in planning


def test_lifecycle_cli_offline(tmp_path):
    import json

    from click.testing import CliRunner

    from cli.main import cli

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    bundle_dir.joinpath("db.json").write_text(
        json.dumps({"endoflife": [_entry("5.0", eol="2026-01-01")]}), encoding="utf-8"
    )
    out = tmp_path / "lifecycle.md"
    result = CliRunner().invoke(
        cli,
        [
            "lifecycle-report",
            "--month",
            "2026-09",
            "--raw-bundle-dir",
            str(bundle_dir),
            "--projects",
            "db",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "# OpenPulse Lifecycle Posture — 2026-09" in text
    assert "| db | EOL |" in text
