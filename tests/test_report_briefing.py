"""Monthly intelligence briefing tests: decision-support structure.

Proves the report answers, in order: what changed, why it matters,
who may be affected, how strong the evidence is, when it matters,
and what to investigate next — without implementation metadata or
customer-impact claims. Deterministic: identical inputs, identical
markdown.
"""

from datetime import date, timedelta

from reports.generate import build_report


def _item(project, findings):
    return {"project": project, "pulse": {"facets": {}}, "findings": findings}


def _eol(title="db 5.0 is end-of-life", impact="ACTION", **kw):
    base = {
        "analyst": "change",
        "event_type": "EOL",
        "signal": "lifecycle",
        "impact": impact,
        "title": title,
        "lifecycle_state": "EFFECTIVE",
        "effective_at": "2026-09-01",
        "scope": {"kind": "version", "versions": ["5.0"]},
        "affected_versions": ["5.0"],
        "sources": ["endoflife"],
    }
    base.update(kw)
    return base


def _distribution(title="Tag `7.2` disappeared from bitnami/redis", **kw):
    base = {
        "analyst": "change",
        "event_type": "DISTRIBUTION_CHANGE",
        "signal": "distribution",
        "title": title,
        "summary": "Observed tag_disappeared.",
        "impact": "REVIEW",
        "significance": "high",
        "detection_method": "registry_observation",
        "evidence_strength": "moderate",
        "scope": {"kind": "artifact", "artifacts": ["docker.io/bitnami/redis:7.2"]},
        "affected_versions": ["*"],
        "affected_artifacts": [{"kind": "docker-image", "ref": "docker.io/bitnami/redis:7.2"}],
        "references": ["https://hub.docker.com/r/bitnami/redis/tags"],
        "observation_evidence": {
            "observation_id": "docker-hub:docker.io/bitnami/redis:abc",
            "source": "docker-hub",
            "source_url": "https://hub.docker.com/r/bitnami/redis/tags",
            "observed_at": "2026-09-02",
            "content_hash": "sha256:cur",
            "chain_hash": "sha256:chain",
            "previous_observation_id": "docker-hub:docker.io/bitnami/redis:prev",
            "previous_observed_at": "2026-09-01",
            "previous_content_hash": "sha256:prev",
            "fact": {
                "type": "tag_disappeared",
                "image": "docker.io/bitnami/redis",
                "tag": "7.2",
                "previous_digests": ["sha256:111"],
                "current_digests": None,
                "tags_present": ["7.2", "latest"],
            },
        },
        "supporting": [],
    }
    base.update(kw)
    return base


def test_executive_summary_exists_and_leads_with_value():
    md = build_report("2026-09", [_item("db", [_eol()]), _item("quiet", [])])
    assert "## Executive Summary" in md
    summary = md.split("## Executive Summary")[1].split("## Top Changes")[0]
    assert "OpenPulse detected 1 material upstream change across" in summary
    assert "- Projects monitored: 2" in summary
    assert "- Changes requiring attention: 1" in summary
    assert "- Data gaps:" in summary
    # Value first: no bare finding count leads the section.
    assert "significant events" not in summary


def test_top_changes_ranked_non_lifecycle_first():
    md = build_report(
        "2026-09",
        [_item("db", [_eol()]), _item("zeta", [_distribution()])],
    )
    top = md.split("## Top Changes")[1].split("## OpenPulse Reference Discovery")[0]
    assert "1. **zeta**" in top
    assert "2. **db**" in top


def test_top_changes_deterministic_ties():
    kwargs = {"impact": "REVIEW", "significance": "low", "detection_method": "x"}
    items_ab = [_item("b", [_distribution(**kwargs)]), _item("a", [_distribution(**kwargs)])]
    items_ba = [_item("a", [_distribution(**kwargs)]), _item("b", [_distribution(**kwargs)])]
    md1 = build_report("2026-09", items_ab)
    md2 = build_report("2026-09", items_ba)
    assert md1 == md2
    top = md1.split("## Top Changes")[1]
    assert top.index("**a**") < top.index("**b**")


def test_reference_discovery_when_suitable_finding_exists():
    md = build_report("2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()])
    section = md.split("## OpenPulse Reference Discovery")[1].split("## Changes Requiring")[0]
    assert "OpenPulse detects upstream changes and connects them to dependency identity." in md
    for block in (
        "WHAT CHANGED",
        "WHY IT MATTERS",
        "HOW OPENPULSE DETECTED IT",
        "WHAT WAS AFFECTED",
        "WHAT WAS NOT AFFECTED",
        "EVIDENCE",
        "WARNING WINDOW",
    ):
        assert block in section
    # NOT-AFFECTED derived from tags still present — concrete, not assumed.
    assert "latest" in section


def test_reference_discovery_omitted_without_suitable_finding():
    md = build_report("2026-09", [_item("db", [_eol()])])
    assert "## OpenPulse Reference Discovery" not in md


def test_no_implementation_metadata_rendered():
    md = build_report(
        "2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()]
    )
    assert "_analyst=" not in md
    assert "suggested impact=" not in md


def test_confidence_rendered_with_meanings():
    md = build_report("2026-09", [_item("db", [_eol()])])
    assert "Evidence confidence: EMERGING" in md
    quality = md.split("## Evidence Quality")[1].split("## What OpenPulse Added This Month")[0]
    for level in ("CONFIRMED", "CORROBORATED", "EMERGING", "UNVERIFIED"):
        assert level in quality
    assert "never action-framed" in quality


def test_upcoming_warning_window_uses_first_detection():
    future = (date.today() + timedelta(days=60)).isoformat()
    detected = (date.today() - timedelta(days=13)).isoformat()
    finding = _eol(
        title="db 6.0 EOL approaching",
        impact="REVIEW",
        lifecycle_state="UPCOMING",
        effective_at=future,
        event_date=future,
        first_detected_at=detected,
    )
    md = build_report("2026-09", [_item("db", [finding])])
    upcoming = md.split("## Upcoming Changes")[1].split("## Category Overview")[0]
    assert f"Detected {detected} → Effective {future} (Warning window: 73 days)" in upcoming


def test_public_customer_boundary_rendered():
    md = build_report("2026-09", [_item("db", [_eol()])])
    boundary = md.split("## For Your Environment")[1].split("## Appendix")[0]
    assert "does not establish that a specific customer environment is affected" in boundary
    assert "public intelligence → dependency context" in boundary
    assert "affected dependency" in boundary
    assert "actionable warning" in boundary


def test_lifecycle_appendix_remains_available():
    md = build_report("2026-09", [_item("db", [_eol()])])
    appendix = md.split("## Appendix")[1]
    assert "### A. All project findings" in appendix
    assert "db 5.0 is end-of-life" in appendix
    assert "### B. Source references" in appendix
    assert "### C. Data gaps and limitations" in appendix
    # Category table keeps lifecycle visible without dominating.
    assert "| Lifecycle | 1 | 1 |" in md


def test_output_deterministic():
    items = [_item("db", [_eol()]), _item("zeta", [_distribution()])]
    assert build_report("2026-09", items) == build_report("2026-09", items)


def test_no_unsupported_customer_impact_language():
    md = build_report(
        "2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()]
    ).lower()
    narrative = md.split("## for your environment")[0]
    for phrase in (
        "you are affected",
        "your environment is affected",
        "your dependencies are affected",
        "will affect your",
        "assessment: action_required",
    ):
        assert phrase not in narrative


def _value_section(md):
    return md.split("## What OpenPulse Added This Month")[1].split("## For Your Environment")[0]


def test_value_section_exists_with_all_dimensions():
    md = build_report("2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()])
    section = _value_section(md)
    assert "Does it affect what we depend on?" in section
    assert "### Upstream Change Detection" in section
    assert "### Dependency Attribution" in section
    assert "### Evidence-backed Intelligence" in section
    assert "### Early Warning" in section
    assert "### Reference Case" in section
    assert "### From Public Intelligence to Early Warning" in section
    assert "does not replace SCA" in section


def test_value_section_lists_only_present_categories():
    md = build_report("2026-09", [_item("db", [_eol()])])
    section = _value_section(md)
    assert "- Lifecycle (1):" in section
    assert "- Security (" not in section
    assert "- Distribution (" not in section


def test_value_section_bitnami_distinction_when_present():
    md = build_report("2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()])
    section = _value_section(md)
    assert "docker.io/bitnami/redis is not docker.io/redis" in section


def test_value_section_no_bitnami_callout_when_absent():
    md = build_report("2026-09", [_item("db", [_eol()])])
    section = _value_section(md)
    assert "bitnami" not in section.lower()


def test_value_section_evidence_counts_are_real():
    md = build_report("2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()])
    section = _value_section(md)
    assert "strongest finding this month is EMERGING" in section
    assert "1 independent source family" in section
    assert "1 supporting reference" in section
    assert "Scope established for 2/2 findings." in section


def test_value_section_early_warning_max_window():
    future = (date.today() + timedelta(days=60)).isoformat()
    detected = (date.today() - timedelta(days=13)).isoformat()
    finding = _eol(
        title="db 6.0 EOL approaching",
        impact="REVIEW",
        lifecycle_state="UPCOMING",
        effective_at=future,
        event_date=future,
        first_detected_at=detected,
    )
    md = build_report("2026-09", [_item("db", [finding])])
    assert "up to 73 days" in _value_section(md)


def test_value_section_graceful_without_evidence():
    md = build_report("2026-09", [])
    section = _value_section(md)
    assert "No upcoming changes with trustworthy dates" in section
    assert "No scoped attributions this month." in section
    assert "### Reference Case" not in section
    # Detection dimension omitted, never padded.
    assert "e.g." not in section.split("### Upstream Change Detection")[1].split("###")[0]


def test_value_section_reference_case_stages_from_data():
    md = build_report("2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()])
    case = _value_section(md).split("### Reference Case")[1]
    for stage in (
        "Problem:",
        "Signal:",
        "Evidence:",
        "Identity:",
        "Applicability:",
        "Recommended investigation:",
    ):
        assert stage in case
    assert "Distribution · registry_observation" in case
    assert "docker.io/bitnami/redis:7.2" in case


def test_value_section_no_vanity_headline():
    md = build_report("2026-09", [_item("db", [_eol()])], sweep_findings=[_distribution()])
    section = _value_section(md)
    assert "Projects monitored:" not in section
    assert "Something changed upstream. Does it affect what we depend on?" in section
