"""Exclusive locks for the local-first stores (observations, ledger).

One implementation for both stores (they previously carried copies),
built on OS advisory locks - ``fcntl.flock`` on POSIX, ``msvcrt.locking``
on Windows - held on a persistent lock file:

- the OS releases the lock when its holder exits or crashes, so there is
  no staleness heuristic and no reclaim race. The earlier lock-file
  scheme (O_CREAT|O_EXCL plus age-based reclaim) let two waiters both
  acquire, and could spin forever when a stale file could not be removed;
- ``flock`` locks belong to the open file description and Windows region
  locks to the handle, so threads that each open the file exclude one
  another as well as other processes;
- the lock file is never unlinked: deleting a file other processes may be
  about to lock would reintroduce the race. It is an empty marker beside
  the data it protects;
- acquisition polls a non-blocking lock until ``wait_seconds`` elapses,
  then raises TimeoutError. Callers record it as an error and never
  proceed unlocked.
"""

from __future__ import annotations

import contextlib
import os
import time
from collections.abc import Iterator
from pathlib import Path

_POLL_SECONDS = 0.02

if os.name == "nt":  # pragma: no cover - exercised on the Windows CI runner
    import msvcrt

    def _try_lock(fd: int) -> bool:
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_lock(fd: int) -> bool:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


@contextlib.contextmanager
def exclusive_lock(lock: Path, wait_seconds: float, label: str) -> Iterator[None]:
    """Hold ``lock`` exclusively; raise TimeoutError(``label``) when busy."""
    deadline = time.monotonic() + wait_seconds
    fd = os.open(str(lock), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        while not _try_lock(fd):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{label} lock busy: {lock}")
            time.sleep(_POLL_SECONDS)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                _unlock(fd)
    finally:
        os.close(fd)
