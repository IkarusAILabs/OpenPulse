"""Lock waits read their module constant at call time.

A default argument `wait_seconds=_LOCK_WAIT_SECONDS` is bound when the
function is defined, so patching the constant changed nothing: a test that
set it to 0.05 s still waited the full 30 s (a third of the CI suite).
"""

from __future__ import annotations

import time

import pytest

from core.filelock import exclusive_lock


def _held(path):
    return exclusive_lock(path, 1.0, "test")


def _assert_quick(call):
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        call()
    assert time.monotonic() - started < 5


def test_ledger_lock_follows_the_constant(tmp_path, monkeypatch):
    from core.detections import ledger

    monkeypatch.setattr(ledger, "_LOCK_WAIT_SECONDS", 0.05)
    with ledger.ledger_lock(tmp_path, "django", wait_seconds=1):

        def again():
            with ledger.ledger_lock(tmp_path, "django"):
                pass

        _assert_quick(again)


def test_observation_lock_follows_the_constant(tmp_path, monkeypatch):
    from core.observations import store

    monkeypatch.setattr(store, "_LOCK_WAIT_SECONDS", 0.05)
    args = (tmp_path, "docker.io", "library", "redis")
    with store.repo_lock(*args, wait_seconds=1):

        def again():
            with store.repo_lock(*args):
                pass

        _assert_quick(again)


def test_delivery_lock_follows_the_constant(tmp_path, monkeypatch):
    from core import delivery

    monkeypatch.setattr(delivery, "_LOCK_WAIT_SECONDS", 0.05)
    with _held(tmp_path / delivery.LOCK_FILE):
        _assert_quick(lambda: delivery.deliver(tmp_path, [], lambda _b: {}, lambda _a: ""))
