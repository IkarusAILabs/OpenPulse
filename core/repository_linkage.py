"""Repository linkage: is the package really from the repository it claims? (T-A4).

Registry metadata can name any repository (npm ``repository``, PyPI
``project_urls``). A package that claims a popular repository borrows its
stars and reputation (starjacking, threat T4). This check asks whether the
claim is bound in either direction, and reports T-F1 records:

- verified provenance (T-B1) names the claimed repository as the publisher:
  VERIFIED_RELATIONSHIP; it names a different repository: VERIFIED_FAILURE,
  the artifact was built somewhere other than the repository it claims;
- otherwise the claimed repository's own manifest (``package.json``, or
  ``pyproject.toml`` / ``setup.cfg``, read at the default branch) names the
  package back: VERIFIED_RELATIONSHIP; it names a different package:
  SUSPICIOUS_INCONCLUSIVE (monorepos and renames do this too);
- the metadata names no GitHub repository, or the repository has no
  readable manifest: MISSING_EVIDENCE;
- the registry or GitHub gave no usable answer, offline, a spent budget, an
  unsupported ecosystem: NOT_PERFORMED.

GitHub repositories only. Repository names, paths and the manifest's name
are validated before they appear; statements are fixed templates and no
upstream text is echoed (T-F3). Manifests are parsed, never executed (no
``setup.py``). Nothing here feeds a verdict.
"""

from __future__ import annotations

import configparser
import json
import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from core.registry_existence import (
    _NPM_NAME,
    _NPM_VERSION,
    _PYPI_NAME,
    _PYPI_VERSION,
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    SUSPICIOUS_INCONCLUSIVE,
    VERIFIED_FAILURE,
    VERIFIED_RELATIONSHIP,
    _now,
    ecosystem_of,
    urls,
)

CHECK = "repository_linkage"
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_CLAIMED = 5
RAW = "https://raw.githubusercontent.com"

_DIRECTORY = re.compile(r"[A-Za-z0-9._@-]+(?:/[A-Za-z0-9._@-]+){0,15}")
# PyPI project_urls labels that name the source, most specific first.
_SOURCE_LABELS = ("source", "source code", "repository", "code", "github", "homepage", "home")

_STATEMENTS = {
    (VERIFIED_RELATIONSHIP, "provenance"): (
        "verified provenance names the claimed repository as the publisher ({at})"
    ),
    (VERIFIED_FAILURE, "provenance"): (
        "verified provenance names a different repository than the registry metadata "
        "claims ({at}): the artifact was not built from the repository it claims"
    ),
    (VERIFIED_RELATIONSHIP, "manifest"): (
        "the claimed repository's manifest names this package ({at})"
    ),
    (SUSPICIOUS_INCONCLUSIVE, "manifest"): (
        "the claimed repository's manifest names a different package ({at}); monorepos "
        "and renamed packages do this too, so this is an indicator, not a verdict"
    ),
    (MISSING_EVIDENCE, "no_repository"): (
        "the registry metadata names no GitHub repository; nothing to check the package against"
    ),
    (MISSING_EVIDENCE, "no_manifest"): (
        "the claimed repository has no readable manifest at its default branch ({at})"
    ),
    (NOT_PERFORMED, ""): "repository linkage not checked: {why}",
}
_WHY = {
    "unsupported": "checked for PyPI and npm packages only",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "invalid": "the name or version does not match the ecosystem's grammar",
    "registry": "the registry gave no usable answer",
    "github": "GitHub gave no usable answer",
    "toml": "reading pyproject.toml needs Python 3.11 or later",
    "private": "the package is on your private-name list; a public repository claim does not apply",
}

#: url -> (http status, parsed JSON or None); url -> (http status, text or None).
FetchJson = Callable[[str], tuple[int, Any]]
FetchText = Callable[[str], tuple[int, str | None]]


def http_text(url: str) -> tuple[int, str | None]:
    """GET ``url`` (size-capped); (status, UTF-8 text or None). Never raises."""
    from collectors import http
    from core.registry_existence import TIMEOUT_SECONDS, user_agent

    try:
        response = http.get(
            url,
            max_bytes=MAX_MANIFEST_BYTES,
            timeout=TIMEOUT_SECONDS,
            headers={"user-agent": user_agent()},
        )
    except Exception:  # network, DNS, TLS, oversize: NOT_PERFORMED, never a crash
        return 0, None
    if response.status_code != 200:
        return response.status_code, None
    try:
        return 200, response.content.decode("utf-8")
    except UnicodeDecodeError:
        return 200, None


#: The text fetch used when none is injected (tests replace it to stay offline).
default_fetch_text: FetchText = http_text


def _record(status: str, how: str, at: str, *, why: str = "", **evidence: Any) -> dict:
    template = _STATEMENTS[(status, how)]
    return {
        "check": CHECK,
        "status": status,
        "statement": template.format(at=at, why=_WHY.get(why, "")),
        "checked_at": at,
        "evidence": evidence,
    }


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, "", _now(), why=why)


#: First path segments that are GitHub pages, never accounts (GitHub reserves
#: them as names): ``github.com/sponsors/<user>`` is a Funding link, not a
#: repository.
_RESERVED_OWNERS = frozenset(
    {
        "about", "apps", "collections", "enterprise", "explore", "features", "issues",
        "login", "marketplace", "notifications", "orgs", "pricing", "pulls", "search",
        "settings", "site", "sponsors", "topics",
    }
)


def github_repository(value: Any) -> tuple[str, str] | None:
    """(owner/repo, directory) for a GitHub URL in any common spelling, else None."""
    from core.github_reader import _valid_repo_parts

    text = str(value or "").strip()
    if not text or len(text) > 500:
        return None
    if text.startswith("github:"):
        text = "https://github.com/" + text[len("github:") :]
    elif text.startswith("git@github.com:"):
        text = "https://github.com/" + text[len("git@github.com:") :]
    elif re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+", text):  # npm shorthand
        text = "https://github.com/" + text
    text = re.sub(r"^git\+", "", text)
    parts = urlsplit(text)
    if parts.scheme not in ("https", "http", "git", "ssh") or (parts.hostname or "") not in (
        "github.com",
        "www.github.com",
    ):
        return None
    segments = [s for s in parts.path.split("/") if s]
    if len(segments) < 2:
        return None
    owner, name = segments[0], re.sub(r"\.git$", "", segments[1])
    if owner.lower() in _RESERVED_OWNERS or not _valid_repo_parts(owner, name):
        return None
    directory = ""
    if len(segments) > 4 and segments[2] in ("tree", "blob"):
        candidate = "/".join(segments[4:])
        if _DIRECTORY.fullmatch(candidate) and ".." not in candidate.split("/"):
            directory = candidate
    return f"{owner}/{name}", directory


def _claimed(ecosystem: str, doc: dict[str, Any]) -> list[tuple[str, str]]:
    """Distinct (repository, directory) claims, most specific first."""
    found: list[tuple[str, str]] = []
    if ecosystem == "npm":
        repository = doc.get("repository")
        if isinstance(repository, dict):
            claim = github_repository(repository.get("url"))
            directory = str(repository.get("directory") or "").strip("/")
            if claim and directory:
                ok = _DIRECTORY.fullmatch(directory) and ".." not in directory.split("/")
                claim = (claim[0], directory if ok else claim[1])
        else:
            claim = github_repository(repository)
        if claim:
            found.append(claim)
        return found
    info = doc.get("info") if isinstance(doc.get("info"), dict) else {}
    project_urls = info.get("project_urls") if isinstance(info.get("project_urls"), dict) else {}
    ranked = sorted(
        project_urls.items(),
        key=lambda kv: (
            _SOURCE_LABELS.index(str(kv[0]).strip().lower())
            if str(kv[0]).strip().lower() in _SOURCE_LABELS
            else len(_SOURCE_LABELS)
        ),
    )
    for _, url in [*ranked, ("home_page", info.get("home_page"))]:
        claim = github_repository(url)
        if claim and claim[0].lower() not in {c[0].lower() for c in found}:
            found.append(claim)
    return found[:MAX_CLAIMED]


def _normalize(ecosystem: str, name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower() if ecosystem == "PyPI" else name.lower()


def _manifest_name(
    ecosystem: str, repository: str, directory: str, fetch_text: FetchText
) -> tuple[str, str | None, str]:
    """('found' | 'missing' | 'unreachable' | 'toml', name or None, manifest path)."""
    prefix = f"{RAW}/{repository}/HEAD/" + (f"{directory}/" if directory else "")
    if ecosystem == "npm":
        status, text = fetch_text(prefix + "package.json")
        if status == 404:
            return "missing", None, "package.json"
        if status != 200 or text is None:
            return "unreachable", None, "package.json"
        try:
            doc = json.loads(text)
        except ValueError:
            return "missing", None, "package.json"
        name = doc.get("name") if isinstance(doc, dict) else None
        return "found", name if isinstance(name, str) else None, "package.json"
    status, text = fetch_text(prefix + "pyproject.toml")
    if status == 200 and text is not None:
        try:
            import tomllib
        except ImportError:
            return "toml", None, "pyproject.toml"
        try:
            project = tomllib.loads(text).get("project")
        except tomllib.TOMLDecodeError:
            project = None
        name = project.get("name") if isinstance(project, dict) else None
        if isinstance(name, str):
            return "found", name, "pyproject.toml"
    elif status not in (200, 404):
        return "unreachable", None, "pyproject.toml"
    status, text = fetch_text(prefix + "setup.cfg")
    if status == 404:
        return "missing", None, "pyproject.toml or setup.cfg"
    if status != 200 or text is None:
        return "unreachable", None, "setup.cfg"
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(text)
        name = parser.get("metadata", "name", fallback=None)
    except configparser.Error:
        name = None
    return ("found", name, "setup.cfg") if name else ("missing", None, "setup.cfg")


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    publishers: list[dict[str, Any]] | None = None,
    fetch_json: FetchJson | None = None,
    fetch_text: FetchText | None = None,
) -> dict[str, Any]:
    """One T-F1 record for one package. ``publishers``: verified T-B1 publishers.

    Never raises on registry or GitHub trouble.
    """
    from core import digest_integrity

    eco = ecosystem_of(ecosystem)
    if eco is None:
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
        return _record(NOT_PERFORMED, "", _now(), why="registry", http_status=status or None)
    claims = _claimed(eco, doc)
    if not claims:
        return _record(MISSING_EVIDENCE, "no_repository", _now())
    repository, directory = claims[0]
    evidence: dict[str, Any] = {
        "claimed_repository": repository,
        "claimed_repositories": [c[0] for c in claims],
        "url": f"https://github.com/{repository}",
    }
    named = {
        str(p.get("repository")).lower()
        for p in publishers or []
        if isinstance(p, dict) and p.get("repository")
    }
    if named:
        evidence["provenance_repositories"] = sorted(named)
        if repository.lower() in named:
            return _record(VERIFIED_RELATIONSHIP, "provenance", _now(), **evidence)
        return _record(VERIFIED_FAILURE, "provenance", _now(), **evidence)
    outcome, manifest_name, manifest = _manifest_name(
        eco, repository, directory, fetch_text or default_fetch_text
    )
    at = _now()
    evidence["manifest"] = f"{directory}/{manifest}" if directory else manifest
    if outcome == "toml":
        return _record(NOT_PERFORMED, "", at, why="toml", **evidence)
    if outcome == "unreachable":
        return _record(NOT_PERFORMED, "", at, why="github", **evidence)
    if outcome == "missing" or manifest_name is None:
        return _record(MISSING_EVIDENCE, "no_manifest", at, **evidence)
    if name_ok.fullmatch(manifest_name if eco == "PyPI" else manifest_name.lower()):
        evidence["manifest_names"] = manifest_name
    if _normalize(eco, manifest_name) == _normalize(eco, name):
        return _record(VERIFIED_RELATIONSHIP, "manifest", at, **evidence)
    return _record(SUSPICIOUS_INCONCLUSIVE, "manifest", at, **evidence)


__all__ = ["CHECK", "check", "default_fetch_text", "github_repository", "http_text"]
