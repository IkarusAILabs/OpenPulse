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
- Limits are stated, never silent (v0.11.0 W4): every answer carries a
  ``lookups`` block (session budget, used, remaining, per-source
  timeout); a lookup the budget or a per-file cap refused is listed in
  ``not_established`` with the reason.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from datetime import time as dt_time
from pathlib import Path
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
#: Live fetches one server session may make (cache hits are free). Past
#: it, lookups are refused and every answer says so (W4).
MAX_SESSION_LOOKUPS = 200
#: Per-source HTTP timeout of the live collectors, in seconds.
LOOKUP_TIMEOUT_SECONDS = 10.0
#: Cross-session cache for project_lifecycle (W4): same TTL as in session.
CACHE_DIR_ENV = "OPENPULSE_CACHE_DIR"
_CACHE_MAX_BYTES = 2_000_000
_BUDGET_REASON = "session lookup budget spent ({budget} live lookups); ask again in a new session"

NOTE = (
    "OpenPulse evidence, not a decision: verdicts state what the cited sources "
    "establish for this exact dependency; UNKNOWN means not established, never safe. "
    "NOT_AFFECTED means outside the cited evidence's directly named scope only, never "
    "safe: decide from verdict.meaning, whose fields say what was not evaluated, and "
    "from evaluation_context, which says whether evidence age was bounded."
)

#: Appended to NOTE whenever no freshness bound was applied: a missing
#: bound is stated, never left for the reader to infer from a null.
UNBOUNDED_NOTE = (
    " NO FRESHNESS BOUND: this answer was computed in replay mode, so a NOT_AFFECTED "
    "may rest on evidence of any age."
)

#: Assessment modes (TR-2026-01 N4). ``current`` answers "is this dependency
#: affected now": a negative needs evidence no older than the bound, so a
#: stale event can associate a dependency but never clear it. ``replay``
#: re-evaluates recorded evidence offline, where every negative would
#: otherwise be stale; it disables the bound and says so in the response.
CURRENT = "current"
REPLAY = "replay"
MODES = (CURRENT, REPLAY)

#: Default freshness bound for current assessments, in days (the
#: retrospective study, ``evaluation/run.py``, uses the same 90).
DEFAULT_MAX_EVIDENCE_AGE_DAYS = 90

Bundle = dict[str, list[dict[str, Any]]]
Fetcher = Callable[[str], Bundle]


class Evaluation:
    """The time frame one agent answer is computed under.

    ``as_of`` defaults to ``today`` at 00:00 UTC when a date is pinned
    (deterministic tests and replays of a known day), else the current
    time. ``context`` is the contract 1.2.0 ``evaluation_context`` block
    plus the mode, so the response describes the verdict it carries.
    """

    def __init__(
        self,
        mode: str = CURRENT,
        *,
        as_of: datetime | None = None,
        max_evidence_age_days: int | None = None,
        today: date | None = None,
    ):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {', '.join(MODES)}, not {mode!r}")
        self.mode = mode
        self.as_of: datetime | None = None
        self.max_evidence_age: timedelta | None = None
        if mode == CURRENT:
            days = (
                DEFAULT_MAX_EVIDENCE_AGE_DAYS
                if max_evidence_age_days is None
                else int(max_evidence_age_days)
            )
            if days < 0:
                raise ValueError("max_evidence_age_days must not be negative")
            if as_of is None:
                as_of = (
                    datetime.combine(today, dt_time.min, tzinfo=timezone.utc)
                    if today is not None
                    else datetime.now(timezone.utc)
                )
            elif as_of.tzinfo is None:
                as_of = as_of.replace(tzinfo=timezone.utc)
            self.as_of = as_of
            self.max_evidence_age = timedelta(days=days)

    @property
    def bounded(self) -> bool:
        return self.as_of is not None and self.max_evidence_age is not None

    @property
    def context(self) -> dict[str, Any]:
        as_of = self.as_of.isoformat().replace("+00:00", "Z") if self.as_of else None
        return {
            "mode": self.mode,
            "as_of": as_of,
            "max_evidence_age_days": self.max_evidence_age.days
            if self.max_evidence_age is not None
            else None,
            "freshness_bound_applied": self.bounded,
            "unresolved_identity": "undetermined",
        }

    @property
    def note(self) -> str:
        return NOTE if self.bounded else NOTE + UNBOUNDED_NOTE


def curated_events() -> list[Any]:
    """The bundled curated events as validated OSSEvents."""
    from core.schema.models import OSSEvent

    events = []
    for name in CURATED_EVENTS:
        with open(data_path("fixtures", name, "event.json"), encoding="utf-8") as f:
            events.append(OSSEvent(**json.load(f)))
    return events


def live_fetcher(timeout: float = LOOKUP_TIMEOUT_SECONDS) -> Fetcher:
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


class BudgetExhausted(Exception):
    """The session's live-lookup budget is spent (W4)."""


def default_cache_dir() -> Path | None:
    """``OPENPULSE_CACHE_DIR``, else the user cache directory; '' disables."""
    configured = os.environ.get(CACHE_DIR_ENV)
    if configured is not None:
        return Path(configured) if configured.strip() else None
    base = os.environ.get("XDG_CACHE_HOME") or os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / ".cache"
    return root / "openpulse" / "lookups"


class Lookups:
    """Per-process cache of live bundles (an agent asks about the same
    projects repeatedly; the public APIs should not be hammered).

    ``budget`` caps live fetches per session (cache hits are free);
    ``cache_dir`` backs :func:`project_lifecycle` across sessions with the
    same TTL. Only bundles without a source error are written there, so a
    failure is never replayed from disk.
    """

    def __init__(
        self,
        fetch: Fetcher | None = None,
        ttl: float = _CACHE_TTL_SECONDS,
        budget: int = MAX_SESSION_LOOKUPS,
        cache_dir: Path | str | None = None,
        clock: Callable[[], float] = time.time,
        head: Callable[[str], int] | None = None,
    ):
        self._fetch = fetch
        self._ttl = ttl
        self._cache: dict[str, tuple[float, Bundle]] = {}
        self.budget = budget
        self.used = 0
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._clock = clock
        #: slug -> age in seconds when the last answer came from the disk cache.
        self.disk_hits: dict[str, int] = {}
        self._head = head
        self._existence: dict[tuple[str, str, str], tuple[float, list[dict[str, Any]]]] = {}

    @property
    def remaining(self) -> int:
        return max(self.budget - self.used, 0)

    def status(self) -> dict[str, Any]:
        """The ``lookups`` block every answer carries."""
        return {
            "budget": self.budget,
            "used": self.used,
            "remaining": self.remaining,
            "timeout_seconds_per_source": LOOKUP_TIMEOUT_SECONDS,
            "cache_ttl_seconds": int(self._ttl),
        }

    def bundle(self, slug: str, persistent: bool = False) -> Bundle:
        """Live bundle for ``slug``; raises BudgetExhausted instead of fetching past the budget."""
        hit = self._cache.get(slug)
        now = time.monotonic()
        if hit is not None and now - hit[0] < self._ttl:
            return hit[1]
        if persistent and (cached := self._read_disk(slug)) is not None:
            self._cache[slug] = (now, cached)
            return cached
        if self.used >= self.budget:
            raise BudgetExhausted(_BUDGET_REASON.format(budget=self.budget))
        if self._fetch is None:
            self._fetch = live_fetcher()
        self.used += 1
        raw = self._fetch(slug)
        self._cache[slug] = (now, raw)
        if persistent:
            self._write_disk(slug, raw)
        return raw

    def existence(
        self, ecosystem: str, name: str, version: str | None
    ) -> list[dict[str, Any]]:
        """Registry existence records (T-M1), cached per session like bundles.

        One check spends one lookup from the budget, even when it needs a
        second request to tell a missing version from a missing package.
        A NOT_PERFORMED answer is never cached.
        """
        from core import registry_existence

        key = (ecosystem, name, version or "")
        hit = self._existence.get(key)
        now = time.monotonic()
        if hit is not None and now - hit[0] < self._ttl:
            return hit[1]
        if self.used >= self.budget:
            raise BudgetExhausted(_BUDGET_REASON.format(budget=self.budget))
        self.used += 1
        records = registry_existence.check(ecosystem, name, version, head=self._head)
        if all(r["status"] != registry_existence.NOT_PERFORMED for r in records):
            self._existence[key] = (now, records)
        return records

    def _disk_path(self, slug: str) -> Path | None:
        if self._cache_dir is None:
            return None
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in slug)[:120]
        return self._cache_dir / f"{safe}.json"

    def _read_disk(self, slug: str) -> Bundle | None:
        path = self._disk_path(slug)
        if path is None:
            return None
        try:
            from core.bounded_io import read_bytes

            entry = json.loads(read_bytes(str(path), _CACHE_MAX_BYTES, "lookup cache"))
            age = self._clock() - float(entry["fetched_at"])
            raw = entry["bundle"]
        except (OSError, ValueError, KeyError, TypeError):
            return None  # missing or unreadable: fetch again, never trust it
        if not 0 <= age < self._ttl or entry.get("slug") != slug or not isinstance(raw, dict):
            return None
        self.disk_hits[slug] = int(age)
        return raw

    def _write_disk(self, slug: str, raw: Bundle) -> None:
        path = self._disk_path(slug)
        if path is None or any(
            isinstance(e, dict) and e.get("error") for entries in raw.values() for e in entries
        ):
            return
        import tempfile

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"slug": slug, "fetched_at": self._clock(), "bundle": raw}
            fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, default=str)
            os.replace(tmp, path)
        except (OSError, TypeError, ValueError):
            return  # a cache that cannot be written is only a slower answer


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


#: Identifier shapes for anything an agent hands us (T-F3, Phase 0 audit A).
#: Deliberately general - every ecosystem's names and versions, and legacy
#: npm names with capitals, fit - and deliberately closed: no whitespace,
#: control, bidi, zero-width or Markdown characters, so a name can never
#: carry an instruction into an answer. Registry URLs use the stricter
#: per-ecosystem grammars of core.registry_existence.
_IDENTIFIER_SHAPES = {
    "package": re.compile(r"[A-Za-z0-9@][A-Za-z0-9@/._:+~-]{0,213}"),
    "version": re.compile(r"[A-Za-z0-9][A-Za-z0-9.+!_~:-]{0,63}"),
    "ecosystem": re.compile(r"[A-Za-z][A-Za-z0-9.+_-]{0,31}"),
    "image": re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,254}"),
}
_SHAPE_HELP = {
    "package": "letters, digits and @ / . _ : + ~ -, at most 214 characters",
    "version": "letters, digits and . + ! _ ~ : -, at most 64 characters",
    "ecosystem": "letters, digits and . + _ -, at most 32 characters",
    "image": "letters, digits and . _ : / @ + -, at most 255 characters",
}


def _identifier(field: str, value: str) -> str:
    """``value`` when it has the identifier shape; else ValueError. Never echoes it."""
    if not _IDENTIFIER_SHAPES[field].fullmatch(value):
        raise ValueError(
            f"{field} is not an identifier ({_SHAPE_HELP[field]}); the value is not repeated"
        )
    return value


def _refused_entry(dep: dict[str, Any]) -> str | None:
    """The field of a file entry that fails its identifier shape, if any."""
    fields = {"ref": "image"} if dep.get("kind") == "image" else {
        "package": "package", "version": "version", "ecosystem": "ecosystem"
    }
    for key, field in fields.items():
        value = dep.get(key)
        if value is not None and not _IDENTIFIER_SHAPES[field].fullmatch(str(value)):
            return field
    return None


def _dependency(
    package: str | None, version: str | None, ecosystem: str | None, image: str | None
) -> dict[str, Any]:
    if image:
        return {"kind": "image", "ref": _identifier("image", image.strip())}
    if not package or not package.strip():
        raise ValueError("give a package name (with ecosystem and version) or an image ref")
    dep: dict[str, Any] = {"kind": "package", "package": _identifier("package", package.strip())}
    if ecosystem:
        dep["ecosystem"] = _identifier("ecosystem", ecosystem.strip())
    if version:
        dep["version"] = _identifier("version", version.strip())
    return dep


def _trust(dep: dict[str, Any]) -> dict[str, Any]:
    """Identity the way the verdict engine resolves it: packages per ecosystem (F1)."""
    from core.entities.identity import package_trust, resolution_trust

    if dep["kind"] == "package":
        return package_trust(str(dep["package"]), dep.get("ecosystem"))
    return resolution_trust(str(dep["ref"]))


def _registry_existence(dep: dict[str, Any], lookups: Lookups | None) -> list[dict[str, Any]]:
    """T-M1: does the package (and version) exist in its registry? Never a verdict input."""
    from core import registry_existence

    ecosystem = registry_existence.ecosystem_of(dep.get("ecosystem"))
    if dep["kind"] != "package" or ecosystem is None:
        return registry_existence.not_performed("unsupported")
    if lookups is None:
        return registry_existence.not_performed("offline", ecosystem=ecosystem)
    try:
        return lookups.existence(ecosystem, str(dep["package"]), dep.get("version"))
    except BudgetExhausted:
        return registry_existence.not_performed("budget", ecosystem=ecosystem)


def _assess(
    dep: dict[str, Any],
    lookups: Lookups | None,
    events: list[Any],
    today: date | None,
    evaluation: Evaluation,
    existence: bool = False,
) -> dict[str, Any]:
    from core.risk.check import check_dependency
    from core.verdict_meaning import DIRECT_SCOPE, scope_completeness, verdict_meaning

    trust = _trust(dep)
    slug = str(trust["slug"])
    sources: list[dict[str, Any]] = [
        {"source": "curated-events", "status": "ok", "records": len(events)}
    ]
    bundles: dict[str, Bundle] = {}
    repository = None
    all_events = list(events)
    raw = None
    if lookups is None:
        sources.append({"source": "live lookups", "status": "disabled"})
    else:
        try:
            raw = lookups.bundle(slug)
        except BudgetExhausted as exc:
            sources.append(
                {"source": "live lookups", "status": "budget-exhausted", "detail": str(exc)}
            )
    if raw is not None:
        sources += [
            _source_status("endoflife.date", raw.get("endoflife", [])),
            _source_status("osv.dev", raw.get("osv", [])),
            _source_status("github", raw.get("github_meta", [])),
        ]
        all_events += lifecycle_events(slug, raw, today=today)
        bundles[slug] = raw
        repository = _repository(raw)
    verdict = check_dependency(
        dep,
        all_events,
        bundles,
        as_of=evaluation.as_of,
        max_evidence_age=evaluation.max_evidence_age,
    )
    urls = _event_urls(all_events)
    scopes = {e.id: e.scope for e in all_events}
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
            "direct_scope": DIRECT_SCOPE.get(str(c.get("relationship")), "undetermined"),
            "scope_completeness": scope_completeness(scopes.get(str(c.get("event_id")))),
            "affected": c.get("affected"),
            "evidence_confidence": c.get("evidence_confidence"),
            "reason": c.get("reason"),
            "evidence_urls": urls.get(str(c.get("event_id")), []),
        }
        for c in relevant
        if c.get("cause") != "security_vulnerability"
    ]
    advisories = _advisories([c for c in relevant if c.get("cause") == "security_vulnerability"])
    unknowns = [
        s["source"] if s["status"] != "budget-exhausted" else f"live lookups ({s['detail']})"
        for s in sources
        if s["status"] in ("error", "no-data", "disabled", "budget-exhausted")
    ]
    if dep["kind"] == "package" and not dep.get("version"):
        unknowns.append("version (without it only project-level applicability is possible)")
    if not evaluation.bounded:
        unknowns.append("evidence currency (replay mode: no freshness bound applied)")
    answer: dict[str, Any] = {
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
            "meaning": verdict_meaning(verdict.relationship),
            "reason": _short(verdict.reason),
        },
        "causes": causes,
        "advisories": advisories,
        "repository": repository,
        "sources": sources,
        "not_established": unknowns,
        "evaluation_context": evaluation.context,
        "lookups": lookups.status() if lookups is not None else None,
        "note": evaluation.note,
    }
    if existence:
        # Track T (T-M1): additive, separately labelled, never read by the verdict.
        answer["registry_existence"] = _registry_existence(dep, lookups)
        if lookups is not None:
            answer["lookups"] = lookups.status()
    return answer


def dependency_status(
    package: str | None = None,
    version: str | None = None,
    ecosystem: str | None = None,
    image: str | None = None,
    *,
    lookups: Lookups | None = None,
    live: bool = True,
    today: date | None = None,
    mode: str = CURRENT,
    as_of: datetime | None = None,
    max_evidence_age_days: int | None = None,
) -> dict[str, Any]:
    """Evidence for one dependency: EOL/EOS, curated upstream changes
    (distribution, license, support) and OSV advisories for its version,
    plus whether the package and version exist in their registry (PyPI
    and npm; ``registry_existence``, track T T-M1).

    ``mode="current"`` (default) bounds evidence age for negatives
    (``max_evidence_age_days``, default 90, as of ``as_of``);
    ``mode="replay"`` disables the bound and the response says so.
    """
    evaluation = Evaluation(
        mode, as_of=as_of, max_evidence_age_days=max_evidence_age_days, today=today
    )
    dep = _dependency(package, version, ecosystem, image)
    if live and lookups is None:
        lookups = Lookups()
    return _assess(
        dep, lookups if live else None, curated_events(), today, evaluation, existence=True
    )


def check_dependency_file(
    path: str,
    *,
    lookups: Lookups | None = None,
    live: bool = True,
    today: date | None = None,
    mode: str = CURRENT,
    as_of: datetime | None = None,
    max_evidence_age_days: int | None = None,
) -> dict[str, Any]:
    """Every pinned dependency of one manifest, lockfile, SBOM or image list.

    Reuses the CLI's readers (bounded, skip-and-record): unpinned entries
    are reported as skipped, never guessed. ``mode``, ``as_of`` and
    ``max_evidence_age_days`` as in :func:`dependency_status`; one time
    frame covers the whole file.
    """
    evaluation = Evaluation(
        mode, as_of=as_of, max_evidence_age_days=max_evidence_age_days, today=today
    )
    deps, skipped, kind = _read_dependency_file(path)
    # The agent writes the files it asks about: an entry whose name is not an
    # identifier is skipped like any unpinned entry, and never echoed (T-F3).
    kept = []
    for number, dep in enumerate(deps, 1):
        field = _refused_entry(dep)
        if field is None:
            kept.append(dep)
        else:
            skipped = [
                *skipped,
                f"entry {number}: {field} is not an identifier - skipped, value not shown",
            ]
    deps = kept
    truncated = len(deps) > MAX_FILE_DEPENDENCIES
    deps = deps[:MAX_FILE_DEPENDENCIES]
    if live and lookups is None:
        lookups = Lookups()
    events = curated_events()
    results = []
    looked_up: set[str] = set()
    capped: list[str] = []
    for dep in deps:
        slug = str(_trust(dep)["slug"])
        use_live = live and (slug in looked_up or len(looked_up) < MAX_LIVE_PROJECTS)
        if use_live:
            looked_up.add(slug)
        elif live and slug not in capped:
            capped.append(slug)
        result = _assess(dep, lookups if use_live else None, events, today, evaluation)
        if live and not use_live:
            result["not_established"] = [
                u for u in result["not_established"] if u != "live lookups"
            ] + [f"live lookups (per-file cap of {MAX_LIVE_PROJECTS} projects reached)"]
        results.append(result)
    flagged = [r for r in results if r["verdict"]["affected"] or r["causes"]]
    return {
        "file": path,
        "format": kind,
        "dependencies_checked": len(results),
        "truncated": truncated,
        "live_projects_looked_up": len(looked_up),
        "live_lookups_capped": capped,
        "lookups": lookups.status() if live and lookups is not None else None,
        "skipped": skipped,
        "affected": [r["dependency"] for r in results if r["verdict"]["affected"]],
        "results": flagged,
        "unflagged": [r["dependency"] for r in results if r not in flagged],
        "evaluation_context": evaluation.context,
        "note": evaluation.note,
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
    lookups = lookups or Lookups(cache_dir=default_cache_dir())
    raw = lookups.bundle(slug, persistent=True)  # BudgetExhausted reaches the agent
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
        "cached_age_seconds": lookups.disk_hits.get(slug),
        "lookups": lookups.status(),
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
