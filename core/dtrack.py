"""Evidence contracts -> Dependency-Track (INTERNAL vulnerabilities).

Dependency-Track only tracks vulnerabilities, so an OpenPulse finding
enters it the way DT itself supports manual findings: as an INTERNAL
vulnerability (`PUT /api/v1/vulnerability`, VULNERABILITY_MANAGEMENT)
assigned to the matching components of one project
(`POST /api/v1/vulnerability/source/INTERNAL/vuln/{vulnId}/component/{uuid}`,
PORTFOLIO_MANAGEMENT). Endpoints verified against DT's v1 REST resources.

What is pushed, and what is not:

- only AFFECTED dependency x event pairs: DT treats anything assigned as
  vulnerable, so RELATED / UNKNOWN / NOT_AFFECTED stay out (they remain
  in the JSONL, SARIF and DefectDojo outputs);
- one DT vulnerability per OpenPulse event (`OPENPULSE-<event id>`),
  assigned to every affected component - the same event never becomes N
  duplicate vulnerabilities;
- severity follows the DefectDojo mapping (core.defectdojo.finding_severity);
- a dependency that is not a component of the DT project is reported as
  not found, never guessed onto a different component.

Planning (`plan`) is pure; `upload` takes an httpx.Client so tests use a
MockTransport. Re-running is idempotent: an existing vulnerability (409)
is reused and re-assigning is a no-op in DT.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import quote, urlsplit

import httpx

from collectors.errors import safe_message
from core.defectdojo import finding_severity
from core.sarif import _evidence_urls

VULN_PREFIX = "OPENPULSE-"
API_KEY_ENV = "OPENPULSE_DTRACK_API_KEY"


def _vuln_id(event_id: str) -> str:
    printable = "".join(c if c.isprintable() and not c.isspace() else "-" for c in event_id)
    return (VULN_PREFIX + printable)[:255]


def _coordinates(label: str) -> dict[str, str]:
    """DT component identity (group/name/version) for a dependency label.

    Maven `group:artifact` and npm `@scope/name` carry a group; images use
    the repository name and tag, which is how container SBOMs record them.
    """
    coords: dict[str, str] = {}
    if "==" in label:
        name, version = label.split("==", 1)
        if name.startswith("@") and "/" in name:  # npm scope
            coords["group"], name = name.split("/", 1)
        elif ":" in name:  # maven group:artifact
            coords["group"], name = name.split(":", 1)
    else:  # image ref: repository name + tag (a digest is not a version)
        repo = label.split("@", 1)[0].rsplit("/", 1)[-1]
        name, _, version = repo.partition(":")
    coords["name"] = name
    if version:
        coords["version"] = version
    return coords


def plan(docs: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Affected pairs grouped per event -> [{vulnerability, components}]."""
    by_event: dict[str, dict[str, Any]] = {}
    for doc in docs:
        if not doc["assessment"]["affected"]:
            continue
        severity = finding_severity(doc)
        if severity is None:
            continue
        event = doc["event_context"]
        entry = by_event.setdefault(
            str(event["id"]),
            {"vulnerability": _vulnerability(doc, severity), "components": []},
        )
        label = str(doc["affected_dependency"]["label"])
        if all(c["label"] != label for c in entry["components"]):
            entry["components"].append(
                {
                    "label": label,
                    "identity": _coordinates(label),
                    "content_hash": doc["provenance"]["content_hash"],
                }
            )
    return [by_event[k] for k in sorted(by_event)]


def _vulnerability(doc: dict[str, Any], severity: str) -> dict[str, Any]:
    event = doc["event_context"]
    urls = _evidence_urls(doc)
    temporal = doc.get("temporal") or {}
    dates = ", ".join(
        f"{key.replace('_', ' ')}: {temporal[key]}"
        for key in ("announcement_date", "effective_date")
        if temporal.get(key)
    )
    description = (
        f"OpenPulse upstream-change finding ({event['event_type']}, impact "
        f"{event['impact']}, evidence {event['confidence']}). {event['title']}."
        + (f" {dates}." if dates else "")
        + " Assigned components are those OpenPulse established as affected; see each "
        "dependency's evidence contract (content hash in the OpenPulse output)."
    )
    return {
        "vulnId": _vuln_id(str(event["id"])),
        "source": "INTERNAL",
        "title": str(event["title"])[:255],
        "description": description,
        "recommendation": str((doc.get("recommendation") or {}).get("text") or ""),
        "references": "\n".join(f"* {u}" for u in urls),
        "severity": severity.upper(),
        "credits": "OpenPulse",
    }


def check_url(url: str, allow_http: bool = False) -> str:
    """Base URL sanity: https unless opted out, no credentials, no query."""
    parts = urlsplit(url)
    if parts.scheme not in ("https", "http") or not parts.hostname:
        raise ValueError("Dependency-Track URL must be http(s)://host[:port][/path]")
    if parts.scheme == "http" and not allow_http:
        raise ValueError("http Dependency-Track URLs need --allow-http (the API key is sent)")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Dependency-Track URL must not carry credentials, query or fragment")
    return url.rstrip("/")


def lookup_project(client: httpx.Client, name: str, version: str) -> str:
    response = client.get("/api/v1/project/lookup", params={"name": name, "version": version})
    if response.status_code == 404:
        raise ValueError(f"Dependency-Track project {name!r} {version!r} not found")
    response.raise_for_status()
    return str(response.json()["uuid"])


def upload(
    client: httpx.Client, project_uuid: str, planned: list[dict[str, Any]]
) -> dict[str, Any]:
    """Create/reuse each vulnerability and assign it to the project's components."""
    report: dict[str, Any] = {
        "created": [],
        "existing": [],
        "assigned": [],
        "not_found": [],
        "errors": [],
    }
    for item in planned:
        vuln = item["vulnerability"]
        vuln_id = vuln["vulnId"]
        try:
            response = client.put("/api/v1/vulnerability", json=vuln)
            if response.status_code == 409:
                report["existing"].append(vuln_id)
            else:
                response.raise_for_status()
                report["created"].append(vuln_id)
        except httpx.HTTPError as exc:
            report["errors"].append(f"{vuln_id}: create failed: {safe_message(exc)}")
            continue
        for component in item["components"]:
            label = component["label"]
            try:
                found = client.get(
                    "/api/v1/component/identity",
                    params={**component["identity"], "project": project_uuid},
                )
                found.raise_for_status()
                matches = [c for c in found.json() or [] if c.get("uuid")]
                if not matches:
                    report["not_found"].append(label)
                    continue
                for match in matches:
                    path = (
                        f"/api/v1/vulnerability/source/INTERNAL/vuln/{quote(vuln_id, safe='')}"
                        f"/component/{quote(str(match['uuid']), safe='')}"
                    )
                    client.post(path).raise_for_status()
                    report["assigned"].append(f"{vuln_id} -> {label}")
            except httpx.HTTPError as exc:
                report["errors"].append(f"{vuln_id} -> {label}: {safe_message(exc)}")
    return report
