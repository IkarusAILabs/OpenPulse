"""Watchlist checking — Dependency Early Warning preview.

A watchlist names the dependencies a team actually runs (image refs
and/or packages with versions). `check_watchlist` evaluates each
against intelligence events (artifact/project matching) and, where a
raw bundle is available, version-aware correlation (OSV/CPE ranges →
AFFECTS_VERSION for exact pins). Pure functions; no network.
"""

from __future__ import annotations

from typing import Any

from analyzers.security_analyst import correlate
from core.entities.resolve import resolve_project
from core.risk.match import event_affects_ref
from core.schema.models import OSSEvent

_REL_RANK = {
    "UNKNOWN": 0,
    "RELATED": 1,
    "AFFECTS_PROJECT": 2,
    "AFFECTS_PACKAGE": 3,
    "AFFECTS_VERSION": 4,
    "AFFECTS_ARTIFACT": 5,
}


def load_watchlist_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate a parsed watchlist document into normalized dep entries."""
    if not isinstance(doc, dict):
        raise ValueError("watchlist must be a mapping")
    deps = doc.get("dependencies", [])
    if not isinstance(deps, list) or not deps:
        raise ValueError("watchlist needs a non-empty `dependencies` list")
    normalized = []
    for i, dep in enumerate(deps):
        if not isinstance(dep, dict):
            raise ValueError(f"dependency #{i} must be a mapping")
        if dep.get("ref"):
            normalized.append({"kind": "image", "ref": str(dep["ref"])})
        elif dep.get("package"):
            normalized.append(
                {
                    "kind": "package",
                    "package": str(dep["package"]),
                    "ecosystem": str(dep.get("ecosystem", "")),
                    "version": str(dep["version"]) if dep.get("version") else None,
                }
            )
        else:
            raise ValueError(f"dependency #{i} needs `ref` or `package`")
    return normalized


def _strongest_correlation(findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    best = None
    for finding in findings:
        rank = _REL_RANK.get(str(finding.get("relationship", "UNKNOWN")), 0)
        if best is None or rank > _REL_RANK.get(str(best.get("relationship", "UNKNOWN")), 0):
            best = finding
    return best


def check_dependency(
    dep: dict[str, Any], events: list[OSSEvent], bundles: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any]:
    """One dep vs events (+ optional raw bundles) -> verdict dict."""
    bundles = bundles or {}
    verdicts = []
    if dep["kind"] == "image":
        for event in events:
            match = event_affects_ref(event, dep["ref"])
            if match["affected"]:
                verdicts.append(
                    {
                        "affected": True,
                        "relationship": match["relationship"],
                        "via": match["via"],
                        "event_id": event.id,
                        "impact": event.impact.value,
                        "detail": match["detail"],
                    }
                )
    else:
        slug = resolve_project(dep["package"])
        for event in events:
            if slug == event.project_slug:
                verdicts.append(
                    {
                        "affected": True,
                        "relationship": "AFFECTS_PROJECT",
                        "via": "project",
                        "event_id": event.id,
                        "impact": event.impact.value,
                        "detail": f"{dep['package']} resolves to {event.project_slug}",
                    }
                )
        raw = bundles.get(slug)
        if raw is not None:
            context = {
                "slug": slug,
                "package": dep["package"],
                "ecosystem": dep["ecosystem"],
                "version": dep["version"],
            }
            best = _strongest_correlation(correlate(raw, context))
            if best and str(best.get("relationship", "UNKNOWN")) not in ("UNKNOWN",):
                verdicts.append(
                    {
                        "affected": best["relationship"] in ("AFFECTS_VERSION", "AFFECTS_PACKAGE"),
                        "relationship": best["relationship"],
                        "via": f"correlation:{best.get('match_method')}",
                        "event_id": None,
                        "impact": best.get("impact"),
                        "detail": (
                            f"{best.get('cve_id')} [{best.get('relationship')}]"
                            f" via {best.get('match_method')}"
                        ),
                    }
                )
    if not verdicts:
        return {"dep": dep, "affected": False, "relationship": "UNKNOWN", "verdicts": []}
    top = max(verdicts, key=lambda v: _REL_RANK.get(str(v["relationship"]), 0))
    return {
        "dep": dep,
        "affected": any(v["affected"] for v in verdicts),
        "relationship": top["relationship"],
        "verdicts": verdicts,
    }
