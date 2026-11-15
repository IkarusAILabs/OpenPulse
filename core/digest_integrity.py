"""Digest integrity: does the locked artifact match what the registry publishes? (T-B4).

A lockfile pins each artifact by digest (poetry ``files[].hash``,
package-lock ``integrity``). If the registry publishes a different digest
for that version, the locked artifact is not the one the registry serves:
substituted, re-uploaded or tampered between build and install (threat T8,
``docs/research/TRACK_T_PHASE0.md``). The check compares the two and
reports T-F1 records:

- every locked digest is published by the registry: VERIFIED_RELATIONSHIP;
- any locked digest is not: VERIFIED_FAILURE;
- the lockfile pins no usable digest: MISSING_EVIDENCE;
- the registry gave no usable answer (any status but 200, a bad body, a
  spent budget, offline, an unsupported ecosystem): NOT_PERFORMED.

Hashing only, no cryptography of our own and no new dependency. Lockfile
digests are validated before use and only well-formed digests appear in a
record (T-F3). Nothing here feeds a verdict.
"""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Callable
from typing import Any

from core.registry_existence import (
    _NPM_NAME,
    _NPM_VERSION,
    _PYPI_NAME,
    _PYPI_VERSION,
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    VERIFIED_FAILURE,
    VERIFIED_RELATIONSHIP,
    _now,
    ecosystem_of,
    urls,
)

CHECK = "digest_integrity"
#: Registry JSON bodies (PyPI lists every file of a release) stay small.
MAX_REGISTRY_BYTES = 8 * 1024 * 1024

_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_SRI = re.compile(r"(sha1|sha256|sha384|sha512)-([A-Za-z0-9+/]+={0,2})")
_HOSTS = {"PyPI": "pypi.org", "npm": "registry.npmjs.org"}

_STATEMENTS = {
    VERIFIED_RELATIONSHIP: "every locked digest matches registry {host} at {at}",
    VERIFIED_FAILURE: (
        "a locked digest is not published by registry {host} at {at}: the locked "
        "artifact is not the one the registry serves"
    ),
    MISSING_EVIDENCE: "the lockfile pins no usable digest for this package",
    NOT_PERFORMED: "digest integrity not established: {why}",
}
_WHY = {
    "unsupported": "checked for PyPI and npm lockfiles only",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "invalid": "the name or version does not match the ecosystem's grammar",
    "unreachable": "registry {host} gave no usable answer at {at}",
}

#: url -> (http status, parsed JSON or None). 0 means no response.
FetchJson = Callable[[str], tuple[int, Any]]


def http_json(url: str) -> tuple[int, Any]:
    """GET ``url`` (size-capped, no redirects); (status, JSON or None). Never raises."""
    from collectors import http
    from core.registry_existence import TIMEOUT_SECONDS, user_agent

    try:
        response = http.get(
            url,
            max_bytes=MAX_REGISTRY_BYTES,
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


#: The fetch used when none is injected (tests replace it to stay offline).
default_fetch: FetchJson = http_json


def _record(status: str, at: str, *, host: str = "", why: str = "", **evidence: Any) -> dict:
    statement = _STATEMENTS[status].format(
        host=host, at=at, why=_WHY.get(why, "").format(host=host, at=at)
    )
    return {
        "check": CHECK,
        "status": status,
        "statement": statement,
        "checked_at": at,
        "evidence": evidence,
    }


def not_performed(why: str, ecosystem: str | None = None) -> dict[str, Any]:
    return _record(NOT_PERFORMED, _now(), host=_HOSTS.get(str(ecosystem), ""), why=why)


def usable_digests(ecosystem: str, locked: dict[str, list[str]]) -> dict[str, list[str]]:
    """Only well-formed digests: lowercase hex sha256 (PyPI), SRI (npm)."""
    if ecosystem == "PyPI":
        good = sorted({d for d in locked.get("sha256", []) if _HEX64.fullmatch(d)})
        return {"sha256": good} if good else {}
    good = sorted({d for d in locked.get("integrity", []) if _sri_bytes(d) is not None})
    return {"integrity": good} if good else {}


def _sri_bytes(value: str) -> tuple[str, bytes] | None:
    match = _SRI.fullmatch(value)
    if not match:
        return None
    try:
        return match.group(1), base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        return None


def _npm_matches(locked: str, dist: dict[str, Any]) -> bool | None:
    """True/False when comparable with the registry's dist; None when not."""
    algorithm, digest = _sri_bytes(locked) or ("", b"")
    for candidate in str(dist.get("integrity") or "").split():
        theirs = _sri_bytes(candidate)
        if theirs and theirs[0] == algorithm:
            return theirs[1] == digest
    shasum = str(dist.get("shasum") or "")
    if algorithm == "sha1" and _HEX40.fullmatch(shasum):
        return digest.hex() == shasum
    return None


def check(
    ecosystem: str | None,
    name: str,
    version: str,
    locked: dict[str, list[str]],
    *,
    fetch: FetchJson | None = None,
) -> dict[str, Any]:
    """One T-F1 record for one locked package. Never raises on registry trouble."""
    eco = ecosystem_of(ecosystem)
    if eco is None:
        return not_performed("unsupported")
    name_ok, version_ok = (
        (_PYPI_NAME, _PYPI_VERSION) if eco == "PyPI" else (_NPM_NAME, _NPM_VERSION)
    )
    if not name_ok.fullmatch(name) or not version_ok.fullmatch(version):
        return not_performed("invalid", eco)
    usable = usable_digests(eco, locked)
    if not usable:
        return _record(MISSING_EVIDENCE, _now())
    host = _HOSTS[eco]
    _, version_url = urls(eco, name, version)
    status, doc = (fetch or default_fetch)(str(version_url))
    at = _now()
    if status != 200 or not isinstance(doc, dict):
        return _record(NOT_PERFORMED, at, host=host, why="unreachable", http_status=status or None)
    if eco == "PyPI":
        published = {
            str((f.get("digests") or {}).get("sha256") or "")
            for f in doc.get("urls") or []
            if isinstance(f, dict)
        }
        unmatched = [d for d in usable["sha256"] if d not in published]
        if not published:
            return _record(NOT_PERFORMED, at, host=host, why="unreachable", http_status=200)
    else:
        dist = doc.get("dist") if isinstance(doc.get("dist"), dict) else {}
        results = {d: _npm_matches(d, dist) for d in usable["integrity"]}
        if all(r is None for r in results.values()):
            return _record(NOT_PERFORMED, at, host=host, why="unreachable", http_status=200)
        unmatched = [d for d, ok in results.items() if ok is False]
    locked_count = len(next(iter(usable.values())))
    if unmatched:
        return _record(VERIFIED_FAILURE, at, host=host, locked=locked_count, unmatched=unmatched)
    return _record(VERIFIED_RELATIONSHIP, at, host=host, locked=locked_count)


__all__ = ["CHECK", "check", "default_fetch", "http_json", "not_performed", "usable_digests"]
