"""Public web-report proofs: metadata artifact and information boundary."""

from datetime import date

from reports.generate import build_report, build_report_metadata, prepare_report

TODAY = date(2026, 10, 2)


def _eol(title="db 5.0 is end-of-life"):
    return {
        "analyst": "change",
        "event_type": "EOL",
        "signal": "lifecycle",
        "impact": "ACTION",
        "title": title,
        "lifecycle_state": "EFFECTIVE",
        "effective_at": "2026-09-01",
        "scope": {"kind": "version", "versions": ["5.0"]},
        "sources": ["endoflife"],
    }


def test_metadata_companion():
    items = [{"project": "db", "pulse": {"facets": {}}, "findings": [_eol()]}]
    prepared = prepare_report(items, [], today=TODAY)
    meta = build_report_metadata(
        "2026-10", items, prepared["pairs"], prepared["historical"], False, TODAY
    )
    assert meta["report_id"] == "openpulse-2026-10"
    assert meta["reporting_period"] == "2026-10"
    assert meta["generated_at"]
    assert meta["openpulse_version"]
    assert meta["freshness_policy"]["name"] == "freshness/v1"
    assert meta["freshness_policy"]["recency_days"] >= 1
    assert meta["coverage"]["projects_monitored"] == 1
    assert meta["coverage"]["sweep_included"] is False
    assert meta["counts"]["narrated_findings"] == 1
    assert meta["counts"]["by_status"]
    assert meta["counts"]["by_category"] == {"Lifecycle": 1}
    assert meta["report_date"] == "2026-10-02"
    # No finding content, no infrastructure: identification only.
    blob = str(meta)
    for token in (".openpulse", "token", "Authorization", "traceback"):
        assert token not in blob


def test_metadata_cli_sidecar(tmp_path):
    import json
    import shutil

    from click.testing import CliRunner

    from cli.main import cli

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    shutil.copy("data/fixtures/redis/raw_bundle.json", bundle_dir / "redis.json")
    out = tmp_path / "report.md"
    result = CliRunner().invoke(
        cli,
        [
            "report",
            "--month",
            "2026-09",
            "--raw-bundle-dir",
            str(bundle_dir),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    meta_path = tmp_path / "report.meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["report_id"] == "openpulse-2026-09"
    assert meta["coverage"]["projects_monitored"] == 1


def test_public_boundary_no_internal_tokens():
    md = build_report(
        "2026-10",
        [{"project": "db", "pulse": {"facets": {}}, "findings": [_eol()]}],
        today=TODAY,
    )
    for token in (
        "_analyst",
        "suggested impact",
        "suggested_impact",
        "parser_version",
        "parser-version",
        ".openpulse",
        "_refs",
        "evidence_links",
        "distribution_model_change",
        "stories_merged",
        "lifecycle_state",
        "match_method",
        "identity_via",
        "evidence_confidence",
        "match_strength",
        "first_detected_at",
        "observed_at",
        "last_observed_at",
        "Traceback",
    ):
        assert token not in md, token


def test_public_headings_are_stable_and_plain():
    md = build_report(
        "2026-10",
        [{"project": "db", "pulse": {"facets": {}}, "findings": [_eol()]}],
        today=TODAY,
    )
    for heading in (
        "# OpenPulse OSS Dependency Intelligence",
        "## Executive Summary",
        "## Top Changes",
        "## Upcoming Changes",
        "## Changes by Category",
        "## What OpenPulse Watches",
        "## Methodology",
        "## For Your Environment",
        "## Appendix",
    ):
        assert heading in md
    assert md.startswith("# OpenPulse OSS Dependency Intelligence")
    assert md.count("\n# ") == 0
