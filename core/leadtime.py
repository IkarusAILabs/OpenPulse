"""Warning lead time — recorded per finding, never averaged or marketed.

Lead time = effective_at - first_detected_at, in whole days, where
first_detected_at is the first trustworthy OpenPulse detection of the
material change — NOT the latest observation, NOT "today", and never
an estimate. If first detection is unknown, there is no lead-time
claim (None), full stop.

Temporal roles (never conflated):

- published_at / announcement_at — what the source claims;
- first_detected_at — our first trustworthy detection of the change;
- last_observed_at — the most recent confirmation (re-observation,
  not discovery);
- effective_at — when the change applies.

Only meaningful for *upcoming* changes: unknown, unparseable, or
already-past effective dates yield None — not zero, not a guess.

No aggregation lives here on purpose. Averages over heterogeneous
changes would manufacture a metric the system cannot defend; that
stays out until independently measured customer incidents exist.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def parse_day(value: Any) -> date | None:
    """Timezone-safe day parsing: date/datetime objects and ISO strings
    (with or without offsets). Garbage -> None, never an exception."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        moment = value
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return moment.date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def lead_time_days(first_detected: Any, effective: Any) -> int | None:
    """Days between first detection and effect. None when unknown or past."""
    start, end = parse_day(first_detected), parse_day(effective)
    if start is None or end is None:
        return None
    delta = (end - start).days
    return delta if delta >= 0 else None


def temporal_roles(finding: dict[str, Any]) -> dict[str, Any]:
    """The five temporal roles for one finding, parsed (None when absent)."""
    if not isinstance(finding, dict):
        return {}
    return {
        "published_at": parse_day(finding.get("published") or finding.get("published_at")),
        "announcement_at": parse_day(finding.get("announcement_at")),
        "first_detected_at": parse_day(finding.get("first_detected_at")),
        "last_observed_at": parse_day(
            finding.get("last_observed_at") or finding.get("observed_at")
        ),
        "effective_at": parse_day(finding.get("effective_at") or finding.get("event_date")),
    }


def finding_lead_time(finding: dict[str, Any]) -> tuple[int | None, str | None, str | None]:
    """(days, first_detected, effective) for one finding.

    Detection is first_detected_at ONLY — observed_at/last sightings
    are re-observations, not discovery, and must never stand in.
    Unknown first detection -> (None, None, None): no claim.
    """
    if not isinstance(finding, dict):
        return None, None, None
    detected = parse_day(finding.get("first_detected_at"))
    effective = parse_day(finding.get("effective_at") or finding.get("event_date"))
    if detected is None or effective is None:
        return None, None, None
    return lead_time_days(detected, effective), str(detected), str(effective)


def event_effective_day(event: Any) -> date | None:
    """The evidence-declared effective date for one event, or None.

    First evidence that declares one wins - the same semantics the
    evidence contract pins in its dates block - so there is ONE
    derivation of "when this event takes effect", shared by every
    consumer (attestation, alert digest) instead of re-walked per
    surface. An event whose evidences declare no effective date has
    no deadline: None, never a date borrowed from published or
    announcement fields.
    """
    for evidence in getattr(event, "evidences", None) or []:
        day = parse_day(getattr(evidence, "effective_date", None))
        if day is not None:
            return day
    return None
