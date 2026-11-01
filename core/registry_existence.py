"""Registry existence: does this package and version exist? (track T, T-M1 / T-A1).

Coding agents propose package names and versions that do not exist, and
an attacker can register a hallucinated name (threat T2,
``docs/research/TRACK_T_PHASE0.md``). This check asks the registry and
reports the answer as T-F1 status records:

- the version (or, without a version, the package) is found:
  VERIFIED_RELATIONSHIP;
- the registry answers 404: VERIFIED_FAILURE, a fact about registry R
  at time *t*, never evidence of malice. When the version is missing,
  a second request says whether the package exists at all;
- anything else (a 5xx, 429, redirect, timeout, DNS failure, an
  unsupported ecosystem, offline mode, a spent lookup budget, a name
  that fails the ecosystem's grammar): NOT_PERFORMED. An unreachable
  registry never reads as "absent".

Untrusted text (T-F3): names are validated against the ecosystem's
grammar before they go into a URL, and refused (NOT_PERFORMED) when
they fail. Requests are HEAD only, so no upstream body is ever read.
``statement`` is a fixed template per (check, status) filled with the
registry host and a timestamp; the validated subject sits in its own
field. Nothing here feeds a verdict.

PyPI and npm only (Phase 0 feasibility table). Stdlib + httpx.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

CHECK = "registry_existence"

CONFIRMED_MALICIOUS = "CONFIRMED_MALICIOUS"
VERIFIED_FAILURE = "VERIFIED_FAILURE"
SUSPICIOUS_INCONCLUSIVE = "SUSPICIOUS_INCONCLUSIVE"
MISSING_EVIDENCE = "MISSING_EVIDENCE"
VERIFIED_RELATIONSHIP = "VERIFIED_RELATIONSHIP"
NOT_PERFORMED = "NOT_PERFORMED"
#: T-F1: closed, and deliberately without a SAFE value.
STATUSES = (
    CONFIRMED_MALICIOUS,
    VERIFIED_FAILURE,
    SUSPICIOUS_INCONCLUSIVE,
    MISSING_EVIDENCE,
    VERIFIED_RELATIONSHIP,
    NOT_PERFORMED,
)

TIMEOUT_SECONDS = 10.0

#: PEP 508 project names (case-insensitive), normalized per PEP 503 for the URL.
_PYPI_NAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,198}[A-Za-z0-9])?$")
#: PEP 440 spellings stay within these characters ("!" epochs, "+" local versions).
_PYPI_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.!+_-]{0,63}$")
#: npm package names: lowercase, optional @scope/, at most 214 characters.
_NPM_NAME = re.compile(r"^(?:@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*$")
_NPM_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$")

_ECOSYSTEMS = {"pypi": "PyPI", "npm": "npm"}
_HOSTS = {"PyPI": "pypi.org", "npm": "registry.npmjs.org"}

#: Fixed statements: only the registry host and a timestamp are filled in.
_STATEMENTS = {
    ("version", VERIFIED_RELATIONSHIP): "version found in registry {host} at {at}",
    ("version", VERIFIED_FAILURE): (
        "version not found in registry {host} at {at}; an identity fact, not evidence of malice"
    ),
    ("package", VERIFIED_RELATIONSHIP): "package found in registry {host} at {at}",
    ("package", VERIFIED_FAILURE): (
        "package not found in registry {host} at {at}; an identity fact, not evidence of malice"
    ),
}
_NOT_PERFORMED = {
    "unsupported": "registry existence is checked for PyPI and npm packages only",
    "offline": "registry existence not checked: live lookups are off",
    "budget": "registry existence not checked: the session lookup budget is spent",
    "invalid_name": "registry existence not checked: the name does not match the ecosystem's "
    "package-name grammar",
    "invalid_version": "registry existence not checked: the version does not match the "
    "ecosystem's version grammar",
    "unreachable": "registry existence not established: registry {host} gave no usable answer "
    "at {at}",
}

Head = Callable[[str], int]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def user_agent() -> str:
    """Identifying, project-only: PyPI and crates.io ask for one (Phase 0, section 2)."""
    from core.version import openpulse_version

    return f"OpenPulse/{openpulse_version()} (+https://github.com/IkarusAILabs/OpenPulse)"


def http_head(url: str) -> int:
    """HEAD ``url``; the HTTP status, or 0 when no response came back.

    HEAD carries no body, so the size-capped ``collectors.http`` helper is
    not needed (and would refuse the Content-Length a registry declares for
    the body it is not sending). Redirects are not followed, TLS is verified.
    """
    import httpx

    try:
        response = httpx.head(
            url,
            follow_redirects=False,
            timeout=TIMEOUT_SECONDS,
            headers={"user-agent": user_agent()},
        )
    except Exception:  # network, DNS, TLS, timeouts: NOT_PERFORMED, never a crash
        return 0
    return response.status_code


#: The HEAD used when none is injected (tests replace it to stay offline).
default_head: Head = http_head


def ecosystem_of(value: str | None) -> str | None:
    """'PyPI' or 'npm' (case-insensitive), else None."""
    return _ECOSYSTEMS.get(str(value or "").strip().lower())


def _pypi_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def urls(ecosystem: str, name: str, version: str | None) -> tuple[str, str | None]:
    """(package URL, version URL or None) for already-validated identifiers."""
    if ecosystem == "PyPI":
        base = f"https://pypi.org/pypi/{_pypi_name(name)}"
        return f"{base}/json", (f"{base}/{quote(version, safe='')}/json" if version else None)
    base = "https://registry.npmjs.org/" + quote(name, safe="@")
    return base, (f"{base}/{quote(version, safe='')}" if version else None)


def _record(
    status: str,
    statement: str,
    *,
    level: str,
    subject: dict[str, Any] | None,
    source: str | None,
    at: str,
    http_status: int | None = None,
) -> dict[str, Any]:
    return {
        "check": CHECK,
        "level": level,
        "status": status,
        "statement": statement,
        "subject": subject,
        "source": source,
        "checked_at": at,
        "evidence": {"http_status": http_status} if http_status is not None else {},
    }


def not_performed(reason: str, *, ecosystem: str | None = None) -> list[dict[str, Any]]:
    """One NOT_PERFORMED record with a fixed statement (no caller text)."""
    at = _now()
    host = _HOSTS.get(str(ecosystem), "")
    statement = _NOT_PERFORMED[reason].format(host=host, at=at)
    return [_record(NOT_PERFORMED, statement, level="package", subject=None, source=None, at=at)]


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    head: Head | None = None,
    now: Callable[[], str] = _now,
) -> list[dict[str, Any]]:
    """T-F1 records for one package (and version). Never raises on registry trouble."""
    eco = ecosystem_of(ecosystem)
    if eco is None:
        return not_performed("unsupported")
    name_ok = _PYPI_NAME if eco == "PyPI" else _NPM_NAME
    version_ok = _PYPI_VERSION if eco == "PyPI" else _NPM_VERSION
    if not name_ok.fullmatch(name) or len(name) > 214:
        return not_performed("invalid_name", ecosystem=eco)
    if version is not None and not version_ok.fullmatch(version):
        return not_performed("invalid_version", ecosystem=eco)
    head = head or default_head
    host = _HOSTS[eco]
    package_url, version_url = urls(eco, name, version)
    subject = {"ecosystem": eco, "name": name, "version": version}

    def ask(level: str, url: str) -> dict[str, Any]:
        status_code = head(url)
        at = now()
        if status_code == 200:
            status = VERIFIED_RELATIONSHIP
        elif status_code == 404:
            status = VERIFIED_FAILURE
        else:
            statement = _NOT_PERFORMED["unreachable"].format(host=host, at=at)
            return _record(
                NOT_PERFORMED,
                statement,
                level=level,
                subject=subject,
                source=url,
                at=at,
                http_status=status_code or None,
            )
        statement = _STATEMENTS[(level, status)].format(host=host, at=at)
        return _record(
            status,
            statement,
            level=level,
            subject=subject,
            source=url,
            at=at,
            http_status=status_code,
        )

    if version_url is None:
        return [ask("package", package_url)]
    found = ask("version", version_url)
    if found["status"] != VERIFIED_FAILURE:
        return [found]
    # The version is missing: say whether the package exists at all.
    return [found, ask("package", package_url)]


__all__ = [
    "CHECK",
    "NOT_PERFORMED",
    "STATUSES",
    "VERIFIED_FAILURE",
    "VERIFIED_RELATIONSHIP",
    "check",
    "default_head",
    "http_head",
    "ecosystem_of",
    "not_performed",
    "urls",
    "user_agent",
]
