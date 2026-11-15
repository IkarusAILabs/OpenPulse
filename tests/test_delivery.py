"""Persistent alert delivery state (v0.11.0 W1, C1, #78)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from core import delivery
from core.delivery import (
    DEAD_LETTER,
    DELIVERED,
    MAX_ATTEMPTS,
    PENDING,
    collect_alerts,
    deliver,
    load_state,
    render_alerts,
)
from core.risk.check import check_dependency
from core.schema.models import OSSEvent

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def django_event():
    with open("data/fixtures/django-eol/event.json", encoding="utf-8") as f:
        return OSSEvent(**json.load(f))


@pytest.fixture(scope="module")
def affected(django_event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    result = check_dependency(dep, [django_event])
    assert result.affected
    return result


class Poster:
    """Stands in for core.notify.post_digest; scripted outcomes, records bodies."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes) or [True]
        self.bodies: list[str] = []

    def __call__(self, markdown):
        self.bodies.append(markdown)
        ok = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if ok:
            return {"ok": True, "status_code": 200, "error": None}
        return {"ok": False, "status_code": 503, "error": "webhook returned HTTP 503 from hooks"}


def _deliver(root, alerts, poster, at=T0):
    return deliver(root, alerts, poster, render_alerts, now=lambda: at, sleep=lambda _s: None)


# ---------------------------------------------------------------------------
# Alert identity
# ---------------------------------------------------------------------------


def test_alert_ids_are_stable_across_runs(affected, django_event):
    first = collect_alerts([affected], [django_event])
    again = collect_alerts([affected], [django_event])
    assert first and [a["id"] for a in first] == [a["id"] for a in again]
    assert all(a["kind"] == "finding" and a["dependency"] == affected.dependency for a in first)


def test_a_revised_event_or_raised_impact_is_a_new_alert(affected, django_event):
    base = {a["id"] for a in collect_alerts([affected], [django_event])}
    revised = django_event.model_copy(update={"summary": django_event.summary + " (revised)"})
    assert base.isdisjoint(a["id"] for a in collect_alerts([affected], [revised]))
    raised = affected.model_copy(deep=True)
    for cause in raised.verdicts:
        cause["impact"] = "CRITICAL" if cause.get("impact") != "CRITICAL" else "ACTION"
    assert base.isdisjoint(a["id"] for a in collect_alerts([raised], [django_event]))


def test_unaffected_verdicts_raise_no_alert(django_event):
    dep = {"kind": "package", "package": "flask", "ecosystem": "PyPI", "version": "3.0"}
    assert collect_alerts([check_dependency(dep, [django_event])], [django_event]) == []


@pytest.mark.parametrize(
    ("status", "alerts"), [("FAILED", 1), ("PARTIAL", 1), ("COMPLETE", 0), ("NOT_APPLICABLE", 0)]
)
def test_an_unread_repository_is_an_alert(status, alerts):
    found = collect_alerts([], [], {"status": status, "reasons": ["tree truncated"]})
    assert len(found) == alerts
    assert all(a["kind"] == "coverage" and a["status"] == status for a in found)


# ---------------------------------------------------------------------------
# Delivered once
# ---------------------------------------------------------------------------


def test_each_alert_is_posted_once(tmp_path, affected, django_event):
    alerts = collect_alerts([affected], [django_event])
    poster = Poster(True)
    first = _deliver(tmp_path, alerts, poster)
    assert first["sent"] == len(alerts) and first["delivered"]
    second = _deliver(tmp_path, alerts, poster, T0 + timedelta(hours=1))
    assert second["sent"] == 0 and second["already_delivered"] == len(alerts)
    assert len(poster.bodies) == 1
    entries = load_state(tmp_path)["alerts"]
    assert {e["status"] for e in entries.values()} == {DELIVERED}


def test_only_new_alerts_are_posted(tmp_path, affected, django_event):
    old = collect_alerts([affected], [django_event])
    _deliver(tmp_path, old, Poster(True))
    new = collect_alerts([], [], {"status": "FAILED", "reasons": ["repository not enumerable"]})
    poster = Poster(True)
    report = _deliver(tmp_path, old + new, poster)
    assert report["sent"] == 1 and report["already_delivered"] == len(old)
    assert affected.dependency not in poster.bodies[0]
    assert "inspection" in poster.bodies[0].lower() or poster.bodies[0].startswith("# ")


# ---------------------------------------------------------------------------
# Retry, backoff, dead letter
# ---------------------------------------------------------------------------


def test_a_failed_post_is_retried_once_in_run_then_left_pending(tmp_path, affected, django_event):
    alerts = collect_alerts([affected], [django_event])
    poster, pauses = Poster(False), []
    report = deliver(tmp_path, alerts, poster, render_alerts, now=lambda: T0, sleep=pauses.append)
    assert len(poster.bodies) == 2 and pauses == [delivery.IN_RUN_RETRY_SECONDS]
    assert report["sent"] == len(alerts) and not report["delivered"]
    entry = next(iter(load_state(tmp_path)["alerts"].values()))
    assert entry["status"] == PENDING and entry["attempts"] == 1
    assert entry["last_error"] == "webhook returned HTTP 503 from hooks"


def test_a_transient_failure_recovers_within_the_run(tmp_path, affected, django_event):
    alerts = collect_alerts([affected], [django_event])
    report = _deliver(tmp_path, alerts, Poster(False, True))
    assert report["delivered"]
    assert {e["status"] for e in load_state(tmp_path)["alerts"].values()} == {DELIVERED}


def test_pending_alerts_wait_for_the_backoff(tmp_path, affected, django_event):
    alerts = collect_alerts([affected], [django_event])
    _deliver(tmp_path, alerts, Poster(False))
    early = _deliver(tmp_path, alerts, Poster(True), T0 + delivery.RETRY_BASE / 2)
    assert early["sent"] == 0 and early["waiting"] == len(alerts)
    later = _deliver(tmp_path, alerts, Poster(True), T0 + delivery.RETRY_BASE)
    assert later["sent"] == len(alerts) and later["delivered"]


def test_repeated_failures_are_dead_lettered_and_never_resent(tmp_path, affected, django_event):
    alerts = collect_alerts([affected], [django_event])
    at = T0
    for run in range(MAX_ATTEMPTS):
        report = _deliver(tmp_path, alerts, Poster(False), at)
        assert report["sent"] == len(alerts), run
        at += delivery.RETRY_CAP
    assert report["dead_lettered"] == len(alerts) and report["dead_letter"] == len(alerts)
    entries = load_state(tmp_path)["alerts"].values()
    assert {e["status"] for e in entries} == {DEAD_LETTER}
    assert all(e["attempts"] == MAX_ATTEMPTS and e["last_error"] for e in entries)
    poster = Poster(True)
    after = _deliver(tmp_path, alerts, poster, at + delivery.RETRY_CAP)
    assert after["sent"] == 0 and poster.bodies == []


def test_backoff_doubles_and_is_capped():
    entry = {"last_attempt_at": T0.isoformat()}
    for failed, wait in ((1, delivery.RETRY_BASE), (2, delivery.RETRY_BASE * 2)):
        entry["attempts"] = failed
        assert not delivery._retry_due(entry, T0 + wait - timedelta(seconds=1))
        assert delivery._retry_due(entry, T0 + wait)
    entry["attempts"] = 30
    assert delivery._retry_due(entry, T0 + delivery.RETRY_CAP)


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


def test_a_corrupt_state_file_is_kept_aside_not_overwritten(tmp_path, affected, django_event):
    (tmp_path / "alerts.json").write_text("{not json", encoding="utf-8")
    report = _deliver(tmp_path, collect_alerts([affected], [django_event]), Poster(True))
    assert report["delivered"]
    kept = list(tmp_path.glob("alerts.json.corrupt-*"))
    assert len(kept) == 1 and kept[0].read_text(encoding="utf-8") == "{not json"


def test_a_concurrent_run_is_refused_not_duplicated(tmp_path, affected, django_event):
    from core.filelock import exclusive_lock

    alerts = collect_alerts([affected], [django_event])
    with exclusive_lock(tmp_path / delivery.LOCK_FILE, 1.0, "test"):
        with pytest.raises(TimeoutError):
            deliver(tmp_path, alerts, Poster(True), render_alerts, wait_seconds=0.2)


# ---------------------------------------------------------------------------
# CLI: check --webhook
# ---------------------------------------------------------------------------


def _check(tmp_path, monkeypatch, *outcomes):
    import core.notify as notify

    poster = Poster(*outcomes)
    monkeypatch.setattr(notify, "post_digest", lambda url, text, **kw: poster(text))
    monkeypatch.setattr(delivery, "IN_RUN_RETRY_SECONDS", 0.0)  # the in-run retry pause
    result = CliRunner().invoke(
        cli,
        [
            "check",
            "--manifest",
            "data/fixtures/manifests/requirements.txt",
            "--event",
            "data/fixtures/django-eol/event.json",
            "--replay",
            "--ledger",
            "",
            "--webhook",
            "https://hooks.example/secret-path",
            "--delivery-state",
            str(tmp_path / "deliveries"),
        ],
    )
    return result, poster


def test_check_webhook_posts_new_alerts_once(tmp_path, monkeypatch):
    first, poster = _check(tmp_path, monkeypatch, True)
    assert first.exit_code == 0, first.output
    assert "posted" in first.output and "new alert(s)" in first.output
    assert poster.bodies and poster.bodies[0].startswith("# OpenPulse new alerts")
    second, poster2 = _check(tmp_path, monkeypatch, True)
    assert second.exit_code == 0, second.output
    assert "no new alerts: nothing posted" in second.output and poster2.bodies == []
    state = (tmp_path / "deliveries" / "alerts.json").read_text(encoding="utf-8")
    assert "secret-path" not in state and "hooks.example" not in state


def test_check_webhook_failure_is_reported_and_never_changes_the_exit(tmp_path, monkeypatch):
    result, _poster = _check(tmp_path, monkeypatch, False)
    assert result.exit_code == 0, result.output
    assert "webhook delivery failed" in result.output
    assert "pending: retried on a later run" in result.output
    entries = json.loads(Path(tmp_path / "deliveries" / "alerts.json").read_text("utf-8"))
    assert {e["status"] for e in entries["alerts"].values()} == {PENDING}


def test_load_time_stamps_do_not_change_the_alert(affected, django_event):
    """Regression: OSSEvent.created_at defaults to the load time, which made
    every scheduled run look like a revised event and re-post every alert."""
    reloaded = django_event.model_copy(
        update={"created_at": django_event.created_at + timedelta(hours=1)}
    )
    first = [a["id"] for a in collect_alerts([affected], [django_event])]
    assert first == [a["id"] for a in collect_alerts([affected], [reloaded])]
