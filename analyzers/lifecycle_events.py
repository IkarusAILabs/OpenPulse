"""Lifecycle finding -> OSSEvent bridge (P0 §6).

Lifecycle findings carry machine-readable scope (``scope.kind`` /
``versions`` / ``artifacts``) since the v2.5 analyst update. This
module converts one such finding into an ``OSSEvent`` so lifecycle
matching reuses the exact dependency-verdict machinery as security
events (``core.risk.match`` + ``core.risk.check``) — never a second
implementation.

Bridge rules (conservative, documented):
- Confidence comes from the finding's supporting sources: an
  ``official`` authority yields CONFIRMED, else EMERGING for a single
  secondary source. Lifecycle findings never self-declare
  CORROBORATED (single-source by construction here).
- Impact maps through the eligibility layer (``core.risk.impact``):
  public-context eligibility, never the raw analyst proposal.
- Evidence requires a fetchable URL: supporting entries expose
  ``link``/``url``. Entries without URLs contribute excerpts only.
- Findings without scope bridge with scope ``None`` (project-wide
  legacy semantics) — callers should prefer scoped findings; the
  UNKNOWN-vs-match behavior then follows match.py exactly.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from core.schema.enums import Confidence
from core.schema.models import OSSEvent


def _source_entries(finding: dict[str, Any]) -> list[dict[str, Any]]:
    supporting = finding.get("supporting") or []
    return [e for e in supporting if isinstance(e, dict)]


def _evidences(
    finding: dict[str, Any], observed_at: str
) -> list[dict[str, Any]]:
    evidences = []
    for entry in _source_entries(finding):
        url = entry.get("link") or entry.get("url")
        if not isinstance(url, str) or not url.startswith("http"):
            continue
        product = entry.get("product") or entry.get("repo") or "source"
        collector = entry.get("collector", "unknown")
        evidences.append(
            {
                "source": {
                    "name": f"{collector}/{product}",
                    "url": url,
                    "authority": "secondary",
                    "fetched_at": f"{observed_at}T00:00:00Z",
                },
                "excerpt": str(entry.get("excerpt") or finding.get("summary") or "")[:2000],
                "effective_date": finding.get("effective_at"),
                "announcement_date": None,
                "relation": "supports",
            }
        )
    if not evidences:
        evidences.append(
            {
                "source": {
                    "name": f"{finding.get('analyst', 'change')}/finding",
                    "url": "https://endoflife.date/",
                    "authority": "secondary",
                    "fetched_at": f"{observed_at}T00:00:00Z",
                },
                "excerpt": str(finding.get("summary") or finding.get("title") or "")[:2000],
                "effective_date": finding.get("effective_at"),
                "announcement_date": None,
                "relation": "supports",
            }
        )
    return evidences


def _confidence(finding: dict[str, Any]) -> str:
    for entry in _source_entries(finding):
        source = entry.get("source") if isinstance(entry.get("source"), dict) else None
        if source and source.get("authority") == "official":
            return Confidence.CONFIRMED.value
    return Confidence.EMERGING.value


def _scope(finding: dict[str, Any]) -> dict[str, Any] | None:
    scope = finding.get("scope")
    if not isinstance(scope, dict):
        return None
    kind = str(scope.get("kind") or "project")
    if kind not in ("project", "package", "artifact", "version", "registry"):
        return None
    return {
        "kind": kind,
        "versions": [str(v) for v in scope.get("versions") or []],
        "artifacts": [str(a) for a in scope.get("artifacts") or []],
        "packages": [str(p) for p in scope.get("packages") or []],
        "registries": [str(r) for r in scope.get("registries") or []],
    }


def finding_to_event(
    finding: dict[str, Any],
    project_slug: str,
    observed_at: str | None = None,
    today: date | None = None,
) -> OSSEvent:
    """Convert one lifecycle finding into a matchable OSSEvent.

    Deterministic: the event id derives from project, event type, and
    scope versions (no wall-clock, no randomness). Impact flows through
    eligibility so bridged events never smuggle analyst ACTION into
    gates; ``check`` verdicts decide impact downstream.
    """
    from core.risk.impact import evaluate_impact

    finding = dict(finding or {})
    slug = str(project_slug or "unknown")
    observed = str(observed_at or finding.get("observed_at") or
                   (today or date.today()).isoformat())
    versions = [str(v) for v in (finding.get("scope") or {}).get("versions", [])
                if isinstance(finding.get("scope"), dict)] or [
        str(v) for v in finding.get("affected_versions", []) if v != "*"
    ]
    event_id = f"evt-{slug}-{str(finding.get('event_type', 'OTHER')).lower()}"
    if versions:
        event_id += "-" + "-".join(sorted(set(versions))[:4])
    eligibility = evaluate_impact(finding).get("eligibility", "REVIEW")
    impact = {"ACTION": "REVIEW", "CRITICAL": "REVIEW"}.get(
        str(eligibility), str(eligibility))
    return OSSEvent(
        id=event_id,
        project_slug=slug,
        event_type=str(finding.get("event_type") or "OTHER_CRITICAL"),
        title=str(finding.get("title") or "lifecycle finding"),
        summary=str(finding.get("summary") or ""),
        confidence=_confidence(finding),
        impact=impact,
        affected_versions=[str(v) for v in finding.get("affected_versions", [])],
        affected_artifacts=[
            {"kind": str(a.get("kind", "unknown")), "ref": str(a.get("ref", ""))}
            for a in finding.get("affected_artifacts", [])
            if isinstance(a, dict) and a.get("ref")
        ],
        evidences=_evidences(finding, observed[:10]),
        scope=_scope(finding),
        created_at=datetime.now(timezone.utc),
    )
