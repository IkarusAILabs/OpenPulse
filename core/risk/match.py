"""Impact match — does an OSSEvent affect a dependency ref?

Conservative by construction:
- Exact artifact triple equality → AFFECTS_ARTIFACT.
- Populated event scope narrows everything else: a dependency outside
  an explicit, exhaustive scope is NOT_AFFECTED, not UNKNOWN. A scope
  declared non-exhaustive lists known members only: outside it is
  RELATED, never a clearance.
- Every scope element is evaluated: a clearance needs every element
  decisively excluded, and one undetermined element withholds it.
- Version scopes belong to the event's project: a tag that merely
  collides with a scope version of a different project
  (docker.io/bitnami/redis:6.2 vs an upstream redis EOL) is
  identity-excluded, never an AFFECTS_VERSION claim.
- Bare project-slug equality is contextual (AFFECTS_PROJECT) and never
  means affected on its own.
- No scope at all → legacy fallback (artifact, then project context).

`docker.io/redis:7.2` does NOT match a `docker.io/bitnami/redis`
artifact: different namespace, different stack. That distinction is
the whole point of the Bitnami case.
"""

from __future__ import annotations

import re

from core.entities.identity import resolution_trust
from core.entities.resolve import normalize_ref, resolve_project
from core.schema.models import OSSEvent
from core.versions import detect_scheme, in_release_line


def split_image_ref(ref: str) -> tuple[str, str, str]:
    """(registry, namespace, name) with tags/digests/schemes stripped."""
    r = normalize_ref(ref)
    for scheme in ("oci://", "https://", "http://", "docker://"):
        if r.startswith(scheme):
            r = r[len(scheme) :]
    parts = r.split("/")
    # A first segment with a dot, a port or "localhost" is a registry host,
    # also in a two-segment ref: `docker.io/redis` is Docker's spelling of
    # `docker.io/library/redis`, not namespace "docker.io" (TR-2026-01 D12).
    if len(parts) >= 2 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
        registry, rest = parts[0], parts[1:]
    else:
        registry, rest = "docker.io", parts
    if len(rest) == 1:
        # Only Docker Hub puts single-name repositories under "library".
        namespace, name = ("library" if registry == "docker.io" else ""), rest[0]
    else:
        namespace, name = "/".join(rest[:-1]), rest[-1]
    return registry, namespace, name


#: Docker variant tags: `13.5-alpine`, `3.12-slim-bookworm` -> version head.
_TAG_VARIANT = re.compile(r"^(v?\d+(?:\.\d+)*)-[A-Za-z][A-Za-z0-9._-]*$")


def _tag_version(tag: str) -> str:
    """The comparable version in an image tag (variant suffix dropped)."""
    match = _TAG_VARIANT.match(tag)
    return match.group(1) if match else tag


def tag_of(ref: str) -> str | None:
    """Image tag, or None when absent (digests stripped first)."""
    r = str(ref).split("@")[0]
    last = r.rsplit("/", 1)[-1]
    if ":" not in last:
        return None
    return last.rsplit(":", 1)[-1]


def digest_of(ref: str) -> str | None:
    """Pinned digest, or None when the ref names a tag (or is bare).

    A digest is an immutable content address: it survives a tag move
    and stays meaningful after a registry prunes the tag. Digest
    comparison is byte identity — equal digests are the same bytes,
    different digests are provably different content.
    """
    r = str(ref).strip()
    if "@" not in r:
        return None
    digest = r.split("@", 1)[1].strip()
    if not digest:
        return None
    return digest


def match_artifact(ref: str, artifact_ref: str) -> bool:
    return split_image_ref(ref) == split_image_ref(artifact_ref)


def namespace_pattern(artifact_ref: str) -> tuple[str, str] | None:
    """(registry, namespace) for a `<registry>/<namespace>/*` scope element.

    A namespace element names every repository under it -- how a
    catalogue-wide change (the Bitnami move) is stated without listing
    example images as if they were the scope. Without a tag predicate it
    is an *envelope* (see ``element_role``).
    """
    registry, namespace, name = split_image_ref(artifact_ref)
    return (registry, namespace) if name == "*" else None


#: Tag predicates an artifact element may carry instead of a literal tag:
#: ``<version>`` -- every version-like tag (``1.25``, ``7.2.4-debian-12-r3``,
#: not ``latest``); ``*`` -- every tag.
TAG_VERSION = "<version>"
TAG_ANY = "*"


def _version_like(tag: str) -> bool:
    return detect_scheme(_tag_version(tag)) == "generic"


def element_role(artifact_ref: str) -> str:
    """``envelope`` or ``exact`` (TR-2026-01, element roles).

    An exact element claims everything it denotes is in scope, so
    membership is a positive. An envelope only bounds the affected set:
    membership is "possibly in scope" (RELATED), and only exclusion from
    it is decisive. The role follows from the element's form: a
    namespace without a tag predicate is an envelope -- a catalogue-wide
    change rarely reaches every tag (Bitnami's ``latest`` stayed) -- and
    every other element is exact.
    """
    if namespace_pattern(artifact_ref) is not None and tag_of(artifact_ref) is None:
        return "envelope"
    return "exact"


def _tag_membership(ref: str, element_tag: str | None) -> bool | None:
    """Does ref's tag fall under the element's tag or tag predicate?

    True / False when decided. None when ref pins only a digest: its tag,
    and so its membership in a tag-restricted element, is unknown. A ref
    with neither tag nor digest is ``latest``, as Docker reads it.
    """
    if element_tag in (None, TAG_ANY):
        return True
    dep_tag = tag_of(ref)
    if dep_tag is None:
        if digest_of(ref):
            return None
        dep_tag = "latest"
    if element_tag == TAG_VERSION:
        return _version_like(dep_tag)
    return dep_tag == element_tag


def _scope(event: OSSEvent) -> dict:
    scope = event.scope
    if scope is None:
        return {
            "kind": "project",
            "versions": [],
            "artifacts": [],
            "packages": [],
            "registries": [],
        }
    return {
        "kind": scope.kind,
        "versions": list(scope.versions or []),
        "artifacts": list(scope.artifacts or []),
        "packages": list(scope.packages or []),
        "registries": list(scope.registries or []),
    }


def tag_vs_digest_policy(ref: str, artifact_ref: str) -> dict[str, str | bool | None]:
    """Tag-vs-digest pinning policy for two refs of the same artifact.

    Same-identity precondition: callers reach here only after
    split_image_ref equality, so both refs name the same
    registry/namespace/name and only the pinning form can differ.

    - digest vs digest, equal: the same immutable bytes — the only
      form that is exact artifact identity.
    - digest vs digest, different: different bytes, but not proof of
      exclusion. OCI object levels are not recorded, so one digest may
      be an image index and the other one of its platform manifests --
      the same image. RELATED until levels are resolved, never a clear.
    - digest vs tag (or tag vs digest): the refs agree on the
      repository but one side pins bytes while the other names a
      moving pointer. A tag can move onto (or away from) the pinned
      digest at any time, so this is RELATED with the uncertainty
      visible — never AFFECTS_ARTIFACT, never NOT_AFFECTED.
    - tag vs tag: current tag semantics apply unchanged (see
      event_affects_ref); comparing tags says nothing about bytes.

    The policy, not the volume of code, is the deliverable: a moving
    tag never reports digest-level certainty.
    """
    dep_digest = digest_of(ref)
    art_digest = digest_of(artifact_ref)
    if dep_digest is None or art_digest is None:
        if dep_digest == art_digest:
            return {}  # tag vs tag: no policy opinion, caller decides
        return {
            "affected": False,
            "via": None,
            "relationship": "RELATED",
            "detail": (
                f"{ref} and {artifact_ref} name the same repository but mix pinning "
                "forms (digest vs tag); a moving tag never reports digest-level "
                "certainty"
            ),
        }
    if dep_digest == art_digest:
        return {}  # equal pinned digests: exact identity, caller reports
    return {
        "affected": False,
        "via": None,
        "relationship": "RELATED",
        "detail": (
            f"{ref} pins digest {dep_digest} and {artifact_ref} pins {art_digest}; "
            "OCI object levels are unknown (an index and its platform manifest "
            "differ in digest), so this is not a clearance"
        ),
    }


def _artifact_candidates(
    ref: str, candidates: list[str], inside: str, *, examples: bool = False
) -> dict[str, str | bool | None] | None:
    """Every candidate evaluated against ref -- no early return.

    Membership in an exact element is AFFECTS_ARTIFACT. Membership in an
    envelope, an undetermined pinning comparison (digest vs tag), or an
    unknown tag is RELATED, and RELATED beats a decisive exclusion. With
    ``examples`` (an event's named ``affected_artifacts``, which
    illustrate a change rather than bound it), another tag of a named
    repository is RELATED rather than excluded: naming ``redis:7.2``
    says nothing either way about ``redis:latest`` (TR-2026-01 D7).
    None when no candidate relates to ref at all.
    """
    undetermined = None
    excluded = None
    for candidate in candidates:
        element_tag = tag_of(candidate)
        pattern = namespace_pattern(candidate)
        if pattern is not None:
            if split_image_ref(ref)[:2] != pattern:
                continue
            if element_role(candidate) == "envelope":
                undetermined = undetermined or {
                    "affected": False,
                    "via": None,
                    "relationship": "RELATED",
                    "detail": (
                        f"{ref} is inside envelope {candidate}: possibly in scope, "
                        "but the envelope may include unaffected tags"
                    ),
                }
                continue
            member = _tag_membership(ref, element_tag)
            if member:
                return {
                    "affected": True,
                    "via": "artifact",
                    "relationship": "AFFECTS_ARTIFACT",
                    "detail": f"{ref} is inside event namespace scope {candidate}",
                }
            if member is None:
                undetermined = undetermined or {
                    "affected": False,
                    "via": None,
                    "relationship": "RELATED",
                    "detail": f"{ref} pins a digest; its tag under {candidate} is unknown",
                }
            continue
        if not match_artifact(ref, candidate):
            continue
        if digest_of(candidate) is None and element_tag in (None, TAG_ANY):
            # A repository element covers every reference to the repository,
            # whatever its tag or digest: no pinning comparison to make
            # (TR-2026-01 D14).
            return {
                "affected": True,
                "via": "artifact",
                "relationship": "AFFECTS_ARTIFACT",
                "detail": f"{ref} {inside} {candidate}",
            }
        policy = tag_vs_digest_policy(ref, candidate)
        if policy:
            if policy["relationship"] == "RELATED":
                undetermined = undetermined or policy
            else:
                excluded = excluded or policy
            continue
        if digest_of(candidate) and digest_of(ref):
            member = True  # equal pinned digests: exact identity
        else:
            member = _tag_membership(ref, element_tag)
        if member:
            return {
                "affected": True,
                "via": "artifact",
                "relationship": "AFFECTS_ARTIFACT",
                "detail": f"{ref} {inside} {candidate}",
            }
        if member is None or examples:
            undetermined = undetermined or {
                "affected": False,
                "via": None,
                "relationship": "RELATED",
                "detail": (
                    f"{ref} shares the repository of {candidate} but not its tag; "
                    "the named tag does not establish the others"
                ),
            }
        else:
            excluded = excluded or {
                "affected": False,
                "via": None,
                "relationship": "NOT_AFFECTED",
                "detail": f"{ref} carries a tag outside event element {candidate}",
            }
    return undetermined or excluded


def _strongest(
    *results: dict[str, str | bool | None] | None,
) -> dict[str, str | bool | None] | None:
    """Affected beats undetermined beats excluded; None if all are None."""
    present = [r for r in results if r]
    for result in present:
        if result.get("affected"):
            return result
    for result in present:
        if result.get("relationship") == "RELATED":
            return result
    return present[0] if present else None


def _exclusion(
    event: OSSEvent, result: dict[str, str | bool | None]
) -> dict[str, str | bool | None]:
    """A NOT_AFFECTED result stands only against a declared-complete scope.

    Completeness is opt-in (``Scope.exhaustive`` defaults to False): an
    unspecified or partial scope lists known members only, so absence
    from it is not evidence of exclusion -- RELATED instead. A
    declaration must also record its basis (TR-2026-01 N3).
    """
    if result.get("relationship") != "NOT_AFFECTED":
        return result
    if event.scope is not None and event.scope.admits_negative():
        return result
    why = (
        "scope completeness has no recorded basis"
        if event.scope is not None and event.scope.exhaustive
        else "scope is not exhaustive"
    )
    return {
        **result,
        "relationship": "RELATED",
        "detail": f"{result['detail']}; {why}, so not a clearance",
    }


def event_affects_ref(event: OSSEvent, ref: str) -> dict[str, str | bool | None]:
    """Return {affected, via, relationship, detail} for one dependency ref."""
    return _exclusion(event, _event_affects_ref(event, ref))


def _event_affects_ref(event: OSSEvent, ref: str) -> dict[str, str | bool | None]:
    """Named examples and the scope, evaluated together; the strongest wins.

    A named example that leaves ref undetermined (a tag against an
    example digest) must not hide what the scope decides: a member of
    the event's release line is affected whatever the examples say
    (TR-2026-01 D15).
    """
    # The pinning policy owns the verdict whenever the two refs mix
    # forms or disagree on bytes: a moving tag never reports
    # digest-level certainty.
    named = _artifact_candidates(
        ref,
        [a.ref for a in event.affected_artifacts],
        "matches affected artifact",
        examples=True,
    )
    if named is not None and named.get("affected"):
        return named
    scoped = _scope_result(event, ref)
    return _strongest(named, scoped) or scoped


def _scope_result(event: OSSEvent, ref: str) -> dict[str, str | bool | None]:
    """What the event's scope (not its named examples) says about ref."""
    scope = _scope(event)
    kind = scope["kind"]
    inside = (
        _artifact_candidates(ref, scope["artifacts"], "is inside event artifact scope")
        if kind == "artifact" and scope["artifacts"]
        else None
    )
    if inside is not None:
        return inside
    if kind == "artifact" and scope["artifacts"]:
        return {
            "affected": False,
            "via": None,
            "relationship": "NOT_AFFECTED",
            "detail": f"{ref} is outside the event artifact scope",
        }
    if kind == "version" and scope["versions"]:
        slug = resolve_project(ref)
        if slug != event.project_slug:
            unresolved = _unresolved_identity(event, ref)
            if unresolved:
                return unresolved
            trust = resolution_trust(ref)
            # A version scope belongs to the event's project. A tag that
            # merely collides with a scope version of a different project
            # has nothing to do with it: docker.io/bitnami/redis:6.2 must
            # not inherit an upstream redis EOL, and docker.io/postgres:6.2
            # must not match anything by tag alone. Identity decides before
            # the tag is read, and only a curated mapping proves another
            # project: a heuristic or distrusted one is undetermined.
            if trust["identity_status"] != "VERIFIED":
                return {
                    "affected": False,
                    "via": None,
                    "relationship": "RELATED",
                    "detail": (
                        f"{ref} resolves to {slug} only via {trust['via']} "
                        f"({trust['identity_status']}); not a proven exclusion from "
                        f"{event.project_slug} version scope {scope['versions']}"
                    ),
                }
            # A curated mapping to another project is positive evidence of
            # no association; it needs no complete scope (TR-2026-01 S2).
            return {
                "affected": False,
                "via": None,
                "relationship": "UNKNOWN",
                "detail": (
                    f"{ref} resolves to project {slug}, not {event.project_slug}: "
                    f"no association with version scope {scope['versions']}"
                ),
            }
        tag = tag_of(ref)
        if not tag or tag == "latest":
            return {
                "affected": False,
                "via": None,
                "relationship": "RELATED",
                "detail": f"{ref} carries no comparable version for scope {scope['versions']}",
            }
        tag_version = _tag_version(tag)
        comparable = True
        for version in scope["versions"]:
            within = in_release_line(tag_version, str(version))
            if within is None:
                comparable = False
            elif within:
                return {
                    "affected": True,
                    "via": "version",
                    "relationship": "AFFECTS_VERSION",
                    "detail": f"{ref} tag {tag} is within event scope version {version}",
                }
        if not comparable:
            # Never a clear: a tag we cannot compare is not "outside" a scope.
            return {
                "affected": False,
                "via": None,
                "relationship": "RELATED",
                "detail": f"{ref} tag {tag} is not comparable with scope {scope['versions']}",
            }
        return {
            "affected": False,
            "via": None,
            "relationship": "NOT_AFFECTED",
            "detail": f"{ref} tag {tag} is outside event scope versions {scope['versions']}",
        }
    if kind == "package" and scope["packages"]:
        if resolve_project(ref) != event.project_slug:
            # A package scope belongs to the event's project; an image of
            # another project has no association with it at all.
            unresolved = _unresolved_identity(event, ref)
            if unresolved:
                return unresolved
            return {
                "affected": False,
                "via": None,
                "relationship": "UNKNOWN",
                "detail": f"{ref} matches nothing in {event.id}",
            }
        return {
            "affected": False,
            "via": None,
            "relationship": "RELATED",
            "detail": f"{ref} is an image ref; event scope names packages {scope['packages']}",
        }
    if kind == "registry" and scope["registries"]:
        registry = split_image_ref(ref)[0]
        if registry in scope["registries"]:
            return {
                "affected": False,
                "via": None,
                "relationship": "RELATED",
                "detail": f"{ref} shares event registry scope but no artifact was established",
            }
        return {
            "affected": False,
            "via": None,
            "relationship": "NOT_AFFECTED",
            "detail": f"{ref} registry is outside event scope {scope['registries']}",
        }
    if resolve_project(ref) == event.project_slug:
        return {
            "affected": False,
            "via": "project",
            "relationship": "AFFECTS_PROJECT",
            "detail": (
                f"{ref} resolves to event project {event.project_slug}; impact not established"
            ),
        }
    unresolved = _unresolved_identity(event, ref)
    if unresolved:
        return unresolved
    return {
        "affected": False,
        "via": None,
        "relationship": "UNKNOWN",
        "detail": f"{ref} matches nothing in {event.id}",
    }


def _unresolved_identity(event: OSSEvent, ref: str) -> dict[str, str | bool | None] | None:
    """RELATED whenever ref's identity is unresolved, whatever its name.

    An unmapped ref resolves only to itself ("self" identity). That is
    not evidence of *another* project: github.com/etcd-io/etcd is
    self-resolved while naming etcd, and a mirror, fork or rename of a
    project can carry any name at all. Only a curated mapping to a
    different project supports "no association" or an identity-based
    exclusion; an unmapped ref is undetermined -- never dropped as
    unrelated, never excluded (TR-2026-01 D10).
    """
    trust = resolution_trust(ref)
    if trust["via"] != "self":
        return None
    return {
        "affected": False,
        "via": None,
        "relationship": "RELATED",
        "detail": (
            f"{ref} resolves only to itself; identity unresolved, so it is "
            f"neither excluded from nor unrelated to project {event.project_slug}"
        ),
    }
