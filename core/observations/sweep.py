"""Catalog sweep — distribution discovery across every known image.

`sweep_catalog` takes an injected `probe_fn(namespace, repo)` so the
whole flow is testable offline; the CLI passes the live Docker Hub
probe. Each image, under a per-repository lock: load history, verify
its integrity, probe → chain-linked observation → save → diff against
verified history → distribution findings.

Trust rules (never silently accept a broken chain):

- no history → genesis baseline, no findings;
- BROKEN history → no diff, no save, integrity error recorded;
- legacy (unchained) history → diffable, new saves upgrade the chain;
- a diff is a *candidate change*, not intelligence: findings carry
  observation evidence and an explicit evidence strength, and the
  report/impact layers decide eligibility downstream.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from analyzers.change_analyst import analyze_diffs
from analyzers.event_correlation import aggregate_distribution, split_moves
from collectors.errors import as_error, safe_message
from core.history_key import keyring
from core.observations.chain import (
    BROKEN,
    GENESIS_PREVIOUS,
    link_hash_for,
    order_history,
    verify_keyed_history,
)
from core.observations.registry import (
    RegistryObservation,
    diff_observations,
    to_observation,
    verify_registry_history,
)
from core.observations.store import (
    load_all,
    read_tip,
    repo_dir,
    repo_lock,
    save_observation,
    write_tip,
)
from core.risk.match import split_image_ref

#: Cap on history rescan for first-detection (one file per run keeps
#: real histories small; the cap bounds adversarial directory stuffing).
_HISTORY_SCAN_LIMIT = 500


def sweep_targets(catalog: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """(slug, namespace, repo) for every probeable catalog image.

    Only registry/namespace/repo triples probe cleanly; bare namespace
    refs are skipped (they name a catalogue, not an image).
    """
    targets = []
    for entry in catalog:
        if not isinstance(entry, dict):
            continue
        for image in entry.get("docker_images") or []:
            registry, namespace, name = split_image_ref(str(image))
            # Catalog convention: `<host>/<name>` with nothing after it
            # names a namespace (catalogue), not an image to probe.
            segments = str(image).split("://")[-1].split("/")
            bare = len(segments) == 2 and ("." in segments[0] or ":" in segments[0])
            if "/" in str(image) and not bare and namespace and name:
                targets.append((str(entry.get("slug", "")), namespace, name))
    return targets


#: Inverse change types: the occurrence that closes an episode, so a
#: later recurrence starts a NEW episode (a re-appeared tag is a new
#: event, not the original appearance). Digest moves have no inverse:
#: every new digest value is a distinct fact, earliest occurrence wins.
_INVERSE_CHANGE = {
    "tag_appeared": "tag_disappeared",
    "tag_disappeared": "tag_appeared",
    "repo_missing": "repo_restored",
    "repo_restored": "repo_missing",
}


def first_detected_at_for(
    change_key: tuple[str | None, str | None],
    observations: list[RegistryObservation],
) -> datetime | None:
    """First trustworthy detection of one change key in a history scan.

    Oldest adjacent pair producing (type, tag) within the current
    episode wins; its current observation timestamp is the first
    detection. An inverse change for the same tag closes the episode.
    Any content-BROKEN record in the walk poisons the answer -> None
    (never estimate).
    """
    for obs in observations:
        if obs.verify_record() == BROKEN:
            return None
    episode_start: datetime | None = None
    inverse = _INVERSE_CHANGE.get(str(change_key[0]))
    previous: RegistryObservation | None = None
    for obs in observations:
        if previous is not None:
            for change in diff_observations(previous, obs):
                key = (change.type, change.tag)
                if key == change_key:
                    if episode_start is None:
                        episode_start = obs.observed_at
                elif change.tag == change_key[1] and change.type == inverse:
                    episode_start = None
        previous = obs
    return episode_start


def observe_repository(
    registry: str,
    namespace: str,
    repository: str,
    probe: dict[str, Any],
    store_root: str = ".openpulse/observations",
    observed_at: datetime | None = None,
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
) -> dict[str, Any]:
    """One locked load-verify-observe-save-diff cycle. Never raises.

    Returns {observation, history_status, changes, saved_path, error},
    plus ``history_integrity`` after a successful save.
    ``history_status`` is VALID | BROKEN | UNKNOWN | GENESIS (no
    history). BROKEN history yields no changes and no save — the
    corrupt predecessor stays on disk as evidence of tampering.

    ``history_key`` (a ``core.history_key.HistoryKey``) MACs the new
    record (B3). A history that already holds MACs is never appended to
    without its key: that would end its keyed run (KEY_REQUIRED,
    KEY_MISMATCH). ``history_integrity`` is VALID_KEYED, VALID_UNKEYED,
    BROKEN or UNKNOWN for the whole history including the new record.

    ``previous_keys`` are retired, verify-only keys (B3b). When the
    history's newest keyed run is under one of them, the new record is
    a handover to ``history_key``, MACed by both keys.
    """
    now = observed_at or datetime.now(timezone.utc)
    try:
        with repo_lock(store_root, registry, namespace, repository):
            result = _observe_locked(
                registry, namespace, repository, probe, store_root, now, history_key, previous_keys
            )
            if result["error"] is None:
                result["history_integrity"] = _history_integrity(
                    registry, namespace, repository, store_root, history_key, previous_keys
                )
            return result
    except TimeoutError as exc:
        return {
            "observation": None,
            "history_status": "LOCKED",
            "changes": [],
            "saved_path": None,
            "error": {
                "collector": "registries",
                "error": True,
                "category": "contention",
                "retryable": True,
                "status_code": None,
                "safe_message": safe_message(exc),
                "namespace": namespace,
                "repo": repository,
            },
        }


def _history_integrity(
    registry: str,
    namespace: str,
    repository: str,
    store_root: str,
    history_key: Any,
    previous_keys: tuple[Any, ...] = (),
) -> str:
    """Keyed integrity of one repository's stored history (B3)."""
    ordered, chain_ok = order_history(load_all(registry, namespace, repository, root=store_root))
    if not chain_ok or verify_registry_history(ordered)["status"] == BROKEN:
        return BROKEN
    return str(verify_keyed_history(ordered, keyring(history_key, previous_keys))["status"])


def _adopted_at(
    ordered: list[dict[str, Any]],
    current: Any,
    history_key: Any,
    previous_keys: tuple[Any, ...] = (),
) -> datetime | None:
    """When a keyed history was adopted (B3c), or None when unkeyed or keyed from genesis."""
    if history_key is None:
        return None
    records = [*ordered, current.model_dump(mode="json")]
    adopted = verify_keyed_history(records, keyring(history_key, previous_keys))["adopted_at"]
    if adopted is None:
        return None
    moment = datetime.fromisoformat(str(adopted).replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _keyed_refusal(
    ordered: list[dict[str, Any]],
    history_key: Any,
    namespace: str,
    repository: str,
    previous_keys: tuple[Any, ...] = (),
) -> tuple[dict[str, Any] | None, Any]:
    """(refusal, retired key to hand over from) for appending to this history.

    Refuses a keyed history without a key, a history whose newest keyed
    run is under a key that is neither current nor supplied as retired,
    and a history whose MACs do not verify.
    """
    keyed = [r for r in ordered if r.get("history_mac")]
    if not keyed:
        return None, None
    key_ids = sorted({str(r.get("key_id")) for r in keyed})
    ring = keyring(history_key, previous_keys)
    verdict = verify_keyed_history(ordered, ring)
    active = verdict["active_key_id"]
    retired = None
    if history_key is None:
        status = "KEY_REQUIRED"
        detail = (
            f"observation history for {namespace}/{repository} is keyed "
            f"({', '.join(key_ids)}); set OPENPULSE_HISTORY_KEY or pass "
            "--history-key-file to append to it"
        )
    elif active not in ring:
        status = "KEY_MISMATCH"
        detail = (
            f"observation history for {namespace}/{repository} is keyed with "
            f"{active}, which is neither the current key ({history_key.key_id}) "
            "nor a previous key; refusing to append"
        )
    elif verdict["status"] == BROKEN:
        status = BROKEN
        detail = (
            f"observation history for {namespace}/{repository} has a record whose "
            "history MAC or key handover does not verify; refusing to diff or append"
        )
    else:
        if active != history_key.key_id:
            retired = ring[active]
        return None, retired
    return {
        "observation": None,
        "history_status": status,
        "changes": [],
        "saved_path": None,
        "error": {
            "collector": "registries",
            "error": True,
            "category": "integrity",
            "retryable": False,
            "status_code": None,
            "safe_message": detail,
            "namespace": namespace,
            "repo": repository,
            "integrity": BROKEN if status == BROKEN else "UNKNOWN",
        },
    }, None


def _observe_locked(
    registry: str,
    namespace: str,
    repository: str,
    probe: dict[str, Any],
    store_root: str,
    now: datetime,
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
) -> dict[str, Any]:
    if not isinstance(probe, dict):
        return {
            "observation": None,
            "history_status": "INVALID_PROBE",
            "changes": [],
            "saved_path": None,
            "error": {
                "collector": "registries",
                "error": True,
                "category": "parse",
                "retryable": False,
                "status_code": None,
                "safe_message": f"probe for {namespace}/{repository} is not a mapping",
                "namespace": namespace,
                "repo": repository,
            },
        }
    history = load_all(registry, namespace, repository, root=store_root)
    directory = repo_dir(store_root, registry, namespace, repository)
    if not history:
        stale_tip = read_tip(directory)
        if stale_tip and stale_tip.get("tip"):
            # Data files are gone but the tip pointer survived: a wipe
            # or rollback, not a first run. Refuse a silent re-baseline.
            return {
                "observation": None,
                "history_status": "ROLLBACK",
                "changes": [],
                "saved_path": None,
                "error": {
                    "collector": "registries",
                    "error": True,
                    "category": "integrity",
                    "retryable": False,
                    "status_code": None,
                    "safe_message": (
                        f"observation history for {namespace}/{repository} is "
                        "missing but a tip pointer survives; refusing a "
                        "silent re-baseline"
                    ),
                    "namespace": namespace,
                    "repo": repository,
                    "integrity": BROKEN,
                },
            }
        status = "GENESIS"
        ordered: list[dict[str, Any]] = []
    else:
        # Chain order, never filename order: colliding timestamps must
        # not reorder linked history (concurrent writers).
        ordered, chain_ok = order_history(history)
        if not chain_ok:
            return {
                "observation": None,
                "history_status": "BROKEN",
                "changes": [],
                "saved_path": None,
                "error": {
                    "collector": "registries",
                    "error": True,
                    "category": "integrity",
                    "retryable": False,
                    "status_code": None,
                    "safe_message": (
                        f"observation history for {namespace}/{repository} is "
                        "forked or gapped; refusing to diff or append"
                    ),
                    "namespace": namespace,
                    "repo": repository,
                    "integrity": BROKEN,
                },
            }
        status = str(verify_registry_history(ordered)["status"])
    if status != BROKEN and ordered:
        # Rollback tripwire: the tip pointer must agree with the
        # chain tip. A wiped newest file without a tip update refuses
        # here; a missing tip is adopted (pre-upgrade histories).
        tip = read_tip(directory)
        tip_hash = tip.get("tip") if tip else None
        actual_tip = link_hash_for(ordered[-1])
        if tip_hash and tip_hash != actual_tip:
            status = "ROLLBACK"
    if status in (BROKEN, "ROLLBACK"):
        if status == "ROLLBACK":
            detail = (
                f"observation history for {namespace}/{repository} does not "
                "reach the recorded tip (newest file missing or rolled back); "
                "refusing to diff or append"
            )
        else:
            detail = (
                f"observation history for {namespace}/{repository} failed "
                "integrity verification; refusing to diff or append"
            )
        return {
            "observation": None,
            "history_status": status,
            "changes": [],
            "saved_path": None,
            "error": {
                "collector": "registries",
                "error": True,
                "category": "integrity",
                "retryable": False,
                "status_code": None,
                "safe_message": detail,
                "namespace": namespace,
                "repo": repository,
                "integrity": BROKEN,
            },
        }
    refusal, retired = _keyed_refusal(ordered, history_key, namespace, repository, previous_keys)
    if refusal is not None:
        return refusal
    try:
        previous = RegistryObservation(**ordered[-1]) if ordered else None
    except Exception as exc:
        return {
            "observation": None,
            "history_status": "BROKEN",
            "changes": [],
            "saved_path": None,
            "error": {
                **as_error("registries", exc, namespace=namespace, repo=repository),
                "integrity": BROKEN,
            },
        }
    try:
        current = to_observation({**probe, "registry": registry}, observed_at=now)
        current = current.link(ordered[-1] if ordered else None)
        if history_key is not None:
            current = current.keyed(history_key, retired=retired)
    except Exception as exc:
        return {
            "observation": None,
            "history_status": status,
            "changes": [],
            "saved_path": None,
            "error": as_error("registries", exc, namespace=namespace, repo=repository),
        }
    if previous is None:
        baseline_status = "GENESIS"
        rebased = False
    elif previous.parser_version != current.parser_version:
        # Probe semantics changed under a stored history (e.g. windowed
        # tag samples vs full tag sets): the bytes chain continues, but
        # diffing across incomparable semantics would manufacture
        # changes. Re-baseline explicitly instead.
        baseline_status = "REBASELINED"
        rebased = True
    else:
        baseline_status = ""
        rebased = False
    if previous is None or rebased:
        saved = save_observation(current.model_dump(mode="json"), root=store_root)
        write_tip(
            repo_dir(store_root, registry, namespace, repository),
            str(current.chain_hash or current.content_hash),
        )
        return {
            "observation": current.model_dump(mode="json"),
            "history_status": baseline_status,
            "changes": [],
            "saved_path": str(saved),
            "error": None,
        }
    models: list[RegistryObservation] = []
    for record in ordered[-_HISTORY_SCAN_LIMIT:]:
        try:
            models.append(RegistryObservation(**record))
        except Exception:
            break  # unreadable middle history: only verified prefix counts
    else:
        models.append(current)
        changes = diff_observations(previous, current)
        adopted = _adopted_at(ordered, current, history_key, previous_keys)
        stamped = []
        for change in changes:
            first = first_detected_at_for((change.type, change.tag), [*models])
            first = first or current.observed_at
            if adopted is not None and first < adopted:
                first = adopted  # keyed history proves nothing before adoption (B3c)
            stamped.append(change.model_copy(update={"first_detected_at": first}))
        saved = save_observation(current.model_dump(mode="json"), root=store_root)
        write_tip(
            repo_dir(store_root, registry, namespace, repository),
            str(current.chain_hash or current.content_hash),
        )
        return {
            "observation": current.model_dump(mode="json"),
            "history_status": status,
            "changes": [c.model_dump(mode="json") for c in stamped],
            "saved_path": str(saved),
            "error": None,
        }
    # History contained an unreadable record mid-walk: treat the usable
    # prefix as untrusted for first-detection and diff against previous.
    changes = diff_observations(previous, current)
    saved = save_observation(current.model_dump(mode="json"), root=store_root)
    write_tip(
        repo_dir(store_root, registry, namespace, repository),
        str(current.chain_hash or current.content_hash),
    )
    return {
        "observation": current.model_dump(mode="json"),
        "history_status": status,
        "changes": [c.model_dump(mode="json") for c in changes],
        "saved_path": str(saved),
        "error": None,
    }


def sweep_catalog(
    catalog: list[dict[str, Any]],
    probe_fn: Callable[[str, str], dict[str, Any]],
    store_root: str = ".openpulse/observations",
    slugs: list[str] | None = None,
    observed_at: datetime | None = None,
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
) -> dict[str, Any]:
    """Probe, persist, diff, and analyse. Returns observations/changes/findings/errors."""
    now = observed_at or datetime.now(timezone.utc)
    observations: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for slug, namespace, repo in sweep_targets(catalog):
        if slugs and slug not in slugs:
            continue
        try:
            probe = probe_fn(namespace, repo)
        except Exception as exc:  # custom probes may raise; record, never crash
            errors.append(
                {**as_error("registries", exc), "namespace": namespace, "repo": repo, "slug": slug}
            )
            continue
        if isinstance(probe, dict) and probe.get("error"):
            errors.append({**probe, "slug": slug})
            continue
        result = observe_repository(
            "docker.io",
            namespace,
            repo,
            probe if isinstance(probe, dict) else {},
            store_root=store_root,
            observed_at=now,
            history_key=history_key,
            previous_keys=previous_keys,
        )
        if result["error"] is not None:
            errors.append({**result["error"], "slug": slug})
            continue
        if result["observation"] is not None:
            observations.append(result["observation"])
        changes += result["changes"]
    moves, remaining = split_moves(changes)
    findings = aggregate_distribution(analyze_diffs(remaining)) + moves
    return {
        "observations": observations,
        "changes": changes,
        "findings": findings,
        "errors": errors,
    }


__all__ = [
    "GENESIS_PREVIOUS",
    "first_detected_at_for",
    "link_hash_for",
    "observe_repository",
    "sweep_catalog",
    "sweep_targets",
]
