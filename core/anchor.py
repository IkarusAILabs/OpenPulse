"""History anchors: checkpoints kept outside the store (v0.9.0 item B5, finding H2).

Keyed MACs (B3) stop an edit, and the tip pointer and downgrade checks
(B4) stop a partial rollback. Neither can stop a deletion that takes its
own evidence with it: wiping a repository's whole history folder, tip
included, or a ledger entry, or the rotation log. Whatever deletes the
data can delete any local marker too.

An anchor is a checkpoint of what the store held at one moment, kept
somewhere the store's writer cannot reach (a git commit, a CI artifact).
``verify_anchor`` then reports anything the anchor saw that is now gone
or changed:

- **observations:** per repository, the chain tip, the record count and
  the re-baseline count. The anchored tip must still be a record of the
  current chain: a wipe, truncation or rewrite removes it.
- **ledger:** one leaf per entry (its file, ``first_seen`` and
  ``adopted_at``, the dates a lead time rests on), and the RFC 6962
  Merkle root over the leaves, compact enough to publish. Entries may
  gain sightings; they may not disappear or change those dates.
- **rotations:** a hash of each rotation-log entry. The log is
  append-only, so every anchored entry must remain.

A re-baseline (B4) can legitimately replace an anchored tip. It is
reported as a notice, not a violation, only when its log entry is newer
than the anchor and MAC-verified under a supplied key; otherwise it
proves nothing and the missing tip is a violation.

With a history key the anchor carries ``key_id`` and an HMAC over its
canonical JSON, so a forged anchor fails verification. Without one, the
anchor's integrity is the integrity of where it is stored.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.observations.chain import link_hash_for, order_history
from core.observations.store import (
    observation_files,
    read_rebaselines,
    read_tip,
    repo_dirs,
    try_load,
)

ANCHOR_VERSION = 1

#: The current key's MAC over an anchor's canonical JSON.
ANCHOR_DOMAIN = "openpulse-anchor-v1"

OK = "OK"
VIOLATED = "VIOLATED"


# ---------------------------------------------------------------------------
# Merkle tree (RFC 6962, section 2.1)
# ---------------------------------------------------------------------------


def _leaf_hash(data: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + data).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def _mth(leaves: list[bytes]) -> bytes:
    if len(leaves) == 1:
        return _leaf_hash(leaves[0])
    split = 1
    while split * 2 < len(leaves):
        split *= 2
    return _node_hash(_mth(leaves[:split]), _mth(leaves[split:]))


def merkle_root(leaves: list[bytes]) -> str:
    """RFC 6962 Merkle tree hash over ``leaves`` in order; empty -> SHA-256 of b''."""
    if not leaves:
        return "sha256:" + hashlib.sha256(b"").hexdigest()
    return "sha256:" + _mth(leaves).hex()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


# ---------------------------------------------------------------------------
# Reading the store
# ---------------------------------------------------------------------------


def _repo_name(root: Path, directory: Path) -> str:
    return directory.relative_to(root).as_posix()


def _observations(store_root: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(store_root)
    out: dict[str, dict[str, Any]] = {}
    for directory in repo_dirs(root):
        records = [r for r in (try_load(p) for p in observation_files(directory)) if r]
        tip = read_tip(directory)
        if not records and not tip:
            continue
        ordered, _ = order_history(records)
        out[_repo_name(root, directory)] = {
            "tip": link_hash_for(ordered[-1]) if ordered else None,
            "records": len(records),
            "rebaselines": len(read_rebaselines(directory)),
        }
    return out


def _chain_links(directory: Path) -> set[str]:
    records = [r for r in (try_load(p) for p in observation_files(directory)) if r]
    return {link for link in (link_hash_for(r) for r in records) if link}


def _ledger_leaves(ledger_root: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(ledger_root)
    out: dict[str, dict[str, Any]] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*/*.json")):
        if path.name.startswith("."):
            continue
        entry = try_load(path)
        if entry is None:
            continue
        out[path.relative_to(root).as_posix()] = {
            "first_seen": entry.get("first_seen"),
            "adopted_at": entry.get("adopted_at"),
        }
    return out


def _rotation_hashes(ledger_root: str | Path) -> list[str]:
    from core.detections.ledger import ROTATIONS_FILE

    data = try_load(Path(ledger_root) / ROTATIONS_FILE) or {}
    return sorted(_sha(r) for r in data.get("rotations") or [] if isinstance(r, dict))


# ---------------------------------------------------------------------------
# Anchor
# ---------------------------------------------------------------------------


def _unsigned(anchor: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in anchor.items() if k not in ("key_id", "mac")}


def build_anchor(
    store_root: str | Path,
    ledger_root: str | Path,
    history_key: Any = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Checkpoint of the observation store and the ledger, MACed when keyed."""
    leaves = _ledger_leaves(ledger_root)
    anchor: dict[str, Any] = {
        "anchor_version": ANCHOR_VERSION,
        "created_at": (now or datetime.now(timezone.utc)).isoformat(),
        "observations": _observations(store_root),
        "ledger": {
            "entries": leaves,
            "merkle_root": merkle_root([_canonical([k, leaves[k]]) for k in sorted(leaves)]),
        },
        "rotations": _rotation_hashes(ledger_root),
    }
    if history_key is not None:
        anchor["key_id"] = history_key.key_id
        anchor["mac"] = history_key.mac(ANCHOR_DOMAIN, _canonical(_unsigned(anchor)).decode())
    return anchor


def anchor_signature(anchor: dict[str, Any], keys: dict[str, Any] | None = None) -> str:
    """VALID / UNSIGNED / UNKNOWN (key not supplied) / BROKEN for an anchor's MAC."""
    mac, key_id = anchor.get("mac"), anchor.get("key_id")
    if not mac and not key_id:
        return "UNSIGNED"
    if not mac or not key_id:
        return "BROKEN"
    key = (keys or {}).get(str(key_id))
    if key is None:
        return "UNKNOWN"
    ok = key.verify(mac, ANCHOR_DOMAIN, _canonical(_unsigned(anchor)).decode())
    return "VALID" if ok else "BROKEN"


def _parse(value: Any) -> datetime | None:
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _verified_rebaselines_since(
    directory: Path, since: datetime | None, keys: dict[str, Any]
) -> list[dict[str, Any]]:
    """Re-baselines logged after ``since`` whose MAC verifies under ``keys``."""
    from core.history_key import REBASELINE_DOMAIN

    out = []
    for entry in read_rebaselines(directory):
        at = _parse(entry.get("at"))
        key = keys.get(str(entry.get("key_id") or ""))
        if at is None or since is None or at <= since or key is None:
            continue
        unsigned = {k: v for k, v in entry.items() if k not in ("key_id", "mac")}
        parts = [str(unsigned[k] or "") for k in sorted(unsigned)]
        if key.verify(entry.get("mac"), REBASELINE_DOMAIN, *parts):
            out.append(entry)
    return out


def verify_anchor(
    anchor: dict[str, Any],
    store_root: str | Path,
    ledger_root: str | Path,
    keys: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare the store with an anchor. VIOLATED when anything anchored is gone or changed.

    Returns {status, signature, violations, notices}; each violation is
    {kind, subject, detail}. A BROKEN signature is itself a violation.
    """
    keys = keys or {}
    violations: list[dict[str, str]] = []
    notices: list[dict[str, str]] = []

    def violate(kind: str, subject: str, detail: str) -> None:
        violations.append({"kind": kind, "subject": subject, "detail": detail})

    if anchor.get("anchor_version") != ANCHOR_VERSION:
        violate(
            "ANCHOR_VERSION",
            "anchor",
            f"unsupported anchor_version {anchor.get('anchor_version')!r}",
        )
    signature = anchor_signature(anchor, keys)
    if signature == "BROKEN":
        violate("ANCHOR_SIGNATURE", "anchor", "the anchor's MAC does not verify: it was edited")
    since = _parse(anchor.get("created_at"))

    root = Path(store_root)
    for name, anchored in sorted((anchor.get("observations") or {}).items()):
        directory = root / name
        tip = anchored.get("tip")
        links = _chain_links(directory)
        if tip and tip not in links:
            accepted = _verified_rebaselines_since(directory, since, keys)
            if accepted:
                notices.append(
                    {
                        "kind": "REBASELINED",
                        "subject": name,
                        "detail": f"re-baselined after the anchor: {accepted[-1].get('reason')}",
                    }
                )
            elif not links and read_tip(directory) is None:
                violate("WIPED", name, "the anchored history is gone, tip included")
            else:
                violate("ROLLBACK", name, f"the anchored tip {tip} is no longer in the chain")
        if len(read_rebaselines(directory)) < int(anchored.get("rebaselines") or 0):
            violate("REBASELINE_LOG", name, "re-baseline log entries the anchor saw are gone")

    current = _ledger_leaves(ledger_root)
    for path, leaf in sorted(((anchor.get("ledger") or {}).get("entries") or {}).items()):
        now_leaf = current.get(path)
        if now_leaf is None:
            violate("LEDGER_DELETED", path, "a ledger entry the anchor saw is gone")
        elif now_leaf != leaf:
            violate(
                "LEDGER_REWRITTEN",
                path,
                f"first_seen/adopted_at changed from {leaf} to {now_leaf}",
            )

    missing = set(anchor.get("rotations") or []) - set(_rotation_hashes(ledger_root))
    if missing:
        violate(
            "ROTATION_LOG", "rotations.json", f"{len(missing)} anchored rotation entries are gone"
        )

    return {
        "status": VIOLATED if violations else OK,
        "signature": signature,
        "violations": violations,
        "notices": notices,
    }
