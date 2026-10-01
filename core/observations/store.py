"""Local-first observation history — portable JSON, no server or database.

Layout: {root}/{registry}/{namespace}/{repository}/{timestamp}.json
Filenames sort chronologically, so "previous observation" is the
latest file before the current run. The store directory
(`.openpulse/`) is git-ignored and safe to delete: history rebuilds
from new observations (first sighting after a wipe is a baseline).

Concurrency: writers hold a per-repository lock file across
load-diff-save so two simultaneous sweeps cannot fork the hash chain.
Writes are atomic (temp file + os.replace). Corrupt files never raise
here — ``try_load`` returns None and the caller treats an unreadable
predecessor as untrusted history.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

#: How long a lock file may live before it is considered stale (a
#: crashed holder must not block automation forever).
_LOCK_STALE_SECONDS = 120.0
_LOCK_WAIT_SECONDS = 30.0


def _safe(part: str) -> str:
    """Filesystem-safe path segment. Dots alone (`..`) never survive:
    traversal segments collapse to `_`, so hostile registry/namespace
    values stay under the store root."""
    cleaned = "".join(c if c.isalnum() or c in (".", "-", "_") else "_" for c in str(part))
    if cleaned.strip(".") == "":
        return "_"
    return cleaned


def repo_dir(root: str | Path, registry: str, namespace: str, repository: str) -> Path:
    return Path(root) / _safe(registry) / _safe(namespace) / _safe(repository)


def _lock_path(directory: Path) -> Path:
    return directory / ".lock"


#: Tip pointer: {"tip": <latest chain/content hash>}. Rollback
#: tripwire — deleting the newest data file without updating the tip
#: is detected on the next run. The hash chain remains the primary
#: mechanism; the tip only catches partial wipes. A missing or corrupt
#: tip is adopted (pre-upgrade histories), never fatal.
_TIP_FILENAME = "tip.json"


def read_tip(directory: Path) -> dict[str, Any] | None:
    """Tip mapping, or None when absent/unreadable (never raises)."""
    try:
        data = json.loads((directory / _TIP_FILENAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_tip(directory: Path, tip_hash: str) -> None:
    """Atomically record the newest link hash (best effort, never raises)."""
    payload = json.dumps({"tip": tip_hash}, sort_keys=True)
    fd, tmp = tempfile.mkstemp(dir=str(directory), prefix=".tmp-", suffix=".tip")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp, str(directory / _TIP_FILENAME))
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmp)


@contextlib.contextmanager
def repo_lock(
    root: str | Path,
    registry: str,
    namespace: str,
    repository: str,
    wait_seconds: float = _LOCK_WAIT_SECONDS,
) -> Iterator[None]:
    """Per-repository exclusive lock across load-diff-save.

    Lock file creation is atomic (O_CREAT|O_EXCL); stale locks from
    dead processes are reclaimed after ``_LOCK_STALE_SECONDS``.
    Raises TimeoutError when the lock cannot be acquired in time —
    the caller records it as an error, never proceeds unlocked.
    """
    directory = repo_dir(root, registry, namespace, repository)
    directory.mkdir(parents=True, exist_ok=True)
    lock = _lock_path(directory)
    deadline = time.monotonic() + wait_seconds
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except OSError:
                age = 0.0
            if age > _LOCK_STALE_SECONDS:
                with contextlib.suppress(OSError):
                    lock.unlink()
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"observation lock busy: {lock}")
            time.sleep(0.05)
    try:
        os.write(fd, f"{os.getpid()}".encode("ascii"))
        yield
    finally:
        os.close(fd)
        with contextlib.suppress(OSError):
            lock.unlink()


def save_observation(obs: dict[str, Any], root: str | Path = ".openpulse/observations") -> Path:
    """Persist one observation dict atomically. Returns the file path.

    Filenames carry a hash suffix so two observations in the same
    timestamp never collide: concurrent writers under the repo lock
    still produce distinct, linearly-linked files.
    """
    observed = obs.get("observed_at") or datetime.now().isoformat()
    stamp = str(observed).replace(":", "").replace("-", "").replace("+0000", "Z")
    stamp = "".join(c if c.isalnum() or c in ("T", "Z", ".") else "" for c in stamp)
    digest = str(obs.get("chain_hash") or obs.get("content_hash") or "unhashed")
    short = "".join(c for c in digest if c.isalnum())[:12] or "unhashed"
    directory = repo_dir(
        root,
        str(obs.get("registry", "?")),
        str(obs.get("namespace", "?")),
        str(obs.get("repository", "?")),
    )
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stamp}-{short}.json"
    payload = json.dumps(obs, indent=2, sort_keys=True, default=str)
    fd, tmp = tempfile.mkstemp(dir=str(directory), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return path


def list_observations(
    registry: str, namespace: str, repository: str, root: str | Path = ".openpulse/observations"
) -> list[Path]:
    directory = repo_dir(root, registry, namespace, repository)
    if not directory.is_dir():
        return []
    return sorted(
        p
        for p in directory.glob("*.json")
        if p.is_file() and not p.name.startswith(".") and p.name != _TIP_FILENAME
    )


def try_load(path: Path) -> dict[str, Any] | None:
    """One file -> dict, or None when missing/corrupt (never raises)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load_all(
    registry: str, namespace: str, repository: str, root: str | Path = ".openpulse/observations"
) -> list[dict[str, Any]]:
    """Every readable observation oldest->newest; corrupt files are skipped."""
    records = []
    for path in list_observations(registry, namespace, repository, root):
        record = try_load(path)
        if record is not None:
            records.append(record)
    return records


def load_previous(
    registry: str, namespace: str, repository: str, root: str | Path = ".openpulse/observations"
) -> dict[str, Any] | None:
    """Latest readable observation, if any (corrupt tails are skipped)."""
    for path in reversed(list_observations(registry, namespace, repository, root)):
        record = try_load(path)
        if record is not None:
            return record
    return None


def first_observed(
    registry: str, namespace: str, repository: str, root: str | Path = ".openpulse/observations"
) -> dict[str, Any] | None:
    """Earliest readable observation, if any."""
    for path in list_observations(registry, namespace, repository, root):
        record = try_load(path)
        if record is not None:
            return record
    return None
