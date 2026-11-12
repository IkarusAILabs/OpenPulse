"""What this run detected for the first time (v0.21.0 item W4).

A scheduled run repeats itself: the same end-of-life date, the same
deprecated package, every day. The detection ledger already remembers when
each durable fact was first recorded (``core.detections.ledger``); this
module records a run's facts and returns the ones the ledger had not seen,
so a run can say what is new since the last one.

A fact's identity is the ledger's (``durable_fact_from_cause``): a
lifecycle event for a release cycle, a CVE, or a registry or repository
change built for one dependency. A fact shared by several dependencies is
recorded once and reported for each of them.

"New" means new to this ledger. On a ledger no run has used (a first run,
or a cache that was evicted), everything is new: ``baseline`` says so, and
nothing is backdated. ``first_seen`` is given only for an entry written
under a history key, since an unkeyed entry proves no date.

A run that detects nothing still leaves a marker (``STARTED_MARKER``) in the
ledger. Without it a ledger with no entries would look unused, and the first
finding of a project that began clean would be taken for a starting point
and never reported as new. The marker carries no key: removing it can only
turn the next run into a starting point, which removing the whole ledger
does as well.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.detections import ledger
from core.risk.check import DependencyVerdict, durable_fact_from_cause
from core.schema.models import OSSEvent

#: Written at the ledger root by every run that recorded, even with no entry.
STARTED_MARKER = "STARTED"


def ledger_is_empty(ledger_root: str | Path) -> bool:
    """True when no run has used the ledger (a first run, or an evicted cache)."""
    base = Path(ledger_root)
    if not base.is_dir():
        return True
    if (base / STARTED_MARKER).is_file():
        return False
    return not any(p.is_file() and not p.name.startswith(".") for p in base.glob("*/*.json"))


def _mark_started(ledger_root: str | Path) -> None:
    """Leave the marker, so a later run is not a first run. Never raises."""
    marker = Path(ledger_root) / STARTED_MARKER
    try:
        if not marker.is_file():
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                '{"note": "a run has used this ledger; later runs report what is new"}\n',
                encoding="utf-8",
            )
    except OSError:
        pass


def _item(verdict: DependencyVerdict, cause: dict[str, Any], event: OSSEvent | None) -> dict:
    urls = [str(e.source.url) for e in event.evidences] if event is not None else []
    return {
        "dependency": str(verdict.dependency),
        "event_id": str(cause.get("event_id") or ""),
        "event_type": str(cause.get("event_type") or ""),
        "title": str(event.title) if event is not None else str(cause.get("event_id") or ""),
        "impact": str(cause.get("impact") or ""),
        "relationship": str(cause.get("relationship") or ""),
        "evidence_urls": urls,
    }


def record_new_detections(
    verdicts: list[DependencyVerdict],
    events: list[OSSEvent],
    *,
    ledger_root: str | Path,
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
) -> dict[str, Any]:
    """Record this run's durable facts; return which were recorded for the first time.

    Returns ``baseline`` (the ledger was empty before this run), ``new``
    (one item per dependency and newly recorded fact, in verdict order),
    ``facts`` (distinct facts this run) and ``new_facts``. Raises
    ``TimeoutError`` when the ledger is locked, like ``record_detection``:
    the caller decides how to degrade.
    """
    events_by_id = {e.id: e for e in events or []}
    baseline = ledger_is_empty(ledger_root)
    grouped: dict[tuple[str, str, str, tuple[str, ...]], dict[str, Any]] = {}
    for verdict in verdicts:
        for cause in verdict.verdicts:
            fact = durable_fact_from_cause(cause, events_by_id)
            if fact is None:
                continue
            key = (
                str(fact["project"]),
                str(fact["finding_class"]),
                str(fact["subject"]),
                tuple(str(v) for v in fact["scope"]),
            )
            group = grouped.setdefault(key, {"fact": fact, "seen": []})
            group["seen"].append((verdict, cause))
    new: list[dict[str, Any]] = []
    new_facts = 0
    for group in grouped.values():
        fact = group["fact"]
        entry = ledger.record_detection(
            fact["project"],
            fact["finding_class"],
            fact["subject"],
            scope=fact["scope"],
            root=ledger_root,
            history_key=history_key,
            previous_keys=previous_keys,
        )
        if not entry.get("recorded_now"):
            continue
        new_facts += 1
        first_seen = str(entry["first_seen"]) if entry.get("history_mac") else None
        listed: set[tuple[str, str]] = set()
        for verdict, cause in group["seen"]:
            mark = (str(verdict.dependency), str(cause.get("event_id") or ""))
            if mark in listed:
                continue
            listed.add(mark)
            item = _item(verdict, cause, events_by_id.get(str(cause.get("event_id") or "")))
            new.append({**item, "finding_class": fact["finding_class"], "first_seen": first_seen})
    _mark_started(ledger_root)
    return {"baseline": baseline, "new": new, "facts": len(grouped), "new_facts": new_facts}


def render_new_md(result: dict[str, Any]) -> str:
    """The "new since the last run" section of a job summary. Upstream text is escaped."""
    from core.sarif import _md

    lines = ["", "### New since the last run", ""]
    if result["baseline"]:
        lines += [
            f"First run with this history: {result['new_facts']} detection(s) recorded as the "
            "starting point. Later runs list only what is new.",
            "",
        ]
        return "\n".join(lines)
    if not result["new"]:
        lines += [f"Nothing new. {result['facts']} detection(s) were already known.", ""]
        return "\n".join(lines)
    lines += [
        f"{result['new_facts']} new of {result['facts']} detection(s).",
        "",
        "| Dependency | Type | What | Impact | Evidence |",
        "|---|---|---|---|---|",
    ]
    for item in result["new"]:
        urls = item["evidence_urls"]
        evidence = " ".join(f"[{i + 1}]({_md(u)})" for i, u in enumerate(urls)) or "-"
        lines.append(
            f"| `{_md(item['dependency'])}` | {_md(item['event_type'])} | {_md(item['title'])} | "
            f"{_md(item['impact'])} | {evidence} |"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = ["ledger_is_empty", "record_new_detections", "render_new_md"]
