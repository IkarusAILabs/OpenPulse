"""Persistent alert delivery state for scheduled webhooks (v0.11.0 W1, C1, #78).

A scheduled ``openpulse check --webhook`` used to post the whole digest on
every run: the same alerts again and again, and a failed post was simply
lost. This module gives each alert a stable identity and remembers what
happened to it:

- **Alert identity.** One alert per affected cause of a verdict, keyed by
  ``sha256`` over the dependency, the event id, the relationship, the
  impact and a fingerprint of the event's content. A revised event or a
  raised impact is a new alert; the same finding on the next run is not.
  A repository whose inspection is not COMPLETE is an alert too, so
  deduplication can never turn an unread repository into silence.
- **Delivered once.** A run posts only alerts not yet delivered, and
  nothing at all when there are none.
- **Retry, then dead letter.** A failed post is tried again once in the
  same run, then left ``pending``. Later runs retry it after an
  exponential backoff (``RETRY_BASE`` doubling, capped at ``RETRY_CAP``).
  After ``MAX_ATTEMPTS`` failed runs the alert is ``dead_letter``: never
  sent again, kept with its last error for an operator to read.

State lives in ``<root>/alerts.json``, written atomically (temp file +
``os.replace``) under an OS advisory lock held across load, post and
save, so two runs at once cannot both send the same alert
(``core.filelock``, as the detection ledger). Errors are stored already
redacted by ``core.notify``; the webhook URL is never stored.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.filelock import exclusive_lock

STATE_FILE = "alerts.json"
LOCK_FILE = ".delivery-lock"
#: Failed runs before an alert is dead-lettered.
MAX_ATTEMPTS = 5
#: Backoff between failed runs: RETRY_BASE, doubling, at most RETRY_CAP.
RETRY_BASE = timedelta(minutes=5)
RETRY_CAP = timedelta(hours=6)
#: Pause before the one in-run retry.
IN_RUN_RETRY_SECONDS = 2.0
_LOCK_WAIT_SECONDS = 30.0

DELIVERED, PENDING, DEAD_LETTER = "delivered", "pending", "dead_letter"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat()


def _digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


#: Event fields stamped when the event is loaded, not part of its content
#: (``OSSEvent.created_at`` defaults to the load time when a file omits it).
_LOAD_TIME_FIELDS = ("created_at",)


def event_fingerprint(event: Any) -> str:
    """Content fingerprint of an event: a revised event fires again."""
    dumped = event.model_dump(mode="json") if hasattr(event, "model_dump") else dict(event)
    return _digest({k: v for k, v in dumped.items() if k not in _LOAD_TIME_FIELDS})


def collect_alerts(
    results: list[Any],
    events: list[Any],
    coverage: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Alerts for one run, in a stable order, each with its ``id``.

    ``coverage`` is the run-level repository inspection block; anything
    but COMPLETE (or no repository at all, ``None``) is an alert.
    """
    fingerprints = {str(getattr(e, "id", "")): event_fingerprint(e) for e in events}
    alerts: dict[str, dict[str, Any]] = {}
    status = str((coverage or {}).get("status") or "COMPLETE")
    if status not in ("COMPLETE", "NOT_APPLICABLE"):
        reasons = [str(r) for r in (coverage or {}).get("reasons") or []]
        key = {"kind": "coverage", "status": status, "reasons": reasons}
        alert_id = _digest(key)
        alerts[alert_id] = {"id": alert_id, **key}
    for result in results:
        if not getattr(result, "affected", False):
            continue
        dependency = str(getattr(result, "dependency", "?"))
        for cause in getattr(result, "verdicts", None) or []:
            if not cause.get("affected"):
                continue
            event_id = str(cause.get("event_id") or "")
            key = {
                "kind": "finding",
                "dependency": dependency,
                "event_id": event_id,
                "relationship": str(cause.get("relationship") or ""),
                "impact": str(cause.get("impact") or ""),
                "event": fingerprints.get(event_id, ""),
            }
            alert_id = _digest(key)
            alerts[alert_id] = {
                "id": alert_id,
                **{k: v for k, v in key.items() if k != "event"},
                "reason": str(cause.get("reason") or getattr(result, "reason", "")),
            }
    return sorted(alerts.values(), key=lambda a: (a["kind"], a.get("dependency", ""), a["id"]))


def render_alerts(alerts: list[dict[str, Any]], coverage_note: str | None = None) -> str:
    """Markdown body for the alerts posted in one run."""
    findings = [a for a in alerts if a["kind"] == "finding"]
    lines = ["# OpenPulse new alerts", ""]
    if coverage_note and any(a["kind"] == "coverage" for a in alerts):
        lines += [f"> {coverage_note}", ""]
    if findings:
        lines.append(f"{len(findings)} new alert(s)")
        lines.append("")
        for alert in findings:
            lines.append(
                f"- 🚨 **{alert['dependency']}** [{alert['relationship']}] {alert['impact']}"
                f" · {alert['event_id']} — {alert['reason']}"
            )
    return "\n".join(lines).rstrip()


def _retry_due(entry: dict[str, Any], now: datetime) -> bool:
    last = entry.get("last_attempt_at")
    if not last:
        return True
    try:
        moment = datetime.fromisoformat(str(last))
    except ValueError:
        return True
    failed = max(int(entry.get("attempts") or 1), 1)
    wait = min(RETRY_BASE * (2 ** (failed - 1)), RETRY_CAP)
    return now >= moment + wait


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def load_state(root: str | Path) -> dict[str, Any]:
    """``{"alerts": {id: entry}}``; a missing or unreadable file is empty.

    An unreadable file is moved aside (``alerts.json.corrupt-<time>``)
    by ``deliver`` before it writes, so a corrupt state is kept as
    evidence, never silently overwritten.
    """
    path = Path(root) / STATE_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"alerts": {}}
    except (OSError, ValueError):
        return {"alerts": {}, "corrupt": True}
    if not isinstance(data, dict) or not isinstance(data.get("alerts"), dict):
        return {"alerts": {}, "corrupt": True}
    return data


@contextlib.contextmanager
def _locked(root: Path, wait_seconds: float) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(root / LOCK_FILE, wait_seconds, "delivery"):
        yield


def deliver(
    root: str | Path,
    alerts: list[dict[str, Any]],
    post: Callable[[str], dict[str, Any]],
    render: Callable[[list[dict[str, Any]]], str],
    *,
    now: Callable[[], datetime] = _now,
    sleep: Callable[[float], None] | None = None,
    wait_seconds: float = _LOCK_WAIT_SECONDS,
) -> dict[str, Any]:
    """Post the alerts not yet delivered; record the outcome. Never raises on delivery.

    ``post(markdown)`` returns ``core.notify.post_digest``'s ``{ok,
    status_code, error}``. Returns a report: ``sent`` (alerts in the
    posted body), ``delivered`` (bool), ``already_delivered``,
    ``waiting`` (pending, backoff not yet over), ``dead_lettered`` (this
    run), ``dead_letter`` (all), ``error`` and ``status_code``.
    Raises TimeoutError when another run holds the lock.
    """
    import time

    root = Path(root)
    pause = sleep if sleep is not None else time.sleep
    with _locked(root, wait_seconds):
        state = load_state(root)
        path = root / STATE_FILE
        if state.pop("corrupt", False) and path.exists():
            stamp = now().strftime("%Y%m%dT%H%M%SZ")
            os.replace(path, root / f"{STATE_FILE}.corrupt-{stamp}")
        entries: dict[str, dict[str, Any]] = state["alerts"]
        moment = now()
        due, already, waiting = [], 0, 0
        for alert in alerts:
            entry = entries.get(alert["id"])
            if entry is None:
                due.append(alert)
            elif entry.get("status") == DELIVERED:
                already += 1
            elif entry.get("status") == PENDING and _retry_due(entry, moment):
                due.append(alert)
            elif entry.get("status") == PENDING:
                waiting += 1
        report: dict[str, Any] = {
            "sent": 0,
            "delivered": False,
            "already_delivered": already,
            "waiting": waiting,
            "dead_lettered": 0,
            "error": None,
            "status_code": None,
        }
        if due:
            body = render(due)
            outcome = post(body)
            if not outcome.get("ok"):
                pause(IN_RUN_RETRY_SECONDS)
                outcome = post(body)
            report.update(
                sent=len(due),
                delivered=bool(outcome.get("ok")),
                error=outcome.get("error"),
                status_code=outcome.get("status_code"),
            )
            stamp = _iso(now())
            for alert in due:
                entry = entries.setdefault(
                    alert["id"],
                    {
                        **{k: v for k, v in alert.items() if k != "id"},
                        "first_seen_at": stamp,
                        "attempts": 0,
                    },
                )
                entry["attempts"] = int(entry.get("attempts") or 0) + 1
                entry["last_attempt_at"] = stamp
                if outcome.get("ok"):
                    entry.update(status=DELIVERED, delivered_at=stamp, last_error=None)
                elif entry["attempts"] >= MAX_ATTEMPTS:
                    entry.update(
                        status=DEAD_LETTER, dead_lettered_at=stamp, last_error=outcome.get("error")
                    )
                    report["dead_lettered"] += 1
                else:
                    entry.update(status=PENDING, last_error=outcome.get("error"))
            _write_atomic(path, {"alerts": entries})
        report["dead_letter"] = sum(1 for e in entries.values() if e.get("status") == DEAD_LETTER)
        return report


__all__ = [
    "DEAD_LETTER",
    "DELIVERED",
    "MAX_ATTEMPTS",
    "PENDING",
    "collect_alerts",
    "deliver",
    "event_fingerprint",
    "load_state",
    "render_alerts",
]
