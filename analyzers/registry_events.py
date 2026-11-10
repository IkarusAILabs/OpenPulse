"""Registry change finding -> OSSEvent bridge (v0.21.0 W1).

The v0.20.0 checks read what a publisher declared on npm or PyPI: a
deprecation, a yanked release, an Inactive classifier
(``core.registry_deprecation``) and the license each release records
(``core.release_license``). ``analyzers.change_analyst`` turns them into
findings. This module turns one such finding into an ``OSSEvent`` so a
dependency you use is judged by the same verdict machinery as every other
upstream change (``core.risk.check``), and reaches contracts, SARIF, the
digest and ``--fail-on`` without a second implementation.

Bridge rules:
- The event is built for one dependency and evaluated against that
  dependency only. Its scope names the package as a purl (exact
  self-identity, no catalog mapping), so it can never reach another
  package. A version-level flag is about the release you use because the
  check was asked about that release; the event is never offered to
  another version of the same package.
- Scope versions stay empty: a registry flag carries no release-cycle
  identity, so it is not recorded as a lifecycle fact in the detection
  ledger (``durable_fact_from_cause``).
- Impact is REVIEW, as the finding placed it; confidence is the
  finding's own (C5): CONFIRMED for a flag the publisher set, EMERGING
  for a classifier or an observed license difference.
- The evidence is the registry's own page for the release, with authority
  ``primary``: the publisher's statement on its distribution channel,
  not on the project's own domain.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any

from core.schema.models import OSSEvent

_SOURCES = {"registry.npmjs.org", "pypi.org"}
_ID_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
_FALLBACK_PAGES = {"registry.npmjs.org": "https://www.npmjs.com/", "pypi.org": "https://pypi.org/"}


def _id_part(value: Any) -> str:
    return _ID_UNSAFE.sub("_", str(value)).strip("_") or "_"


def event_id(finding: dict[str, Any]) -> str:
    """A deterministic event id: kind, package and the releases concerned."""
    evidence = finding.get("registry_evidence") or {}
    package = str(evidence.get("package") or "")
    if finding.get("event_type") == "LICENSE_CHANGE":
        parts = ["license", package, evidence.get("from_version"), evidence.get("to_version")]
    else:
        level_version = evidence.get("version") if evidence.get("level") == "version" else None
        parts = [evidence.get("flag"), package, level_version]
    return "evt-registry-" + "-".join(_id_part(p) for p in parts if p)


def _effective(value: Any) -> str | None:
    text = str(value or "")[:10]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def registry_finding_to_event(
    finding: dict[str, Any], project_slug: str, today: date | None = None
) -> OSSEvent:
    """One LICENSE_CHANGE or DEPRECATION finding -> a matchable OSSEvent."""
    evidence = finding.get("registry_evidence") or {}
    source = str(evidence.get("source") or "")
    if source not in _SOURCES:
        raise ValueError(f"not a registry finding: source {source!r}")
    purl = str(evidence.get("package") or "")
    if not purl.startswith("pkg:"):
        raise ValueError("a registry finding names its package as a purl")
    references = [r for r in finding.get("references") or [] if str(r).startswith("https://")]
    observed = (today or date.today()).isoformat()
    return OSSEvent(
        id=event_id(finding),
        project_slug=str(project_slug or purl),
        event_type=str(finding["event_type"]),
        title=str(finding.get("title") or ""),
        summary=str(finding.get("summary") or ""),
        confidence=str(finding.get("confidence") or "EMERGING"),
        impact="REVIEW",
        affected_versions=[str(v) for v in finding.get("affected_versions") or ["*"]],
        affected_artifacts=[{"kind": "package", "ref": purl}],
        evidences=[
            {
                "source": {
                    "name": source,
                    "url": references[0] if references else _FALLBACK_PAGES[source],
                    "authority": "primary",
                    "fetched_at": f"{observed}T00:00:00Z",
                    "acquisition_method": "https-collector",
                },
                "excerpt": str(finding.get("summary") or finding.get("title") or "")[:2000],
                "effective_date": _effective(finding.get("effective_at")),
                "announcement_date": None,
                "relation": "supports",
            }
        ],
        scope={"kind": "package", "packages": [purl], "versions": []},
        created_at=datetime.now(timezone.utc),
    )


def repository_finding_to_event(
    finding: dict[str, Any],
    purl: str,
    project_slug: str,
    repository: str,
    today: date | None = None,
) -> OSSEvent:
    """A repository-history finding -> an event for one dependency (v0.21.0 W3).

    ``repository`` is the GitHub repository the package's registry metadata
    names as its source; the finding is a change OpenPulse saw between two
    records of that repository's history (``analyze_repository_changes``).
    The event is scoped to the package's purl and offered to that dependency
    only, like a registry event. The link from package to repository is the
    publisher's claim, not verified here, and the summary says so. The id
    carries the day the change was first seen, so the same kind of change
    seen again later is another event.
    """
    if not str(purl).startswith("pkg:"):
        raise ValueError("a dependency event names its package as a purl")
    event_type = str(finding.get("event_type") or "")
    if event_type not in ("LICENSE_CHANGE", "PROJECT_ARCHIVED", "OWNERSHIP_CHANGE"):
        raise ValueError(f"not a repository-history finding: {event_type!r}")
    references = [r for r in finding.get("references") or [] if str(r).startswith("https://")]
    observed = (today or date.today()).isoformat()
    seen = _effective(finding.get("effective_at")) or observed
    summary = (
        f"{finding.get('summary') or ''} {purl} names {repository} as its source "
        "repository on the registry; that link is the publisher's claim and is not "
        "verified here."
    ).strip()
    return OSSEvent(
        id="evt-repository-"
        + "-".join(_id_part(p) for p in (event_type.lower(), repository, purl, seen)),
        project_slug=str(project_slug or purl),
        event_type=event_type,
        title=str(finding.get("title") or ""),
        summary=summary,
        confidence=str(finding.get("confidence") or "EMERGING"),
        impact="REVIEW",
        affected_versions=["*"],
        affected_artifacts=[
            {"kind": "package", "ref": purl},
            {"kind": "source-repository", "ref": f"github.com/{repository}"},
        ],
        evidences=[
            {
                "source": {
                    "name": "github.com",
                    "url": references[0] if references else f"https://github.com/{repository}",
                    "authority": "primary",
                    "fetched_at": f"{observed}T00:00:00Z",
                    "acquisition_method": "https-collector",
                },
                "excerpt": summary[:2000],
                "effective_date": seen,
                "announcement_date": None,
                "relation": "supports",
            }
        ],
        scope={"kind": "package", "packages": [purl], "versions": []},
        created_at=datetime.now(timezone.utc),
    )


__all__ = ["event_id", "registry_finding_to_event", "repository_finding_to_event"]
