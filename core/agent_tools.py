"""Dependency intelligence for AI coding agents (the MCP server's engine).

The functions here are what `openpulse mcp` exposes as tools. They are
plain, SDK-free functions over the existing pipeline, so they are tested
without the optional MCP SDK and reusable by any other agent integration:

    live collectors (endoflife.date, OSV, GitHub repo metadata)
      -> change_analyst lifecycle findings -> finding_to_event
      + curated events (the same set the GitHub Action bundles)
      -> check_dependency (one verdict engine, never a second one)

Principles carried over unchanged:

- Evidence, not a decision: every answer says what was established, from
  which sources, and what was not. The agent (and its human) decides.
- UNKNOWN stays UNKNOWN: an unreachable source or an uncatalogued package
  is reported as such, never as "no problems".
- Read-only and bounded: lookups are cached per process, file inputs go
  through the bounded readers, and dependency counts are capped.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from datetime import date
from typing import Any

from core.resources import data_path

#: Curated events bundled with OpenPulse - the same default set as the
#: GitHub Action (`action.yml`), so every channel answers alike.
CURATED_EVENTS = ("bitnami", "spark-mainline-empty", "django-eol", "itext-license")

#: Lifecycle findings bridged into events (the analyst types whose bridge
#: is pinned by the golden suite). Repository health stays context.
_BRIDGED_EVENT_TYPES = ("EOL", "EOS")

#: Bounds for one file check: an agent call must stay fast and polite to
#: the public APIs it queries.
MAX_FILE_DEPENDENCIES = 300
MAX_LIVE_PROJECTS = 40
_CACHE_TTL_SECONDS = 3600.0

NOTE = (
    "OpenPulse evidence, not a decision: verdicts state what the cited sources "
    "establish for this exact dependency; UNKNOWN means not established, never safe."
)

Bundle = dict[str, list[dict[str, Any]]]
Fetcher = Callable[[str], Bundle]


def curated_events() -> list[Any]:
    """The bundled curated events as validated OSSEvents."""
    from core.schema.models import OSSEvent

    events = []
    for name in CURATED_EVENTS:
        with open(data_path("fixtures", name, "event.json"), encoding="utf-8") as f:
            events.append(OSSEvent(**json.load(f)))
    return events


def live_fetcher(timeout: float = 10.0) -> Fetcher:
    """Real collectors for one project slug; every source degrades to an
    error/skipped record, never an exception (collector contract)."""
    from collectors.endoflife.collector import EndoflifeCollector
    from collectors.github.collector import GitHubCollector
    from collectors.osv.collector import OSVCollector
    from core.entities.catalog import endoflife_map, load_catalog, osv_map

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo_map = {e["slug"]: e["github"] for e in load_catalog() if e.get("github")}
    endoflife = EndoflifeCollector(endoflife_map(), timeout=timeout)
    osv = OSVCollector(osv_map(), timeout=timeout)
    github = GitHubCollector(repo_map, timeout=timeout, token=token)

    def fetch(slug: str) -> Bundle:
        return {
            "endoflife": endoflife.collect(slug),
            "osv": osv.collect(slug),
            "github_meta": [github.fetch_repo_meta(slug)],
        }

    return fetch


class Lookups:
    """Per-process cache of live bundles (an agent asks about the same
    projects repeatedly; the public APIs should not be hammered)."""

    def __init__(self, fetch: Fetcher | None = None, ttl: float = _CACHE_TTL_SECONDS):
        self._fetch = fetch
        self._ttl = ttl
        self._cache: dict[str, tuple[float, Bundle]] = {}

    def bundle(self, slug: str) -> Bundle:
        hit = self._cache.get(slug)
        now = time.monotonic()
        if hit is not None and now - hit[0] < self._ttl:
            return hit[1]
        if self._fetch is None:
            self._fetch = live_fetcher()
        raw = self._fetch(slug)
        self._cache[slug] = (now, raw)
        return raw


def _source_status(name: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [e for e in entries if isinstance(e, dict) and e.get("error")]
    skipped = [e for e in entries if isinstance(e, dict) and e.get("skipped")]
    if errors:
        return {"source": name, "status": "error", "detail": errors[0].get("safe_message")}
    if skipped and len(skipped) == len(entries):
        return {"source": name, "status": "no-data", "detail": str(skipped[0].get("skipped"))}
    return {"source": name, "status": "ok", "records": len(entries) - len(skipped)}


def lifecycle_events(slug: str, raw: Bundle, today: date | None = None) -> list[Any]:
    """Lifecycle findings from a live bundle, bridged into matchable events."""
    from analyzers.change_analyst import analyze_endoflife
    from analyzers.lifecycle_events import finding_to_event

    findings = analyze_endoflife(raw.get("endoflife", []), today=today or date.today())
    return [
        finding_to_event(f, slug, today=today)
        for f in findings
        if f.get("event_type") in _BRIDGED_EVENT_TYPES
    ]


def _repository(raw: Bundle) -> dict[str, Any] | None:
    for meta in raw.get("github_meta", []):
        if isinstance(meta, dict) and meta.get("kind") == "repo_meta":
            return {
                "repo": meta.get("full_name") or meta.get("repo"),
                "archived": meta.get("archived"),
                "last_push": meta.get("pushed_at"),
                "license": meta.get("license"),
                "url": meta.get("url"),
                "note": "context only: repository health is not part of the verdict",
            }
    return None


def _event_urls(events: list[Any]) -> dict[str, list[str]]:
    return {e.id: [str(ev.source.url) for ev in e.evidences] for e in events}


def _short(reason: str, keep: int = 3) -> str:
    """The engine joins every cause into one reason; agents need the gist."""
    parts = [p for p in str(reason).split("; ") if p]
    if len(parts) <= keep:
        return str(reason)
    return "; ".join(parts[:keep]) + f"; ... (+{len(parts) - keep} more)"


def _advisories(security: list[dict[str, Any]], limit: int = 20) -> dict[str, Any]:
    """OSV advisory causes, version-specific ones first and listed by id.

    AFFECTS_PACKAGE means the advisory names the package but its version
    applicability could not be established - counted, not listed, so a
    2012 advisory is not presented as applying to a 2026 release.
    """
    exact = sorted({str(c.get("event_id")) for c in security if c.get("relationship") ==
                    "AFFECTS_VERSION"})
    package_level = {str(c.get("event_id")) for c in security} - set(exact)
    return {
        "affecting_this_version": [
            {"id": i, "url": f"https://osv.dev/vulnerability/{i}"} for i in exact[:limit]
        ],
        "affecting_this_version_count": len(exact),
        "package_level_unconfirmed_count": len(package_level),
        "source": "osv.dev",
    }


def _dependency(
    package: str | None, version: str | None, ecosystem: str | None, image: str | None
) -> dict[str, Any]:
    if image:
        return {"kind": "image", "ref": image.strip()}
    if not package or not package.strip():
        raise ValueError("give a package name (with ecosystem and version) or an image ref")
    dep: dict[str, Any] = {"kind": "package", "package": package.strip()}
    if ecosystem:
        dep["ecosystem"] = ecosystem.strip()
    if version:
        dep["version"] = version.strip()
    return dep


def _assess(
    dep: dict[str, Any],
    lookups: Lookups | None,
    events: list[Any],
    today: date | None,
) -> dict[str, Any]:
    from core.entities.identity import resolution_trust
    from core.entities.resolve import resolve_project
    from core.risk.check import check_dependency

    ref = str(dep.get("ref") or dep.get("package"))
    slug = resolve_project(ref)
    trust = resolution_trust(ref)
    sources: list[dict[str, Any]] = [
        {"source": "curated-events", "status": "ok", "records": len(events)}
    ]
    bundles: dict[str, Bundle] = {}
    repository = None
    all_events = list(events)
    if lookups is None:
        sources.append({"source": "live lookups", "status": "disabled"})
    else:
        raw = lookups.bundle(slug)
        sources += [
            _source_status("endoflife.date", raw.get("endoflife", [])),
            _source_status("osv.dev", raw.get("osv", [])),
            _source_status("github", raw.get("github_meta", [])),
        ]
        all_events += lifecycle_events(slug, raw, today=today)
        bundles[slug] = raw
        repository = _repository(raw)
    verdict = check_dependency(dep, all_events, bundles)
    urls = _event_urls(all_events)
    relevant = [
        c
        for c in verdict.verdicts
        # Only causes about THIS project: a curated Bitnami event clearing
        # a Postgres image is true but noise to an agent choosing a version.
        if c.get("relationship") not in (None, "UNKNOWN") and c.get("project") == slug
    ]
    causes = [
        {
            "event": c.get("event_id"),
            "type": c.get("event_type"),
            "relationship": c.get("relationship"),
            "affected": c.get("affected"),
            "evidence_confidence": c.get("evidence_confidence"),
            "reason": c.get("reason"),
            "evidence_urls": urls.get(str(c.get("event_id")), []),
        }
        for c in relevant
        if c.get("cause") != "security_vulnerability"
    ]
    advisories = _advisories([c for c in relevant if c.get("cause") == "security_vulnerability"])
    unknowns = [s["source"] for s in sources if s["status"] in ("error", "no-data", "disabled")]
    if dep["kind"] == "package" and not dep.get("version"):
        unknowns.append("version (without it only project-level applicability is possible)")
    return {
        "dependency": verdict.dependency,
        "identity": {
            "project": slug,
            "resolved_via": trust["via"],
            "identity_status": trust["identity_status"],
        },
        "verdict": {
            "affected": verdict.affected,
            "relationship": verdict.relationship,
            "confidence": verdict.confidence,
            "reason": _short(verdict.reason),
        },
        "causes": causes,
        "advisories": advisories,
        "repository": repository,
        "sources": sources,
        "not_established": unknowns,
        "note": NOTE,
    }


def dependency_status(
    package: str | None = None,
    version: str | None = None,
    ecosystem: str | None = None,
    image: str | None = None,
    *,
    lookups: Lookups | None = None,
    live: bool = True,
    today: date | None = None,
) -> dict[str, Any]:
    """Evidence for one dependency: EOL/EOS, curated upstream changes
    (distribution, license, support) and OSV advisories for its version."""
    dep = _dependency(package, version, ecosystem, image)
    if live and lookups is None:
        lookups = Lookups()
    return _assess(dep, lookups if live else None, curated_events(), today)


def check_dependency_file(
    path: str,
    *,
    lookups: Lookups | None = None,
    live: bool = True,
    today: date | None = None,
) -> dict[str, Any]:
    """Every pinned dependency of one manifest, lockfile, SBOM or image list.

    Reuses the CLI's readers (bounded, skip-and-record): unpinned entries
    are reported as skipped, never guessed.
    """
    deps, skipped, kind = _read_dependency_file(path)
    truncated = len(deps) > MAX_FILE_DEPENDENCIES
    deps = deps[:MAX_FILE_DEPENDENCIES]
    if live and lookups is None:
        lookups = Lookups()
    events = curated_events()
    results = []
    looked_up: set[str] = set()
    from core.entities.resolve import resolve_project

    for dep in deps:
        slug = resolve_project(str(dep.get("ref") or dep.get("package")))
        use_live = live and (slug in looked_up or len(looked_up) < MAX_LIVE_PROJECTS)
        if use_live:
            looked_up.add(slug)
        results.append(_assess(dep, lookups if use_live else None, events, today))
    flagged = [r for r in results if r["verdict"]["affected"] or r["causes"]]
    return {
        "file": path,
        "format": kind,
        "dependencies_checked": len(results),
        "truncated": truncated,
        "live_projects_looked_up": len(looked_up),
        "skipped": skipped,
        "affected": [r["dependency"] for r in results if r["verdict"]["affected"]],
        "results": flagged,
        "unflagged": [r["dependency"] for r in results if r not in flagged],
        "note": NOTE,
    }


def _read_dependency_file(path: str) -> tuple[list[dict[str, Any]], list[str], str]:
    """Structural detection across the existing readers (no new parser)."""
    from core.image_inventory import read_image_inventory
    from core.lockfile_reader import read_lockfile
    from core.manifest_reader import read_manifest
    from core.sbom_reader import read_sbom, read_spdx

    errors = []
    for kind, reader in (
        ("lockfile", read_lockfile),
        ("manifest", read_manifest),
        ("cyclonedx", read_sbom),
        ("spdx", read_spdx),
    ):
        try:
            out = reader(path)
        except (ValueError, KeyError, TypeError) as e:
            errors.append(f"{kind}: {e}")
            continue
        deps, skipped = out[0], out[1]
        fmt = out[2] if len(out) > 2 else kind
        return deps, skipped, str(fmt)
    if path.lower().endswith((".txt", ".yaml", ".yml")):
        deps, skipped = read_image_inventory(path)
        return deps, skipped, "images"
    raise ValueError(f"{path}: not a recognized dependency file ({'; '.join(errors)})")


def project_lifecycle(
    project: str, *, lookups: Lookups | None = None, today: date | None = None
) -> dict[str, Any]:
    """Release cycles of one project with their support status today
    (endoflife.date), so an agent can pick a supported version."""
    from core.entities.resolve import resolve_project

    today = today or date.today()
    slug = resolve_project(project)
    raw = (lookups or Lookups()).bundle(slug)
    entries = raw.get("endoflife", [])
    cycles = []
    for e in entries:
        if not isinstance(e, dict) or e.get("error") or e.get("skipped"):
            continue
        cycles.append(
            {
                "cycle": e.get("cycle"),
                "latest": e.get("latest"),
                "eol": e.get("eol"),
                "support_ends": e.get("support"),
                "status": _cycle_status(e.get("eol"), today),
                "source": e.get("link"),
            }
        )
    return {
        "project": slug,
        "source": _source_status("endoflife.date", entries),
        "cycles": cycles,
        "supported_cycles": [c["cycle"] for c in cycles if c["status"] == "supported"],
        "repository": _repository(raw),
        "note": NOTE,
    }


def _cycle_status(eol: Any, today: date) -> str:
    if eol is True:
        return "end-of-life"
    if eol is False or eol is None:
        return "supported" if eol is False else "unknown"
    try:
        return "end-of-life" if date.fromisoformat(str(eol)[:10]) <= today else "supported"
    except ValueError:
        return "unknown"
