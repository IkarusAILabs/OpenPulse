"""Inventory-driven discovery: watch what the dependencies name.

The live collectors look projects up by catalog slug, so an uncatalogued
dependency was never observed. The retrospective study found 0 of 15
relocation, archival and distribution events as shipped, against 8 of 15
when each repository was supplied (evaluation/retrospective/REPORT.md §5,
§7a). This module derives the targets from the dependencies themselves:

- a Go module path names its source repository (``github.com/o/r/...``,
  plus the ``gopkg.in`` and ``golang.org/x`` conventions);
- a source-repository reference names its repository;
- a Docker Hub image names its Hub repository.

Each target is probed with the same collectors and change analyst as a
catalogued project, and every finding becomes an event through
``finding_to_event`` and the claim gate. Nothing is inferred beyond those
conventions: a vanity import path, a non-GitHub host or a package from
another ecosystem is reported as ``unmapped`` with its reason, never
guessed. Discovery is the only step that touches the network; ``check``
then runs offline on the events it writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from core.entities.resolve import normalize_ref
from core.schema.models import OSSEvent

#: GitHub path components (owner and repository names).
_GH_PART = re.compile(r"^[A-Za-z0-9_.-]+$")
#: gopkg.in/pkg.v3 -> go-pkg/pkg; gopkg.in/user/pkg.v3 -> user/pkg.
_GOPKG = re.compile(r"^gopkg\.in/(?:([A-Za-z0-9_-]+)/)?([A-Za-z0-9_-]+)\.v\d+(?:/.*)?$")
#: golang.org/x/name -> golang/name.
_GOLANG_X = re.compile(r"^golang\.org/x/([A-Za-z0-9_-]+)(?:/.*)?$")

#: Default cap on probed targets: anonymous GitHub API quota is 60/hour.
DEFAULT_MAX_TARGETS = 200


@dataclass(frozen=True)
class Target:
    kind: str  # "github" | "dockerhub"
    name: str  # "owner/repo" or "namespace/repo"


@dataclass
class DiscoveryResult:
    targets: dict[Target, list[str]] = field(default_factory=dict)  # target -> dep labels
    unmapped: list[tuple[str, str]] = field(default_factory=list)  # (dep label, reason)
    skipped_targets: list[Target] = field(default_factory=list)  # over the cap
    errors: list[tuple[Target, str]] = field(default_factory=list)
    events: list[OSSEvent] = field(default_factory=list)
    #: Offline OSV bundles by trust slug, for ``check --raw-bundle-dir``.
    bundles: dict[str, dict[str, list[dict[str, Any]]]] = field(default_factory=dict)
    advisories: int = 0


def _github_repo(path: str) -> str | None:
    """owner/repo for a github.com path, or None."""
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "github.com":
        owner, repo = parts[1], parts[2].removesuffix(".git")
        if _GH_PART.match(owner) and _GH_PART.match(repo) and repo not in (".", ".."):
            return f"{owner}/{repo}"
    return None


def go_module_repository(module: str) -> str | None:
    """The GitHub owner/repo a Go module path is hosted at, by convention only."""
    path = module.strip().lower()
    if path.startswith("github.com/"):
        return _github_repo(path)
    m = _GOPKG.match(path)
    if m:
        user, pkg = m.groups()
        return f"{user}/{pkg}" if user else f"go-{pkg}/{pkg}"
    m = _GOLANG_X.match(path)
    if m:
        return f"golang/{m.group(1)}"
    return None


def _label(dep: dict[str, Any]) -> str:
    return str(dep.get("ref") or dep.get("package") or "?")


def target_for(dep: dict[str, Any]) -> tuple[Target | None, str]:
    """(target, "") for a mappable dependency, else (None, reason)."""
    if dep.get("kind") == "package":
        ecosystem = str(dep.get("ecosystem") or "").strip().lower()
        if ecosystem not in ("go", "golang"):
            named = dep.get("ecosystem") or "unknown"
            return None, f"no repository convention for {named} packages"
        repo = go_module_repository(str(dep["package"]))
        if repo is None:
            return None, "Go module path is not on github.com, gopkg.in or golang.org/x"
        return Target("github", repo), ""
    ref = normalize_ref(str(dep.get("ref") or ""))
    ref = re.sub(r"^[a-z][a-z0-9+.-]*://", "", ref)
    if ref.startswith("github.com/"):
        repo = _github_repo(ref)
        return (Target("github", repo), "") if repo else (None, "not an owner/repo path")
    first, _, rest = ref.partition("/")
    # Docker's rule: the first segment is a registry host only when it has
    # a dot or a port, or is localhost; otherwise the image is on Docker Hub.
    if rest and ("." in first or ":" in first or first == "localhost"):
        if first != "docker.io":
            return None, f"no collector for registry {first} (Docker Hub only)"
        ref = rest
    parts = ref.split("/")
    if len(parts) == 1:
        parts = ["library", *parts]
    if len(parts) == 2 and all(parts):
        return Target("dockerhub", "/".join(parts)), ""
    return None, "not a namespace/repository Docker Hub path"


def plan(deps: list[dict[str, Any]], max_targets: int = DEFAULT_MAX_TARGETS) -> DiscoveryResult:
    """Map dependencies to targets; nothing is fetched."""
    result = DiscoveryResult()
    for dep in deps:
        target, reason = target_for(dep)
        if target is None:
            # npm/PyPI/Maven/crates packages have no repository convention to
            # fail: OSV covers them (osv_packages), so they are not unmapped.
            ecosystem = str(dep.get("ecosystem") or "").strip().lower()
            if dep.get("kind") != "package" or ecosystem == "go" or ecosystem not in OSV_ECOSYSTEMS:
                result.unmapped.append((_label(dep), reason))
            continue
        result.targets.setdefault(target, []).append(_label(dep))
    ordered = sorted(result.targets, key=lambda t: (t.kind, t.name))
    result.skipped_targets = ordered[max_targets:]
    for t in result.skipped_targets:
        del result.targets[t]
    return result


#: Inventory ecosystems OSV indexes, by the readers' spelling (lowercased).
OSV_ECOSYSTEMS = {
    "npm": "npm",
    "pypi": "PyPI",
    "maven": "Maven",
    "go": "Go",
    "crates.io": "crates.io",
}

#: A bundle file name: one or more safe path segments, never `..` or absolute.
_SAFE_SLUG = re.compile(r"^(?!.*(?:^|/)\.\.?(?:/|$))[A-Za-z0-9@._-]+(?:/[A-Za-z0-9@._-]+)*$")


def osv_packages(
    deps: list[dict[str, Any]], result: DiscoveryResult
) -> dict[tuple[str, str], str]:
    """(OSV ecosystem, package) -> trust slug for every queryable package dep.

    The slug is the key the security stream reads bundles under, so a
    bundle written for it is the one ``check`` correlates.
    """
    from core.entities.identity import package_trust

    out: dict[tuple[str, str], str] = {}
    for dep in deps:
        if dep.get("kind") != "package":
            continue
        ecosystem = OSV_ECOSYSTEMS.get(str(dep.get("ecosystem") or "").strip().lower())
        if ecosystem is None:
            continue
        name = str(dep["package"])
        slug = package_trust(name, dep.get("ecosystem"))["slug"]
        if not slug or not _SAFE_SLUG.match(slug):
            result.unmapped.append((name, "no stable identity key for an OSV bundle"))
            continue
        out[(ecosystem, name)] = slug
    return out


def _event_slug(target: Target) -> str:
    from core.entities.resolve import resolve_project

    ref = f"github.com/{target.name}" if target.kind == "github" else f"docker.io/{target.name}"
    return resolve_project(ref)


def discover(
    deps: list[dict[str, Any]],
    token: str | None = None,
    *,
    today: date | None = None,
    max_targets: int = DEFAULT_MAX_TARGETS,
    github: Any = None,
    registries: Any = None,
    osv: Any = None,
    max_packages: int = 500,
) -> DiscoveryResult:
    """Probe every target and return the events its findings support.

    ``github``, ``registries`` and ``osv`` are collector factories (tests
    pass fakes); by default the live GitHub, Docker Hub and OSV collectors.
    Every package dependency in an OSV ecosystem is also queried there,
    by its own (ecosystem, name), and its advisories are kept as an
    offline bundle: the security stream then decides it by version, with
    no catalog entry needed (malicious and compromised packages).
    """
    from analyzers import change_analyst
    from analyzers.lifecycle_events import finding_to_event
    from collectors.github.collector import GitHubCollector
    from collectors.osv.collector import OSVCollector
    from collectors.registries.docker import RegistryCollector
    from core.evidence.policy import gate

    today = today or date.today()
    result = plan(deps, max_targets)
    hub = (registries or RegistryCollector)()
    for target in sorted(result.targets, key=lambda t: (t.kind, t.name)):
        if target.kind == "github":
            collector = (github or GitHubCollector)({target.name: target.name}, token=token)
            raw = {"github_meta": [collector.fetch_repo_meta(target.name)]}
            entries = raw["github_meta"]
        else:
            namespace, repo = target.name.split("/")
            raw = {"registries": [hub.check_image(namespace, repo)]}
            entries = raw["registries"]
        for entry in entries:
            if isinstance(entry, dict) and entry.get("error"):
                result.errors.append((target, str(entry.get("safe_message") or "error")))
        slug = _event_slug(target)
        for finding in change_analyst.analyze(raw, today=today):
            event = finding_to_event(finding, slug, today=today)
            if not gate(event):
                result.events.append(event)
    packages = sorted(osv_packages(deps, result).items())
    for (ecosystem, name), _ in packages[max_packages:]:
        result.skipped_targets.append(Target("osv", f"{ecosystem}/{name}"))
    for (ecosystem, name), slug in packages[:max_packages]:
        records = (osv or OSVCollector)({slug: (name, ecosystem)}).collect(slug)
        for record in records:
            if record.get("error"):
                message = str(record.get("safe_message") or "error")
                result.errors.append((Target("osv", f"{ecosystem}/{name}"), message))
        found = [r for r in records if r.get("id")]
        result.advisories += len(found)
        if found:
            result.bundles.setdefault(slug, {"osv": []})["osv"].extend(found)
    return result
