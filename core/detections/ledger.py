"""Local-first detection ledger - durable per-entity first-detection history.

The ledger closes the gap issue #41 names: sweep findings carry
``first_detected_at`` (diffed against observation history), but
lifecycle and security findings detected in a fresh run have no
persistent memory - a second run cannot tell "detected 90 days ago"
from "seen first now", so warning windows died with the process.

Model (deliberately the same trust treatment as
``core.observations.store`` - atomic writes, per-key locking,
content hashes - NOT a second storage model):

- Layout: ``{root}/{project}/{key}.json`` - one file per detected
  fact, keyed by stable entity identity (project slug + finding
  class + subject + scope), value = earliest detection timestamp +
  content hash over identity AND the sighting dates, verified on
  every read (``verify_entry``): a post-write edit of ``first_seen``
  breaks the hash and the entry degrades to unknown - the integrity
  claim above is enforced, not aspirational.
- ``first_seen`` is set once, when the entry is created: a
  re-detection never moves it, later or earlier. A stamp earlier than
  the entry's creation is a sighting the ledger did not witness, so it
  is not taken (clock trust, finding L7).
- Every stamp must lie within ``MAX_CLOCK_SKEW`` of UTC wall-clock time
  at the moment of recording. A caller cannot backdate a detection and
  so inflate a lead time; a stamp outside the bound raises
  ``ClockSkewError`` and nothing is written.
- Writes are atomic (temp file + ``os.replace``) under a per-project
  lock (``O_CREAT|O_EXCL``, stale reclaim after 120s) borrowed from
  the observation store so two simultaneous ``openpulse check`` runs
  cannot interleave half-written ledgers.
- Git-ignored under ``.openpulse/``; safe to delete. A missing or
  corrupt entry means *unknown*, never a fabricated date: deletion
  degrades to current per-run behavior, never to invented dates.

Hash-chain decision: observations chain because each record derives
meaning from its position in history (diffs read the predecessor);
a ledger entry is a standalone earliest-witness record whose
integrity need is met by its own content hash. Chaining would add
verification machinery without changing any decision this system
makes. Absence (or deletion) of entries is indistinguishable from
never-detected, and both mean "no claim" - the tripwire an
observation chain provides has no decision to protect here.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.filelock import exclusive_lock
from core.history_key import keyring

#: Same staleness policy as the observation store: a crashed lock
#: holder must not block automation forever.
_LOCK_WAIT_SECONDS = 30.0

#: Finding classes with durable, re-detectable identity. Both
#: lifecycle (endoflife-derived) and security (CVE) findings are
#: covered - per issue #41 each has a stable subject.
LIFECYCLE = "lifecycle"
SECURITY = "security"

#: Event types whose findings describe a *durable* lifecycle fact -
#: re-detectable across runs, and the ledger is what makes their first
#: detection survive the process. Distribution/registry changes keep
#: their own durable first-detection via observation history diffs.
#: Single source of truth: the writer (``check.detections_from_verdicts``)
#: and the reader (``reports._ledger_fact``) MUST key identically, so
#: the set lives here, next to the identity contract it defines.
LIFECYCLE_EVENT_TYPES = frozenset({"EOL", "EOS", "DEPRECATION", "SUPPORT_CHANGE"})


#: Largest distance between a recorded stamp and UTC wall-clock time
#: at the moment of recording. Covers clock reads a few seconds apart
#: within one run; anything further is a backdated or future-dated
#: claim, never a detection this process witnessed.
MAX_CLOCK_SKEW = timedelta(minutes=5)


class ClockSkewError(ValueError):
    """A ledger stamp is unparseable or too far from wall-clock time."""


def _safe(part: str) -> str:
    """Filesystem-safe path segment. Dots alone (`..`) never survive:
    traversal segments collapse to `_`, hostile values stay inside
    the ledger root."""
    cleaned = "".join(c if c.isalnum() or c in (".", "-", "_") else "_" for c in str(part))
    if cleaned.strip(".") == "":
        return "_"
    return cleaned


def now_iso() -> str:
    """Current UTC time, ISO-8601 with offset. One clock read per call."""
    return datetime.now(timezone.utc).isoformat()


def _project_dir(root: str | Path, project: str) -> Path:
    return Path(root) / _safe(project)


def _key_file(directory: Path, key: str) -> Path:
    return directory / f"{key}.json"


def _lock_path(directory: Path) -> Path:
    return directory / ".ledger-lock"


def _identity_terms(project: str, finding_class: str, subject: str, scope: list[str]) -> list[str]:
    """Canonical identity of one detected fact, ONE normalization.

    Project/class/subject keep their case (they are identifiers, not
    free text); scope terms are trimmed and lowercased (version
    strings differ only in casing/whitespace between sources). Both
    the ledger key and the content hash run over this exact list, so
    the hash written at record time is the hash checked on read -
    the integrity claim in the module docstring stays honest.
    """
    terms = [str(project), str(finding_class), str(subject)]
    terms += sorted(str(s).strip().lower() for s in (scope or []))
    return terms


def _entry_content_hash(
    project: str,
    finding_class: str,
    subject: str,
    scope: list[str],
    first_seen: str,
    last_seen: str,
) -> str:
    """SHA-256 over one ledger entry's full content.

    Covers identity AND both sighting timestamps: a post-write edit
    of ``first_seen`` (the date every consumer trusts) breaks the
    hash, so verification on read catches it. Recomputed at every
    write, so legitimate earliest-wins merges always re-pin it.
    """
    material = json.dumps(
        _identity_terms(project, finding_class, subject, scope) + [str(first_seen), str(last_seen)],
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def fact_key(project: str, finding_class: str, subject: str, scope: list[str]) -> str:
    """Stable ledger key for one detected fact.

    SHA-256 over the normalized identity terms so the key doubles as
    the (content-derived) filename - a hostile subject string cannot
    forge path segments, and two sources reporting the same CVE or
    lifecycle cycle produce the same key, so a re-report cannot
    split the history.
    """
    joined = "|".join(_identity_terms(project, finding_class, subject, scope))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def verify_entry(entry: dict[str, Any]) -> bool:
    """True when one loaded ledger entry is internally consistent.

    The content hash recorded at write time must match a hash
    recomputed over the entry's own fields - identity AND the
    first/last sighting dates a consumer would trust. A mismatch
    means the file was edited after the fact: the entry degrades to
    unknown/fresh - never trusted for a detection claim, never an
    exception.
    """
    if not isinstance(entry, dict):
        return False
    expected = _entry_content_hash(
        str(entry.get("project") or ""),
        str(entry.get("finding_class") or ""),
        str(entry.get("subject") or ""),
        [str(s) for s in entry.get("scope") or []],
        str(entry.get("first_seen") or ""),
        str(entry.get("last_seen") or ""),
    )
    return str(entry.get("content_hash") or "") == expected


@contextlib.contextmanager
def ledger_lock(
    root: str | Path, project: str, wait_seconds: float = _LOCK_WAIT_SECONDS
) -> Iterator[None]:
    """Per-project exclusive lock across load-merge-save.

    Same mechanics as ``core.observations.store.repo_lock`` (shared
    ``core.filelock.exclusive_lock``): OS advisory lock released on holder
    exit, TimeoutError when busy (never proceed unlocked). Lock files live
    in the project directory so concurrent runs on different projects
    never serialize.
    """
    directory = _project_dir(root, project)
    directory.mkdir(parents=True, exist_ok=True)
    lock = _lock_path(directory)
    with exclusive_lock(lock, wait_seconds, "ledger"):
        yield


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Temp file + os.replace: readers never see a partial entry."""
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _try_load(path: Path) -> dict[str, Any] | None:
    """One file -> dict, or None when missing/corrupt (never raises)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _parse_moment(value: Any) -> datetime | None:
    """ISO timestamp -> aware datetime; garbage -> None (never estimated)."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        moment = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def _check_wall_clock(stamp: str) -> None:
    """Raise ClockSkewError unless ``stamp`` is near UTC wall-clock time."""
    moment = _parse_moment(stamp)
    if moment is None:
        raise ClockSkewError(f"ledger stamp is not an ISO-8601 time: {stamp!r}")
    wall = _parse_moment(now_iso())
    if wall is None or abs(moment - wall) > MAX_CLOCK_SKEW:
        raise ClockSkewError(
            f"ledger stamp {stamp} is more than {MAX_CLOCK_SKEW} from wall-clock time"
        )


#: Keyed integrity states, the same vocabulary as the observation chain.
VALID_KEYED = "VALID_KEYED"
VALID_UNKEYED = "VALID_UNKEYED"
BROKEN = "BROKEN"
UNKNOWN = "UNKNOWN"


def _ledger_mac_parts(entry: dict[str, Any]) -> tuple[str, ...]:
    """What a ledger MAC covers: the content hash, and the adoption time if any."""
    parts = (str(entry.get("content_hash") or ""),)
    return parts + (str(entry["adopted_at"]),) if entry.get("adopted_at") else parts


def _keyed(entry: dict[str, Any], history_key: Any) -> dict[str, Any]:
    """The entry with its history MAC, or as is."""
    if history_key is None:
        return entry
    from core.history_key import LEDGER_DOMAIN

    mac = history_key.mac(LEDGER_DOMAIN, *_ledger_mac_parts(entry))
    return {**entry, "key_id": history_key.key_id, "history_mac": mac}


#: Ledger-wide rotation log (B3b): when each retired key was handed over.
ROTATIONS_FILE = "rotations.json"


def _rotation_parts(entry: dict[str, Any]) -> tuple[str, str, str]:
    return str(entry.get("from") or ""), str(entry.get("to") or ""), str(entry.get("at") or "")


def load_rotations(root: str | Path, keys: dict[str, Any] | None = None) -> dict[str, datetime]:
    """retired key_id -> earliest verified handover time.

    A rotation entry counts when either key it names MACs it under a
    supplied key. A missing or unreadable log means no rotations: deleting
    it is a rollback, which B4 is for.
    """
    from core.history_key import ROTATION_DOMAIN

    keys = keys or {}
    data = _try_load(Path(root) / ROTATIONS_FILE) or {}
    out: dict[str, datetime] = {}
    for entry in data.get("rotations") or []:
        if not isinstance(entry, dict):
            continue
        retired, current, _ = parts = _rotation_parts(entry)
        moment = _parse_moment(entry.get("at"))
        if moment is None:
            continue
        verified = any(
            key_id in keys and keys[key_id].verify(entry.get(field), ROTATION_DOMAIN, *parts)
            for key_id, field in ((current, "mac_to"), (retired, "mac_from"))
        )
        if verified and (retired not in out or moment < out[retired]):
            out[retired] = moment
    return out


def record_rotation(root: str | Path, retired: Any, current: Any) -> None:
    """Log the handover from ``retired`` to ``current``, MACed by both (once)."""
    from core.history_key import ROTATION_DOMAIN

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(root / ".rotations-lock", _LOCK_WAIT_SECONDS, "ledger"):
        path = root / ROTATIONS_FILE
        rotations = list((_try_load(path) or {}).get("rotations") or [])
        if any(
            isinstance(r, dict)
            and r.get("from") == retired.key_id
            and r.get("to") == current.key_id
            for r in rotations
        ):
            return
        parts = (retired.key_id, current.key_id, now_iso())
        rotations.append(
            {
                "from": parts[0],
                "to": parts[1],
                "at": parts[2],
                "mac_from": retired.mac(ROTATION_DOMAIN, *parts),
                "mac_to": current.mac(ROTATION_DOMAIN, *parts),
            }
        )
        _write_atomic(path, {"rotations": rotations})


def entry_integrity(
    entry: Any,
    keys: dict[str, Any] | None = None,
    rotations: dict[str, datetime] | None = None,
) -> str:
    """VALID_KEYED / VALID_UNKEYED / BROKEN / UNKNOWN for one ledger entry.

    The content hash covers identity and both sighting dates; the MAC
    covers the content hash. ``keys`` maps key_id -> HistoryKey. A keyed
    entry whose key is not supplied is UNKNOWN, never VALID_KEYED.
    ``rotations`` (``load_rotations``): an entry under a retired key that
    was seen after that key's handover is BROKEN, so a leaked retired key
    cannot add sightings after its rotation.
    """
    from core.history_key import LEDGER_DOMAIN

    if not isinstance(entry, dict) or not verify_entry(entry):
        return BROKEN
    mac, key_id = entry.get("history_mac"), entry.get("key_id")
    if not mac:
        return VALID_UNKEYED
    if not key_id:
        return BROKEN
    key = (keys or {}).get(str(key_id))
    if key is None:
        return UNKNOWN
    if not key.verify(mac, LEDGER_DOMAIN, *_ledger_mac_parts(entry)):
        return BROKEN
    handed_over = (rotations or {}).get(str(key_id))
    last = _parse_moment(entry.get("last_seen"))
    if handed_over is not None and (last is None or last > handed_over):
        return BROKEN
    return VALID_KEYED


def record_detection(
    project: str,
    finding_class: str,
    subject: str,
    scope: list[str] | None = None,
    detected_at: str | None = None,
    root: str | Path = ".openpulse/detections",
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
) -> dict[str, Any]:
    """Record one detection; return the ledger entry after merge.

    A re-detection refreshes ``last_seen`` but never moves
    ``first_seen``. ``recorded_now`` tells the caller whether this call
    created the entry (first detection). Raises ``ClockSkewError``,
    writing nothing, when ``detected_at`` is unparseable or further
    than ``MAX_CLOCK_SKEW`` from UTC wall-clock time.

    ``history_key`` (a ``core.history_key.HistoryKey``) MACs new entries
    and keeps keyed entries keyed (B3). A keyed entry is never rewritten
    without its key: the call returns it unchanged with
    ``key_refused: True``. An entry written before any key is adopted
    (B3c): it is MACed now with ``adopted_at`` set to this moment, so
    its keyed lead time counts from the adoption, never from the earlier,
    unkeyed ``first_seen`` (``keyed_first_seen``).

    ``previous_keys`` are retired, verify-only keys (B3b). An entry under
    one of them is verified with it, the handover is logged in
    ``rotations.json``, and the entry is rewritten under ``history_key``.
    """
    scope = list(scope or [])
    stamp = detected_at or now_iso()
    _check_wall_clock(stamp)
    directory = _project_dir(root, project)
    key = fact_key(project, finding_class, subject, scope)
    path = _key_file(directory, key)
    with ledger_lock(root, project):
        existing = _try_load(path)
        if existing is not None and not verify_entry(existing):
            # Tampered entry: no honest merge is possible from it.
            # Degrade to unknown - write fresh, exactly like absence.
            existing = None
        if existing is not None and existing.get("history_mac"):
            ring = keyring(history_key, previous_keys)
            entry_key = str(existing.get("key_id"))
            if history_key is None or entry_key not in ring:
                # Rewriting it unkeyed (or under an unknown key) would end
                # its keyed run; leave it as it is.
                return {**existing, "recorded_now": False, "key_refused": True}
            if entry_integrity(existing, ring, load_rotations(root, ring)) == BROKEN:
                existing = None  # MAC forged: degrade to unknown, as above
            elif entry_key != history_key.key_id:
                record_rotation(root, ring[entry_key], history_key)
        keep_key = history_key is not None
        # Adoption (B3c): an unkeyed entry keyed now carries the moment of
        # keying; a keyed one keeps its adoption time, if it has one.
        adopted_at = None
        if existing is not None and keep_key:
            adopted_at = existing.get("adopted_at") if existing.get("history_mac") else stamp
        if existing is None:
            entry = {
                "project": str(project),
                "finding_class": str(finding_class),
                "subject": str(subject),
                "scope": sorted(str(s) for s in scope),
                "first_seen": stamp,
                "last_seen": stamp,
                "content_hash": _entry_content_hash(
                    project, finding_class, subject, scope, stamp, stamp
                ),
            }
            entry = _keyed(entry, history_key if keep_key else None)
            _write_atomic(path, entry)
            return {**entry, "recorded_now": True}
        incoming = _parse_moment(stamp)
        if _parse_moment(existing.get("first_seen")) is None:
            # Unreadable first sighting: this is the first one witnessed.
            first_seen = stamp
        else:
            # Set at creation. An earlier stamp predates the entry, so
            # the ledger never witnessed it (L7): it is not taken.
            first_seen = str(existing.get("first_seen"))
        last_prev = _parse_moment(existing.get("last_seen"))
        last_seen = str(existing.get("last_seen") or stamp)
        if last_prev is None or (incoming is not None and incoming > last_prev):
            last_seen = stamp
        entry = {
            "project": str(project),
            "finding_class": str(finding_class),
            "subject": str(subject),
            "scope": sorted(str(s) for s in scope),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "content_hash": _entry_content_hash(
                project, finding_class, subject, scope, first_seen, last_seen
            ),
        }
        if adopted_at:
            entry["adopted_at"] = str(adopted_at)
        entry = _keyed(entry, history_key if keep_key else None)
        _write_atomic(path, entry)
    return {**entry, "recorded_now": False}


def first_seen(
    project: str,
    finding_class: str,
    subject: str,
    scope: list[str] | None = None,
    root: str | Path = ".openpulse/detections",
) -> str | None:
    """Earliest recorded detection of one fact, or None (never a guess)."""
    directory = _project_dir(root, project)
    path = _key_file(directory, fact_key(project, finding_class, subject, list(scope or [])))
    entry = _try_load(path)
    if entry is None or not verify_entry(entry):
        # Absent or tampered (hash mismatch) - both mean no claim.
        return None
    value = entry.get("first_seen")
    return str(value) if value else None


def keyed_first_seen(
    project: str,
    finding_class: str,
    subject: str,
    scope: list[str] | None = None,
    root: str | Path = ".openpulse/detections",
    keys: dict[str, Any] | None = None,
) -> str | None:
    """First detection a lead time may rest on, or None (B3c).

    Only a VALID_KEYED entry counts (under ``keys``, with the ledger's
    rotation log). An adopted entry counts from its adoption: the result
    is the later of ``first_seen`` and ``adopted_at``, a lower bound on
    the lead time that never overstates it. Without keys, nothing counts.
    """
    if not keys:
        return None
    directory = _project_dir(root, project)
    path = _key_file(directory, fact_key(project, finding_class, subject, list(scope or [])))
    entry = _try_load(path)
    if entry is None or entry_integrity(entry, keys, load_rotations(root, keys)) != VALID_KEYED:
        return None
    first = _parse_moment(entry.get("first_seen"))
    adopted = _parse_moment(entry.get("adopted_at"))
    if first is None:
        return None
    if adopted is not None and adopted > first:
        return str(entry["adopted_at"])
    return str(entry["first_seen"])
