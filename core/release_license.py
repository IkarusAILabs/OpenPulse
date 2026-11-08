"""License changes between releases, from what the registry records per release (v0.20.0 C3).

npm and PyPI record a license for every release, so a relicense is
visible today, without waiting for OpenPulse's own repository history
to build up (C1, C2). This module compares those per-release values:

- **npm:** the packument carries every version's ``license`` (and the
  legacy ``licenses`` list), so one request shows every transition.
- **PyPI:** the project document describes only the latest release, and
  each other release costs one request. Two releases are compared: the
  latest and the given version (or, without one, the release before the
  latest). A difference says the license changed somewhere in between,
  and the record says the releases in between were not compared.

Releases are ordered by version precedence (semver for npm, PEP 440 for
PyPI), never by publish time: a 4.x patch published after 5.0 would
otherwise make a license seem to flip back and forth. Prereleases and
versions that do not order are left out.

PyPI records a license three ways: a PEP 639 ``license_expression``, the
free-text ``license`` field, and ``License ::`` classifiers. Values of
different kinds are compared only when they are equal: "MIT" and
"MIT License" are not a relicense, they are two spellings, and the record
says the two releases were not comparable.

Untrusted text: names and versions are validated against the ecosystem's
grammar before any URL is built, license values are bounded, single-line
and printable, and responses are size-capped
(``core.digest_integrity.default_fetch``). Nothing here is a verdict:
``analyzers.change_analyst.analyze_release_license_changes`` turns
transitions into findings for review.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import cmp_to_key
from typing import Any
from urllib.parse import quote

from core.registry_existence import (
    _NPM_NAME,
    _NPM_VERSION,
    _PYPI_NAME,
    _PYPI_VERSION,
    ecosystem_of,
    urls,
)
from core.versions import compare

#: Status of one comparison: the registry was read and releases compared,
#: or it was not (the reason says why). Never a statement about the package.
COMPARED = "COMPARED"
NOT_PERFORMED = "NOT_PERFORMED"

_SCHEME = {"npm": "semver", "PyPI": "pep440"}
_MAX_LICENSE = 128
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
#: Why a fetch gave nothing to compare (the size cap refuses very large packuments).
_NO_ANSWER = "the registry gave no usable answer (unreachable, or over the size cap)"
#: Free text that says nothing about the license.
_NO_LICENSE = frozenset({"", "unknown", "none", "n/a", "see license", "license"})

FetchJson = Callable[[str], tuple[int, Any]]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _short(value: Any) -> str | None:
    """A bounded, single-line, printable license value, or None."""
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if not text or len(text) > _MAX_LICENSE or not text.isprintable():
        return None
    if text.casefold() in _NO_LICENSE:
        return None
    return text


def _norm(value: str) -> str:
    text = " ".join(value.casefold().split())
    if text.startswith("(") and text.endswith(")") and text.count("(") == 1:
        text = text[1:-1].strip()
    return text


def npm_license(meta: Any) -> tuple[str, str] | None:
    """("declared", value) from one npm version document, or None."""
    meta = _dict(meta)
    raw = meta.get("license")
    if isinstance(raw, dict):
        raw = raw.get("type")
    value = _short(raw)
    if value is None and isinstance(meta.get("licenses"), list):
        types = []
        for entry in meta["licenses"]:
            entry_type = _short(entry.get("type") if isinstance(entry, dict) else entry)
            if entry_type is None:
                return None
            types.append(entry_type)
        value = _short(" OR ".join(sorted(set(types)))) if types else None
    return ("declared", value) if value else None


def pypi_license(info: Any) -> tuple[str, str] | None:
    """(kind, value) from one PyPI release's ``info``: the PEP 639 expression,
    else a short ``license`` field, else the ``License ::`` classifiers."""
    info = _dict(info)
    expression = _short(info.get("license_expression"))
    if expression:
        return "expression", expression
    field = info.get("license")
    if isinstance(field, str) and "\n" not in field.strip():
        value = _short(field)
        if value and len(value) <= 64:
            return "field", value
    classifiers = sorted(
        {
            c.split("::")[-1].strip()
            for c in info.get("classifiers") or []
            if isinstance(c, str) and c.startswith("License ::")
        }
    )
    value = _short(" AND ".join(classifiers)) if classifiers else None
    return ("classifier", value) if value else None


def differs(a: tuple[str, str] | None, b: tuple[str, str] | None) -> bool | None:
    """True for a license change, False for the same license, None when the
    two cannot be compared (one is missing, or two kinds with different text)."""
    if a is None or b is None:
        return None
    if _norm(a[1]) == _norm(b[1]):
        return False
    if a[0] != b[0]:
        return None
    return True


def _main_line(versions: list[str], ecosystem: str) -> list[str]:
    """Release versions in precedence order; prereleases and unorderable ones left out."""
    scheme = _SCHEME[ecosystem]
    pattern = _NPM_VERSION if ecosystem == "npm" else _PYPI_VERSION
    kept = []
    for version in versions:
        if not isinstance(version, str) or not pattern.fullmatch(version):
            continue
        if ecosystem == "npm" and "-" in version.split("+")[0]:
            continue  # a semver prerelease
        if ecosystem == "PyPI" and re.search(r"(a|b|c|rc|alpha|beta|pre|preview|dev)\d*$", version):
            continue
        if compare(version, version, scheme) != 0:
            continue  # not orderable by the scheme
        kept.append(version)
    return sorted(kept, key=cmp_to_key(lambda x, y: compare(x, y, scheme) or 0))


def _time(value: Any) -> str | None:
    text = str(value or "")
    return text if _TIME.fullmatch(text) else None


def npm_release_licenses(doc: Any) -> list[dict[str, Any]]:
    """Every main-line npm release, in precedence order: version, published, license."""
    versions, times = _dict(_dict(doc).get("versions")), _dict(_dict(doc).get("time"))
    return [
        {
            "version": version,
            "published": _time(times.get(version)),
            "license": npm_license(versions.get(version)),
        }
        for version in _main_line(list(versions), "npm")
    ]


def transitions(releases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each change of license between consecutive releases that declare one.

    A release without a usable license is skipped, not read as a change.
    Two releases whose values cannot be compared (different kinds, different
    text) yield no transition; the next comparable pair still does.
    """
    found = []
    previous = None
    for release in releases:
        if release.get("license") is None:
            continue
        if previous is not None and differs(previous["license"], release["license"]):
            found.append(
                {
                    "from_version": previous["version"],
                    "to_version": release["version"],
                    "from_license": previous["license"][1],
                    "to_license": release["license"][1],
                    "published": release.get("published"),
                    "between_compared": True,
                }
            )
        previous = release
    return found


def _purl(ecosystem: str, name: str) -> str:
    if ecosystem == "npm":
        return "pkg:npm/" + quote(name, safe="/")
    return "pkg:pypi/" + re.sub(r"[-_.]+", "-", name).lower()


def _result(ecosystem: str | None, name: str, version: str | None, **fields: Any) -> dict:
    return {
        "ecosystem": ecosystem,
        "name": name,
        "version": version,
        "purl": _purl(ecosystem, name) if ecosystem in _SCHEME else None,
        "status": COMPARED,
        "reason": None,
        "latest": None,
        "releases_compared": 0,
        "transitions": [],
        "not_comparable": [],
        **fields,
    }


def _not_performed(ecosystem: str | None, name: str, version: str | None, reason: str) -> dict:
    return _result(ecosystem, name, version, status=NOT_PERFORMED, reason=reason)


def _after(version: str | None, ecosystem: str, found: list[dict[str, Any]]) -> list[dict]:
    if version is None:
        return found[-1:]  # the most recent transition only
    scheme = _SCHEME[ecosystem]
    return [t for t in found if (compare(t["to_version"], version, scheme) or 0) > 0]


def _check_npm(name: str, version: str | None, fetch: FetchJson) -> dict[str, Any]:
    package_url, _ = urls("npm", name, None)
    status, doc = fetch(package_url)
    if status == 404:
        return _not_performed("npm", name, version, "the registry has no such package")
    if status != 200 or not isinstance(doc, dict):
        return _not_performed("npm", name, version, _NO_ANSWER)
    releases = npm_release_licenses(doc)
    if version is not None and version not in {r["version"] for r in releases}:
        return _not_performed(
            "npm", name, version, "the version is not a main-line release the registry lists"
        )
    if not releases:
        return _not_performed("npm", name, version, "the registry lists no main-line release")
    latest = releases[-1]
    declared = [r for r in releases if r["license"]]
    pairs = [
        {"from_version": a["version"], "to_version": b["version"]}
        for a, b in zip(declared, declared[1:], strict=False)
        if differs(a["license"], b["license"]) is None
    ]
    return _result(
        "npm",
        name,
        version,
        latest={
            "version": latest["version"],
            "license": latest["license"][1] if latest["license"] else None,
            "published": latest["published"],
        },
        releases_compared=len(declared),
        transitions=_after(version, "npm", transitions(releases)),
        not_comparable=pairs,
    )


def _first_upload(files: Any) -> str | None:
    times = sorted(
        t
        for t in (_time(f.get("upload_time_iso_8601")) for f in files or [] if isinstance(f, dict))
        if t
    )
    return times[0] if times else None


def _check_pypi(name: str, version: str | None, fetch: FetchJson) -> dict[str, Any]:
    package_url, _ = urls("PyPI", name, None)
    status, doc = fetch(package_url)
    if status == 404:
        return _not_performed("PyPI", name, version, "the registry has no such package")
    if status != 200 or not isinstance(doc, dict):
        return _not_performed("PyPI", name, version, _NO_ANSWER)
    info, files = _dict(doc.get("info")), _dict(doc.get("releases"))
    latest = str(info.get("version") or "")
    line = _main_line([v for v, f in files.items() if f], "PyPI")
    if latest not in line:
        return _not_performed(
            "PyPI", name, version, "the latest release is not a main-line release"
        )
    if version is None:
        earlier = line[: line.index(latest)]
        if not earlier:
            return _not_performed("PyPI", name, version, "there is no earlier release to compare")
        base = earlier[-1]
    else:
        # PEP 440: 2.7.0 and 2.7 are one version, under the registry's spelling.
        same = [v for v in line if compare(v, version, "pep440") == 0]
        if not same:
            return _not_performed(
                "PyPI", name, version, "the version is not a main-line release the registry lists"
            )
        base = same[0]
    latest_license = pypi_license(info)
    summary = {
        "version": latest,
        "license": latest_license[1] if latest_license else None,
        "published": _first_upload(files.get(latest)),
    }
    if base == latest:
        return _result("PyPI", name, version, latest=summary, releases_compared=1)
    _, base_url = urls("PyPI", name, base)
    status, base_doc = fetch(str(base_url))
    if status != 200 or not isinstance(base_doc, dict):
        return _not_performed("PyPI", name, version, _NO_ANSWER)
    base_license = pypi_license(base_doc.get("info"))
    change = differs(base_license, latest_license)
    found = []
    if change and base_license and latest_license:
        found.append(
            {
                "from_version": base,
                "to_version": latest,
                "from_license": base_license[1],
                "to_license": latest_license[1],
                "published": summary["published"],
                # Releases between the two were not read: the change is somewhere
                # after `from_version`, at the latest by `to_version`.
                "between_compared": line.index(latest) - line.index(base) == 1,
            }
        )
    return _result(
        "PyPI",
        name,
        version,
        latest=summary,
        releases_compared=2,
        transitions=found,
        not_comparable=[{"from_version": base, "to_version": latest}] if change is None else [],
    )


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    fetch_json: FetchJson | None = None,
) -> dict[str, Any]:
    """Compare the licenses a registry records per release. Never raises.

    With ``version``: every license change in releases after it (what an
    upgrade would bring). Without: the most recent change only.
    """
    eco = ecosystem_of(ecosystem)
    if eco is None:
        return _not_performed(None, str(name), version, "only npm and PyPI are compared")
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
    "COMPARED",
    "NOT_PERFORMED",
    "check",
    "differs",
    "npm_license",
    "npm_release_licenses",
    "pypi_license",
    "transitions",
]
