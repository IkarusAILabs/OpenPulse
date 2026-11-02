"""Known-malicious records: does OSV publish a malicious-package record? (v0.13 X1).

OSV carries the OpenSSF malicious-packages feed as ``MAL-`` records. This
check asks OSV about one PyPI or npm package (and version, when given) and
reports T-F1 records:

- a ``MAL-`` record that is not withdrawn: CONFIRMED_MALICIOUS, citing
  each record. OpenPulse never assigns this status on its own indicators;
- no such record: MISSING_EVIDENCE. The feed covers what was reported, so
  absence is not evidence that a package is safe;
- OSV gave no usable or complete answer (any status but 200, a bad body, a
  paged answer, offline, a spent budget, an unsupported ecosystem):
  NOT_PERFORMED.

There is no VERIFIED_RELATIONSHIP: nothing here can show a package is
benign. Record ids are validated before they appear, statements are fixed
templates and no advisory text is echoed (T-F3). Nothing here feeds a
verdict.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from core.registry_existence import (
    _NPM_NAME,
    _NPM_VERSION,
    _PYPI_NAME,
    _PYPI_VERSION,
    CONFIRMED_MALICIOUS,
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    _now,
    ecosystem_of,
)

CHECK = "malicious"
API = "https://api.osv.dev/v1/query"
#: OSV answers for one package stay small; a popular package's full history fits.
MAX_OSV_BYTES = 8 * 1024 * 1024
MAX_CITED = 10

_MAL_ID = re.compile(r"MAL-[0-9]{4}-[0-9]{1,9}")

_STATEMENTS = {
    CONFIRMED_MALICIOUS: (
        "OSV published {n} malicious-package record(s) for this {scope} at {at}, cited "
        "under evidence"
    ),
    MISSING_EVIDENCE: (
        "OSV published no malicious-package record for this {scope} at {at}; the feed "
        "covers reported packages only, so this is not evidence that the package is safe"
    ),
    NOT_PERFORMED: "malicious-package records not checked: {why}",
}
_WHY = {
    "unsupported": "checked for PyPI and npm packages only",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "invalid": "the name or version does not match the ecosystem's grammar",
    "unreachable": "OSV gave no usable answer at {at}",
    "partial": "OSV paged its answer at {at}; the first page held no such record",
}

#: request body -> (http status, parsed JSON or None). 0 means no response.
Query = Callable[[dict[str, Any]], tuple[int, Any]]


def http_query(body: dict[str, Any]) -> tuple[int, Any]:
    """POST ``body`` to OSV (size-capped); (status, JSON or None). Never raises."""
    from collectors import http
    from core.registry_existence import TIMEOUT_SECONDS, user_agent

    try:
        response = http.post(
            API,
            json=body,
            max_bytes=MAX_OSV_BYTES,
            timeout=TIMEOUT_SECONDS,
            headers={"user-agent": user_agent(), "accept": "application/json"},
        )
    except Exception:  # network, DNS, TLS, oversize: NOT_PERFORMED, never a crash
        return 0, None
    if response.status_code != 200:
        return response.status_code, None
    try:
        return 200, response.json()
    except ValueError:
        return 200, None


#: The query used when none is injected (tests replace it to stay offline).
default_query: Query = http_query


def _record(status: str, at: str, *, scope: str = "package", why: str = "", **evidence: Any):
    statement = _STATEMENTS[status].format(
        n=evidence.get("records_total", 0), scope=scope, at=at, why=_WHY.get(why, "").format(at=at)
    )
    return {
        "check": CHECK,
        "status": status,
        "statement": statement,
        "checked_at": at,
        "evidence": evidence,
    }


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, _now(), why=why)


def _malicious_ids(vuln: dict[str, Any]) -> list[str]:
    """The valid MAL- ids a record carries as its id or an alias."""
    candidates = [vuln.get("id"), *(vuln.get("aliases") or [])]
    return [str(c) for c in candidates if isinstance(c, str) and _MAL_ID.fullmatch(c)]


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    query: Query | None = None,
) -> dict[str, Any]:
    """One T-F1 record for one package (and version). Never raises on OSV trouble."""
    eco = ecosystem_of(ecosystem)
    if eco is None:
        return not_performed("unsupported")
    name_ok, version_ok = (
        (_PYPI_NAME, _PYPI_VERSION) if eco == "PyPI" else (_NPM_NAME, _NPM_VERSION)
    )
    if not name_ok.fullmatch(name) or (version and not version_ok.fullmatch(version)):
        return not_performed("invalid")
    body: dict[str, Any] = {"package": {"name": name, "ecosystem": eco}}
    if version:
        body["version"] = version
    status, doc = (query or default_query)(body)
    at = _now()
    if status != 200 or not isinstance(doc, dict) or not isinstance(doc.get("vulns", []), list):
        return _record(NOT_PERFORMED, at, why="unreachable", http_status=status or None)
    scope = "package and version" if version else "package"
    found: list[str] = []
    withdrawn = 0
    for vuln in doc.get("vulns") or []:
        if not isinstance(vuln, dict):
            continue
        ids = _malicious_ids(vuln)
        if not ids:
            continue
        if vuln.get("withdrawn"):
            withdrawn += 1
            continue
        found.extend(i for i in ids if i not in found)
    if found:
        return _record(
            CONFIRMED_MALICIOUS,
            at,
            scope=scope,
            records=[
                {"id": i, "url": f"https://osv.dev/vulnerability/{i}"} for i in found[:MAX_CITED]
            ],
            records_total=len(found),
            withdrawn=withdrawn,
            source="OSV (OpenSSF malicious-packages)",
        )
    if doc.get("next_page_token"):
        return _record(NOT_PERFORMED, at, why="partial")
    return _record(MISSING_EVIDENCE, at, scope=scope, withdrawn=withdrawn)


__all__ = ["API", "CHECK", "check", "default_query", "http_query", "not_performed"]
