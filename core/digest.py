"""Alert digest - the first M6 Early Warning surface (issue #63).

The digest answers the commercial question "What is changing in
MY software?" from two durable stores the check command already
maintains: the detection ledger (first trustworthy detections,
core.detections.ledger) and the dependency inputs a customer just
checked (watchlist/SBOM/lockfile/images/manifests). It is a
read-only join over the SAME identity derivation the check writer
uses (durable_fact_from_cause), so a fact can never be recorded
under one identity and surfaced under another.

Evidence-first rules this module inherits, not reinvents:

- Customer evidence is required: an entry exists only for a
  dependency the caller actually declared, with an impact-asserting
  verdict. Public intelligence never implies customer impact.
- Lead time comes from the ledger (first_seen) and the event's
  evidence-declared effective date, via core.leadtime - never
  estimated, never "today". Unknown first detection means the
  entry states that, and no lead-time claim is made.
- Effective dates come from event evidences ONLY (the same
  derivation the evidence contract uses). An affected dependency
  whose event declares no effective date stays in the check
  output but has no digest deadline to count down to.
- The window is symmetric around today: a change effective within
  N days - upcoming OR newly-effective - is in scope. A weekly
  digest must not drop a change the day it becomes effective:
  that is the moment the customer most needs to hear about it, and
  an overdue deadline is the most actionable line of all.
- A busy ledger lock degrades to "no first-detection claim" for
  that entry, never to an exception: the digest is a briefing a
  cron schedule depends on rendering.

No new storage model: the ledger stays the ONLY durable state, and
the digest is computed per run from ledger + inputs. Nothing in
this module writes.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from core.detections import ledger
from core.leadtime import event_effective_day, lead_time_days, parse_day
from core.risk.check import DependencyVerdict, durable_fact_from_cause
from core.schema.models import OSSEvent

DEFAULT_WINDOW_DAYS = 90

#: Action vocabulary mirrors analyzers.report_analyst.ADVICE, but
#: stays local so the digest never imports rendering logic to make
#: a decision-support claim. Lines say what the evidence supports.
ACTION_ADVICE = {
    "CRITICAL": "Act now: plan the migration before the effective date.",
    "ACTION": "Schedule the upgrade before the effective date.",
    "REVIEW": "Review in the next planning cycle; no confirmed deadline yet.",
    "WATCH": "Watch: track the project for changes.",
    "INFORMATIONAL": "Informational: no action required.",
}


def _advice(impact: str) -> str:
    return ACTION_ADVICE.get(str(impact).upper(), "Review the evidence and decide.")


def _event_by_id(events: list[OSSEvent]) -> dict[str, OSSEvent]:
    return {e.id: e for e in events or []}


def _first_seen_day(fact: dict[str, Any], ledger_root: str) -> date | None:
    """Ledger lookup for one fact, degraded to None - never an exception.

    Reads are lock-free (atomic file reads), so a busy project lock
    during a concurrent check run cannot break the digest; a missing
    or tampered entry also means None: no claim. This function is
    the ONLY place the digest touches durable state.
    """
    try:
        seen = ledger.first_seen(
            fact["project"],
            fact["finding_class"],
            fact["subject"],
            scope=fact["scope"],
            root=ledger_root,
        )
    except (OSError, TimeoutError):
        return None
    return parse_day(seen) if seen else None


def build_digest(
    verdicts: list[DependencyVerdict],
    events: list[OSSEvent],
    ledger_root: str | None = None,
    today: date | None = None,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> dict[str, Any]:
    """Join check verdicts + events + ledger into one briefing.

    Pure function except the (read-only, degrading) ledger lookups.
    Returns {"entries": [...], "generated_at": today.isoformat()} -
    dates as ISO strings, lead_time_days int or None, days_until_effective
    negative for already-effective changes. Ranking is deterministic:
    effective date ascending (most overdue first, then soonest
    deadline), then dependency label, then event id.

    Security causes are excluded on purpose: they carry CVE ids, not
    event ids, so there is no effective-date evidence to join on. A
    CVE fix is available the moment it is published; there is no
    upstream deadline to count down to. They stay in the check
    output with their own severity.
    """
    today = today or date.today()
    events_by_id = _event_by_id(events)
    entries: list[dict[str, Any]] = []
    seen_entry_keys: set[tuple[str, str, str]] = set()
    for verdict in verdicts:
        if not verdict.affected:
            continue  # customer evidence required, always
        for cause in verdict.verdicts:
            if not cause.get("affected"):
                continue
            event = events_by_id.get(str(cause.get("event_id") or ""))
            if event is None:
                continue
            effective_day = event_effective_day(event)
            if effective_day is None:
                continue  # no declared deadline -> nothing to count down to
            until = (effective_day - today).days
            if not -window_days <= until <= window_days:
                # Outside the window on either side. Newly-effective
                # changes stay in until they age past the lookback:
                # the issue defines the digest as "upcoming and
                # newly-effective", and a weekly digest that dropped
                # a change the day it became effective would lose the
                # one line the customer most needs. Older history is
                # the monthly report's to narrate.
                continue
            fact = durable_fact_from_cause(cause, events_by_id)
            first_detected = _first_seen_day(fact, ledger_root) if fact and ledger_root else None
            lead_time = (
                lead_time_days(first_detected, effective_day)
                if first_detected is not None
                else None
            )
            entry_key = (
                str(verdict.dependency),
                str(event.id),
                str(cause.get("relationship") or ""),
            )
            if entry_key in seen_entry_keys:
                continue
            seen_entry_keys.add(entry_key)
            entries.append(
                {
                    "dependency": str(verdict.dependency),
                    "project": str(cause.get("project") or event.project_slug),
                    "event_id": str(event.id),
                    "event_type": str(event.event_type.value),
                    "title": str(event.title),
                    "impact": str(event.impact.value),
                    "relationship": str(cause.get("relationship") or ""),
                    "effective_date": str(effective_day),
                    "days_until_effective": (effective_day - today).days,
                    "first_detected": str(first_detected) if first_detected else None,
                    "lead_time_days": lead_time,
                    "advice": _advice(event.impact.value),
                }
            )
    entries.sort(
        key=lambda e: (
            1 if e["effective_date"] is None else 0,
            str(e["effective_date"]),
            str(e["dependency"]),
            str(e["event_id"]),
        )
    )
    return {"generated_at": today.isoformat(), "entries": entries}


def _detail(e: dict[str, Any]) -> str:
    """One entry - the evidence line under the headline.

    lead_time_days is never invented: a missing first detection
    renders as an explicit note, matching the ledger's degradation
    semantics (no record -> no claim).
    """
    days = e["days_until_effective"]
    if days is not None:
        if days < 0:
            days_note = f"effective {abs(days)} days ago - OVERDUE"
        elif days == 0:
            days_note = "effective today"
        else:
            days_note = f"effective in {days} days"
    else:
        days_note = "no declared deadline"
    if e["first_detected"]:
        if e["lead_time_days"] is not None:
            lead = f"lead time {e['lead_time_days']} days (first detected {e['first_detected']})"
        else:
            lead = "detection recorded but lead time not computable"
    else:
        lead = "no first-detection record in the ledger"
    return (
        f"  {e['impact']} [{e['relationship']}] {e['event_type']}"
        f" - effective {e['effective_date']} | {days_note} | {lead}"
    )


def render_digest_md(digest: dict[str, Any]) -> str:
    """Digest -> actionable markdown briefing (decision support).

    Two urgency bands (Act this cycle / Watch), one headline plus
    evidence line per entry. Overdue entries (already effective
    within the lookback) sort first in each band and render with
    the days-past count. Empty digest -> a clean "no upcoming
    deadlines" message, not an error, and never a fabricated
    "all clear" claim about dependencies outside the window.
    """
    entries = digest.get("entries") or []
    generated = digest.get("generated_at", "unknown date")
    lines = [
        "# OpenPulse alert digest",
        "",
        f"Generated {generated} from the detection ledger and your inputs.",
        "",
    ]
    if not entries:
        lines.append("Nothing upcoming or newly-effective within the warning window.")
        lines.append("")
        lines.append(
            "This says nothing about whether a dependency is affected for"
            " other reasons - run `openpulse check` for the full verdict."
        )
        lines.append("")
        return "\n".join(lines)
    action = [e for e in entries if e["impact"] in ("ACTION", "CRITICAL")]
    watch = [e for e in entries if e["impact"] not in ("ACTION", "CRITICAL")]
    if action:
        lines.append("## Act this cycle")
        lines.append("")
        for e in action:
            lines.append(f"- **{e['dependency']}** - {e['title']}")
            lines.append(_detail(e))
        lines.append("")
    if watch:
        lines.append("## Watch (no confirmed deadline)")
        lines.append("")
        for e in watch:
            lines.append(f"- **{e['dependency']}** - {e['title']}")
            lines.append(_detail(e))
        lines.append("")
    lines.append(
        f"{len(action)} action / {len(watch)} watch entries."
        " Lead times come from your detection ledger;"
    )
    lines.append("no lead-time claim is made without a first-detection record.")
    lines.append("")
    return "\n".join(lines)
