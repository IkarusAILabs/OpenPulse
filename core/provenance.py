"""PyPI provenance: is this release attested by its publisher? (track T, T-B1).

PyPI serves PEP 740 attestations through its Integrity API: Sigstore-signed
statements, grouped by Trusted Publisher, that bind a distribution file's
digest to the workflow that built it. This check fetches them for a
release's files, verifies each against the file's sha256 with
``pypi-attestations`` (the optional ``[provenance]`` extra, Python 3.11+),
and reports one T-F1 record:

- every checked file with provenance verifies, and its publisher names the
  catalog's repository when one is known: VERIFIED_RELATIONSHIP. Its
  statement says what that means: where and how the files were built,
  never that they are benign (threat T7: Ultralytics' first malicious
  releases carried valid provenance);
- an attestation does not verify, or names another repository than the
  catalog's (starjacking, T4): VERIFIED_FAILURE;
- the release publishes no provenance: MISSING_EVIDENCE. Most packages
  publish none, so this is not evidence of a problem;
- the extra is not installed, offline, budget spent, PyPI unreachable,
  not a PyPI package: NOT_PERFORMED.

Verification uses the library, never cryptography of our own (track T,
T-B). Upstream fields (file names, publisher repository and workflow) are
validated before they appear (T-F3). Nothing here feeds a verdict.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from core.registry_existence import (
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

CHECK = "pypi_provenance"
#: Files checked per release: wheels first, then the sdist.
MAX_FILES = 4
MAX_PROVENANCE_BYTES = 2 * 1024 * 1024
ACCEPT = "application/vnd.pypi.integrity.v1+json"

_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+!-]{0,200}\.(?:whl|tar\.gz|zip)", re.ASCII)
_HEX64 = re.compile(r"[0-9a-f]{64}")
_WORKFLOW = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,100}\.ya?ml", re.ASCII)
_KIND = re.compile(r"[A-Za-z]{1,32}")

_STATEMENTS = {
    VERIFIED_RELATIONSHIP: (
        "provenance verified for {n} file(s) at {at}: they were built by the named publisher "
        "workflow; this shows where and how they were built, not that they are benign"
    ),
    VERIFIED_FAILURE: (
        "provenance failed at {at}: an attestation does not verify for its file, or names "
        "another repository than the catalog's"
    ),
    MISSING_EVIDENCE: (
        "the release publishes no provenance at {at}; most packages publish none, so this is "
        "not evidence of a problem"
    ),
    NOT_PERFORMED: "provenance not established: {why}",
}
_WHY = {
    "extra": "install ikarus-openpulse[provenance] (Python 3.11+) to verify attestations",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "invalid": "the name or version does not match PyPI's grammar",
    "unsupported": "checked for PyPI packages with a version only",
    "unreachable": "pypi.org gave no usable answer at {at}",
}


class ExtraMissing(Exception):
    """pypi-attestations is not installed."""


class NotVerified(Exception):
    """An attestation exists but does not verify for its file."""


#: url -> (http status, parsed JSON or None)
FetchJson = Callable[[str], tuple[int, Any]]
#: (provenance JSON, filename, sha256) -> publishers [{kind, repository, workflow}]
Verify = Callable[[Any, str, str], list[dict[str, Any]]]


def library_verify(provenance: Any, filename: str, sha256: str) -> list[dict[str, Any]]:
    """Verify every attestation in a Provenance document with pypi-attestations."""
    try:
        import pypi_attestations as pa
    except ImportError as exc:
        raise ExtraMissing from exc
    try:
        document = pa.Provenance.model_validate(provenance)
        dist = pa.Distribution(name=filename, digest=sha256)
        publishers = []
        for bundle in document.attestation_bundles:
            for attestation in bundle.attestations:
                attestation.verify(bundle.publisher, dist)
            publishers.append(
                {
                    "kind": getattr(bundle.publisher, "kind", None),
                    "repository": getattr(bundle.publisher, "repository", None),
                    "workflow": getattr(bundle.publisher, "workflow", None),
                }
            )
        return publishers
    except pa.AttestationError as exc:
        raise NotVerified from exc
    except ValueError as exc:  # a malformed document (pydantic ValidationError)
        raise NotVerified from exc


def http_provenance(url: str) -> tuple[int, Any]:
    """GET a provenance document (size-capped, no redirects). Never raises."""
    from collectors import http
    from core.registry_existence import TIMEOUT_SECONDS, user_agent

    try:
        response = http.get(
            url,
            max_bytes=MAX_PROVENANCE_BYTES,
            timeout=TIMEOUT_SECONDS,
            headers={"user-agent": user_agent(), "accept": ACCEPT},
        )
    except Exception:
        return 0, None
    if response.status_code != 200:
        return response.status_code, None
    try:
        return 200, response.json()
    except ValueError:
        return 200, None


#: Seams replaced by tests to stay offline.
default_fetch_provenance: FetchJson = http_provenance
default_verify: Verify = library_verify


def _record(status: str, at: str, *, why: str = "", n: int = 0, **evidence: Any) -> dict:
    statement = _STATEMENTS[status].format(n=n, at=at, why=_WHY.get(why, "").format(at=at))
    return {
        "check": CHECK,
        "status": status,
        "statement": statement,
        "checked_at": at,
        "evidence": evidence,
    }


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, _now(), why=why)


def _publisher(raw: dict[str, Any]) -> dict[str, Any]:
    """Only validated publisher fields; anything else is null (T-F3)."""
    from core.github_reader import _valid_repo_parts

    repository = str(raw.get("repository") or "")
    owner, _, name = repository.partition("/")
    workflow, kind = str(raw.get("workflow") or ""), str(raw.get("kind") or "")
    return {
        "kind": kind if _KIND.fullmatch(kind) else None,
        "repository": repository if _valid_repo_parts(owner, name) else None,
        "workflow": workflow if _WORKFLOW.fullmatch(workflow) else None,
    }


def _files(doc: dict[str, Any]) -> list[tuple[str, str]]:
    found = []
    for entry in doc.get("urls") or []:
        if not isinstance(entry, dict):
            continue
        filename = str(entry.get("filename") or "")
        sha256 = str((entry.get("digests") or {}).get("sha256") or "")
        if _FILENAME.fullmatch(filename) and _HEX64.fullmatch(sha256):
            found.append((filename, sha256))
    wheels = [f for f in found if f[0].endswith(".whl")]
    return (wheels + [f for f in found if not f[0].endswith(".whl")])[:MAX_FILES]


def check(
    ecosystem: str | None,
    name: str,
    version: str | None,
    *,
    expected_repository: str | None = None,
    fetch_json: FetchJson | None = None,
    fetch_provenance: FetchJson | None = None,
    verify: Verify | None = None,
) -> dict[str, Any]:
    """One T-F1 record for one PyPI release. Never raises on registry trouble."""
    from core import digest_integrity

    if ecosystem_of(ecosystem) != "PyPI" or not version:
        return not_performed("unsupported")
    if not _PYPI_NAME.fullmatch(name) or not _PYPI_VERSION.fullmatch(version):
        return not_performed("invalid")
    fetch_json = fetch_json or digest_integrity.default_fetch
    fetch_provenance = fetch_provenance or default_fetch_provenance
    verify = verify or default_verify
    _, release_url = urls("PyPI", name, version)
    status, doc = fetch_json(str(release_url))
    if status != 200 or not isinstance(doc, dict) or not _files(doc):
        return _record(NOT_PERFORMED, _now(), why="unreachable", http_status=status or None)
    project = re.sub(r"[-_.]+", "-", name).lower()
    verified, missing, unreachable, failed = [], [], 0, []
    publishers: list[dict[str, Any]] = []
    for filename, sha256 in _files(doc):
        url = f"https://pypi.org/integrity/{project}/{version}/{filename}/provenance"
        status, provenance = fetch_provenance(url)
        if status == 404:
            missing.append(filename)
            continue
        if status != 200 or provenance is None:
            unreachable += 1
            continue
        try:
            found = [_publisher(p) for p in verify(provenance, filename, sha256)]
        except ExtraMissing:
            return not_performed("extra")
        except NotVerified:
            failed.append(filename)
            continue
        verified.append(filename)
        publishers += [p for p in found if p not in publishers]
    at = _now()
    named = {p["repository"].lower() for p in publishers if p["repository"]}
    differs = (
        bool(expected_repository)
        and bool(named)
        and (expected_repository.lower() not in named or len(named) > 1)
    )
    evidence = {
        "files_checked": len(verified) + len(missing) + len(failed),
        "verified": len(verified),
        "without_provenance": len(missing),
        "failed": failed,
        "publishers": publishers,
        "expected_repository": expected_repository,
        "repository_check": (
            "differs"
            if differs
            else "matches"
            if expected_repository and named
            else "not cross-checked"
        ),
    }
    if failed or differs:
        return _record(VERIFIED_FAILURE, at, **evidence)
    if verified:
        return _record(VERIFIED_RELATIONSHIP, at, n=len(verified), **evidence)
    if missing and not unreachable:
        return _record(MISSING_EVIDENCE, at, **evidence)
    return _record(NOT_PERFORMED, at, why="unreachable", **evidence)


__all__ = [
    "CHECK",
    "ExtraMissing",
    "NotVerified",
    "check",
    "default_fetch_provenance",
    "default_verify",
    "http_provenance",
    "library_verify",
    "not_performed",
]
