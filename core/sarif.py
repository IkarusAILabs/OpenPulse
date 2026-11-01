"""Evidence contracts -> SARIF 2.1.0 + Markdown job summary (Phase C3).

A presentation layer over the v1.2 evidence contracts ``attest``
already emits, so the SARIF log, the job summary and the JSONL can
never disagree: every SARIF result carries the exact
``provenance.content_hash`` of the contract it renders.

Level mapping (per dependency x event contract):

- affected + ACTION/CRITICAL impact -> ``error``
- affected + REVIEW impact          -> ``warning``
- affected + WATCH/INFORMATIONAL    -> ``note``
- RELATED / AFFECTS_PROJECT / UNKNOWN with a match -> ``note``
- NOT_AFFECTED                      -> omitted

Unknown stays unknown: a dependency that no event applies to at all
(every contract UNKNOWN with no match method) is reported ONCE as a
``note`` under ``openpulse/no-applicable-evidence`` - never silently
dropped, and never decorated with evidence URLs of events that do not
concern it. Repository inspection coverage other than COMPLETE becomes
a warning tool notification; it is never a pass.

Pure: no I/O, no clock. Same contracts in -> byte-identical SARIF out.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
INFORMATION_URI = "https://github.com/IkarusAILabs/OpenPulse"

#: Rule for dependencies no supplied event applies to.
NO_EVIDENCE_RULE = "openpulse/no-applicable-evidence"

_ERROR_IMPACTS = ("ACTION", "CRITICAL")
_LEVEL_ORDER = {"error": 0, "warning": 1, "note": 2}


def _rule_id(event_type: str) -> str:
    return "openpulse/" + event_type.lower().replace("_", "-")


def contract_level(doc: dict[str, Any]) -> str | None:
    """SARIF level for one contract, or None when it is omitted."""
    assessment = doc["assessment"]
    relationship = str(assessment["relationship"])
    if relationship == "NOT_AFFECTED":
        return None
    if assessment["affected"]:
        impact = str(doc["event_context"]["impact"]).upper()
        if impact in _ERROR_IMPACTS:
            return "error"
        if impact == "REVIEW":
            return "warning"
    return "note"


def _no_applicable_event(doc: dict[str, Any]) -> bool:
    """The pair was evaluated and the event does not concern the dependency."""
    return doc["assessment"]["relationship"] == "UNKNOWN" and not doc["affected_dependency"].get(
        "match_method"
    )


def _fingerprint(*parts: str) -> str:
    """Stable alert identity across runs (contract hashes change with content)."""
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _location(uri: str) -> dict[str, Any]:
    return {"physicalLocation": {"artifactLocation": {"uri": uri}}}


def _evidence_urls(doc: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for ref in doc.get("evidence_refs") or []:
        url = ref.get("url")
        if url and url not in urls:
            urls.append(str(url))
    return urls


def _pair_result(doc: dict[str, Any], uri: str, level: str) -> dict[str, Any]:
    event = doc["event_context"]
    assessment = doc["assessment"]
    label = str(doc["affected_dependency"]["label"])
    content_hash = str(doc["provenance"]["content_hash"])
    urls = _evidence_urls(doc)
    evidence = ", ".join(urls) if urls else "none cited (UNKNOWN)"
    text = (
        f"{label}: {assessment['relationship']} [{event['impact']}] - {event['title']}. "
        f"{assessment['reason']}. Evidence: {evidence}. Contract: {content_hash}"
    )
    return {
        "ruleId": _rule_id(str(event["event_type"])),
        "level": level,
        "message": {"text": text},
        "locations": [_location(uri)],
        "partialFingerprints": {"openpulseFinding/v1": _fingerprint(label, str(event["id"]))},
        "properties": {
            "dependency": label,
            "relationship": assessment["relationship"],
            "affected": bool(assessment["affected"]),
            "confidence": assessment["confidence"],
            "impact": event["impact"],
            "event_id": event["id"],
            "event_type": event["event_type"],
            "evidence_urls": urls,
            "content_hash": content_hash,
            "contract_version": doc["contract_version"],
            "inspection_coverage": doc["inspection_coverage"]["status"],
        },
    }


def _unknown_result(label: str, uri: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = sorted(str(d["provenance"]["content_hash"]) for d in docs)
    text = (
        f"{label}: UNKNOWN - evaluated against {len(docs)} event(s), no applicable "
        "evidence. Not a clean bill of health: no supplied event covers this dependency."
    )
    return {
        "ruleId": NO_EVIDENCE_RULE,
        "level": "note",
        "message": {"text": text},
        "locations": [_location(uri)],
        "partialFingerprints": {"openpulseFinding/v1": _fingerprint(label, NO_EVIDENCE_RULE)},
        "properties": {
            "dependency": label,
            "relationship": "UNKNOWN",
            "affected": False,
            "event_ids": sorted(str(d["event_context"]["id"]) for d in docs),
            "content_hashes": hashes,
            "contract_version": docs[0]["contract_version"],
            "inspection_coverage": docs[0]["inspection_coverage"]["status"],
        },
    }


def _results(entries: list[tuple[dict[str, Any], str]]) -> tuple[list[dict[str, Any]], int]:
    """(results, omitted NOT_AFFECTED count) in a deterministic order."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for doc, uri in entries:
        key = (uri, str(doc["affected_dependency"]["label"]))
        groups.setdefault(key, []).append(doc)
    results: list[dict[str, Any]] = []
    omitted = 0
    for (uri, label), docs in groups.items():
        if all(_no_applicable_event(d) for d in docs):
            results.append(_unknown_result(label, uri, docs))
            continue
        for doc in docs:
            if _no_applicable_event(doc):
                # Superseded: another event did reach a verdict for
                # this dependency, exactly as `check` combines causes.
                continue
            level = contract_level(doc)
            if level is None:
                omitted += 1
                continue
            results.append(_pair_result(doc, uri, level))
    results.sort(
        key=lambda r: (
            _LEVEL_ORDER[r["level"]],
            r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
            r["properties"]["dependency"],
            r["ruleId"],
            str(r["properties"].get("event_id", "")),
        )
    )
    return results, omitted


_RULE_TEXT = {
    NO_EVIDENCE_RULE: "No supplied event applies to this dependency (UNKNOWN, not clean)",
}


def _rules(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules = []
    for rule_id in sorted({r["ruleId"] for r in results}):
        name = rule_id.split("/", 1)[1]
        default = f"Upstream {name.replace('-', ' ')} event affects dependency"
        text = _RULE_TEXT.get(rule_id, default)
        rules.append(
            {
                "id": rule_id,
                "name": "".join(part.capitalize() for part in name.split("-")),
                "shortDescription": {"text": text},
                "helpUri": INFORMATION_URI + "/blob/main/docs/EVIDENCE_CONTRACT.md",
                "properties": {"tags": ["dependency", "supply-chain", "openpulse"]},
            }
        )
    return rules


def build_sarif(
    entries: Iterable[tuple[dict[str, Any], str]],
    *,
    tool_version: str,
    coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """(contract, artifact uri) pairs -> one SARIF 2.1.0 log (single run).

    ``coverage`` is the run-level repository inspection block
    (``{"status", "reasons"}``); PARTIAL and FAILED are surfaced as a
    warning notification so a partial scan can never read as clean.
    NOT_APPLICABLE (no repository in the run) has nothing to warn about.
    """
    pairs = list(entries)
    results, omitted = _results(pairs)
    rules = _rules(results)
    index = {rule["id"]: i for i, rule in enumerate(rules)}
    for result in results:
        result["ruleIndex"] = index[result["ruleId"]]
    status = str((coverage or {}).get("status") or "COMPLETE")
    notifications = []
    if status not in ("COMPLETE", "NOT_APPLICABLE"):
        reasons = "; ".join(str(r) for r in (coverage or {}).get("reasons") or []) or "no reason"
        notifications.append(
            {
                "level": "warning",
                "message": {
                    "text": f"repository inspection coverage {status}: {reasons}. "
                    "Results are not a clean bill of health."
                },
            }
        )
    invocation: dict[str, Any] = {"executionSuccessful": True}
    if notifications:
        invocation["toolExecutionNotifications"] = notifications
    return {
        "$schema": SARIF_SCHEMA_URI,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "OpenPulse",
                        "informationUri": INFORMATION_URI,
                        "version": tool_version,
                        "semanticVersion": tool_version,
                        "rules": rules,
                    }
                },
                "invocations": [invocation],
                "results": results,
                "properties": {
                    "inspection_coverage": status,
                    "contracts": len(pairs),
                    "not_affected_omitted": omitted,
                },
            }
        ],
    }


def _md(text: Any) -> str:
    """Escape table-breaking characters in untrusted event/dependency text."""
    return str(text).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def render_summary(sarif: dict[str, Any]) -> str:
    """Markdown job summary (``$GITHUB_STEP_SUMMARY``) from a SARIF log."""
    run = sarif["runs"][0]
    results = run["results"]
    props = run["properties"]
    counts = {level: sum(1 for r in results if r["level"] == level) for level in _LEVEL_ORDER}
    lines = [
        "## OpenPulse dependency intelligence",
        "",
        f"- **error** (affected, ACTION/CRITICAL): {counts['error']}",
        f"- **warning** (affected, REVIEW): {counts['warning']}",
        f"- **note** (UNKNOWN / RELATED / lower impact): {counts['note']}",
        f"- NOT_AFFECTED pairs omitted: {props['not_affected_omitted']}",
        f"- Evidence contracts rendered: {props['contracts']}",
        f"- Repository inspection coverage: **{props['inspection_coverage']}**",
    ]
    for invocation in run.get("invocations", []):
        for note in invocation.get("toolExecutionNotifications", []):
            lines += ["", f"> [!WARNING]\n> {_md(note['message']['text'])}"]
    if results:
        lines += [
            "",
            "| Level | File | Dependency | Verdict | Impact | Event | Evidence | Contract |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in results:
            p = r["properties"]
            urls = p.get("evidence_urls") or []
            evidence = " ".join(f"[{i + 1}]({_md(u)})" for i, u in enumerate(urls)) or "-"
            hashes = p.get("content_hashes") or [p.get("content_hash", "")]
            contract = ", ".join(f"`{_md(h)[:19]}`" for h in hashes if h) or "-"
            event = p.get("event_id") or f"{len(p.get('event_ids', []))} event(s)"
            uri = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            lines.append(
                f"| {r['level']} | `{_md(uri)}` | `{_md(p['dependency'])}` | {p['relationship']} | "
                f"{_md(p.get('impact', '-'))} | {_md(event)} | {evidence} | {contract} |"
            )
    lines += [
        "",
        "UNKNOWN means no applicable evidence, not safe. Full contracts: the "
        "evidence-contract JSONL (`attest --output`); each hash recomputes from its content.",
        "",
    ]
    return "\n".join(lines)
