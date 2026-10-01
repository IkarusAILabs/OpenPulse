"""Warning lead time — recorded per finding, never averaged or marketed.

Lead time = effective_date - detected_at, in whole days, and it is
only meaningful for *upcoming* changes: when the effective date is
unknown, unparseable, or already past, there is no lead time to
report and the answer is None — not zero, not a guess.

No aggregation lives here on purpose. Averages over heterogeneous
changes would manufacture a metric the system cannot defend; that
stays out until independently measured customer incidents exist.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _parse_day(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def lead_time_days(detected: Any, effective: Any) -> int | None:
    """Days between first detection and effect. None when unknown or past."""
    start, end = _parse_day(detected), _parse_day(effective)
    if start is None or end is None:
        return None
    delta = (end - start).days
    return delta if delta >= 0 else None


def finding_lead_time(finding: dict[str, Any]) -> tuple[int | None, str | None, str | None]:
    """(days, detected, effective) for one finding, using its own dates.

    Detection: observed_at (the analysis date — so this reads as
    *remaining* warning), else published. Effect: effective_at, else
    event_date. Returns Nones when the finding carries no usable pair.
    """
    detected = finding.get("observed_at") or finding.get("published")
    effective = finding.get("effective_at") or finding.get("event_date")
    if detected is None or effective is None:
        return None, None, None
    return lead_time_days(detected, effective), str(detected)[:10], str(effective)[:10]
