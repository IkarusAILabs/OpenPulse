"""GitHub repository observations: a verifiable history of repository facts (v0.20.0 C1).

Repository rules used to judge only the current snapshot: an archived
flag, an owner that differs from the queried path. A snapshot cannot say
that a license *changed*, or when a repository was *first seen* archived.
This module keeps a history instead, with the same guarantees as the
container-registry history in ``core.observations.sweep``:

- one hash-chained, atomically written file per observation, under the
  same store root (``github.com/<owner>/<name>/``), so anchors cover it;
- a per-repository lock across load-verify-save;
- a tip pointer, with ROLLBACK, ROLLBACK_SUSPECTED, DOWNGRADE and BROKEN
  histories refused until an explicit, reasoned re-baseline;
- optional history-key MACs (B3) with key handover (B3b).

What is recorded: the queried path, the path GitHub answered with
(``full_name``), ``archived``, GitHub's license id, ``pushed_at``, the
default branch, and ``missing`` for a 404 (deleted or made private).
Any other failure records nothing: a rate limit is not a fact about the
repository. Paths are stored lower-case, because GitHub's are
case-insensitive; ``full_name`` keeps GitHub's spelling.

This module records and verifies. Reading changes out of the history
(``LICENSE_CHANGE`` and the archive and ownership transitions) is C2.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from collectors.errors import safe_message
from core.evidence.provenance import hash_content
from core.observations.base import GitHubRepositoryObservation
from core.observations.chain import (
    BROKEN,
    UNKNOWN,
    VALID,
    verify_observation_chain,
)
from core.observations.store import load_all, repo_dir, repo_lock, save_observation, write_tip
from core.observations.sweep import (
    REFUSED_HISTORY,
    _assess_history,
    _history_integrity,
    _integrity_refusal,
    _keyed_refusal,
    _rebaseline,
)

REGISTRY = "github.com"
COLLECTOR = "github"

#: One path segment of a GitHub owner or repository name.
_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")

#: Longest string recorded for each free-text fact; a hostile or corrupt
#: response must not grow the history without bound.
_MAX_LENGTH = {"license": 64, "pushed_at": 64, "default_branch": 255}


def split_repo(repo: str) -> tuple[str, str]:
    """``owner/name`` -> (owner, name), lower-case; ValueError when malformed."""
    parts = str(repo or "").strip().split("/")
    if len(parts) != 2 or not all(_SEGMENT.match(p) and p.strip(".") for p in parts):
        raise ValueError(f"not a GitHub repository path (owner/name): {repo!r}")
    return parts[0].lower(), parts[1].lower()


def _text(meta: dict[str, Any], field: str) -> str | None:
    value = meta.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"repository {field} must be text")
    if len(value) > _MAX_LENGTH[field] or not value.isprintable():
        raise ValueError(f"repository {field} is not one short line of text")
    return value


def to_repository_observation(
    meta: dict[str, Any], repo: str, observed_at: datetime | None = None
) -> GitHubRepositoryObservation:
    """A sealed observation from ``GitHubCollector.fetch_repo_meta`` output.

    ``repo`` is the path that was queried. A 404 error becomes a
    ``missing`` observation; any other error, a skip, or metadata for a
    different path raises ValueError, and nothing is recorded.
    """
    namespace, repository = split_repo(repo)
    when = observed_at or datetime.now(timezone.utc)
    base = {
        "namespace": namespace,
        "repository": repository,
        "observed_at": when,
    }
    if not isinstance(meta, dict):
        raise ValueError("repository metadata is not a mapping")
    if meta.get("error"):
        if meta.get("status_code") == 404:
            return GitHubRepositoryObservation(**base, missing=True).seal()
        raise ValueError(
            f"GitHub did not describe {repo}: {meta.get('safe_message') or 'error'}"
            f" (status {meta.get('status_code')}); nothing recorded"
        )
    if meta.get("skipped"):
        raise ValueError(f"GitHub metadata was skipped for {repo}: {meta['skipped']}")
    if meta.get("kind") != "repo_meta":
        raise ValueError("not GitHub repository metadata")
    if split_repo(str(meta.get("repo") or "")) != (namespace, repository):
        raise ValueError(f"metadata is for {meta.get('repo')!r}, not {repo!r}")
    full_name = meta.get("full_name")
    if full_name is not None:
        split_repo(str(full_name))  # validated; GitHub's spelling is kept
    archived = meta.get("archived")
    if not isinstance(archived, bool):
        raise ValueError("repository archived flag must be true or false")
    return GitHubRepositoryObservation(
        **base,
        full_name=full_name,
        archived=archived,
        license=_text(meta, "license"),
        pushed_at=_text(meta, "pushed_at"),
        default_branch=_text(meta, "default_branch"),
    ).seal()


def _raw_body(record: dict[str, Any]) -> dict[str, Any]:
    """Content-covered facts straight from the stored mapping (no coercion)."""
    return {
        field: record.get(field)
        for field in (
            "registry",
            "namespace",
            "repository",
            "full_name",
            "archived",
            "missing",
            "license",
            "pushed_at",
            "default_branch",
        )
    }


def _content_ok(record: Any) -> bool:
    if not isinstance(record, dict) or record.get("source") != COLLECTOR:
        return False
    try:
        return record.get("content_hash") == hash_content(_raw_body(record))
    except Exception:
        return False


def verify_repository_history(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Content and chain verification over oldest->newest stored records.

    The same contract as ``verify_registry_history``: records must be in
    chain order; a record whose facts do not match its content hash, or
    that is not a GitHub repository record, is BROKEN.
    """
    content_breaks = [i for i, record in enumerate(records) if not _content_ok(record)]
    chain = verify_observation_chain(records)
    if content_breaks or chain["status"] == BROKEN:
        return {
            "status": BROKEN,
            "breaks": sorted(set(content_breaks) | set(chain["breaks"])),
            "unknowns": chain["unknowns"],
        }
    if chain["status"] == UNKNOWN:
        return {"status": UNKNOWN, "breaks": [], "unknowns": chain["unknowns"]}
    return {"status": VALID, "breaks": [], "unknowns": []}


def _failure(status: str, category: str, message: str, repo: str, **extra: Any) -> dict[str, Any]:
    return {
        "observation": None,
        "previous": None,
        "history_status": status,
        "saved_path": None,
        "error": {
            "collector": COLLECTOR,
            "error": True,
            "category": category,
            "retryable": category == "contention",
            "status_code": None,
            "safe_message": message,
            "repo": repo,
            **extra,
        },
    }


def observe_github_repository(
    repo: str,
    meta: dict[str, Any],
    store_root: str = ".openpulse/observations",
    observed_at: datetime | None = None,
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
    rebaseline_reason: str | None = None,
) -> dict[str, Any]:
    """One locked load-verify-observe-save cycle for a GitHub repository. Never raises.

    Returns {observation, previous, history_status, saved_path, error}, plus
    ``history_integrity`` (VALID_KEYED, VALID_UNKEYED, BROKEN or UNKNOWN)
    after a save. ``history_status`` is GENESIS for a first observation,
    REBASELINED after an explicit re-baseline or a parser change, else the
    stored history's status. ``previous`` is the record this one follows,
    and only when the two are comparable (never across a genesis or a
    re-baseline): it is what C2 diffs against.

    Refusals match the registry history's: BROKEN, ROLLBACK,
    ROLLBACK_SUSPECTED and DOWNGRADE need ``rebaseline_reason``; a keyed
    history needs its key.
    """
    now = observed_at or datetime.now(timezone.utc)
    try:
        namespace, repository = split_repo(repo)
    except ValueError as exc:
        return _failure("INVALID_REPOSITORY", "parse", str(exc), str(repo))
    try:
        with repo_lock(store_root, REGISTRY, namespace, repository):
            result = _observe_locked(
                repo,
                namespace,
                repository,
                meta,
                store_root,
                now,
                history_key,
                previous_keys,
                rebaseline_reason,
            )
            if result["error"] is None:
                result["history_integrity"] = _history_integrity(
                    REGISTRY,
                    namespace,
                    repository,
                    store_root,
                    history_key,
                    previous_keys,
                    verify=verify_repository_history,
                )
            return result
    except TimeoutError as exc:
        return _failure("LOCKED", "contention", safe_message(exc), repo)


def _observe_locked(
    repo: str,
    namespace: str,
    repository: str,
    meta: dict[str, Any],
    store_root: str,
    now: datetime,
    history_key: Any,
    previous_keys: tuple[Any, ...],
    rebaseline_reason: str | None,
) -> dict[str, Any]:
    try:
        current = to_repository_observation(meta, repo, observed_at=now)
    except ValueError as exc:
        return _failure("NOT_OBSERVED", "parse", str(exc), repo)

    directory = repo_dir(store_root, REGISTRY, namespace, repository)
    history = load_all(REGISTRY, namespace, repository, root=store_root)
    ordered, status, detail = _assess_history(
        history, directory, namespace, repository, verify=verify_repository_history
    )
    rebaselined = False
    if status in REFUSED_HISTORY:
        if not rebaseline_reason:
            refusal = _integrity_refusal(
                status,
                detail,
                namespace,
                repository,
                collector=COLLECTOR,
                command=f"openpulse observe-github --repo {namespace}/{repository}",
            )
            return {**refusal, "previous": None}
        ordered = _rebaseline(directory, ordered, status, rebaseline_reason, now, history_key)
        rebaselined = True
    refusal, retired = _keyed_refusal(
        ordered, history_key, namespace, repository, previous_keys, collector=COLLECTOR
    )
    if refusal is not None:
        return {**refusal, "previous": None}

    previous = None
    if ordered:
        try:
            previous = GitHubRepositoryObservation(**ordered[-1])
        except Exception as exc:
            message = f"the newest stored observation of {repo} is unreadable: {safe_message(exc)}"
            return _failure(BROKEN, "integrity", message, repo, integrity=BROKEN)
    try:
        current = current.link(ordered[-1] if ordered else None)
        if history_key is not None:
            current = current.keyed(history_key, retired=retired)
    except Exception as exc:
        return _failure(status, "parse", safe_message(exc), repo)

    if rebaselined:
        outcome = "REBASELINED"
    elif previous is None:
        outcome = "GENESIS"
    elif previous.parser_version != current.parser_version:
        # Different parsing semantics: the chain continues, comparisons do not.
        outcome = "REBASELINED"
    else:
        outcome = status
    record = current.model_dump(mode="json")
    saved = save_observation(record, root=store_root)
    write_tip(directory, str(current.chain_hash or current.content_hash))
    comparable = previous is not None and outcome not in ("GENESIS", "REBASELINED")
    return {
        "observation": record,
        "previous": previous.model_dump(mode="json") if comparable and previous else None,
        "history_status": outcome,
        "saved_path": str(saved),
        "error": None,
    }


__all__ = [
    "COLLECTOR",
    "REGISTRY",
    "observe_github_repository",
    "split_repo",
    "to_repository_observation",
    "verify_repository_history",
]
