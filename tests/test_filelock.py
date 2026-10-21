"""Shared lock-file semantics (core/filelock.py) - review finding M6."""

import os
import threading
import time

import pytest

from core import filelock
from core.filelock import exclusive_lock


def _make_stale(lock, token="dead-holder"):
    lock.write_text(token, encoding="ascii")
    old = time.time() - 3600
    os.utime(lock, (old, old))


def test_stale_lock_is_reclaimed(tmp_path):
    lock = tmp_path / ".lock"
    _make_stale(lock)
    with exclusive_lock(lock, wait_seconds=2, stale_seconds=120, label="t"):
        assert lock.read_text(encoding="ascii") != "dead-holder"
    assert not lock.exists()


def test_unreclaimable_stale_lock_times_out_instead_of_spinning(tmp_path, monkeypatch):
    """Regression: a failed stale unlink `continue`d past the deadline check
    and spun forever (read-only lock, Windows handle still open)."""
    lock = tmp_path / ".lock"
    _make_stale(lock)

    def pinned(*_args, **_kwargs):
        raise PermissionError("pinned")

    monkeypatch.setattr(filelock.os, "rename", pinned)
    start = time.monotonic()
    with pytest.raises(TimeoutError, match="t lock busy"):
        with exclusive_lock(lock, wait_seconds=0.3, stale_seconds=120, label="t"):
            pass
    assert time.monotonic() - start < 5


def test_release_never_deletes_a_successors_lock(tmp_path):
    lock = tmp_path / ".lock"
    with exclusive_lock(lock, wait_seconds=1, stale_seconds=120, label="t"):
        lock.write_text("successor-token", encoding="ascii")
    assert lock.read_text(encoding="ascii") == "successor-token"


def test_racing_reclaimers_never_both_hold_the_lock(tmp_path):
    lock = tmp_path / ".lock"
    _make_stale(lock)
    inside = 0
    peak = 0
    guard = threading.Lock()
    start = threading.Barrier(6)
    errors = []

    def worker():
        nonlocal inside, peak
        start.wait()
        try:
            with exclusive_lock(lock, wait_seconds=10, stale_seconds=120, label="t"):
                with guard:
                    inside += 1
                    peak = max(peak, inside)
                time.sleep(0.02)
                with guard:
                    inside -= 1
        except Exception as exc:  # surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert errors == []
    assert peak == 1
    assert not lock.exists()
    assert not list(tmp_path.glob(".lock.stale-*"))


def test_both_stores_use_the_shared_lock():
    from core.detections import ledger
    from core.observations import store

    assert store.exclusive_lock is exclusive_lock
    assert ledger.exclusive_lock is exclusive_lock
