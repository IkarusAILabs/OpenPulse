"""Monthly report — seed + facets + top findings to ranked markdown.

Pure functions (no network): `collect_project` turns one raw bundle
into a report item; `build_report` ranks items into action-worthy /
watch / informational sections. Every item names its evidence —
findings carry sources and references, never bare assertions.
"""

from __future__ import annotations

from typing import Any

from analyzers import change_analyst, security_analyst
from analyzers.report_analyst import render_finding_md
from core.entities.catalog import project_context
from core.pulse import compute_pulse

SECTION = {
    "action": "🔴 Action-worthy changes",
    "watch": "🟠 Changes to watch",
    "info": "🟢 Important but low impact",
}


def _worst(finding: dict[str, Any]) -> str:
    impact = str(finding.get("impact", "INFORMATIONAL")).upper()
    if impact in ("CRITICAL", "ACTION"):
        return "action"
    if impact in ("REVIEW", "WATCH"):
        return "watch"
    return "info"


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


def build_report(month: str, items: list[dict[str, Any]]) -> str:
    """Ranked markdown. Significant = any finding above INFORMATIONAL."""
    significant = [i for i in items if any(_worst(f) in ("action", "watch") for f in i["findings"])]
    groups: dict[str, list[dict[str, Any]]] = {"action": [], "watch": [], "info": []}
    for item in significant:
        level = "info"
        for finding in item["findings"]:
            rank = _worst(finding)
            if rank == "action":
                level = "action"
                break
            if rank == "watch":
                level = "watch"
        groups[level].append(item)
    lines = [
        f"# OpenPulse — {month}",
        "",
        f"{len(items)} projects monitored",
        "",
        f"{len(significant)} significant events",
        "",
    ]
    for level in ("action", "watch", "info"):
        group = groups[level]
        if not group:
            continue
        lines.append(f"## {SECTION[level]} ({len(group)})")
        lines.append("")
        for item in sorted(group, key=lambda i: i["project"]):
            lines.append(f"### {item['project']}")
            lines.append("")
            non_ok = [
                f"{k} {v['status']}"
                for k, v in item["pulse"]["facets"].items()
                if v["status"] != "ok"
            ]
            if non_ok:
                lines.append("Pulse: " + ", ".join(non_ok))
                lines.append("")
            for finding in item["findings"]:
                if _worst(finding) == "info":
                    continue
                lines.append(render_finding_md(finding))
                lines.append("")
                evidence = [finding.get("analyst", "analyst")]
                evidence += [s for s in finding.get("sources", []) if s not in evidence]
                lines.append("Evidence: " + ", ".join(evidence))
                for ref in finding.get("references", []) or []:
                    lines.append(f"- {ref}")
                lines.append("")
    return "\n".join(lines).rstrip()
