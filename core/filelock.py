"""Exclusive lock files for the local-first stores (observations, ledger).

One implementation for both stores (they previously carried copies):

- acquisition is atomic ``O_CREAT|O_EXCL``; the holder writes a unique
  owner token into the file;
- a lock older than ``stale_seconds`` is reclaimed by atomically
  *renaming* it aside, so of two waiters racing the same stale lock
  only one wins - the loser sees the rename fail and keeps waiting.
  If the renamed file turns out not to be the stale one we saw (its
  token changed: a live holder replaced it in between), it is linked
  back in place;
- the deadline is checked on every iteration, so a lock that cannot be
  reclaimed (read-only file, Windows handle still open) ends in
  TimeoutError instead of a busy loop;
- release removes the file only while it still carries our token, so
  a holder never deletes a successor's lock.

Callers record TimeoutError as an error and never proceed unlocked.
"""

from __future__ import annotations

import contextlib
import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

_POLL_SECONDS = 0.05


def _read_token(path: Path) -> str | None:
    try:
        return path.read_text(encoding="ascii", errors="replace")
    except OSError:
        return None


def _try_reclaim(lock: Path, stale_seconds: float) -> None:
    """Move a stale lock aside; restore it if it was not the stale one.

    Only ``stat`` a live lock, never open it: on Windows an open handle
    blocks the holder's unlink, which would leave the lock behind.
    """
    try:
        age = time.time() - lock.stat().st_mtime
    except OSError:
        return
    if age <= stale_seconds:
        return
    seen = _read_token(lock)
    aside = lock.with_name(f"{lock.name}.stale-{uuid.uuid4().hex}")
    try:
        os.rename(lock, aside)
    except OSError:
        return  # another waiter won the rename, or the file is pinned
    if _read_token(aside) != seen:
        # A live holder replaced the stale lock between our stat and rename.
        with contextlib.suppress(OSError):
            os.link(aside, lock)
    with contextlib.suppress(OSError):
        aside.unlink()


@contextlib.contextmanager
def exclusive_lock(
    lock: Path, wait_seconds: float, stale_seconds: float, label: str
) -> Iterator[None]:
    """Hold ``lock`` exclusively; raise TimeoutError(``label``) when busy."""
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    deadline = time.monotonic() + wait_seconds
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            _try_reclaim(lock, stale_seconds)
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{label} lock busy: {lock}") from None
            time.sleep(_POLL_SECONDS)
    try:
        os.write(fd, token.encode("ascii"))
    finally:
        os.close(fd)
    try:
        yield
    finally:
        _release(lock, token)


def _release(lock: Path, token: str) -> None:
    """Unlink our own lock; retry briefly when Windows reports it busy."""
    for _ in range(40):
        if _read_token(lock) != token:
            return
        try:
            lock.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError:  # a reclaimer's stat/read handle is open
            time.sleep(_POLL_SECONDS / 5)
        except OSError:
            return
