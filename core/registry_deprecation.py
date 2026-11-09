"""Deprecated and withdrawn packages, as the publisher flagged them on the registry (v0.20.0 C4).

Three flags, each set by the package's publisher on the registry itself:

- **npm ``deprecated``:** ``npm deprecate`` stores a message on a version
  (on every version, when the whole package is deprecated). npm prints it
  on every install. The release npm installs by default (the ``latest``
  dist-tag) carrying it means the package is deprecated; only your
  version carrying it means that version is.
- **PyPI yanked (PEP 592):** a yanked release stays downloadable, but
  installers skip it unless it is pinned exactly; the publisher may give
  a reason. A release counts as yanked when all its files are.
- **PyPI "Development Status :: 7 - Inactive":** the classifier the
  publisher puts on the latest release to say the project is no longer
  developed.

npm is read through version documents (``/<name>/latest`` and
``/<name>/<version>``), not the packument, so a very large package
(react-dom's packument is over the size cap) is still checked. PyPI needs
one request: the project document lists every release's files, and their
yank flags.

Untrusted text: names and versions are validated against the ecosystem's
grammar before any URL is built, and the publisher's message is bounded,
whitespace-collapsed and dropped when it holds control characters. A flag
says what the publisher declared, never why or whether it matters to you:
``analyzers.change_analyst.analyze_deprecations`` turns flags into
findings for review.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.registry_existence import (
    _NPM_NAME,
    _NPM_VERSION,
    _PYPI_NAME,
    _PYPI_VERSION,
    ecosystem_of,
    urls,
)
from core.release_license import _purl
from core.versions import compare

#: Status of one check: the registry was read, or it was not (the reason
#: says why). Never a statement about the package.
CHECKED = "CHECKED"
NOT_PERFORMED = "NOT_PERFORMED"

#: Flag kinds.
NPM_DEPRECATED = "npm_deprecated"
PYPI_YANKED = "pypi_yanked"
PYPI_INACTIVE = "pypi_inactive"

#: What a flag covers: the whole package, or one release.
PACKAGE = "package"
VERSION = "version"

INACTIVE_CLASSIFIER = "Development Status :: 7 - Inactive"

_MAX_MESSAGE = 300
_NO_ANSWER = "the registry gave no usable answer (unreachable, or over the size cap)"

FetchJson = Callable[[str], tuple[int, Any]]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def message(value: Any) -> str | None:
    """The publisher's text, bounded and single-line; None when absent or unsafe."""
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if not text or not text.isprintable():
        return None
    if len(text) > _MAX_MESSAGE:
        text = text[: _MAX_MESSAGE - 1].rstrip() + "…"
    return text


def npm_deprecated(meta: Any) -> tuple[bool, str | None]:
    """(deprecated, message) from one npm version document.

    ``npm deprecate pkg ""`` lifts a deprecation by storing an empty
    string, so only a non-empty string (or ``true``) is a flag.
    """
    raw = _dict(meta).get("deprecated")
    if raw is True:
        return True, None
    if isinstance(raw, str) and raw.strip():
        return True, message(raw)
    return False, None


def pypi_yanked(files: Any) -> tuple[bool, str | None]:
    """(yanked, reason) for one PyPI release's files: yanked only when all are."""
    files = [f for f in files or [] if isinstance(f, dict)]
    if not files or not all(f.get("yanked") is True for f in files):
        return False, None
    reasons = sorted({r for r in (message(f.get("yanked_reason")) for f in files) if r})
    return True, (reasons[0] if len(reasons) == 1 else None)


def pypi_inactive(info: Any) -> bool:
    classifiers = _dict(info).get("classifiers") or []
    return any(isinstance(c, str) and c.strip() == INACTIVE_CLASSIFIER for c in classifiers)


def _flag(kind: str, level: str, version: str, text: str | None) -> dict[str, Any]:
    return {"kind": kind, "level": level, "version": version, "message": text}


def _result(ecosystem: str | None, name: str, version: str | None, **fields: Any) -> dict:
    return {
        "ecosystem": ecosystem,
        "name": name,
        "version": version,
        "purl": _purl(ecosystem, name) if ecosystem in ("npm", "PyPI") else None,
        "status": CHECKED,
        "reason": None,
        "latest": None,
        "flags": [],
        **fields,
    }


def _not_performed(ecosystem: str | None, name: str, version: str | None, reason: str) -> dict:
    return _result(ecosystem, name, version, status=NOT_PERFORMED, reason=reason)


def _check_npm(name: str, version: str | None, fetch: FetchJson) -> dict[str, Any]:
    _, latest_url = urls("npm", name, "latest")
    status, latest_doc = fetch(str(latest_url))
    if status == 404:
        return _not_performed(
            "npm", name, version, "the registry has no such package (or no latest release)"
        )
    if status != 200 or not isinstance(latest_doc, dict):
        return _not_performed("npm", name, version, _NO_ANSWER)
    latest = latest_doc.get("version")
    if not isinstance(latest, str) or not _NPM_VERSION.fullmatch(latest):
        return _not_performed("npm", name, version, _NO_ANSWER)
    flags = []
    deprecated, text = npm_deprecated(latest_doc)
    if deprecated:
        flags.append(_flag(NPM_DEPRECATED, PACKAGE, latest, text))
    if version is not None and version != latest:
        _, version_url = urls("npm", name, version)
        status, version_doc = fetch(str(version_url))
        if status == 404:
            return _not_performed("npm", name, version, "the registry does not list the version")
        if status != 200 or not isinstance(version_doc, dict):
            return _not_performed("npm", name, version, _NO_ANSWER)
        deprecated, text = npm_deprecated(version_doc)
        if deprecated:
            flags.append(_flag(NPM_DEPRECATED, VERSION, version, text))
    return _result("npm", name, version, latest=latest, flags=flags)


def _check_pypi(name: str, version: str | None, fetch: FetchJson) -> dict[str, Any]:
    package_url, _ = urls("PyPI", name, None)
    status, doc = fetch(package_url)
    if status == 404:
        return _not_performed("PyPI", name, version, "the registry has no such package")
    if status != 200 or not isinstance(doc, dict):
        return _not_performed("PyPI", name, version, _NO_ANSWER)
    info, releases = _dict(doc.get("info")), _dict(doc.get("releases"))
    latest = info.get("version")
    if not isinstance(latest, str) or not _PYPI_VERSION.fullmatch(latest):
        return _not_performed("PyPI", name, version, _NO_ANSWER)
    flags = []
    if pypi_inactive(info):
        flags.append(_flag(PYPI_INACTIVE, PACKAGE, latest, None))
    # PyPI's latest is the newest release that is not yanked; it is yanked
    # itself only when every release is.
    yanked, reason = pypi_yanked(releases.get(latest))
    if yanked:
        flags.append(_flag(PYPI_YANKED, PACKAGE, latest, reason))
    if version is not None:
        # PEP 440: 2.0 and 2.0.0 are one version, under the registry's spelling.
        listed = [v for v, files in releases.items() if files and isinstance(v, str)]
        same = [
            v for v in listed if _PYPI_VERSION.fullmatch(v) and compare(v, version, "pep440") == 0
        ]
        if not same:
            return _not_performed("PyPI", name, version, "the registry does not list the version")
        if compare(same[0], latest, "pep440") != 0:
            yanked, reason = pypi_yanked(releases.get(same[0]))
            if yanked:
                flags.append(_flag(PYPI_YANKED, VERSION, same[0], reason))
    return _result("PyPI", name, version, latest=latest, flags=flags)


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    fetch_json: FetchJson | None = None,
) -> dict[str, Any]:
    """Read the publisher's deprecation and withdrawal flags. Never raises.

    Without ``version``: the package-level flags only. With it: also
    whether that release is deprecated (npm) or yanked (PyPI).
    """
    eco = ecosystem_of(ecosystem)
    if eco is None:
        return _not_performed(None, str(name), version, "only npm and PyPI are checked")
    name_ok = _PYPI_NAME if eco == "PyPI" else _NPM_NAME
    version_ok = _PYPI_VERSION if eco == "PyPI" else _NPM_VERSION
    if not isinstance(name, str) or not name_ok.fullmatch(name) or len(name) > 214:
        return _not_performed(eco, str(name), version, "the name does not match the grammar")
    if version is not None and not version_ok.fullmatch(str(version)):
        return _not_performed(eco, name, version, "the version does not match the grammar")
    if fetch_json is None:
        from core import digest_integrity

        fetch_json = digest_integrity.default_fetch
    try:
        if eco == "npm":
            return _check_npm(name, version, fetch_json)
        return _check_pypi(name, version, fetch_json)
    except Exception:  # a malformed document is no answer, never a crash
        return _not_performed(eco, name, version, _NO_ANSWER)


__all__ = [
    "CHECKED",
    "INACTIVE_CLASSIFIER",
    "NOT_PERFORMED",
    "NPM_DEPRECATED",
    "PACKAGE",
    "PYPI_INACTIVE",
    "PYPI_YANKED",
    "VERSION",
    "check",
    "message",
    "npm_deprecated",
    "pypi_inactive",
    "pypi_yanked",
]
