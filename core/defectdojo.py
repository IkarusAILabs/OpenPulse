"""Evidence contracts -> DefectDojo "Generic Findings Import" JSON.

Security teams triage in DefectDojo; this puts OpenPulse findings there
without a new dashboard. Like ``core.sarif`` it is a presentation layer
over the v1.2 contracts ``attest`` emits, and it reuses the SARIF
module's decisions, so the JSONL, SARIF and DefectDojo outputs can never
disagree:

- NOT_AFFECTED pairs are omitted (``sarif.contract_level`` is None);
- severity follows the same impact split as the SARIF level, one step
  finer because DefectDojo has five severities:

    affected + CRITICAL impact  -> Critical
    affected + ACTION impact    -> High
    affected + REVIEW impact    -> Medium
    affected + WATCH/INFO       -> Low
    RELATED / AFFECTS_PROJECT   -> Info (a match, impact not established)

- a dependency no supplied event applies to is ONE Info finding ("no
  applicable OpenPulse evidence"), never silently dropped;
- ``unique_id_from_tool`` is the SARIF fingerprint (dependency + event),
  so re-imports deduplicate instead of piling up.

Pure: no I/O, no clock (dates come from the contracts). Import with the
"Generic Findings Import" scan type, by UI or API.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from core.sarif import _evidence_urls, _fingerprint, _no_applicable_event, contract_level

SCAN_TYPE = "Generic Findings Import"

_SEVERITY = {"CRITICAL": "Critical", "ACTION": "High", "REVIEW": "Medium"}


def finding_severity(doc: dict[str, Any]) -> str | None:
    """DefectDojo severity for one contract, or None when it is omitted."""
    if contract_level(doc) is None:
        return None
    if not doc["assessment"]["affected"]:
        return "Info"
    return _SEVERITY.get(str(doc["event_context"]["impact"]).upper(), "Low")


def _component(label: str) -> tuple[str, str | None]:
    """`django==4.2` -> (django, 4.2); `postgres:13` -> (postgres:13, 13);
    `redis@sha256:..` -> (redis@sha256:.., None): a digest is not a version."""
    if "==" in label:
        name, version = label.split("==", 1)
        return name, version
    tail = label.split("@", 1)[0].rsplit("/", 1)[-1]
    if ":" in tail:
        return label, tail.split(":", 1)[1]
    return label, None


def _date(doc: dict[str, Any]) -> str:
    temporal = doc.get("temporal") or {}
    for key in ("first_detected", "effective_date", "announcement_date"):
        if temporal.get(key):
            return str(temporal[key])[:10]
    return str(doc["provenance"]["generation_timestamp"])[:10]


def _pair_finding(doc: dict[str, Any], path: str, severity: str) -> dict[str, Any]:
    event = doc["event_context"]
    assessment = doc["assessment"]
    label = str(doc["affected_dependency"]["label"])
    name, version = _component(label)
    urls = _evidence_urls(doc)
    unknowns = (doc.get("unknowns") or {}).get("unknowns") or []
    description = "\n".join(
        [
            f"**{label}** - {assessment['relationship']} [{event['impact']}]",
            "",
            f"{event['title']}.",
            "",
            f"- Reason: {assessment['reason']}",
            f"- Confidence: {assessment['confidence']} "
            f"(evidence {assessment.get('evidence_confidence', 'UNVERIFIED')})",
            f"- Identity: {doc['identity']['identity_status']} via "
            f"{doc['identity']['identity_via']}",
            f"- Inspection coverage: {doc['inspection_coverage']['status']}",
            f"- Evidence: {', '.join(urls) if urls else 'none cited (UNKNOWN)'}",
            *[f"- Not established: {u}" for u in unknowns],
            f"- Evidence contract: {doc['provenance']['content_hash']}",
        ]
    )
    finding = {
        "title": f"{label}: {event['title']}"[:500],
        "severity": severity,
        "description": description,
        "mitigation": str((doc.get("recommendation") or {}).get("text") or ""),
        "references": "\n".join(urls),
        "date": _date(doc),
        "component_name": name,
        "file_path": path,
        "unique_id_from_tool": _fingerprint(label, str(event["id"])),
        "vuln_id_from_tool": str(event["id"]),
        "active": True,
        "verified": False,
        "static_finding": True,
        "dynamic_finding": False,
        "tags": ["openpulse", str(event["event_type"]).lower(), str(assessment["relationship"])],
    }
    if version:
        finding["component_version"] = version
    if str(event["id"]).upper().startswith("CVE-"):
        finding["cve"] = str(event["id"])
    return finding


def _unknown_finding(label: str, path: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    name, version = _component(label)
    finding = {
        "title": f"{label}: no applicable OpenPulse evidence",
        "severity": "Info",
        "description": (
            f"**{label}** was evaluated against {len(docs)} event(s); none applies. "
            "UNKNOWN is not NOT_AFFECTED: OpenPulse established nothing about this "
            "dependency."
        ),
        "mitigation": "",
        "references": "",
        "date": str(docs[0]["provenance"]["generation_timestamp"])[:10],
        "component_name": name,
        "file_path": path,
        "unique_id_from_tool": _fingerprint(label, "openpulse/no-applicable-evidence"),
        "vuln_id_from_tool": "openpulse/no-applicable-evidence",
        "active": True,
        "verified": False,
        "static_finding": True,
        "dynamic_finding": False,
        "tags": ["openpulse", "unknown"],
    }
    if version:
        finding["component_version"] = version
    return finding


def build_findings(entries: Iterable[tuple[dict[str, Any], str]]) -> dict[str, Any]:
    """(contract, file path) pairs -> a Generic Findings Import document."""
    # Same grouping as core.sarif._results: per (file, dependency), "no
    # applicable evidence" only when EVERY contract is UNKNOWN; otherwise
    # the UNKNOWN pairs are superseded by the verdicts that were reached.
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for doc, path in entries:
        groups.setdefault((path, str(doc["affected_dependency"]["label"])), []).append(doc)
    findings: list[dict[str, Any]] = []
    for (path, label), docs in groups.items():
        if all(_no_applicable_event(d) for d in docs):
            findings.append(_unknown_finding(label, path, docs))
            continue
        for doc in docs:
            if _no_applicable_event(doc):
                continue
            severity = finding_severity(doc)
            if severity is not None:
                findings.append(_pair_finding(doc, path, severity))
    findings.sort(key=lambda f: (f["file_path"], f["component_name"], f["vuln_id_from_tool"]))
    return {"findings": findings}
