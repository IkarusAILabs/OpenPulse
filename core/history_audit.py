"""Audit a whole local history before it is used (v0.21.0 item W2).

The Action keeps ``.openpulse/observations`` and ``.openpulse/detections``
in the Actions cache between runs. A restored cache is input from outside
the run: anything that can write the repository's caches can edit it. The
stores already refuse to append to a history that does not verify (B3,
B4), but only when that history is touched again; a history no later
command touches would sit unverified. ``audit_history`` checks all of it,
once, before any command runs, and says what it refuses:

- **observations:** every repository history under the store root: a
  forked, gapped or failed chain (BROKEN), a tip pointer the data does not
  reach (ROLLBACK, ROLLBACK_SUSPECTED), an unkeyed or unchained record
  after keyed ones (DOWNGRADE), a MAC that fails (BROKEN), and records
  under a key that was not supplied (UNKNOWN: a foreign history).
- **ledger:** every detection entry, by ``ledger.entry_integrity``: a
  content hash or MAC that fails (BROKEN) or a key that was not supplied
  (UNKNOWN), and a file that is not an entry at all.
- with ``require_keyed``: anything only hash-chained (VALID_UNKEYED). A
  history the Action writes is always keyed, so an unkeyed record in it
  was written by something without the key.

What it cannot see: a whole history replaced by an older genuine copy of
itself (an earlier cache). Only a checkpoint kept outside the cache
detects that (B5 anchors, ``openpulse verify``). Never raises on bad
data; read-only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.detections import ledger
from core.observations.chain import BROKEN, verify_keyed_history
from core.observations.registry import verify_registry_history
from core.observations.repository import REGISTRY as GITHUB
from core.observations.repository import verify_repository_history
from core.observations.store import observation_files, repo_dirs, try_load
from core.observations.sweep import REFUSED_HISTORY, _assess_history

OK = "OK"
REFUSED = "REFUSED"
EMPTY = "EMPTY"

VALID_KEYED = "VALID_KEYED"
VALID_UNKEYED = "VALID_UNKEYED"
UNKNOWN = "UNKNOWN"

#: Problems named one by one; the rest are counted.
MAX_NAMED = 50

#: A restored cache is written by others, so its file names are untrusted
#: text: a subject keeps only path-safe characters, and every detail is a
#: fixed sentence (never a name read from the store).
_UNSAFE = re.compile(r"[^A-Za-z0-9._@+/-]")
_MAX_SUBJECT = 200

_REFUSED_DETAIL = {
    BROKEN: "the chain is forked, gapped or fails verification",
    "ROLLBACK": "the data does not reach the recorded tip (records missing or rolled back)",
    "ROLLBACK_SUSPECTED": "the history is chained but its tip pointer is missing "
    "(truncated or wiped)",
    "DOWNGRADE": "an unchained or unkeyed record follows chained or keyed ones",
}


def _problem(kind: str, subject: str, status: str, detail: str) -> dict[str, str]:
    safe = _UNSAFE.sub("_", subject)[:_MAX_SUBJECT]
    return {"kind": kind, "subject": safe, "status": status, "detail": detail}


def _observations(
    store_root: str | Path, keys: dict[str, Any], require_keyed: bool
) -> tuple[int, list[dict[str, str]]]:
    base = Path(store_root)
    problems = []
    directories = repo_dirs(store_root)
    for directory in directories:
        registry, namespace, repository = directory.relative_to(base).parts
        subject = f"{registry}/{namespace}/{repository}"
        verify = verify_repository_history if registry == GITHUB else verify_registry_history
        records = []
        for path in observation_files(directory):
            record = try_load(path)
            if record is None:
                problems.append(
                    _problem("observations", subject, BROKEN, "a record file is unreadable")
                )
                continue
            records.append(record)
        ordered, status, _ = _assess_history(records, directory, namespace, repository, verify)
        if status in REFUSED_HISTORY:
            problems.append(_problem("observations", subject, status, _REFUSED_DETAIL[status]))
            continue
        if not ordered:
            continue
        keyed = str(verify_keyed_history(ordered, keys)["status"])
        if keyed == BROKEN:
            detail = "a history MAC or key handover does not verify"
        elif keyed == UNKNOWN:
            detail = "records are keyed with a key that was not supplied (a foreign history)"
        elif keyed == VALID_UNKEYED and require_keyed:
            detail = "records are not keyed: written without the history key"
        else:
            continue
        problems.append(_problem("observations", subject, keyed, detail))
    return len(directories), problems


def _ledger(
    ledger_root: str | Path, keys: dict[str, Any], require_keyed: bool
) -> tuple[int, list[dict[str, str]]]:
    base = Path(ledger_root)
    if not base.is_dir():
        return 0, []
    rotations = ledger.load_rotations(base, keys)
    problems = []
    files = sorted(p for p in base.glob("*/*.json") if p.is_file() and not p.name.startswith("."))
    for path in files:
        subject = path.relative_to(base).as_posix()
        entry = try_load(path)
        status = ledger.entry_integrity(entry, keys, rotations) if entry is not None else BROKEN
        if status == BROKEN:
            detail = "the entry's content hash or MAC does not verify"
        elif status == UNKNOWN:
            detail = "the entry is keyed with a key that was not supplied (a foreign ledger)"
        elif status == VALID_UNKEYED and require_keyed:
            detail = "the entry is not keyed: written without the history key"
        else:
            continue
        problems.append(_problem("ledger", subject, status, detail))
    return len(files), problems


def audit_history(
    store_root: str | Path,
    ledger_root: str | Path,
    keys: dict[str, Any] | None = None,
    *,
    require_keyed: bool = False,
) -> dict[str, Any]:
    """Audit every observation history and ledger entry under the two roots.

    ``keys`` maps key_id -> HistoryKey (``core.history_key.keyring``).
    ``status``: OK, REFUSED (``problems`` says what and why) or EMPTY
    (nothing stored: a first run, or an evicted cache).
    """
    keys = keys or {}
    histories, observation_problems = _observations(store_root, keys, require_keyed)
    entries, ledger_problems = _ledger(ledger_root, keys, require_keyed)
    problems = observation_problems + ledger_problems
    if problems:
        status = REFUSED
    elif histories == 0 and entries == 0:
        status = EMPTY
    else:
        status = OK
    return {
        "status": status,
        "histories": histories,
        "ledger_entries": entries,
        "require_keyed": require_keyed,
        "problems": problems[:MAX_NAMED],
        "problems_total": len(problems),
    }


__all__ = ["EMPTY", "OK", "REFUSED", "audit_history"]
