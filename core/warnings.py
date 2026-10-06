"""Warning deadlines - the countdown surface over the alert digest (issue #66).

The digest (core.digest, issue #63) already owns the ONE join that
turns public intelligence into customer deadlines: check verdicts
(customer evidence), event evidences (effective dates), the detection
ledger (first detections). This module adds only what a countdown
needs on top - severity bands, urgency ranking, one action line -
as a projection over that join. Never a second matching engine,
never a second ledger reader, never a second effective-date
derivation: every deadline fact in a warning object comes from
build_digest, so the digest and the warnings surface can never
disagree about a single dependency.

Why the ledger is not queried directly here: the ledger records
first detections per project fact - it stores no effective dates
and no customer dependencies. A deadline needs all three parties
(event, verdict, ledger), and that composition already exists.
The issue's "query ledger for entities with effective_date in the
future" is realized as this projection: ledger first-detections
joined onto evidence-declared effective dates for declared
dependencies.

Severity is the countdown dimension ONLY - how far out the
deadline sits - and stays separate from impact, the evidence's
asserted importance. The two cross exactly once, in
recommended_action, for humans. Bands are defined by planning
horizons, documented in SEVERITY_BANDS: a working week (7), a
planning cycle (30), a quarter (90). Already-effective changes
stay in as OVERDUE - the digest's symmetric window keeps them
until they age out, and a passed deadline is the most actionable
line a warning list can carry.

Lead time is inherited, never recomputed: effective minus first
trustworthy detection, None when no detection is recorded. Ranking
is soonest effective first, then SHORTEST known lead time (the
least-warned change is the most urgent at equal distance), then
ref and event id for full determinism. No aggregation, no
averages - a single deadline is a fact; a mean lead time would be
a marketing number this system refuses to manufacture.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from core.digest import DEFAULT_WINDOW_DAYS, build_digest
from core.risk.check import DependencyVerdict
from core.schema.models import OSSEvent

SEVERITY_OVERDUE = "OVERDUE"
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

#: Display order: the most urgent band leads the briefing.
SEVERITY_ORDER = (
    SEVERITY_OVERDUE,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)

#: Countdown -> severity band, in whole days until effective.
#: Horizons: 7 = one working week, 30 = one planning cycle,
#: 90 = one quarter. Deterministic and documented - severity is
#: time pressure, not fear.
SEVERITY_BANDS: tuple[tuple[int, str], ...] = (
    (-1, SEVERITY_OVERDUE),  # negative days = already effective
    (7, SEVERITY_CRITICAL),
    (30, SEVERITY_HIGH),
    (90, SEVERITY_MEDIUM),
)

#: Impacts that assert no migration urgency: the countdown never
#: turns a WATCH/INFO finding into migration work.
_PASSIVE_IMPACTS = frozenset({"WATCH", "INFORMATIONAL"})

_SEVERITY_ACTION = {
    SEVERITY_OVERDUE: "Deadline passed: confirm exposure and schedule the upgrade now.",
    SEVERITY_CRITICAL: "Act now: complete the upgrade before the effective date.",
    SEVERITY_HIGH: "Schedule the upgrade this cycle, before the effective date.",
    SEVERITY_MEDIUM: "Plan the upgrade into the next planning cycle.",
    SEVERITY_LOW: "Track the deadline; no near-term action required.",
}


def deadline_severity(days_until_effective: int) -> str:
    """Pure countdown -> severity band (issue #66: pure-function deadline calc)."""
    for bound, severity in SEVERITY_BANDS:
        if days_until_effective <= bound:
            return severity
    return SEVERITY_LOW


def recommended_action(severity: str, impact: str) -> str:
    """One action line: severity drives urgency, impact gates it.

    WATCH/INFO evidence never implies migration work however close
    the date; everything else gets the band's action line.
    """
    if str(impact).upper() in _PASSIVE_IMPACTS:
        return "No migration action implied by this evidence; keep monitoring."
    return _SEVERITY_ACTION.get(str(severity), _SEVERITY_ACTION[SEVERITY_LOW])


def _rank(warning: dict[str, Any]) -> tuple[Any, ...]:
    """Urgency: soonest effective, then least-warned (shortest known
    lead time), unknown lead time last, then ref/event id so the
    order is fully deterministic and testable."""
    lead = warning["lead_time_days"]
    return (
        warning["days_until_effective"],
        1 if lead is None else 0,
        0 if lead is None else lead,
        str(warning["ref"]),
        str(warning["event_id"]),
    )


def build_warnings(
    verdicts: list[DependencyVerdict],
    events: list[OSSEvent],
    ledger_root: str | None = None,
    today: date | None = None,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> dict[str, Any]:
    """Verdicts + events + ledger -> ranked warning deadlines.

    Pure projection over build_digest: every field is inherited or
    derived from the digest entry - customer evidence required, the
    symmetric window, security-cause exclusion, ledger degradation.
    Output shape (issue #66): {project, ref, event_type,
    effective_date, first_detected, lead_time_days,
    days_until_effective, severity, recommended_action} plus title /
    impact / event_id / relationship for renderers.
    """
    digest = build_digest(
        verdicts, events, ledger_root=ledger_root, today=today, window_days=window_days
    )
    warnings: list[dict[str, Any]] = []
    for entry in digest["entries"]:
        days_until = int(entry["days_until_effective"])
        severity = deadline_severity(days_until)
        warnings.append(
            {
                "project": entry["project"],
                "ref": entry["dependency"],
                "event_id": entry["event_id"],
                "event_type": entry["event_type"],
                "title": entry["title"],
                "impact": entry["impact"],
                "relationship": entry["relationship"],
                "effective_date": entry["effective_date"],
                "first_detected": entry["first_detected"],
                "lead_time_days": entry["lead_time_days"],
                "days_until_effective": days_until,
                "severity": severity,
                "recommended_action": recommended_action(severity, entry["impact"]),
            }
        )
    warnings.sort(key=_rank)
    return {
        "generated_at": digest["generated_at"],
        "window_days": int(window_days),
        "warnings": warnings,
    }


def _lead_note(w: dict[str, Any]) -> str:
    if w["first_detected"]:
        if w["lead_time_days"] is not None:
            return "{}d (first detected {})".format(w["lead_time_days"], w["first_detected"])
        return "recorded, lead time not computable"
    return "no first-detection record"


def _days_note(days: int) -> str:
    if days < 0:
        return f"{-days}d ago"
    if days == 0:
        return "today"
    return f"in {days}d"


def render_warnings_md(built: dict[str, Any]) -> str:
    """Ranked deadlines -> markdown table per severity band.

    Empty input is a clean empty briefing, never an error and never
    a fabricated all-clear: the closing note says exactly what was
    and was not checked, same discipline as the digest.
    """
    rows = built.get("warnings") or []
    generated = built.get("generated_at", "unknown date")
    window = built.get("window_days", DEFAULT_WINDOW_DAYS)
    lines = [
        "# OpenPulse warning deadlines",
        "",
        f"Generated {generated}. Window: {window} days either side of today"
        " (upcoming and newly-effective).",
        "",
    ]
    if not rows:
        lines.append(f"No warning deadlines within the {window}-day window.")
        lines.append("")
        lines.append(
            "This says nothing about whether a dependency is affected for"
            " other reasons - run `openpulse check` for full verdicts."
        )
        lines.append("")
        return "\n".join(lines)
    for severity in SEVERITY_ORDER:
        band = [w for w in rows if w["severity"] == severity]
        if not band:
            continue
        label = {
            SEVERITY_OVERDUE: "passed deadlines",
            SEVERITY_CRITICAL: "effective within 7 days",
            SEVERITY_HIGH: "effective within 30 days",
            SEVERITY_MEDIUM: "effective within 90 days",
            SEVERITY_LOW: "effective beyond 90 days",
        }[severity]
        lines.append(f"## {severity} - {label} ({len(band)})")
        lines.append("")
        lines.append("| Project | Ref | Change | Effective | In | Lead time | Action |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for w in band:
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} |".format(
                    w["project"],
                    w["ref"],
                    w["event_type"],
                    w["effective_date"],
                    _days_note(w["days_until_effective"]),
                    _lead_note(w),
                    w["recommended_action"],
                )
            )
        lines.append("")
    counts = ", ".join(
        "{} {}".format(sum(1 for w in rows if w["severity"] == s), s.lower())
        for s in SEVERITY_ORDER
        if any(w["severity"] == s for w in rows)
    )
    lines.append(f"{len(rows)} warning(s): {counts}.")
    lines.append(
        "Lead times come from the detection ledger; no claim is made"
        " without a first-detection record."
    )
    lines.append("")
    return "\n".join(lines)
