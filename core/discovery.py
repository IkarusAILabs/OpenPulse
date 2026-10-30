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
    if path.split("/", 1)[0] == "github.com":
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
    if ref.split("/", 1)[0] == "github.com":
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
            result.unmapped.append((_label(dep), reason))
        else:
            result.targets.setdefault(target, []).append(_label(dep))
    ordered = sorted(result.targets, key=lambda t: (t.kind, t.name))
    result.skipped_targets = ordered[max_targets:]
    for t in result.skipped_targets:
        del result.targets[t]
    return result


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
) -> DiscoveryResult:
    """Probe every target and return the events its findings support.

    ``github`` and ``registries`` are collector factories (tests pass fakes);
    by default the live GitHub and Docker Hub collectors.
    """
    from analyzers import change_analyst
    from analyzers.lifecycle_events import finding_to_event
    from collectors.github.collector import GitHubCollector
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
    return result
