"""Shared OS-lock semantics (core/filelock.py) - review finding M6."""

import subprocess
import sys
import threading
import time

import pytest

from core.filelock import exclusive_lock


def test_busy_lock_times_out_instead_of_spinning(tmp_path):
    """Regression: the old lock-file loop could spin forever on a stale
    file it could not remove; a busy lock must end in TimeoutError."""
    lock = tmp_path / ".lock"
    with exclusive_lock(lock, wait_seconds=1, label="t"):
        start = time.monotonic()
        with pytest.raises(TimeoutError, match="t lock busy"):
            with exclusive_lock(lock, wait_seconds=0.2, label="t"):
                pass
        assert time.monotonic() - start < 5


def test_released_lock_is_immediately_reacquirable(tmp_path):
    lock = tmp_path / ".lock"
    with exclusive_lock(lock, wait_seconds=1, label="t"):
        pass
    with exclusive_lock(lock, wait_seconds=0.1, label="t"):
        pass
    # The marker file persists by design: unlinking it would reopen the race.
    assert lock.exists()


def test_racing_threads_never_both_hold_the_lock(tmp_path):
    """Regression: two waiters reclaiming one stale lock could both acquire
    (seen on the Linux CI runner with the rename-based reclaim)."""
    lock = tmp_path / ".lock"
    inside = 0
    peak = 0
    guard = threading.Lock()
    start = threading.Barrier(8)
    errors = []

    def worker():
        nonlocal inside, peak
        start.wait()
        try:
            for _ in range(25):
                with exclusive_lock(lock, wait_seconds=30, label="t"):
                    with guard:
                        inside += 1
                        peak = max(peak, inside)
                    time.sleep(0.001)
                    with guard:
                        inside -= 1
        except Exception as exc:  # surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert errors == []
    assert peak == 1


_HOLDER = """
import sys, time
from pathlib import Path
from core.filelock import exclusive_lock
with exclusive_lock(Path(sys.argv[1]), wait_seconds=5, label="child"):
    print("held", flush=True)
    time.sleep(60)
"""


def test_lock_held_by_a_crashed_process_is_released_by_the_os(tmp_path):
    """No staleness heuristic: a killed holder's lock is freed by the OS."""
    lock = tmp_path / ".lock"
    child = subprocess.Popen(
        [sys.executable, "-c", _HOLDER, str(lock)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout.readline().strip() == "held"
        with pytest.raises(TimeoutError):
            with exclusive_lock(lock, wait_seconds=0.2, label="t"):
                pass
        child.kill()
        child.wait(timeout=10)
        with exclusive_lock(lock, wait_seconds=5, label="t"):
            pass
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


def test_both_stores_use_the_shared_lock():
    from core.detections import ledger
    from core.observations import store

    assert store.exclusive_lock is exclusive_lock
    assert ledger.exclusive_lock is exclusive_lock
