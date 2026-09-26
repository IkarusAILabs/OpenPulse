"""Monthly report tests: ranking, evidence, offline CLI."""

import json


def _item(project, findings):
    return {"project": project, "pulse": {"facets": {}}, "findings": findings}


def test_report_groups_and_counts():
    from reports.generate import build_report

    items = [
        _item(
            "b-proj",
            [
                {
                    "analyst": "c",
                    "event_type": "EOL",
                    "impact": "ACTION",
                    "title": "eol",
                    "sources": ["endoflife"],
                }
            ],
        ),
        _item(
            "a-proj",
            [
                {
                    "analyst": "c",
                    "event_type": "EOL",
                    "impact": "REVIEW",
                    "title": "soon",
                    "sources": ["endoflife"],
                }
            ],
        ),
        _item(
            "c-proj",
            [{"analyst": "c", "event_type": "X", "impact": "INFORMATIONAL", "title": "meh"}],
        ),
    ]
    md = build_report("2026-09", items)
    assert "3 projects monitored" in md
    assert "2 significant events" in md
    assert "## 🔴 Action-worthy changes (1)" in md
    assert "## 🟠 Changes to watch (1)" in md
    assert "c-proj" not in md
    assert md.index("Action-worthy") < md.index("Changes to watch")


def test_report_names_evidence():
    from reports.generate import build_report

    items = [
        _item(
            "redis",
            [
                {
                    "analyst": "security",
                    "cve_id": "CVE-1",
                    "impact": "ACTION",
                    "title": "t",
                    "sources": ["nvd", "osv"],
                    "references": ["https://example.com/x"],
                }
            ],
        )
    ]
    md = build_report("2026-09", items)
    assert "Evidence: security, nvd, osv" in md
    assert "https://example.com/x" in md


def test_collect_project_from_fixture():
    from reports.generate import collect_project

    raw = json.load(open("data/fixtures/redis/raw_bundle.json"))
    item = collect_project("redis", raw)
    assert item["project"] == "redis"
    assert item["pulse"]["facets"]["lifecycle"]["status"] == "action"


def test_popularity_tiers():
    from reports.generate import popularity_tier

    assert popularity_tier(None) == "unranked"
    assert popularity_tier("x") == "unranked"
    assert popularity_tier(999) == "low"
    assert popularity_tier(5000) == "medium"
    assert popularity_tier(20000) == "high"
    assert popularity_tier(80000) == "very high"


def test_report_cli_offline(tmp_path):
    import shutil

    from click.testing import CliRunner

    from cli.main import cli

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    shutil.copy("data/fixtures/redis/raw_bundle.json", bundle_dir / "redis.json")
    out = tmp_path / "report.md"
    result = CliRunner().invoke(
        cli,
        ["report", "--month", "2026-09", "--raw-bundle-dir", str(bundle_dir), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "# OpenPulse — 2026-09" in text
    assert "### redis" in text
