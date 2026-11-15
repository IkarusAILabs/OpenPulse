"""Publisher change: was this release published by someone the earlier ones were not?
(track T Phase 2, T-C, threat T6; v0.16.0 item Q2).

A maintainer-account or token takeover usually shows as a release published
in a new way: by an account that never published the package before, or
without the trusted publishing or provenance its earlier releases had
(ua-parser-js, 2021; the npm "Shai-Hulud" worm, 2025). This check compares
one release with the releases published before it and names every rule
that fires:

- npm ``new_account``: the publishing account (``_npmUser``) published none
  of the earlier releases in the window, and the release was not published
  through trusted publishing (which uses one shared service account);
- npm ``trusted_publishing_dropped``: an earlier release in the window was
  published through trusted publishing, this one was not;
- PyPI ``publisher_changed``: the release's provenance names another
  publisher (kind, repository, workflow) than the latest earlier attested
  release's; the record says which fields changed (a renamed workflow in
  the same repository reads differently from another repository);
- PyPI ``attestations_stopped``: the release has no provenance, the release
  just before it had.

A fired rule is SUSPICIOUS_INCONCLUSIVE: maintainers hand over, add
co-maintainers and rename workflows, so it is an indicator to check, never
a takeover verdict. Each rule's firing rate on legitimate releases is
measured on the organic reputation set (``benchmarks/reputation_set.py``,
``docs/research/TRACK_T_MEASUREMENTS.md``). A release published the same way
as an earlier one is VERIFIED_RELATIONSHIP: continuity of the publisher,
not evidence that the release is benign. An npm release published through
trusted publishing never is: its account is the one shared service account,
and npm's metadata names no repository or workflow to compare, so a
trusted-publishing configuration moved to another repository would read as
continuity. No earlier release or no publisher evidence to compare is
MISSING_EVIDENCE. Unsupported, invalid,
unreachable or budget-limited is NOT_PERFORMED.

PyPI publishers are compared as PyPI's Integrity API serves them (PyPI
verifies attestations at upload); the ``pypi_provenance`` check verifies
this release's files itself. npm accounts are compared and never named:
records carry rule names, counts and validated versions only (T-F3).
Nothing here feeds a verdict.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import quote

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

CHECK = "publisher_change"
#: Earlier releases compared on npm (the packument has them all, at no cost).
NPM_WINDOW = 9
#: Earlier PyPI releases whose provenance may be fetched (one request each).
PYPI_WINDOW = 3
RULES = ("new_account", "trusted_publishing_dropped", "publisher_changed", "attestations_stopped")

_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?")
_TRUSTED = re.compile(r"[a-z][a-z0-9-]{0,19}")

_STATEMENTS = {
    SUSPICIOUS_INCONCLUSIVE: (
        "the release was published differently from the {n} earlier release(s) compared, "
        "under the rules listed; maintainers hand over and rename workflows, so this is an "
        "indicator to check, never a takeover verdict"
    ),
    VERIFIED_RELATIONSHIP: (
        "the release was published the same way as an earlier release ({how}); this is "
        "continuity of the publisher, not evidence that the release is benign"
    ),
    MISSING_EVIDENCE: "no publisher continuity to compare: {why}",
    NOT_PERFORMED: "publisher change not checked: {why}",
}
_HOW = {
    "account": "by an account that published an earlier release",
    "publisher": "by the publisher named in the latest earlier attested release's provenance",
}
_WHY = {
    "first_release": "no earlier release was published before this one",
    "no_publisher": "the registry names no publisher for this release",
    "trusted_publishing_started": (
        "this release was published through trusted publishing and the earlier ones were "
        "not; that switch is common and is not an indicator"
    ),
    "trusted_publishing": (
        "this release was published through trusted publishing, whose one shared service "
        "account publishes for every project, and npm's metadata names no repository or "
        "workflow to compare"
    ),
    "no_attestations": "neither this release nor the release before it publishes provenance",
    "first_attested": "this is the first attested release in the window compared",
    "unsupported": "checked for PyPI and npm packages with a version only",
    "invalid": "the name or version does not match the ecosystem's grammar",
    "unknown_version": "the registry lists no such version",
    "unreachable": "the registry gave no usable answer",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "private": "the package is on your private-name list; public publishers do not apply",
}


def account_key(name: str) -> str:
    """A stable pseudonym for an npm account: compared, never named."""
    return "sha256:" + hashlib.sha256(f"npm-user:{name.strip().lower()}".encode()).hexdigest()[:16]


def _time(value: Any) -> str | None:
    text = str(value or "")
    return text if _TIME.fullmatch(text) else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------------------
# Release histories, in the shape the organic reputation set records
# ---------------------------------------------------------------------------


def npm_releases(doc: Any) -> list[dict[str, Any]]:
    """Every release of an npm packument, oldest first: version, published,
    publisher (an account key), trusted_publisher (provider id) and attested."""
    times, versions = _dict(_dict(doc).get("time")), _dict(_dict(doc).get("versions"))
    dated = sorted(
        (t, v)
        for v, t in ((v, _time(times.get(v))) for v in versions)
        if t and _NPM_VERSION.fullmatch(v)
    )
    releases = []
    for published, version in dated:
        meta = _dict(versions.get(version))
        user = _dict(meta.get("_npmUser"))
        account = str(user.get("name") or "")
        trusted = str(_dict(user.get("trustedPublisher")).get("id") or "")
        releases.append(
            {
                "version": version,
                "published": published,
                "publisher": account_key(account) if account else None,
                "trusted_publisher": trusted if _TRUSTED.fullmatch(trusted) else None,
                "attested": bool(_dict(meta.get("dist")).get("attestations")),
            }
        )
    return releases


def pypi_releases(doc: Any) -> list[tuple[str, str, str]]:
    """(first upload time, version, one file name: a wheel when there is one),
    oldest first, for a PyPI project document."""
    from core.provenance import _FILENAME

    dated = []
    for version, files in _dict(_dict(doc).get("releases")).items():
        files = [f for f in files or [] if isinstance(f, dict) and not f.get("yanked")]
        names = [n for n in (str(f.get("filename") or "") for f in files) if _FILENAME.fullmatch(n)]
        times = sorted(t for t in (_time(f.get("upload_time_iso_8601")) for f in files) if t)
        if names and times and _PYPI_VERSION.fullmatch(version):
            dated.append(
                (times[0], version, next((n for n in names if n.endswith(".whl")), names[0]))
            )
    return sorted(dated)


def pypi_publishers(provenance: Any) -> list[dict[str, Any]]:
    """The validated publishers a provenance document names, in order, once each."""
    from core.provenance import _publisher

    found: list[dict[str, Any]] = []
    for bundle in _dict(provenance).get("attestation_bundles") or []:
        raw = bundle.get("publisher") if isinstance(bundle, dict) else None
        if isinstance(raw, dict) and (publisher := _publisher(raw)) not in found:
            found.append(publisher)
    return found


def provenance_url(name: str, version: str, filename: str) -> str:
    project = re.sub(r"[-_.]+", "-", name).lower()
    return f"https://pypi.org/integrity/{project}/{quote(version)}/{quote(filename)}/provenance"


# ---------------------------------------------------------------------------
# The rules (shared with the organic measurement)
# ---------------------------------------------------------------------------


def npm_rules(target: dict[str, Any], earlier: list[dict[str, Any]]) -> tuple[str, list[str], str]:
    """(status, fired rules, reason) for one npm release against earlier ones."""
    if not earlier:
        return MISSING_EVIDENCE, [], "first_release"
    fired = []
    if not target.get("trusted_publisher") and any(e.get("trusted_publisher") for e in earlier):
        fired.append("trusted_publishing_dropped")
    accounts = {e["publisher"] for e in earlier if e.get("publisher")}
    publisher = target.get("publisher")
    if publisher and publisher not in accounts and not target.get("trusted_publisher"):
        fired.append("new_account")
    if fired:
        return SUSPICIOUS_INCONCLUSIVE, fired, ""
    if target.get("trusted_publisher"):
        # The shared service account is not a publisher: matching it is not continuity.
        if any(e.get("trusted_publisher") for e in earlier):
            return MISSING_EVIDENCE, [], "trusted_publishing"
        return MISSING_EVIDENCE, [], "trusted_publishing_started"
    if publisher in accounts:
        return VERIFIED_RELATIONSHIP, [], "account"
    return MISSING_EVIDENCE, [], "no_publisher"


def _publisher_set(release: dict[str, Any]) -> set[tuple[Any, ...]]:
    return {
        (p.get("kind"), str(p.get("repository") or "").lower() or None, p.get("workflow"))
        for p in release.get("publishers") or []
    }


def changed_fields(target: dict[str, Any], previous: dict[str, Any] | None) -> list[str]:
    """Which publisher fields differ between two attested releases."""
    if previous is None:
        return []
    now, before = _publisher_set(target), _publisher_set(previous)
    return [
        field
        for i, field in enumerate(("kind", "repository", "workflow"))
        if {p[i] for p in now} != {p[i] for p in before}
    ]


def pypi_rules(target: dict[str, Any], earlier: list[dict[str, Any]]) -> tuple[str, list[str], str]:
    """(status, fired rules, reason) for one PyPI release against earlier ones.
    ``attested`` is True, False (no provenance) or None (no answer)."""
    if not earlier:
        return MISSING_EVIDENCE, [], "first_release"
    if target.get("attested") is None:
        return NOT_PERFORMED, [], "unreachable"
    fired = []
    if target["attested"] is False and earlier[-1].get("attested") is True:
        fired.append("attestations_stopped")
    attested = [e for e in earlier if e.get("attested")]
    if target["attested"] and attested and _publisher_set(target) != _publisher_set(attested[-1]):
        fired.append("publisher_changed")
    if fired:
        return SUSPICIOUS_INCONCLUSIVE, fired, ""
    if target["attested"] and attested:
        return VERIFIED_RELATIONSHIP, [], "publisher"
    if target["attested"]:
        return MISSING_EVIDENCE, [], "first_attested"
    return MISSING_EVIDENCE, [], "no_attestations"


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------


def _record(status: str, why: str = "", *, n: int = 0, **evidence: Any) -> dict[str, Any]:
    at = _now()
    if status == VERIFIED_RELATIONSHIP:
        statement = _STATEMENTS[status].format(how=_HOW[why])
    elif status == SUSPICIOUS_INCONCLUSIVE:
        statement = _STATEMENTS[status].format(n=n)
    else:
        statement = _STATEMENTS[status].format(why=_WHY[why])
    return {
        "check": CHECK,
        "status": status,
        "statement": statement,
        "checked_at": at,
        "evidence": evidence,
    }


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, why)


def _result(status: str, fired: list[str], why: str, **evidence: Any) -> dict[str, Any]:
    if status == SUSPICIOUS_INCONCLUSIVE:
        return _record(status, n=evidence["compared_releases"], rules=fired, **evidence)
    return _record(status, why, rules=[], **evidence)


def _check_npm(name: str, version: str, fetch_json) -> dict[str, Any]:
    package_url, _ = urls("npm", name, None)
    status, doc = fetch_json(package_url)
    if status != 200 or not isinstance(doc, dict):
        return _record(NOT_PERFORMED, "unreachable", http_status=status or None)
    releases = npm_releases(doc)
    index = next((i for i, r in enumerate(releases) if r["version"] == version), None)
    if index is None:
        return not_performed("unknown_version")
    earlier = releases[max(0, index - NPM_WINDOW) : index]
    state, fired, why = npm_rules(releases[index], earlier)
    return _result(
        state,
        fired,
        why,
        compared_releases=len(earlier),
        previous_version=earlier[-1]["version"] if earlier else None,
    )


def _check_pypi(name: str, version: str, fetch_json, fetch_provenance) -> dict[str, Any]:
    package_url, _ = urls("PyPI", name, None)
    status, doc = fetch_json(package_url)
    if status != 200 or not isinstance(doc, dict):
        return _record(NOT_PERFORMED, "unreachable", http_status=status or None)
    dated = pypi_releases(doc)
    index = next((i for i, (_t, v, _f) in enumerate(dated) if v == version), None)
    if index is None:
        return not_performed("unknown_version")

    def release(i: int) -> dict[str, Any]:
        _published, v, filename = dated[i]
        code, provenance = fetch_provenance(provenance_url(name, v, filename))
        attested = (
            True if code == 200 and provenance is not None else False if code == 404 else None
        )
        return {
            "version": v,
            "attested": attested,
            "publishers": pypi_publishers(provenance) if attested else [],
        }

    target = release(index)
    if target["attested"] is None and index:
        return _record(NOT_PERFORMED, "unreachable", rules=[])
    earlier: list[dict[str, Any]] = []
    # Newest first, and only as far back as a rule needs: the release just
    # before, then back to the latest attested one within the window.
    for i in range(index - 1, max(-1, index - 1 - PYPI_WINDOW), -1):
        earlier.insert(0, release(i))
        if earlier[0]["attested"] or (not target["attested"] and len(earlier) == 1):
            break
    state, fired, why = pypi_rules(target, earlier)
    previous = next((e for e in reversed(earlier) if e["attested"]), None)
    return _result(
        state,
        fired,
        why,
        compared_releases=len(earlier),
        previous_version=earlier[-1]["version"] if earlier else None,
        publishers=target["publishers"],
        previous_publishers=previous["publishers"] if previous else [],
        changed=changed_fields(target, previous) if "publisher_changed" in fired else [],
    )


def check(
    ecosystem: str | None,
    name: str,
    version: str | None,
    *,
    fetch_json=None,
    fetch_provenance=None,
) -> dict[str, Any]:
    """One T-F1 record for one release. Never raises on registry trouble."""
    from core import digest_integrity, provenance

    eco = ecosystem_of(ecosystem)
    if eco not in ("npm", "PyPI") or not version:
        return not_performed("unsupported")
    name_ok = (_NPM_NAME if eco == "npm" else _PYPI_NAME).fullmatch(name)
    version_ok = (_NPM_VERSION if eco == "npm" else _PYPI_VERSION).fullmatch(version)
    if not name_ok or not version_ok:
        return not_performed("invalid")
    fetch_json = fetch_json or digest_integrity.default_fetch
    if eco == "npm":
        return _check_npm(name, version, fetch_json)
    return _check_pypi(
        name, version, fetch_json, fetch_provenance or provenance.default_fetch_provenance
    )


__all__ = [
    "CHECK",
    "NPM_WINDOW",
    "PYPI_WINDOW",
    "RULES",
    "account_key",
    "changed_fields",
    "check",
    "not_performed",
    "npm_releases",
    "npm_rules",
    "pypi_publishers",
    "pypi_releases",
    "pypi_rules",
]
