"""Specification oracle for TR-2026-01 applicability (Algorithm 1, Section 5).

Written from the report's text, not from the implementation: this module
imports nothing from ``core`` or ``analyzers``. Identity is an *input*
(ground truth per case), not resolved here, so the oracle tests matching
and decision policy, not the resolver.

Verdicts: AFFECTS, RELATED, AFFECTS_PROJECT, NOT_AFFECTED, UNKNOWN, and
UNLOADED for an event that layer 1 does not evaluate at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

M, N, U, P, Z = "M", "N", "?", "P", "0"  # member, excluded, undetermined, project tie, none

#: Section 5.3 canonical form: Docker Hub's other hostnames are docker.io.
_HUB_ALIASES = {"index.docker.io", "registry-1.docker.io"}

#: Section 5.2 tag predicates.
TAG_VERSION = "<version>"
TAG_ANY = "*"

#: "version-like": a dotted numeric release, optionally one pre-release
#: marker, optionally a variant suffix (1.25, 7.2.4-debian-12-r3, 1.0rc1).
_VERSION_LIKE = re.compile(
    r"v?\d+(?:\.\d+)*"
    r"(?:[-._]?(?:dev|alpha|a|beta|b|rc|c|preview|pre)\d*)?"
    r"(?:-[A-Za-z][A-Za-z0-9._-]*)?",
    re.IGNORECASE,
)
_RELEASE = re.compile(r"v?(\d+(?:\.\d+)*)")


@dataclass(frozen=True)
class Ref:
    """A parsed container reference: canonical repository plus pin."""

    registry: str
    namespace: str
    name: str
    tag: str | None
    digest: str | None


def parse_ref(text: str) -> Ref:
    """Parse, then canonicalise identity only (tag and digest kept verbatim)."""
    s = text.strip()
    for scheme in ("oci://", "docker://", "https://", "http://"):
        if s.lower().startswith(scheme):
            s = s[len(scheme) :]
    digest = None
    if "@" in s:
        s, digest = s.split("@", 1)
    head, _, last = s.rpartition("/")
    tag = None
    if ":" in last:
        last, tag = last.split(":", 1)
    parts = [p for p in (head.split("/") if head else [])] + [last]
    first = parts[0].lower()
    if len(parts) > 1 and ("." in first or ":" in first or first == "localhost"):
        registry, rest = first, parts[1:]
    else:
        registry, rest = "docker.io", parts
    if registry in _HUB_ALIASES:
        registry = "docker.io"
    if len(rest) == 1:
        namespace = "library" if registry == "docker.io" else ""
        name = rest[0]
    else:
        namespace, name = "/".join(rest[:-1]), rest[-1]
    return Ref(registry, namespace.lower(), name.lower(), tag, digest)


def version_like(tag: str) -> bool:
    return _VERSION_LIKE.fullmatch(tag) is not None


def _effective_tag(ref: Ref) -> str | None:
    """A reference with neither tag nor digest is ``latest``."""
    if ref.tag is not None:
        return ref.tag
    return None if ref.digest else "latest"


def _tag_member(dep: Ref, predicate: str | None) -> str:
    if predicate in (None, TAG_ANY):
        return M
    tag = _effective_tag(dep)
    if tag is None:
        return U  # digest only: its tag is unknown
    if predicate == TAG_VERSION:
        return M if version_like(tag) else N
    return M if tag == predicate else N


@dataclass(frozen=True)
class Element:
    kind: str  # project | artifact | release_line | package | registry
    value: str
    example: bool = False  # a named affected artifact, which illustrates
    project_element: bool = False  # a package value that names the event's project (F2)

    def role(self) -> str:
        """Section 5.2: a namespace without a tag predicate is an envelope."""
        if self.kind == "registry":
            return "envelope"  # the representation has no exact registry form
        if self.kind == "artifact":
            ref = parse_ref(self.value)
            if ref.name == "*" and ref.tag is None:
                return "envelope"
        return "exact"


@dataclass(frozen=True)
class Dependency:
    kind: str  # image | package
    ref: str = ""
    package: str = ""
    version: str | None = None
    identity: str = "unresolved"  # "project" | "other" | "unresolved"
    ecosystem: str = ""  # PyPI | npm | Maven | Go | crates.io | "" (not stated)


@dataclass
class Event:
    project: str
    elements: list[Element]
    chi: str = "partial"  # partial | declared
    basis: str | None = None
    admissibility: str = "current"  # current|withdrawn|superseded|contested|stale
    notes: list[str] = field(default_factory=list)


#: Hosts of source repositories, whose elements a package reference may
#: name (a Go module path names its repository).
_SOURCE_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def _across_kinds(dep: Dependency, may_be_same_object: bool) -> str:
    """Section 5.3, across reference kinds (S2, S3).

    A curated mapping to another project is positive evidence of no
    association. A package is never a container image or registry
    location, so an unresolved package has no association with those
    elements either. Otherwise the association is undetermined (?).
    """
    if dep.identity == "other":
        return Z
    if dep.identity == "unresolved" and dep.kind == "package" and not may_be_same_object:
        return Z
    return U


def _test_artifact(dep: Dependency, x: Element) -> str:
    if dep.kind != "image":
        if x.example:
            return Z  # an example illustrates an image event; never a package's
        # A package is never a container image or object; it may be the
        # same object as a source repository.
        return _across_kinds(dep, parse_ref(x.value).registry in _SOURCE_HOSTS)
    d, e = parse_ref(dep.ref), parse_ref(x.value)
    if e.name == "*":  # namespace element
        if (d.registry, d.namespace) != (e.registry, e.namespace):
            return N
        if x.role() == "envelope":
            return U
        return _tag_member(d, e.tag)
    if (d.registry, d.namespace, d.name) != (e.registry, e.namespace, e.name):
        return Z if x.example else N  # an example illustrates, never bounds (S4)
    if e.digest is not None:  # object element
        if d.digest is None:
            return U  # a tag can move onto the digest
        return M if d.digest == e.digest else U  # OCI level unknown
    if e.tag is None:
        return M  # repository: whatever its tag or digest
    member = _tag_member(d, e.tag)
    if member == N and x.example:
        return U  # a named tag does not establish the others
    return member


def _release(version: str) -> list[int] | None:
    match = _RELEASE.match(version)
    if not match:
        return None
    return [int(n) for n in match.group(1).split(".")]


def _test_release_line(dep: Dependency, x: Element) -> str:
    if dep.identity == "other":
        return Z  # curated as another project: no association (S2)
    if dep.identity == "unresolved":
        return U
    if dep.kind == "image":
        tag = _effective_tag(parse_ref(dep.ref))
        if tag is None or not version_like(tag):
            return U
        version = tag
    else:
        if not dep.version:
            return U
        version = dep.version
    release, line = _release(version), _release(x.value)
    if release is None or line is None:
        return U
    return M if release[: len(line)] == line else N


#: purl types and the ecosystems they name (SPEC.md section 4.4).
_PURL_TYPES = {"pypi": "pypi", "npm": "npm", "maven": "maven", "golang": "go"}


def canonical_package(ecosystem: str, name: str) -> tuple[str, str]:
    """Section 4.4 canonical form: lowercase; PEP 503 for PyPI; Maven g:a = g/a."""
    eco, key = ecosystem.strip().lower(), name.strip().lower()
    if eco == "pypi":
        key = re.sub(r"[-_.]+", "-", key)
    elif eco == "maven":
        key = key.replace(":", "/", 1)
    return eco, key


def parse_package_purl(value: str) -> tuple[str, str] | None:
    """`pkg:type/namespace/name` -> canonical (ecosystem, name), else None.

    No version (a scope value names a package), no unsupported type.
    Qualifiers and subpath carry no identity and are dropped.
    """
    from urllib.parse import unquote

    if not value.startswith("pkg:"):
        return None
    body = value[4:].split("?", 1)[0].split("#", 1)[0]
    if "@" in body.rsplit("/", 1)[-1]:
        return None
    parts = [unquote(p) for p in body.split("/") if p]
    if len(parts) < 2 or parts[0].lower() not in _PURL_TYPES:
        return None
    return canonical_package(_PURL_TYPES[parts[0].lower()], "/".join(parts[1:]))


def _test_package(dep: Dependency, x: Element) -> str:
    if dep.kind != "package":
        return _across_kinds(dep, may_be_same_object=False)
    stated = dep.ecosystem.strip() and dep.ecosystem.strip().lower() != "generic"
    if x.value.startswith("pkg:"):
        # An ecosystem-qualified value names exactly one package (F3): it
        # decides by (ecosystem, name) before identity.
        key = parse_package_purl(x.value)
        mine = canonical_package(dep.ecosystem, dep.package) if stated else None
        if key is not None and key == mine:
            return M
        if dep.identity == "other":
            return Z
        if key is None or mine is None:
            return U
        return N if key[0] != mine[0] else U  # another ecosystem is another object
    # A bare value carries no ecosystem, so identity decides first (F3):
    # a name alone cannot tell PyPI `redis` (redis-py) from the server.
    if dep.identity == "other":
        return Z
    if dep.identity == "unresolved":
        return U
    eco = dep.ecosystem if stated else ""
    if canonical_package(eco, dep.package)[1] == canonical_package(eco, x.value)[1]:
        return M
    if x.project_element:
        # A project package element (F2) denotes every package curated as
        # the event's project.
        return M
    return U  # names are not fully canonical: inequality alone is ?


def _test_registry(dep: Dependency, x: Element) -> str:
    if dep.kind != "image":
        return _across_kinds(dep, may_be_same_object=False)
    return U if parse_ref(dep.ref).registry == x.value.lower() else N


def _test_project(dep: Dependency, x: Element) -> str:
    return {"project": P, "other": Z}.get(dep.identity, U)


_TESTS = {
    "artifact": _test_artifact,
    "release_line": _test_release_line,
    "package": _test_package,
    "registry": _test_registry,
    "project": _test_project,
}


def applicability(dep: Dependency, event: Event) -> str:
    """Algorithm 1 with its three layers."""
    # Layer 1: event admissibility. Withdrawn and superseded events are
    # not evaluated; contested or stale ones may not clear (S1: layer 1
    # withholds negatives only).
    if event.admissibility in ("withdrawn", "superseded"):
        return "UNLOADED"
    negatives_admissible = event.admissibility not in ("contested", "stale")
    # Layer 2: every element, no early return.
    elements = [
        Element(x.kind, x.value, x.example, project_element=True)
        if x.kind == "package"
        and not x.value.startswith("pkg:")
        and x.value.lower() == event.project.lower()
        else x
        for x in event.elements
    ]
    results = {_TESTS[x.kind](dep, x) for x in elements}
    # Layer 3: per-event aggregation.
    if M in results:
        return "AFFECTS"
    if U in results:
        return "RELATED"
    if N in results:
        admissible = event.chi == "declared" and event.basis is not None
        if results <= {N, Z} and admissible and negatives_admissible:
            return "NOT_AFFECTED"
        return "RELATED"
    if P in results:
        return "AFFECTS_PROJECT"
    return "UNKNOWN"
