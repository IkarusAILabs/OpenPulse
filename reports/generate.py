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


def build_report(
    month: str,
    items: list[dict[str, Any]],
    since: str | None = None,
    include_related: bool = False,
    notes: list[str] | None = None,
) -> str:
    """Ranked markdown. Significant = findings above INFORMATIONAL (after recency)."""
    held_back = 0
    scoped = []
    for item in items:
        # Copy: filtering must never mutate the caller's bundles.
        kept = [f for f in item.get("findings", []) if _fresh(f, since)]
        held_back += sum(1 for f in kept if not _narrate(f, include_related))
        scoped.append({**item, "findings": [f for f in kept if _narrate(f, include_related)]})
    significant = [
        i for i in scoped if any(_worst(f) in ("action", "watch") for f in i["findings"])
    ]
    event_count = sum(
        1 for i in significant for f in i["findings"] if _worst(f) in ("action", "watch")
    )
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
        f"{len(scoped)} projects monitored",
        "",
        f"{event_count} significant events",
        "",
    ]
    if held_back:
        lines.append(
            f"_{held_back} related-but-unconfirmed records held back "
            "(see `openpulse analyze` for the full stream)._"
        )
        lines.append("")
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
                lines += _dependency_block(finding)
                evidence = [finding.get("analyst", "analyst")]
                evidence += [s for s in finding.get("sources", []) if s not in evidence]
                lines.append("Evidence: " + ", ".join(evidence))
                seen = set()
                for ref in list(finding.get("references", []) or []) + _supporting_urls(finding):
                    if ref and ref not in seen:
                        seen.add(ref)
                        lines.append(f"- {ref}")
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
