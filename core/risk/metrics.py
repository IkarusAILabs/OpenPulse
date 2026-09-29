"""Report metrics — source dependence and intelligence ratio (§16, §17).

``finding_source_distribution`` makes the monthly report evidence-aware:
which collectors the findings actually rest on. The Independent
Intelligence Ratio stays internal (methodology not yet stable — never
market it): the share of material findings whose conclusion required
OpenPulse correlation rather than raw source output. Pure functions.
"""

from __future__ import annotations

from typing import Any

#: Collector/system names normalized to reportable source labels.
_SOURCE_LABELS = {
    "endoflife": "endoflife.date",
    "endoflife.date": "endoflife.date",
    "github": "GitHub",
    "github_meta": "GitHub",
    "nvd": "NVD",
    "osv": "OSV",
    "cve": "CVE",
    "kev": "CISA KEV",
    "registries": "Registry",
    "registry": "Registry",
    "change": "OpenPulse change analysis",
    "event-correlation": "OpenPulse correlation",
    "security": "OpenPulse security analysis",
}


def _finding_sources(finding: dict[str, Any]) -> list[str]:
    """Distinct normalized source labels behind one finding."""
    raw: list[str] = []
    for key in ("sources",):
        values = finding.get(key) or []
        if isinstance(values, str):
            values = [values]
        raw.extend(str(v) for v in values if v)
    for entry in finding.get("supporting", []) or []:
        if not isinstance(entry, dict):
            continue
        collector = entry.get("collector")
        if collector:
            raw.append(str(collector))
        source = entry.get("source")
        if isinstance(source, dict) and source.get("name"):
            raw.append(str(source["name"]).split("/")[0])
    seen: list[str] = []
    for name in raw:
        label = _SOURCE_LABELS.get(name, _SOURCE_LABELS.get(name.lower(), name))
        if label not in seen:
            seen.append(label)
    return seen


def finding_source_distribution(
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Share of findings resting on each source + evidence tiers.

    One vote per finding (multi-evidence findings do not skew the
    distribution). Tiers: corroborated (2+ distinct sources),
    single-source (exactly 1), no-source (none recorded).
    """
    counts: dict[str, int] = {}
    corroborated = single_source = no_source = 0
    for finding in findings or []:
        sources = _finding_sources(finding if isinstance(finding, dict) else {})
        if not sources:
            no_source += 1
            continue
        if len(sources) >= 2:
            corroborated += 1
        else:
            single_source += 1
        for source in sources:
            counts[source] = counts.get(source, 0) + 1
    total = corroborated + single_source + no_source
    distribution = {
        source: round(100.0 * count / total, 1) if total else 0.0
        for source, count in sorted(counts.items(), key=lambda kv: -kv[1])
    }
    return {
        "finding_source_distribution": distribution,
        "independent_sources": len(counts),
        "single_source_findings": single_source,
        "corroborated_findings": corroborated,
        "no_source_findings": no_source,
        "total_findings": total,
    }


def _is_derived(finding: dict[str, Any]) -> bool:
    """True when the conclusion required OpenPulse correlation."""
    if not isinstance(finding, dict):
        return False
    if finding.get("analyst") == "event-correlation":
        return True
    relationship = str(finding.get("relationship") or "")
    if relationship in (
        "AFFECTS_ARTIFACT",
        "AFFECTS_VERSION",
        "AFFECTS_PACKAGE",
        "NOT_AFFECTED",
    ):
        return True
    if finding.get("stories_merged"):
        return True
    return False


def derived_intelligence_ratio(
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Internal health metric: derived conclusions over material ones.

    Material = eligibility other than INFORMATIONAL (evaluated lazily
    here via analyst impact as a proxy: CRITICAL/ACTION/REVIEW/WATCH).
    NOT marketed — methodology pending stability.
    """
    material = [
        f for f in (findings or []) if isinstance(f, dict)
        and str(f.get("impact", "INFORMATIONAL")).upper()
        in ("CRITICAL", "ACTION", "REVIEW", "WATCH")
    ]
    derived = [f for f in material if _is_derived(f)]
    ratio = round(len(derived) / len(material), 3) if material else 0.0
    return {
        "derived_intelligence_ratio": ratio,
        "derived_findings": len(derived),
        "material_findings": len(material),
    }


# Backwards-compatible alias (previous name conflated source
# independence with derived correlation; prefer the new name).
def independent_intelligence_ratio(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Deprecated alias of :func:`derived_intelligence_ratio`."""
    result = derived_intelligence_ratio(findings)
    result["independent_intelligence_ratio"] = result.pop("derived_intelligence_ratio")
    return result
