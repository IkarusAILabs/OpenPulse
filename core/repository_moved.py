"""Repository moved: does the claimed repository answer under another name?
(track T Phase 2, T-C; v0.16.0 item Q3).

A package's metadata names its source repository. GitHub answers a
repository that was renamed or transferred under its new name, through a
redirect. A move is how a package can come to point somewhere its users
never vetted: an abandoned project handed to a new owner, or a name freed
and re-registered. Most moves are ordinary (a project joining an
organisation), so this is an indicator:

- the claimed repository answers under another name: SUSPICIOUS_INCONCLUSIVE,
  naming both and whether it was ``renamed`` (same owner) or
  ``transferred`` (another owner);
- it answers under the claimed name (case ignored): VERIFIED_RELATIONSHIP,
  meaning only that the claim is current, not that the code is the
  package's (``repository_linkage`` checks that);
- no GitHub repository is claimed, or GitHub does not know it (deleted,
  private, never existed): MISSING_EVIDENCE;
- unsupported, invalid, GitHub or the registry unreachable or rate-limited,
  budget spent: NOT_PERFORMED.

Its firing rate on legitimate packages is measured on the organic
reputation set (``docs/research/TRACK_T_MEASUREMENTS.md``). Repository names
are validated before they appear (T-F3). The GitHub request follows one
redirect, only within https://api.github.com; ``GITHUB_TOKEN``, when set,
is sent only there. Nothing here feeds a verdict.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from core.registry_existence import (
    _NPM_NAME,
    _NPM_VERSION,
    _PYPI_NAME,
    _PYPI_VERSION,
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    SUSPICIOUS_INCONCLUSIVE,
    VERIFIED_RELATIONSHIP,
    _now,
    ecosystem_of,
    urls,
)

CHECK = "repository_moved"
API = "https://api.github.com/repos/{repo}"
MAX_REPO_BYTES = 1024 * 1024
_REDIRECTS = (301, 302, 307, 308)

_STATEMENTS = {
    SUSPICIOUS_INCONCLUSIVE: (
        "the claimed repository answers under another name ({move}); projects move to "
        "organisations routinely, so this is an indicator to check, never a verdict"
    ),
    VERIFIED_RELATIONSHIP: (
        "the claimed repository answers under the name the package claims; this says the "
        "claim is current, not that the code is the package's"
    ),
    MISSING_EVIDENCE: "no move to report: {why}",
    NOT_PERFORMED: "repository move not checked: {why}",
}
_WHY = {
    "no_repository": "the package claims no GitHub repository",
    "unknown": "GitHub does not know the claimed repository (deleted, private or never existed)",
    "unsupported": "checked for PyPI and npm packages only",
    "invalid": "the name or version does not match the ecosystem's grammar",
    "registry": "the registry gave no usable answer",
    "github": "GitHub gave no usable answer (unreachable or rate-limited)",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "private": "the package is on your private-name list; a public repository claim does not apply",
}

#: url -> (http status, parsed JSON or None)
FetchJson = Callable[[str], tuple[int, Any]]


def http_github(url: str) -> tuple[int, Any]:
    """GET a GitHub API URL, following one redirect within api.github.com. Never raises."""
    import httpx

    from collectors import http
    from core.registry_existence import TIMEOUT_SECONDS, user_agent

    headers = {"user-agent": user_agent(), "accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["authorization"] = f"Bearer {token}"
    try:
        response = http.get(url, max_bytes=MAX_REPO_BYTES, timeout=TIMEOUT_SECONDS, headers=headers)
        if response.status_code in _REDIRECTS:
            target = httpx.URL(url).join(response.headers.get("location", ""))
            if (target.scheme, target.host, target.port) != ("https", "api.github.com", None):
                return 0, None
            response = http.get(
                str(target), max_bytes=MAX_REPO_BYTES, timeout=TIMEOUT_SECONDS, headers=headers
            )
    except Exception:  # network, DNS, TLS, oversize: NOT_PERFORMED, never a crash
        return 0, None
    if response.status_code != 200:
        return response.status_code, None
    try:
        return 200, response.json()
    except ValueError:
        return 200, None


#: The GitHub fetch used when none is injected (tests replace it to stay offline).
default_fetch_github: FetchJson = http_github


def classify(claimed: str, answered: str) -> tuple[str, str | None]:
    """(status, move) for a claimed and an answered ``owner/name``."""
    if claimed.lower() == answered.lower():
        return VERIFIED_RELATIONSHIP, None
    same_owner = claimed.split("/")[0].lower() == answered.split("/")[0].lower()
    return SUSPICIOUS_INCONCLUSIVE, "renamed" if same_owner else "transferred"


def answered_name(doc: Any) -> str | None:
    """The validated ``full_name`` of a GitHub repository document."""
    from core.github_reader import _valid_repo_parts

    full_name = str(doc.get("full_name") or "") if isinstance(doc, dict) else ""
    owner, _, name = full_name.partition("/")
    return full_name if _valid_repo_parts(owner, name) else None


def _record(status: str, why: str = "", **evidence: Any) -> dict:
    template = _STATEMENTS[status]
    return {
        "check": CHECK,
        "status": status,
        "statement": template.format(move=evidence.get("move"), why=_WHY.get(why, "")),
        "checked_at": _now(),
        "evidence": evidence,
    }


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, why)


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    fetch_json: FetchJson | None = None,
    fetch_github: FetchJson | None = None,
) -> dict[str, Any]:
    """One T-F1 record for one package. Never raises on registry or GitHub trouble."""
    from core import digest_integrity
    from core.repository_linkage import _claimed

    eco = ecosystem_of(ecosystem)
    if eco not in ("npm", "PyPI"):
        return not_performed("unsupported")
    name_ok, version_ok = (
        (_PYPI_NAME, _PYPI_VERSION) if eco == "PyPI" else (_NPM_NAME, _NPM_VERSION)
    )
    if not name_ok.fullmatch(name if eco == "PyPI" else name.lower()) or (
        version and not version_ok.fullmatch(version)
    ):
        return not_performed("invalid")
    package_url, version_url = urls(eco, name, version)
    if eco == "npm" and version_url is None:
        version_url = package_url + "/latest"
    status, doc = (fetch_json or digest_integrity.default_fetch)(str(version_url or package_url))
    if status != 200 or not isinstance(doc, dict):
        return _record(NOT_PERFORMED, "registry", http_status=status or None)
    claims = _claimed(eco, doc)
    if not claims:
        return _record(MISSING_EVIDENCE, "no_repository")
    claimed = claims[0][0]
    status, repo = (fetch_github or default_fetch_github)(API.format(repo=claimed))
    if status == 404:
        return _record(MISSING_EVIDENCE, "unknown", claimed_repository=claimed)
    answered = answered_name(repo) if status == 200 else None
    if answered is None:
        return _record(
            NOT_PERFORMED, "github", claimed_repository=claimed, http_status=status or None
        )
    state, move = classify(claimed, answered)
    return _record(
        state,
        claimed_repository=claimed,
        answered_repository=answered,
        move=move,
        url=f"https://github.com/{answered}",
    )


__all__ = [
    "CHECK",
    "answered_name",
    "check",
    "classify",
    "default_fetch_github",
    "http_github",
    "not_performed",
]
