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
from core.versions import in_release_line


def split_image_ref(ref: str) -> tuple[str, str, str]:
    """(registry, namespace, name) with tags/digests/schemes stripped."""
    r = normalize_ref(ref)
    for scheme in ("oci://", "https://", "http://", "docker://"):
        if r.startswith(scheme):
            r = r[len(scheme) :]
    parts = r.split("/")
    if len(parts) >= 3 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
        registry, rest = parts[0], parts[1:]
    else:
        registry, rest = "docker.io", parts
    if len(rest) == 1:
        namespace, name = "library", rest[0]
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
    - digest vs digest, different: provably different content; the
      pinned bytes are not the artifact the event names.
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
        "relationship": "NOT_AFFECTED",
        "detail": (
            f"{ref} pins digest {dep_digest}, not the bytes the event names "
            f"({artifact_ref} pins {art_digest})"
        ),
    }


def _artifact_candidates(
    ref: str, candidates: list[str], inside: str
) -> dict[str, str | bool | None] | None:
    """Every candidate sharing ref's repository, evaluated -- no early return.

    Any exact match wins (AFFECTS_ARTIFACT). Otherwise an undetermined
    pinning comparison (digest vs tag) beats a decisive exclusion
    (different digests): one element that may point at the pinned
    bytes is enough to withhold a clearance. None when no candidate
    shares the repository at all.
    """
    undetermined = None
    excluded = None
    for candidate in candidates:
        if not match_artifact(ref, candidate):
            continue
        policy = tag_vs_digest_policy(ref, candidate)
        if not policy:
            return {
                "affected": True,
                "via": "artifact",
                "relationship": "AFFECTS_ARTIFACT",
                "detail": f"{ref} {inside} {candidate}",
            }
        if policy["relationship"] == "RELATED":
            undetermined = undetermined or policy
        else:
            excluded = excluded or policy
    return undetermined or excluded


def _exclusion(
    event: OSSEvent, result: dict[str, str | bool | None]
) -> dict[str, str | bool | None]:
    """A NOT_AFFECTED result stands only against an exhaustive scope.

    A scope declared non-exhaustive lists known members only, so
    absence from it is not evidence of exclusion: RELATED instead.
    """
    if result.get("relationship") != "NOT_AFFECTED":
        return result
    if event.scope is None or event.scope.exhaustive:
        return result
    return {
        **result,
        "relationship": "RELATED",
        "detail": f"{result['detail']}; scope is not exhaustive, so not a clearance",
    }


def event_affects_ref(event: OSSEvent, ref: str) -> dict[str, str | bool | None]:
    """Return {affected, via, relationship, detail} for one dependency ref."""
    return _exclusion(event, _event_affects_ref(event, ref))


def _event_affects_ref(event: OSSEvent, ref: str) -> dict[str, str | bool | None]:
    # The pinning policy owns the verdict whenever the two refs mix
    # forms or disagree on bytes: a moving tag never reports
    # digest-level certainty.
    named = _artifact_candidates(
        ref, [a.ref for a in event.affected_artifacts], "matches affected artifact"
    )
    if named is not None:
        return named
    scope = _scope(event)
    kind = scope["kind"]
    if kind == "artifact" and scope["artifacts"]:
        inside = _artifact_candidates(ref, scope["artifacts"], "is inside event artifact scope")
        if inside is not None:
            return inside
        return {
            "affected": False,
            "via": None,
            "relationship": "NOT_AFFECTED",
            "detail": f"{ref} is outside the event artifact scope",
        }
    if kind == "version" and scope["versions"]:
        tag = tag_of(ref)
        if not tag or tag == "latest":
            return {
                "affected": False,
                "via": None,
                "relationship": "RELATED",
                "detail": f"{ref} carries no comparable version for scope {scope['versions']}",
            }
        slug = resolve_project(ref)
        if slug != event.project_slug:
            trust = resolution_trust(ref)
            # A version scope belongs to the event's project. A tag that
            # merely collides with a scope version of a different project
            # is identity-excluded: docker.io/bitnami/redis:6.2 must not
            # inherit an upstream redis EOL, and docker.io/postgres:6.2
            # must not match anything by tag alone. The exclusion is only
            # as good as the resolution behind it: a heuristic or
            # distrusted mapping cannot prove a different project.
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
            return {
                "affected": False,
                "via": None,
                "relationship": "NOT_AFFECTED",
                "detail": (
                    f"{ref} resolves to project {slug}, not {event.project_slug}; "
                    f"version scope {scope['versions']} excludes it"
                ),
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
    return {
        "affected": False,
        "via": None,
        "relationship": "UNKNOWN",
        "detail": f"{ref} matches nothing in {event.id}",
    }
