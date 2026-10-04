"""Typed identity references — same identity evidence, same thing.

The slug resolver (`resolve.py`) stays the default path. These refs
add explicit, typed identity where correlation strength matters
(security findings, artifact attribution) so reviewers can see *why*
two names were treated as the same thing.

Resolution trust (`resolution_trust`): every mapping records *how*
the slug was reached and an identity status:

- VERIFIED — curated explicit alias, catalog mapping, or
  self-identity (the ref maps to itself: no alias mapping to
  distrust). Entries may declare an ``identity:`` block with
  source/reviewed_at/maintainer/confidence.
- REVIEW_REQUIRED — heuristic mappings (the generic namespace rule)
  or catalog entries flagged for review. Usable for discovery, never
  enough alone for strong customer-impact conclusions.
- UNVERIFIED — explicitly distrusted mappings. Never elevates impact.

``check.py`` caps affected verdicts that rely on REVIEW_REQUIRED /
UNVERIFIED mappings at EMERGING confidence. Exact artifact equality
needs no mapping and is never capped: triple equality is
self-identity, the strongest form.
"""

from __future__ import annotations

from typing import Any, Literal

from core.entities.resolve import EXPLICIT_ALIASES, _bitnami_rule, _catalog_hit, normalize_ref

IdentityKind = Literal[
    "project", "package", "artifact", "repository", "registry_artifact", "purl", "cpe"
]

VERIFIED = "VERIFIED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
UNVERIFIED = "UNVERIFIED"

VALID_STATUSES = (VERIFIED, REVIEW_REQUIRED, UNVERIFIED)


def catalog_entry_for_slug(
    slug: str, catalog: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Catalog entry for a slug ({} when absent). Testable via `catalog`."""
    if catalog is None:
        from core.entities.catalog import load_catalog

        catalog = load_catalog()
    for entry in catalog:
        if isinstance(entry, dict) and str(entry.get("slug", "")) == slug:
            return entry
    return {}


def identity_block_for_slug(
    slug: str, catalog: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Normalized identity metadata: {status, source, reviewed_at,
    maintainer, confidence, note}. Reads the formal ``identity:`` block
    first, then legacy flat keys (identity_source/reviewed_at/
    maintainer/confidence). Absent metadata -> {} (caller decides)."""
    entry = catalog_entry_for_slug(slug, catalog)
    block = entry.get("identity")
    if isinstance(block, dict):
        status = str(block.get("status", "")).upper()
        return {
            "status": status if status in VALID_STATUSES else REVIEW_REQUIRED,
            "source": block.get("source"),
            "reviewed_at": block.get("reviewed_at"),
            "maintainer": block.get("maintainer"),
            "confidence": block.get("confidence"),
            "note": block.get("note"),
        }
    if any(k in entry for k in ("identity_source", "reviewed_at", "maintainer", "confidence")):
        return {
            "status": VERIFIED,
            "source": entry.get("identity_source"),
            "reviewed_at": entry.get("reviewed_at"),
            "maintainer": entry.get("maintainer"),
            "confidence": entry.get("confidence"),
            "note": None,
        }
    return {}


def resolution_trust(ref: str, catalog: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """How `ref` resolves: {slug, via, identity_status, detail}.

    `via` is explicit | catalog | namespace_rule | self. Only
    non-trivial mappings can be REVIEW_REQUIRED/UNVERIFIED;
    self-identity carries no mapping risk.
    """
    from core.entities.catalog import catalog_alias_map, load_catalog

    normalized = normalize_ref(ref)
    if normalized in EXPLICIT_ALIASES:
        return {
            "slug": EXPLICIT_ALIASES[normalized],
            "via": "explicit",
            "identity_status": VERIFIED,
            "detail": "curated explicit alias",
        }
    alias_map = catalog_alias_map(catalog if catalog is not None else load_catalog())
    hit = _catalog_hit(str(ref), normalized, alias_map)
    if hit:
        slug = hit
        block = identity_block_for_slug(slug, catalog)
        return {
            "slug": slug,
            "via": "catalog",
            "identity_status": block.get("status", VERIFIED),
            "detail": block.get("note") or "catalog alias/image mapping",
        }
    ruled = _bitnami_rule(normalized)
    if ruled:
        return {
            "slug": ruled,
            "via": "namespace_rule",
            "identity_status": REVIEW_REQUIRED,
            "detail": "generic namespace heuristic, not a curated mapping",
        }
    return {
        "slug": normalized,
        "via": "self",
        "identity_status": VERIFIED,
        "detail": "unmapped ref: identity is the ref itself (no alias mapping to distrust)",
    }


def identity_refs_for(ref: str) -> list[dict[str, str]]:
    """All identity forms derivable from one dependency ref, strongest first."""
    from core.entities.catalog import purl_for
    from core.entities.resolve import normalize_ref, resolve_project
    from core.risk.match import split_image_ref

    normalized = normalize_ref(ref)
    slug = resolve_project(ref)
    refs = [
        {"kind": "project", "value": slug},
        {"kind": "artifact", "value": normalized},
    ]
    registry, namespace, name = split_image_ref(ref)
    refs.append({"kind": "registry_artifact", "value": f"{registry}/{namespace}/{name}"})
    if "/" in normalized and "docker.io" not in normalized and "@" not in normalized:
        parts = normalized.split("/")
        if len(parts) == 2:
            refs.append({"kind": "repository", "value": normalized})
            refs.append({"kind": "purl", "value": purl_for("github", parts[0], parts[1])})
    refs.append({"kind": "purl", "value": purl_for("docker", namespace, name)})
    return refs


def same_identity(a: list[dict[str, str]], b: list[dict[str, str]]) -> dict[str, Any]:
    """Do two ref-sets share any identity value? Returns the shared ref or {}."""
    values_b = {r["value"] for r in b}
    for ref in a:
        if ref["value"] in values_b:
            return {"same": True, "via": ref}
    return {"same": False, "via": None}
