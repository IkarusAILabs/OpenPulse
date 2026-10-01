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
    assert "## What changed this month?" in md
    assert "### Lifecycle changes (2)" in md
    assert "Public report findings describe OSS ecosystem changes" in md
    assert "c-proj" not in md.split("## Where our data is incomplete")[0]
    assert "c-proj" in md  # named as having no signals
    assert md.index("What changed") < md.index("What appears actionable?")


def test_report_actionable_requires_scope_and_state():
    from reports.generate import build_report

    scoped = {
        "analyst": "change",
        "event_type": "EOL",
        "impact": "ACTION",
        "title": "django 5.0 is end-of-life",
        "lifecycle_state": "EFFECTIVE",
        "effective_at": "2026-09-01",
        "scope": {"kind": "version", "versions": ["5.0"]},
        "affected_versions": ["5.0"],
        "sources": ["endoflife"],
    }
    unscoped = {
        "analyst": "change",
        "event_type": "EOL",
        "impact": "ACTION",
        "title": "x 9 is end-of-life",
        "sources": ["endoflife"],
    }
    md = build_report(
        "2026-09",
        [_item("django", [scoped]), _item("x", [unscoped])],
    )
    actionable = md.split("## What appears actionable?")[1]
    assert "django 5.0 is end-of-life" in actionable
    assert "Why:" in actionable and "5.0" in actionable
    assert "x 9 is end-of-life" not in actionable


def test_report_archived_is_review_never_actionable():
    from reports.generate import build_report

    finding = {
        "analyst": "change",
        "event_type": "PROJECT_ARCHIVED",
        "impact": "ACTION",
        "title": "minio/minio is archived on GitHub",
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "project", "versions": []},
        "sources": ["github"],
    }
    md = build_report("2026-09", [_item("minio", [finding])])
    assert "### Project signals (1)" in md
    actionable = md.split("## What appears actionable?")[1].split(
        "## Where our data is incomplete"
    )[0]
    assert "archived" not in actionable


def test_report_source_and_gap_sections():
    from reports.generate import build_report

    md = build_report(
        "2026-09",
        [
            _item(
                "p",
                [
                    {
                        "analyst": "security",
                        "cve_id": "CVE-1",
                        "impact": "ACTION",
                        "title": "t",
                        "sources": ["nvd", "osv"],
                    }
                ],
            )
        ],
    )
    assert "## Sources" in md
    assert "NVD" in md and "OSV" in md
    assert "cite 2+ sources" in md
    # NVD + OSV share the vuln-data family: label-corroborated but not
    # family-corroborated — the report must say so honestly.
    assert "0 are corroborated across" in md
    assert "Independent source families observed: 1" in md
    assert "## Where our data is incomplete" in md


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
    assert "#### redis" in text
    # Public/customer boundary travels with every generated report.
    assert "whether it affects YOUR dependencies" in text


def test_report_counts_findings_not_projects():
    from reports.generate import build_report

    items = [
        {
            "project": "p",
            "pulse": {"facets": {}},
            "findings": [
                {"analyst": "c", "event_type": "EOL", "impact": "ACTION", "title": "a"},
                {"analyst": "c", "event_type": "EOL", "impact": "WATCH", "title": "b"},
            ],
        }
    ]
    assert "2 significant events" in build_report("2026-09", items)


def test_report_recency_holds_back_stale_dated_findings():
    from reports.generate import build_report

    def item(published):
        return {
            "project": "p",
            "pulse": {"facets": {}},
            "findings": [
                {
                    "analyst": "security",
                    "cve_id": "CVE-1",
                    "impact": "ACTION",
                    "title": "t",
                    "published": published,
                }
            ],
        }

    assert "0 significant events" in build_report(
        "2026-09", [item("2017-01-01")], since="2026-07-01"
    )
    assert "1 significant events" in build_report(
        "2026-09", [item("2026-08-15")], since="2026-07-01"
    )


def test_report_undated_change_findings_always_pass():
    from reports.generate import build_report

    items = [
        {
            "project": "p",
            "pulse": {"facets": {}},
            "findings": [
                {"analyst": "change", "event_type": "EOL", "impact": "ACTION", "title": "eol"}
            ],
        }
    ]
    assert "1 significant events" in build_report("2026-09", items, since="2026-07-01")


def test_render_finding_never_prints_none():
    from analyzers.report_analyst import render_finding_md

    md = render_finding_md(
        {"analyst": "security", "cve_id": "CVE-1", "impact": "WATCH", "title": "t"}
    )
    assert "[None]" not in md
    assert "\nNone" not in md
    assert "[SECURITY]" in md


def _finding(**kw):
    base = {"analyst": "change", "event_type": "EOL", "impact": "ACTION", "title": "t"}
    base.update(kw)
    return base


def test_report_does_not_mutate_inputs():
    from reports.generate import build_report

    findings = [_finding(event_date="2020-01-01"), _finding(event_date="2026-08-15")]
    items = [{"project": "p", "pulse": {"facets": {}}, "findings": findings}]
    build_report("2026-09", items, since="2026-07-01")
    assert len(items[0]["findings"]) == 2


def test_report_holds_back_stale_lifecycle():
    from reports.generate import build_report

    old = {"project": "p", "pulse": {"facets": {}}, "findings": [_finding(event_date="2020-01-01")]}
    assert "0 significant events" in build_report("2026-09", [old], since="2026-07-01")
    new = {"project": "p", "pulse": {"facets": {}}, "findings": [_finding(event_date="2026-08-15")]}
    assert "1 significant events" in build_report("2026-09", [new], since="2026-07-01")


def test_report_excludes_related_counts_them():
    from reports.generate import build_report

    items = [
        {
            "project": "p",
            "pulse": {"facets": {}},
            "findings": [
                _finding(relationship="RELATED", impact="REVIEW"),
                _finding(relationship="AFFECTS_PACKAGE", impact="REVIEW"),
            ],
        }
    ]
    md = build_report("2026-09", items)
    assert "1 significant events" in md
    assert "1 related-but-unconfirmed or below-bar records held back" in md
    md_all = build_report("2026-09", items, include_related=True)
    # Same class merges into ONE coherent story even when narrated.
    assert "1 significant events" in md_all
    assert "lifecycle:" in md_all
    assert "held back" not in md_all


def test_report_prints_supporting_urls_once():
    from reports.generate import _supporting_urls, build_report

    finding = {
        "analyst": "change",
        "event_type": "EOL",
        "impact": "ACTION",
        "title": "t",
        "supporting": [
            {"collector": "endoflife", "link": "https://endoflife.date/redis"},
            {"collector": "endoflife", "link": "https://endoflife.date/redis"},
            {"collector": "x"},
            "not-a-dict",
        ],
        "references": ["https://endoflife.date/redis"],
    }
    assert _supporting_urls(finding) == ["https://endoflife.date/redis"]
    md = build_report(
        "2026-09",
        [{"project": "redis", "pulse": {"facets": {}}, "findings": [finding]}],
    )
    assert md.count("https://endoflife.date/redis") == 1


def _sweep_finding():
    return {
        "analyst": "change",
        "event_type": "DISTRIBUTION_CHANGE",
        "signal": "distribution",
        "title": "Tag `7.2` disappeared from bitnami/redis",
        "summary": "Observed tag_disappeared.",
        "impact": "REVIEW",
        "significance": "high",
        "detection_method": "registry_observation",
        "scope": {"kind": "artifact", "artifacts": ["docker.io/bitnami/redis:7.2"]},
        "affected_versions": ["*"],
        "affected_artifacts": [{"kind": "docker-image", "ref": "docker.io/bitnami/redis:7.2"}],
        "references": ["https://hub.docker.com/r/bitnami/redis/tags"],
        "supporting": [],
    }


def test_report_renders_sweep_section():
    from reports.generate import build_report

    md = build_report("2026-09", [], sweep_findings=[_sweep_finding()])
    assert "## Distribution discovery (1)" in md
    assert "docker.io/bitnami/redis:7.2" in md
    assert "https://hub.docker.com/r/bitnami/redis/tags" in md


def test_report_without_sweep_has_no_section():
    from reports.generate import build_report

    md = build_report("2026-09", [])
    assert "Distribution discovery" not in md


def _dated_finding(**kw):
    base = {
        "analyst": "c",
        "event_type": "EOL",
        "impact": "ACTION",
        "title": "eol",
        "sources": ["endoflife"],
    }
    base.update(kw)
    return base


def test_report_shows_lead_time_for_upcoming_change():
    from reports.generate import build_report

    md = build_report(
        "2026-09",
        [
            _item(
                "x",
                [
                    _dated_finding(
                        first_detected_at="2026-09-01",
                        observed_at="2026-09-20",
                        effective_at="2026-09-29",
                        event_date="2026-09-29",
                    )
                ],
            )
        ],
    )
    assert "Lead time: 28 days (2026-09-01 → 2026-09-29)" in md


def test_report_silent_lead_time_for_past_or_unknown():
    from reports.generate import build_report

    md = build_report(
        "2026-09",
        [
            _item(
                "past",
                [_dated_finding(first_detected_at="2026-09-26", effective_at="2026-04-30")],
            ),
            # observed_at without first detection: no claim, never estimated.
            _item("unknown", [_dated_finding(observed_at="2026-09-01")]),
        ],
    )
    assert "Lead time" not in md


def test_public_report_never_claims_customer_impact():
    from reports.generate import build_report

    md = build_report(
        "2026-09",
        [
            _item(
                "x",
                [
                    _dated_finding(
                        first_detected_at="2026-09-01",
                        observed_at="2026-09-20",
                        effective_at="2026-09-29",
                        event_date="2026-09-29",
                    )
                ],
            )
        ],
        sweep_findings=[
            {
                "analyst": "change",
                "event_type": "DISTRIBUTION_CHANGE",
                "signal": "distribution",
                "title": "t",
                "summary": "s",
                "impact": "ACTION",
                "significance": "high",
                "distribution_model_change": True,
                "evidence_strength": "weak",
                "scope": {"kind": "project", "versions": []},
            }
        ],
    )
    assert "Assessment: ACTION_REQUIRED" not in md
    assert "never ACTION_REQUIRED" in md
    assert "Assessment: PROJECT_CHANGE" in md
    assert "Applicability:" in md
