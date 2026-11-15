"""Entity resolution: normalize aliases -> CanonicalProject slug.

Precedence:
1. EXPLICIT_ALIASES — curated overrides (Bitnami stacks first).
2. Catalog (data/canonical_projects.yaml) aliases + docker images.
3. Bitnami-namespace rule — any bitnami/bitnamilegacy/bitnamisecure
   image ref becomes a `bitnami-{image}` slug, preserving impact
   attribution for distribution events.
4. Fallback — the normalized ref itself.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from functools import lru_cache

EXPLICIT_ALIASES = {
    "redis": "redis",
    "redis-server": "redis",
    "docker.io/redis": "redis",
    "docker.io/library/redis": "redis",
    "bitnami/redis": "bitnami-redis-stack",
    "docker.io/bitnami/redis": "bitnami-redis-stack",
    "docker.io/bitnamilegacy/redis": "bitnami-redis-stack",
    "docker.io/bitnamisecure/redis": "bitnami-redis-stack",
    "bitnami": "bitnami",
}

BITNAMI_NAMESPACES = (
    "bitnami/",
    "docker.io/bitnami/",
    "bitnamilegacy/",
    "docker.io/bitnamilegacy/",
    "bitnamisecure/",
    "docker.io/bitnamisecure/",
)


#: Hosts that serve Docker Hub under another name. A reference spelled
#: with one of them is the same image as its docker.io spelling, so it
#: must canonicalise to docker.io: otherwise a docker.io namespace scope
#: declared complete clears it (TR-2026-01 D9).
_DOCKER_HUB_HOSTS = re.compile(r"^((?:[a-z][a-z0-9+.-]*://)?)(?:index|registry-1)\.docker\.io/")


def normalize_ref(ref: str) -> str:
    """Lowercase, fold Docker Hub host aliases, strip `@digest`, then
    `:tag` from the LAST path segment.

    A colon in an earlier segment is a registry port or URL scheme, never
    a tag: `localhost:5000/team/redis:7` is `localhost:5000/team/redis`,
    not `localhost` (which would give every image on that registry one
    identity). Single-segment refs keep the old behavior - `name:tag`
    and maven `group:artifact` both cut at the first colon.

    A digest's `@` always follows a name character (`redis@sha256:...`).
    An `@` that starts a segment is part of the name: npm scopes
    (`@types/node`) resolved to the empty string before, so every scoped
    package shared one empty identity.
    """
    r = ref.strip().lower()
    r = _DOCKER_HUB_HOSTS.sub(r"\1docker.io/", r)
    r = re.sub(r"(?<=[^/])@.*$", "", r)  # strip @digest, never a leading @scope
    head, sep, last = r.rpartition("/")
    return head + sep + re.sub(r":.*$", "", last)  # strip :tag


@lru_cache(maxsize=1)
def _catalog_map() -> Mapping[str, str]:
    """The catalog's alias map, or {} only when the catalog file is absent.

    A broken catalog (an alias collision, invalid YAML) raises: turning it
    into {} would silently resolve every reference to itself (#132, #144).
    """
    from core.entities.catalog import catalog_alias_map, load_catalog

    try:
        catalog = load_catalog()
    except FileNotFoundError:
        return {}
    return catalog_alias_map(catalog)


def _bitnami_rule(normalized: str) -> str | None:
    for ns in BITNAMI_NAMESPACES:
        if normalized.startswith(ns):
            image = normalized[len(ns) :].split("/")[0]
            if image and image not in ("bitnami", "bitnamilegacy", "bitnamisecure"):
                return f"bitnami-{image}"
    return None


def _maven_purl_spelling(ref: str) -> str | None:
    """`groupId:artifactId` -> `groupId/artifactId`, else None.

    Maven coordinates join their two identity terms with a colon; the
    catalog lists the purl (slash) spelling because its format forbids
    colons (hygiene rule). Only a bare coordinate qualifies - no path
    segments. A docker `name:tag` also has a single colon, but its
    re-spelling (`name/tag`) never matches a curated alias, so the
    fallback is harmless there.
    """
    if ":" in ref and "/" not in ref:
        return ref.replace(":", "/")
    return None


def _catalog_hit(raw: str, normalized: str, mapping: dict[str, str]) -> str | None:
    """Catalog slug for one ref: direct lookup, then maven re-spelling.

    The maven fallback runs on the RAW ref, not the normalized one:
    tag stripping eats everything from the colon, leaving only the
    groupId, which is not a catalogued identity by itself.
    """
    if normalized in mapping:
        return mapping[normalized]
    purl = _maven_purl_spelling(raw.strip().lower())
    if purl is not None:
        return mapping.get(purl)
    return None


def resolve_project(ref: str) -> str:
    """Return canonical slug for a package/artifact ref."""
    n = normalize_ref(ref)
    if n in EXPLICIT_ALIASES:
        return EXPLICIT_ALIASES[n]
    catalog_hit = _catalog_hit(str(ref), n, _catalog_map())
    if catalog_hit:
        return catalog_hit
    return _bitnami_rule(n) or n
