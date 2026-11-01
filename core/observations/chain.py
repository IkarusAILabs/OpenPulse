"""Tamper-evident observation chains — history that cannot silently change.

Every persisted observation carries ``chain_hash``:

    H[n] = SHA256(canonical_chain_fields(n) + H[n-1])

where ``canonical_chain_fields`` is the deterministic JSON of
{observation_id, source, entity_reference, observed_at, content_hash,
parser_version, previous_observation_hash}. The first observation of an
entity links to the explicit genesis marker ``"genesis"`` — a missing
history is a baseline, never a gap to paper over.

Integrity states:

- VALID — hashes recompute and every link resolves.
- BROKEN — content or a link was altered. Never trust for diffs.
- UNKNOWN — legacy records without chain fields. Diffable for
  back-compat, but new saves always chain.

Pure functions over plain dicts (persisted JSON shape). No network,
no database.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

#: Link value for the first observation of an entity: an explicit
#: baseline, distinguishable from a missing or wiped history.
GENESIS_PREVIOUS = "genesis"

VALID = "VALID"
BROKEN = "BROKEN"
UNKNOWN = "UNKNOWN"

#: Keyed states (B3, ``verify_keyed_history``). VALID_KEYED: hashes verify
#: and every record's MAC verifies under a supplied key. VALID_UNKEYED:
#: hashes verify, but some record has no MAC (or no key was supplied to
#: check it). Only VALID_KEYED history proves it was not rewritten.
VALID_KEYED = "VALID_KEYED"
VALID_UNKEYED = "VALID_UNKEYED"

#: Fields covered by the chain hash, in canonical form.
_CHAIN_FIELDS = (
    "observation_id",
    "source",
    "entity_reference",
    "observed_at",
    "content_hash",
    "parser_version",
    "previous_observation_hash",
)


def canonical_chain_payload(record: dict[str, Any]) -> str:
    """Deterministic JSON of the chain-covered fields (missing -> null)."""
    trimmed = {key: record.get(key) for key in _CHAIN_FIELDS}
    return json.dumps(trimmed, sort_keys=True, separators=(",", ":"), default=str)


def chain_hash(record: dict[str, Any], previous_hash: str) -> str:
    """H[n] = SHA256(canonical_chain_fields(n) + H[n-1])."""
    material = canonical_chain_payload(record) + str(previous_hash)
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def link_hash_for(record: dict[str, Any]) -> str | None:
    """The hash the *next* observation must link to (chain, else content)."""
    chain = record.get("chain_hash")
    if isinstance(chain, str) and chain:
        return chain
    content = record.get("content_hash")
    return str(content) if content else None


def verify_link(record: dict[str, Any], previous_link: str | None) -> str:
    """VALID/BROKEN/UNKNOWN for one record against its expected predecessor.

    ``previous_link`` is the previous record's chain hash (else its
    content hash for legacy records), or None when no predecessor is
    supplied — in which case only an explicit genesis record verifies.
    Legacy predecessors anchor upgraded chains via their content hash.
    """
    chain = record.get("chain_hash")
    if not isinstance(chain, str) or not chain:
        return UNKNOWN  # legacy record: no chain to verify
    expected_prev = record.get("previous_observation_hash")
    if previous_link is None:
        if expected_prev != GENESIS_PREVIOUS:
            return BROKEN  # claims a predecessor that is not supplied
    elif expected_prev != previous_link:
        return BROKEN
    if chain != chain_hash(record, str(expected_prev)):
        return BROKEN
    return VALID


def verify_observation_chain(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Walk oldest->newest. Any BROKEN poisons the chain; UNKNOWN if legacy.

    Callers must pass records in CHAIN order (see ``order_history``):
    filename order is not chain order when timestamps collide.
    """
    breaks: list[int] = []
    unknowns: list[int] = []
    previous_link: str | None = None
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            breaks.append(i)
            continue
        status = verify_link(record, previous_link)
        if status == BROKEN:
            breaks.append(i)
        elif status == UNKNOWN:
            unknowns.append(i)
        previous_link = link_hash_for(record)
    if breaks:
        return {"status": BROKEN, "breaks": breaks, "unknowns": unknowns}
    if unknowns:
        return {"status": UNKNOWN, "breaks": [], "unknowns": unknowns}
    return {"status": VALID, "breaks": [], "unknowns": []}


def order_history(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    """Chain order (oldest->newest) by following links, not filenames.

    Returns (ordered, ok). ``ok`` is False on forks (two records
    claiming the same predecessor, two geneses), gaps (predecessor
    file missing), or cycles — an ambiguous history no diff may trust.
    Legacy (unchained) records keep their input order as the prefix;
    the chained suffix must anchor to genesis or to legacy content.
    """
    if not records:
        return [], True
    legacy = [r for r in records if not (isinstance(r, dict) and r.get("chain_hash"))]
    chained = [r for r in records if isinstance(r, dict) and r.get("chain_hash")]
    if not chained:
        return list(records), True
    pointed = {r.get("previous_observation_hash") for r in chained}
    tips = [r for r in chained if link_hash_for(r) not in pointed]
    if len(tips) != 1:
        return list(records), False  # fork: no single tip
    by_link: dict[str, dict[str, Any]] = {}
    for r in records:
        if not isinstance(r, dict):
            return list(records), False
        link = link_hash_for(r)
        if link:
            by_link[link] = r
    walk = [tips[0]]
    while True:
        prev_hash = walk[0].get("previous_observation_hash")
        if prev_hash == GENESIS_PREVIOUS or not prev_hash:
            break
        parent = by_link.get(str(prev_hash))
        if parent is None or any(parent is w for w in walk):
            return list(records), False  # gap or cycle
        walk.insert(0, parent)
    walk_ids = {id(r) for r in walk}
    legacy_ids = {id(r) for r in legacy}
    if walk_ids - legacy_ids != {id(r) for r in chained}:
        return list(records), False  # chained records outside the single chain
    anchor = walk[0]
    if anchor in chained:
        if anchor.get("previous_observation_hash") != GENESIS_PREVIOUS:
            return list(records), False
    else:
        # Legacy anchor: every legacy record the walk skipped must
        # predate the chained suffix (input/filename order).
        first_chained = next(i for i, r in enumerate(records) if r in chained)
        if any(
            i > first_chained
            for i, r in enumerate(records)
            if r in legacy and id(r) not in walk_ids
        ):
            return list(records), False
    ordered = [r for r in records if id(r) not in walk_ids and r in legacy]
    ordered += walk
    if len(ordered) != len(records):
        return list(records), False
    return ordered, True


def history_mac_parts(record: dict[str, Any]) -> tuple[str, str]:
    """What a record's history MAC covers: its chain hash and first detection.

    The chain hash already covers the chained fields and the link to the
    predecessor, so MACing it protects the whole chain.
    ``first_detected_at`` is outside the chain hash, so it is added here.
    """
    first = record.get("first_detected_at")
    return str(record.get("chain_hash") or ""), "" if first is None else str(first)


def handover_mac_parts(record: dict[str, Any]) -> tuple[str, str, str]:
    """What a handover MAC covers: the record's MACed parts and its new key_id."""
    return (*history_mac_parts(record), str(record.get("key_id") or ""))


def verify_keyed_history(
    records: list[dict[str, Any]], keys: dict[str, Any] | None = None
) -> dict[str, Any]:
    """VALID_KEYED / VALID_UNKEYED / BROKEN / UNKNOWN over chain-ordered records.

    ``keys`` maps key_id -> ``core.history_key.HistoryKey``: the current
    key and any retired ones. A MAC that fails, or a MAC with no key_id,
    is BROKEN. A key_id with no supplied key is UNKNOWN: it cannot be
    checked, so it is never VALID_KEYED.

    Rotation (B3b): keyed records form runs under one key. A run ends only
    at a handover record, which names the retired key in
    ``previous_key_id`` and carries ``handover_mac``, a MAC under that
    retired key. A record under any other key than the active one, and a
    handover that does not follow its retired key's run, are BROKEN: so a
    leaked retired key cannot extend history past its handover.
    ``active_key_id`` is the key of the newest keyed run.
    """
    from core.history_key import HANDOVER_DOMAIN, OBSERVATION_DOMAIN

    keys = keys or {}
    chain = verify_observation_chain(records)
    bad: list[int] = []
    unkeyed: list[int] = []
    unknown_keys: list[int] = []
    active: str | None = None
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        mac, key_id = record.get("history_mac"), record.get("key_id")
        retired = record.get("previous_key_id")
        if not mac:
            if retired or record.get("handover_mac"):
                bad.append(i)  # handover fields without a MAC of its own
            else:
                unkeyed.append(i)
            continue
        if not key_id:
            bad.append(i)
            continue
        key_id = str(key_id)
        if retired:
            if active is None or str(retired) != active or key_id == active:
                bad.append(i)  # handover that does not follow its key's run
            elif active not in keys:
                unknown_keys.append(i)
            elif not keys[active].verify(
                record.get("handover_mac"), HANDOVER_DOMAIN, *handover_mac_parts(record)
            ):
                bad.append(i)
        elif active is not None and key_id != active:
            bad.append(i)  # key switch without a handover, or a retired key reused
        if key_id not in keys:
            unknown_keys.append(i)
        elif not keys[key_id].verify(mac, OBSERVATION_DOMAIN, *history_mac_parts(record)):
            bad.append(i)
        active = key_id
    if chain["status"] == BROKEN or bad:
        status = BROKEN
    elif chain["status"] == UNKNOWN or unknown_keys:
        status = UNKNOWN
    elif unkeyed:
        status = VALID_UNKEYED
    else:
        status = VALID_KEYED
    return {
        "status": status,
        "bad_macs": sorted(set(bad)),
        "unkeyed": unkeyed,
        "unknown_keys": sorted(set(unknown_keys)),
        "breaks": chain["breaks"],
        "active_key_id": active,
    }
