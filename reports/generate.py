"""Monthly report — seed + facets + top findings to ranked markdown.

Pure functions (no network): `collect_project` turns one raw bundle
into a report item; `build_report` ranks items into intelligence
sections. Every item names its evidence — findings carry sources and
references, never bare assertions.

Report semantics (§11): public findings describe OSS ecosystem
changes, never customer impact. Placement follows impact eligibility
(``core.risk.impact``), not raw analyst proposals: only evidence- and
scope-justified findings appear as actionable, and the report states
its incompleteness explicitly.
"""

from __future__ import annotations

from typing import Any

from analyzers import change_analyst, security_analyst
from analyzers.event_correlation import aggregate_lifecycle, lifecycle_first
from analyzers.report_analyst import render_finding_md
from core.entities.catalog import project_context
from core.leadtime import finding_lead_time
from core.pulse import compute_pulse
from core.risk.impact import evaluate_impact
from core.risk.metrics import finding_source_distribution

DISCLAIMER = (
    "_Public report findings describe OSS ecosystem changes. They are "
    "not assertions that a particular customer's environment is "
    "affected._"
)

_ELIGIBLE = ("ACTION", "REVIEW", "WATCH")


def collect_project(
    slug: str, raw: dict[str, list[dict[str, Any]]], version: str | None = None
) -> dict[str, Any]:
    """One raw bundle -> report item (pulse + findings)."""
    context = project_context(slug)
    if version:
        context["version"] = version
    findings = change_analyst.analyze(raw)
    findings += security_analyst.correlate(raw, context)
    metas = [e for e in raw.get("github_meta", []) if e.get("kind") == "repo_meta"]
    activity = {"releases": raw.get("github", []), "repo_meta": metas[0] if metas else None}
    stars = (metas[0].get("stargazers") if metas else None) or None
    pulse = compute_pulse(
        slug, findings=findings, activity=activity, popularity_note=_popularity_note(stars)
    )
    return {"project": slug, "pulse": pulse, "findings": findings}


def _popularity_note(stars: Any) -> str:
    return f"popularity {popularity_tier(stars)}" + (
        f" ({stars} stars)" if isinstance(stars, int) else " (unranked)"
    )


def popularity_tier(stars: Any) -> str:
    """Documented bands (see METHODOLOGY): stars inform reach, never risk."""
    if not isinstance(stars, int):
        return "unranked"
    if stars >= 50000:
        return "very high"
    if stars >= 10000:
        return "high"
    if stars >= 1000:
        return "medium"
    return "low"


def _fresh(finding: dict[str, Any], since: str | None) -> bool:
    """Recency gate for dated findings only.

    Security findings carry `published`; lifecycle findings carry
    `event_date` (EOL/support dates — future ones always pass, they are
    early warnings). Undated findings always pass. Only dated items
    older than `since` (YYYY-MM-DD) are held back.
    """
    if since is None:
        return True
    stamp = str(finding.get("published") or finding.get("event_date") or "")[:10]
    if not stamp:
        return True
    return stamp >= since


def _narrate(finding: dict[str, Any], include_related: bool) -> bool:
    """Monthly narrative rule: established relationships and all change
    findings; keyword-only RELATED/UNKNOWN items are counted, not told."""
    relationship = str(finding.get("relationship", ""))
    if relationship in ("RELATED", "UNKNOWN"):
        return include_related
    return True


def _eligibility(finding: dict[str, Any]) -> dict[str, Any]:
    """Public-context eligibility, computed fresh (never stored)."""
    try:
        return evaluate_impact(finding)
    except Exception:
        return {
            "assessment": "PROJECT_SIGNAL",
            "eligibility": "INFORMATIONAL",
            "reasons": ["eligibility evaluation failed; held back"],
        }


def _trust_block(finding: dict[str, Any]) -> list[str]:
    """Machine-checkable trust boundary per finding: what was observed,
    what it applies to, what was concluded, and how actionable it is.

    Observed change, dependency match, impact, and actionability stay
    on separate lines so no reader — human or machine — can mistake
    ecosystem framing for a claim about their environment.
    """
    assessment = finding.get("_assessment") or {}
    scope = finding.get("scope") or {}
    applies: list[str] = []
    for key in ("versions", "artifacts", "packages", "registries"):
        for value in scope.get(key) or []:
            applies.append(str(value))
    lines = [
        f"Assessment: {assessment.get('assessment', '?')} "
        f"(eligibility {assessment.get('eligibility', '?')})"
    ]
    applies_line = ", ".join(applies) if applies else scope.get("kind", "project")
    lines.append(f"Applicability: {applies_line}")
    return lines


def _lead_time_line(finding: dict[str, Any]) -> str | None:
    """One honest sentence when a finding carries both detection and effect.

    Past or unknown effective dates yield None — silence, not a number.
    """
    days, detected, effective = finding_lead_time(finding)
    if days is None:
        return None
    return f"Lead time: {days} days ({detected} → {effective})"


def _change_class(finding: dict[str, Any]) -> str:
    """Intelligence section for one finding."""
    event_type = str(finding.get("event_type", ""))
    signal = str(finding.get("signal", ""))
    if event_type in ("EOL", "EOS"):
        return "Lifecycle changes"
    if event_type in ("DISTRIBUTION_CHANGE", "REGISTRY_CHANGE") or signal == "distribution":
        return "Distribution changes"
    if event_type == "SECURITY" or signal == "security" or finding.get("cve_id"):
        return "Security changes"
    return "Project signals"


def build_report(
    month: str,
    items: list[dict[str, Any]],
    since: str | None = None,
    include_related: bool = False,
    notes: list[str] | None = None,
    sweep_findings: list[dict[str, Any]] | None = None,
) -> str:
    """Ranked markdown. Narrative = eligible findings (eligibility above
    INFORMATIONAL after recency); actionable = eligibility ACTION only,
    each with its justification; incompleteness stated explicitly.

    `sweep_findings` (distribution discovery output) renders as its own
    section — cross-project observations don't belong to any single
    project item, and merging them in would hide their provenance.
    """
    held_back = 0
    scoped = []
    for item in items:
        # Copy: filtering must never mutate the caller's bundles.
        kept = [f for f in item.get("findings", []) if _fresh(f, since)]
        held_back += sum(1 for f in kept if not _narrate(f, include_related))
        narrated = aggregate_lifecycle([f for f in kept if _narrate(f, include_related)])
        assessed = []
        for finding in narrated:
            assessment = _eligibility(finding)
            if assessment["eligibility"] not in _ELIGIBLE:
                held_back += 1
                continue
            assessed.append({**finding, "_assessment": assessment})
        scoped.append({**item, "findings": assessed})
    event_count = sum(len(i["findings"]) for i in scoped)
    assessed_findings = [f for i in scoped for f in i["findings"]]
    lines = [
        f"# OpenPulse — {month}",
        "",
        f"{len(scoped)} projects monitored",
        "",
        f"{event_count} significant events",
        "",
        DISCLAIMER,
        "",
    ]
    if held_back:
        lines.append(
            f"_{held_back} related-but-unconfirmed or below-bar records held back "
            "(see `openpulse analyze` for the full stream)._"
        )
        lines.append("")
    lines.append("## What changed this month?")
    lines.append("")
    classes: dict[str, list[dict[str, Any]]] = {}
    for item in lifecycle_first(sorted(scoped, key=lambda i: i["project"])):
        if not item["findings"]:
            continue
        for finding in item["findings"]:
            classes.setdefault(_change_class(finding), []).append((item, finding))
    for heading in (
        "Lifecycle changes",
        "Distribution changes",
        "Security changes",
        "Project signals",
    ):
        group = classes.get(heading, [])
        if not group:
            continue
        lines.append(f"### {heading} ({len(group)})")
        lines.append("")
        seen_projects: set[str] = set()
        for item, finding in group:
            project = item["project"]
            if project not in seen_projects:
                seen_projects.add(project)
                lines.append(f"#### {project}")
                non_ok = [
                    f"{k} {v['status']}"
                    for k, v in item["pulse"]["facets"].items()
                    if v["status"] != "ok"
                ]
                if non_ok:
                    lines.append("Pulse: " + ", ".join(non_ok))
                lines.append("")
            lines.append(render_finding_md(finding))
            lead = _lead_time_line(finding)
            if lead:
                lines.append(lead)
            lines += _trust_block(finding)
            lines.append("")
            lines += _dependency_block(finding)
            evidence = [finding.get("analyst", "analyst")]
            evidence += [s for s in finding.get("sources", []) if s not in evidence]
            lines.append("Evidence: " + ", ".join(evidence))
            seen = set()
            refs = (
                list(finding.get("references", []) or [])
                + _supporting_urls(finding)
                + list(finding.get("evidence_links", []) or [])
            )
            for ref in refs:
                if ref and ref not in seen:
                    seen.add(ref)
                    lines.append(f"- {ref}")
            lines.append("")
    assessed_sweep = []
    for finding in sweep_findings or []:
        if not _fresh(finding, since):
            continue
        assessment = _eligibility(finding)
        if assessment["eligibility"] == "INFORMATIONAL":
            continue
        assessed_sweep.append({**finding, "_assessment": assessment})
    if assessed_sweep:
        lines.append(f"## Distribution discovery ({len(assessed_sweep)})")
        lines.append("")
        lines.append(
            "Observed registry diffs across catalog images — the standing "
            "non-lifecycle discovery capability, not curated fixtures."
        )
        lines.append("")
        for finding in assessed_sweep:
            lines.append(render_finding_md(finding))
            lead = _lead_time_line(finding)
            if lead:
                lines.append(lead)
            lines += _trust_block(finding)
            lines.append("")
            artifacts = [
                a.get("ref")
                for a in finding.get("affected_artifacts", []) or []
                if isinstance(a, dict) and a.get("ref")
            ]
            if artifacts:
                lines.append("Affected artifacts:")
                lines += [f"- `{ref}`" for ref in artifacts]
                lines.append("")
            lines += _dependency_block(finding)
            evidence = [finding.get("analyst", "analyst")]
            evidence += [s for s in finding.get("sources", []) if s not in evidence]
            lines.append("Evidence: " + ", ".join(evidence))
            seen = set()
            refs = (
                list(finding.get("references", []) or [])
                + _supporting_urls(finding)
                + list(finding.get("evidence_links", []) or [])
            )
            for ref in refs:
                if ref and ref not in seen:
                    seen.add(ref)
                    lines.append(f"- {ref}")
            lines.append("")
    actionable = [
        (item, finding)
        for item in scoped
        for finding in item["findings"]
        if finding["_assessment"]["eligibility"] == "ACTION"
    ]
    actionable += [
        ({"project": "registry sweep"}, finding)
        for finding in assessed_sweep
        if finding["_assessment"]["eligibility"] == "ACTION"
    ]
    lines.append("## What appears actionable?")
    lines.append("")
    lines.append(
        "_Action-oriented ecosystem framing, not customer impact: without "
        "a linked dependency in your inventory this is never ACTION_REQUIRED. "
        "Run `openpulse check` against a watchlist to cross the boundary._"
    )
    lines.append("")
    if not actionable:
        lines.append(
            "No changes met the action bar this month: nothing with "
            "evidence and scope justifying action-oriented framing."
        )
        lines.append("")
    for item, finding in actionable:
        reasons = finding["_assessment"].get("reasons") or []
        lines.append(f"- **{item['project']}** — {finding.get('title', 'untitled')}")
        if reasons:
            lines.append(f"  Why: {reasons[0]}")
        scope = finding.get("scope") or {}
        versions = scope.get("versions") or []
        if versions:
            lines.append(f"  Scope: {', '.join(str(v) for v in versions)}")
    if actionable:
        lines.append("")
    metrics = finding_source_distribution(assessed_findings + list(assessed_sweep))
    lines.append("## Where our data is incomplete")
    lines.append("")
    silent = sorted(i["project"] for i in scoped if not i["findings"])
    if silent:
        lines.append(f"No signals observed for: {', '.join(silent)}.")
        lines.append("")
    lines.append(
        f"{metrics['single_source_findings']} findings rest on a single recorded source; "
        f"{metrics['corroborated_findings']} cite 2+ sources, of which "
        f"{metrics['corroborating_family_count']} are corroborated across "
        "independent source families; "
        f"{metrics['no_source_findings']} carry no recorded source."
    )
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    distribution = metrics["finding_source_distribution"]
    if distribution:
        lines.append(
            "Finding source distribution: "
            + ", ".join(f"{source} {pct}%" for source, pct in distribution.items())
        )
    else:
        lines.append("Finding source distribution: no findings this month.")
    lines.append(
        f"Independent source families observed: {metrics['source_family_count']} "
        f"(across {metrics['source_count']} recorded source labels)."
    )
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        lines += [f"- {note}" for note in notes]
        lines.append("")
    return "\n".join(lines).rstrip()


def _supporting_urls(finding: dict[str, Any]) -> list[str]:
    """Source URLs carried inside supporting raw entries (endoflife links,
    GitHub release/advisory URLs). Deduplicated by the caller."""
    urls = []
    for entry in finding.get("supporting", []) or []:
        if not isinstance(entry, dict):
            continue
        for key in ("link", "url"):
            value = entry.get(key)
            if isinstance(value, str) and value.startswith("http") and value not in urls:
                urls.append(value)
    return urls


def _dependency_block(finding: dict[str, Any]) -> list[str]:
    """Structured attribution for security findings — only known fields.

    No confidence is printed: findings carry relationships, not event
    confidence. Nothing here is inferred beyond the finding data.
    """
    if not finding.get("affected_package"):
        return []
    lines = [
        f"Affected dependency: {finding['affected_package']}"
        f" {finding.get('affected_version') or '(version unknown)'}"
    ]
    action = finding.get("recommended_action")
    if action and action not in ("none", "track"):
        lines.append(f"Recommended action: {action}")
    return lines + [""]
