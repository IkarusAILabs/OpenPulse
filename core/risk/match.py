"""Impact match — does an OSSEvent affect a dependency ref?

Conservative by construction:
- Exact artifact triple equality → AFFECTS_ARTIFACT.
- Populated event scope narrows everything else: a dependency outside
  an explicit scope is NOT_AFFECTED, not UNKNOWN.
- Bare project-slug equality is contextual (AFFECTS_PROJECT) and never
  means affected on its own.
- No scope at all → legacy fallback (artifact, then project context).

`docker.io/redis:7.2` does NOT match a `docker.io/bitnami/redis`
artifact: different namespace, different stack. That distinction is
the whole point of the Bitnami case.
"""

from __future__ import annotations

from core.entities.resolve import normalize_ref, resolve_project
from core.schema.models import OSSEvent
from core.versions import compare


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


def tag_of(ref: str) -> str | None:
    """Image tag, or None when absent (digests stripped first)."""
    r = str(ref).split("@")[0]
    last = r.rsplit("/", 1)[-1]
    if ":" not in last:
        return None
    return last.rsplit(":", 1)[-1]


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


def event_affects_ref(event: OSSEvent, ref: str) -> dict[str, str | bool | None]:
    """Return {affected, via, relationship, detail} for one dependency ref."""
    for a in event.affected_artifacts:
        if match_artifact(ref, a.ref):
            return {
                "affected": True,
                "via": "artifact",
                "relationship": "AFFECTS_ARTIFACT",
                "detail": f"{ref} matches affected artifact {a.ref}",
            }
    scope = _scope(event)
    kind = scope["kind"]
    if kind == "artifact" and scope["artifacts"]:
        for candidate in scope["artifacts"]:
            if match_artifact(ref, candidate):
                return {
                    "affected": True,
                    "via": "artifact",
                    "relationship": "AFFECTS_ARTIFACT",
                    "detail": f"{ref} is inside event artifact scope {candidate}",
                }
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
        for version in scope["versions"]:
            if compare(tag, str(version)) == 0:
                return {
                    "affected": True,
                    "via": "version",
                    "relationship": "AFFECTS_VERSION",
                    "detail": f"{ref} tag {tag} matches event scope version {version}",
                }
        return {
            "affected": False,
            "via": None,
            "relationship": "NOT_AFFECTED",
            "detail": f"{ref} tag {tag} is outside event scope versions {scope['versions']}",
        }
    if kind == "package" and scope["packages"]:
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
