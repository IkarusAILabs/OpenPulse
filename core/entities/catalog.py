"""Canonical catalog loader — data/canonical_projects.yaml.

The catalog is the single source for entity resolution. Aliases in the
file must be lowercase and tag/digest-free (enforced by tests).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from functools import lru_cache
from types import MappingProxyType
from typing import Any

import yaml

from core.resources import data_path

#: Checkout `data/` or the installed `openpulse_data` package (core.resources).
DEFAULT_PATH = data_path("canonical_projects.yaml")


@lru_cache(maxsize=4)
def load_catalog(path: str | None = None) -> list[dict[str, Any]]:
    with open(path or DEFAULT_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


#: Derived maps, memoised per catalog object. Identity resolution asked for
#: them on every dependency check and rebuilt them each time, which made
#: matching about 1.8x slower after F1 (benchmarks/REPORT.md). Each entry
#: keeps its catalog alive, so an id() cannot be reused while cached, and
#: is checked against the catalog's length as a guard. Values are
#: read-only, so a caller cannot corrupt the shared result.
_DERIVED: dict[tuple[str, int], tuple[list[dict[str, Any]], int, Any]] = {}
_DERIVED_LIMIT = 16


def _memo(kind: str, catalog: list[dict[str, Any]], build: Callable[[], Any]) -> Any:
    key = (kind, id(catalog))
    hit = _DERIVED.get(key)
    if hit is not None and hit[0] is catalog and hit[1] == len(catalog):
        return hit[2]
    value = build()
    if len(_DERIVED) >= _DERIVED_LIMIT:
        _DERIVED.pop(next(iter(_DERIVED)))
    _DERIVED[key] = (catalog, len(catalog), value)
    return value


def catalog_alias_map(catalog: list[dict[str, Any]]) -> Mapping[str, str]:
    """alias -> slug for every alias and docker image in the catalog."""
    return _memo("alias", catalog, lambda: MappingProxyType(_alias_map(catalog)))


def _alias_map(catalog: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for entry in catalog:
        slug = entry.get("slug", "")
        for alias in (entry.get("aliases") or []) + (entry.get("docker_images") or []):
            out.setdefault(str(alias).strip().lower(), slug)
    return out


def endoflife_map(catalog: list[dict[str, Any]] | None = None) -> dict[str, str]:
    """slug -> endoflife.date product for entries that declare one."""
    return {
        str(e["slug"]): str(e["endoflife"])
        for e in (catalog if catalog is not None else load_catalog())
        if e.get("slug") and e.get("endoflife")
    }


def osv_map(catalog: list[dict[str, Any]] | None = None) -> dict[str, tuple[str, str]]:
    """slug -> (package, ecosystem) for entries that declare an `osv` block.

    Only entries with a verified (package, ecosystem) mapping belong here —
    OSV queries are package-scoped, so a wrong mapping would poison
    identity evidence downstream.
    """
    out: dict[str, tuple[str, str]] = {}
    for e in catalog if catalog is not None else load_catalog():
        block = e.get("osv")
        if not (e.get("slug") and isinstance(block, dict)):
            continue
        package = block.get("package")
        ecosystem = block.get("ecosystem")
        if package and ecosystem:
            out[str(e["slug"])] = (str(package), str(ecosystem))
    return out


def package_name_key(ecosystem: str, name: str) -> tuple[str, str]:
    """(ecosystem, name) as compared: lowercase, PyPI names PEP 503-folded,
    and Maven `groupId:artifactId` (as manifests and SBOMs spell it) in the
    catalog's `groupId/artifactId` form."""
    eco = ecosystem.strip().lower()
    key = name.strip().lower()
    if eco == "pypi":
        key = re.sub(r"[-_.]+", "-", key)
    elif eco == "maven":
        key = key.replace(":", "/", 1)
    return eco, key


def qualified_package(value: str) -> tuple[str, str] | None:
    """A package-scope value written as a purl -> canonical (ecosystem, name).

    ``pkg:pypi/redis`` names exactly one package (TR-2026-01 F3). None for
    a purl that does not parse, maps to no supported ecosystem, or carries
    a version: a scope value names a package, and versions belong in a
    version scope. Callers treat None as undetermined, never as exclusion.
    """
    from core.sbom_reader import _dep_from_purl, _split_purl

    parts = _split_purl(value)
    if parts is None or parts["version"]:
        return None
    dep, _ = _dep_from_purl(value)
    if dep is None or dep.get("kind") != "package":
        return None
    return package_name_key(str(dep["ecosystem"]), str(dep["package"]))


def is_qualified(value: str) -> bool:
    """Is a package-scope value ecosystem-qualified (a purl)?"""
    return str(value).startswith("pkg:")


def package_map(catalog: list[dict[str, Any]] | None = None) -> Mapping[tuple[str, str], str]:
    """(ecosystem, name) -> slug, from `packages` lists and `osv` blocks.

    A package name is an identity only inside its ecosystem: PyPI `redis`
    (redis-py) and the Redis server share a name, not a project.
    """
    entries = catalog if catalog is not None else load_catalog()
    return _memo("package", entries, lambda: MappingProxyType(_package_map(entries)))


def _package_map(catalog: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for e in catalog:
        slug = str(e.get("slug", ""))
        if not slug:
            continue
        pairs = [(p.get("ecosystem"), p.get("name")) for p in e.get("packages") or []]
        block = e.get("osv")
        if isinstance(block, dict):
            pairs.append((block.get("ecosystem"), block.get("package")))
        for ecosystem, name in pairs:
            if ecosystem and name:
                out.setdefault(package_name_key(str(ecosystem), str(name)), slug)
    return out


def package_curated_slugs(catalog: list[dict[str, Any]] | None = None) -> frozenset[str]:
    """Slugs whose published packages are curated (`packages` or `osv` present).

    For these, a package that merely shares an alias is not the project:
    only a listed (ecosystem, name) is.
    """
    entries = catalog if catalog is not None else load_catalog()
    return _memo(
        "curated",
        entries,
        lambda: frozenset(
            str(e["slug"])
            for e in entries
            if e.get("slug") and ("packages" in e or isinstance(e.get("osv"), dict))
        ),
    )


def purl_for(kind: str, namespace: str, name: str, version: str | None = None) -> str:
    """Minimal Package-URL builder (https://github.com/package-url/purl-spec)."""
    base = {
        "docker": f"pkg:docker/{namespace}/{name}",
        "github": f"pkg:github/{namespace}/{name}",
        "generic": f"pkg:generic/{name}",
    }.get(kind, f"pkg:generic/{name}")
    return f"{base}@{version}" if version else base


def project_context(slug: str) -> dict[str, Any]:
    """Identity context for correlation: slug + aliases + vendor-ish names."""
    entry = next((e for e in load_catalog() if e.get("slug") == slug), None)
    if not entry:
        return {"slug": slug}
    return {
        "slug": slug,
        "aliases": list(entry.get("aliases") or []),
        "vendors": [entry.get("display_name", ""), slug],
    }
