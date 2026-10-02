"""Finding freshness — the research window OpenPulse reasons within.

OpenPulse researches the last 12 months (`RESEARCH_WINDOW_DAYS`): a
finding whose change already applied over a year ago is background
knowledge, not news. A monthly intelligence report headlining a
2024 EOL as a current change is stale output, however accurate the
underlying fact.

States:

- CURRENT — effective within the window, or upcoming (future
  effective dates are current by definition).
- BACKGROUND — effective date older than the window.
- UNKNOWN — no trustworthy effective date (dateless `eol: true`,
  unparseable, missing). Unknown age is never called old.

Freshness demotes and labels; it never deletes. The appendix keeps
the full record, and lifecycle matrices stay cumulative. Pure
functions; `today` injectable for deterministic tests.

The event-temporal classification (`classify`) answers a different
question — *what is this finding's position in time* — with its own
vocabulary (NEW / UPCOMING / ACTIVE / RECENTLY_UPDATED / EXPIRED /
UNKNOWN_DATE). It drives report placement; freshness drives ranking
and labels. Both are deterministic and evidence-driven: no LLM, no
heuristics beyond documented date arithmetic.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from core.leadtime import parse_day

#: Rolling research window: findings effective before this are background.
RESEARCH_WINDOW_DAYS = 365

#: Announcement/update recency window. Justification: three monthly
#: reporting cycles; OSS disclosure-to-impact typically spans weeks to
#: months; lifecycle notices run 3–12 months (covered by effective-date
#: precedence, not this window). Effective-date rules always take
#: precedence over this fallback age. Configurable via env.
DEFAULT_RECENCY_DAYS = 90
RECENCY_ENV_VAR = "OPENPULSE_REPORT_FRESHNESS_DAYS"

CURRENT = "CURRENT"
BACKGROUND = "BACKGROUND"
UNKNOWN = "UNKNOWN"

#: Freshness-classification states (report placement vocabulary).
NEW = "NEW"
UPCOMING = "UPCOMING"
ACTIVE = "ACTIVE"
RECENTLY_UPDATED = "RECENTLY_UPDATED"
EXPIRED = "EXPIRED"
UNKNOWN_DATE = "UNKNOWN_DATE"

#: States narrated in the main report. EXPIRED findings live in the
#: Historical appendix; UNKNOWN_DATE findings join the main report
#: only when REVIEW/ACTION-eligible (benefit of the doubt, stated).
MAIN_REPORT_STATES = (NEW, UPCOMING, ACTIVE, RECENTLY_UPDATED)


def recency_days(default: int = DEFAULT_RECENCY_DAYS) -> int:
    """Recency window in days (env override, garbage falls back)."""
    try:
        value = int(os.environ.get(RECENCY_ENV_VAR, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def finding_age_days(finding: dict[str, Any], today: date | None = None) -> int | None:
    """Days since the change applied. None when unknown or upcoming.

    Upcoming changes (effective in the future) have no age — they are
    current by definition, handled by the caller, never background.
    """
    today = today or date.today()
    if not isinstance(finding, dict):
        return None
    effective = parse_day(finding.get("effective_at") or finding.get("event_date"))
    if effective is None or effective > today:
        return None
    return (today - effective).days


def freshness(finding: dict[str, Any], today: date | None = None) -> tuple[str, str | None]:
    """(state, reason). Background only on a trustworthy old date."""
    today = today or date.today()
    if not isinstance(finding, dict):
        return UNKNOWN, "not a finding"
    effective = parse_day(finding.get("effective_at") or finding.get("event_date"))
    if effective is None:
        return UNKNOWN, "no trustworthy effective date"
    if effective > today:
        return CURRENT, "upcoming change"
    age = (today - effective).days
    if age > RESEARCH_WINDOW_DAYS:
        return BACKGROUND, f"effective {effective} is over 12 months ago"
    return CURRENT, None


def is_background(finding: dict[str, Any], today: date | None = None) -> bool:
    """True only for BACKGROUND (unknown age never counts as old)."""
    return freshness(finding, today)[0] == BACKGROUND


def _finding_dates(finding: dict[str, Any]) -> dict[str, date | None]:
    """The five temporal roles, parsed. Never substituted for another."""
    announced = parse_day(finding.get("announced_at") or finding.get("published"))
    effective = parse_day(finding.get("effective_at") or finding.get("event_date"))
    detected = parse_day(finding.get("first_detected_at"))
    verified = parse_day(finding.get("last_observed_at") or finding.get("observed_at"))
    return {
        "announced": announced,
        "effective": effective,
        "detected": detected,
        "verified": verified,
    }


def classify(
    finding: dict[str, Any],
    today: date | None = None,
    window_days: int | None = None,
) -> tuple[str, list[str]]:
    """Event-temporal status + reasons. Deterministic date arithmetic.

    Precedence is event semantics, not age thresholds: a future
    effective date always wins over an old announcement (upcoming
    consequences stay visible); a recent announcement always wins over
    a past effective date (new disclosures surface). Only when neither
    applies do recency and verification decide.
    """
    today = today or date.today()
    window = window_days if window_days and window_days > 0 else recency_days()
    if not isinstance(finding, dict):
        return UNKNOWN_DATE, ["not a finding"]
    dates = _finding_dates(finding)
    announced, effective = dates["announced"], dates["effective"]
    detected, verified = dates["detected"], dates["verified"]

    def ago(day: date) -> int:
        return (today - day).days

    if effective is not None and effective > today:
        return UPCOMING, [f"effective {effective} is in the future"]
    if announced is not None and ago(announced) <= window:
        return NEW, [f"announced {announced}, within {window} days"]
    if announced is not None and ago(announced) > window:
        if detected is not None and ago(detected) <= window:
            return RECENTLY_UPDATED, [
                f"announced {announced} but first detected {detected}"
            ]
        if effective is not None and effective <= today:
            return EXPIRED, [f"effective {effective}; announced {announced}"]
        if effective is None and verified is not None and ago(verified) <= window:
            return ACTIVE, [f"ongoing condition, verified {verified}"]
        return EXPIRED, [f"announced {announced}, no recent verification"]
    if detected is not None and ago(detected) <= window:
        return NEW, [f"first detected {detected}, no announcement on record"]
    if effective is not None and effective <= today:
        if ago(effective) > RESEARCH_WINDOW_DAYS:
            return EXPIRED, [f"effective {effective} is over 12 months ago"]
        return ACTIVE, [f"effective {effective} within the research window"]
    if verified is not None and ago(verified) <= window:
        return ACTIVE, [f"verified {verified}, no dates to age it by"]
    if effective is not None or verified is not None:
        return EXPIRED, ["stale and undated-or-past with no recent verification"]
    return UNKNOWN_DATE, ["no announcement, effective, detection, or verification date"]
