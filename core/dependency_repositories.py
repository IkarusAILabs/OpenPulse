"""Observe the GitHub repositories your dependencies name (v0.21.0 item W3).

v0.20.0 keeps a verifiable history of a GitHub repository
(``core.observations.repository``) and turns a license change, an archive
and a move to a new owner between two records into findings, but only for
repositories someone names (``observe-github``, the catalog). This module
does it for a project's own dependencies:

1. For each npm and PyPI dependency, the repository its registry metadata
   claims (npm ``repository``, PyPI ``project_urls``;
   ``core.repository_moved.claimed_repository``).
2. Each distinct repository is observed once and appended to its history in
   the store, under the history key. A first observation is a baseline:
   nothing can have changed yet, so the snapshot rules apply instead
   (``analyze_github_meta``): a repository that is already archived, or
   that answers under another owner than the one claimed, is reported once.
3. A change between two comparable records becomes a finding
   (``analyze_repository_changes``), a GitHub license change is checked
   against the registry's license (C5), and each finding is bridged into
   an event for every dependency that names the repository
   (``analyzers.registry_events``).

The claim is the publisher's own statement and is not verified here
(``repository_linkage`` is the trust check that does); the event says so.
Nothing is dropped silently: packages with no claimed repository, registry
or GitHub failures, refused histories and repositories past the cap are
counted, and the failures named. Never raises.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date
from typing import Any

#: Repositories observed per run (one GitHub request each).
MAX_REPOSITORIES = 300
#: Failures named one by one; the rest are counted.
MAX_NAMED = 20

#: Snapshot findings reported on a repository's first observation.
_BASELINE_EVENT_TYPES = ("PROJECT_ARCHIVED", "OWNERSHIP_CHANGE")

FetchJson = Callable[[str], tuple[int, Any]]
FetchMeta = Callable[[str], dict[str, Any]]


def default_fetch_meta(repo: str) -> dict[str, Any]:
    """GitHub's repository document, parsed (``collectors.github``). Token from the environment."""
    from collectors.github.collector import GitHubCollector

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return GitHubCollector({repo: repo}, token=token).fetch_repo_meta(repo)


def _claims(
    deps: list[dict[str, Any]], fetch_json: FetchJson | None
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    """({repo key: {"repo", "indexes", "packages"}}, counts) for the deps' claimed repositories."""
    from core.agent_tools import _refused_entry
    from core.registry_existence import ecosystem_of
    from core.repository_moved import claimed_repository

    counts = {"packages": 0, "unsupported": 0, "no_repository": 0, "registry_unanswered": 0}
    answers: dict[tuple[str, str, str], tuple[str | None, str | None]] = {}
    claims: dict[str, dict[str, Any]] = {}
    for index, dep in enumerate(deps):
        if dep.get("kind") != "package":
            continue
        ecosystem = ecosystem_of(dep.get("ecosystem"))
        if ecosystem is None or _refused_entry(dep) is not None:
            counts["unsupported"] += 1
            continue
        name = str(dep["package"])
        version = str(dep["version"]) if dep.get("version") else None
        key = (ecosystem, name, version or "")
        if key not in answers:
            counts["packages"] += 1
            why, claimed, _ = claimed_repository(ecosystem, name, version, fetch_json)
            answers[key] = (why, claimed)
            if why == "no_repository":
                counts["no_repository"] += 1
            elif why is not None:
                counts["registry_unanswered"] += 1
        why, claimed = answers[key]
        if why is not None or not claimed:
            continue
        entry = claims.setdefault(claimed.lower(), {"repo": claimed, "indexes": [], "packages": []})
        entry["indexes"].append(index)
        if (ecosystem, name) not in entry["packages"]:
            entry["packages"].append((ecosystem, name))
    return claims, counts


def _registry_licenses(
    packages: list[tuple[str, str]], fetch_json: FetchJson | None
) -> list[dict[str, Any]]:
    """{"purl", "license"} the registry declares for each package's latest release (C5)."""
    from core import release_license

    declared = []
    for ecosystem, name in packages:
        result = release_license.check(ecosystem, name, fetch_json=fetch_json)
        latest = result.get("latest") or {}
        if result.get("status") == release_license.COMPARED and latest.get("license"):
            declared.append({"purl": result["purl"], "license": latest["license"]})
    return declared


def observe_dependency_repositories(
    deps: list[dict[str, Any]],
    *,
    store_root: str,
    history_key: Any = None,
    previous_keys: tuple[Any, ...] = (),
    fetch_json: FetchJson | None = None,
    fetch_meta: FetchMeta | None = None,
    max_repositories: int = MAX_REPOSITORIES,
    today: date | None = None,
) -> dict[str, Any]:
    """Observe each dependency's claimed repository; events for what changed.

    Returns ``events`` ({dependency index: [OSSEvent]}), ``summary`` (counts)
    and ``failures`` (up to ``MAX_NAMED`` ``{"repository", "reason"}``; the
    reasons are OpenPulse's own messages).
    """
    from analyzers.change_analyst import (
        analyze_github_meta,
        analyze_repository_changes,
        corroborate_repository_license,
    )
    from analyzers.registry_events import repository_finding_to_event
    from core.agent_tools import _trust
    from core.observations.repository import observe_github_repository
    from core.release_license import _purl

    fetch_meta = fetch_meta or default_fetch_meta
    claims, counts = _claims(deps, fetch_json)
    summary = {
        **counts,
        "repositories": len(claims),
        "observed": 0,
        "baselines": 0,
        "changes": 0,
        "findings": 0,
        "failed": 0,
        "not_observed": max(len(claims) - max_repositories, 0),
    }
    events: dict[int, list[Any]] = {}
    failures: list[dict[str, str]] = []
    for key in sorted(claims)[:max_repositories]:
        claim = claims[key]
        repo = claim["repo"]
        meta: dict[str, Any] = {}
        try:
            meta = fetch_meta(repo)
            result = observe_github_repository(
                repo,
                meta,
                store_root=store_root,
                history_key=history_key,
                previous_keys=previous_keys,
            )
        except Exception:  # a collector that raises is a failed observation
            result = {"error": {"safe_message": "the repository could not be read"}}
        if result.get("error") is not None:
            summary["failed"] += 1
            reason = str(result["error"].get("safe_message") or "not observed")
            failures.append({"repository": repo, "reason": reason})
            continue
        summary["observed"] += 1
        changes = result.get("changes") or []
        summary["changes"] += len(changes)
        if result.get("history_status") == "GENESIS":
            # Nothing to compare with yet: what the repository already is.
            summary["baselines"] += 1
            findings = [
                f
                for f in analyze_github_meta([meta], today=today)
                if f["event_type"] in _BASELINE_EVENT_TYPES
            ]
        else:
            findings = analyze_repository_changes(changes, today=today)
        if any(f["event_type"] == "LICENSE_CHANGE" for f in findings):
            declared = _registry_licenses(claim["packages"], fetch_json)
            findings = [corroborate_repository_license(f, declared) for f in findings]
        summary["findings"] += len(findings)
        for index in claim["indexes"]:
            dep = deps[index]
            purl = _purl(
                "npm" if str(dep.get("ecosystem")).lower() == "npm" else "PyPI",
                str(dep["package"]),
            )
            slug = str(_trust(dep)["slug"])
            for finding in findings:
                events.setdefault(index, []).append(
                    repository_finding_to_event(finding, purl, slug, repo, today=today)
                )
    return {"events": events, "summary": summary, "failures": failures[:MAX_NAMED]}


__all__ = ["MAX_REPOSITORIES", "default_fetch_meta", "observe_dependency_repositories"]
