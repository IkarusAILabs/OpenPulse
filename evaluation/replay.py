"""Replay recorded evidence as it was known at a stated time.

An event in the dataset names a fixture and a replay time ``as_of``.
Raw bundles are re-analysed by the production analysts with
``today = as_of``, so the event is re-derived from the recorded
responses, not copied from a stored result. Curated ``event.json``
records are loaded as they are. Either way, evidence acquired after
``as_of`` is dropped (the knowledge cut), and an event with no evidence
left was not known at that time and is not loaded.

This is the simplest mechanism that answers "what did OpenPulse know,
and when": recorded inputs plus a time, replayed through current code.
It does not reconstruct the code that ran at the time; results name the
commit they were produced by.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyzers.change_analyst import analyze  # noqa: E402
from analyzers.lifecycle_events import finding_to_event  # noqa: E402
from core.schema.models import OSSEvent  # noqa: E402

FIXTURES = ROOT / "data" / "fixtures"


def as_of_time(spec: dict[str, Any]) -> datetime:
    """End of the replay day, UTC: evidence fetched that day is known."""
    day = date.fromisoformat(spec["as_of"])
    return datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc)


def _from_raw_bundle(spec: dict[str, Any]) -> OSSEvent:
    raw = json.loads((FIXTURES / spec["fixture"] / "raw_bundle.json").read_text("utf-8"))
    today = date.fromisoformat(spec["as_of"])
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == spec["event_type"]]
    if "versions" in spec:
        findings = [
            f for f in findings if (f.get("scope") or {}).get("versions") == spec["versions"]
        ]
    if len(findings) != 1:
        raise ValueError(f"{spec['fixture']}: expected one finding, got {len(findings)}")
    return finding_to_event(findings[0], spec["project"], today=today)


def _from_event_file(spec: dict[str, Any]) -> OSSEvent:
    data = json.loads((FIXTURES / spec["fixture"] / "event.json").read_text("utf-8"))
    return OSSEvent(**data)


def knowledge_cut(event: OSSEvent, at: datetime) -> OSSEvent | None:
    """The event as known at ``at``: later evidence removed, or None."""
    known = [e for e in event.evidences if e.source.fetched_at <= at]
    if not known:
        return None
    if len(known) == len(event.evidences):
        return event
    return event.model_copy(update={"evidences": known})


def replay(spec: dict[str, Any]) -> OSSEvent | None:
    """One dataset event specification -> the event known at its ``as_of``."""
    if spec["source"] == "raw_bundle":
        event = _from_raw_bundle(spec)
    elif spec["source"] == "event":
        event = _from_event_file(spec)
    else:
        raise ValueError(f"unknown event source {spec['source']!r}")
    return knowledge_cut(event, as_of_time(spec))
