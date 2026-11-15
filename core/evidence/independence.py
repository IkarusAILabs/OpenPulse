"""Evidence independence — 2 sources != 2 independent sources.

A republished announcement (Source B quoting Source A) must not count
as corroboration, and neither does a second page on the same site.
Evidences are grouped, and two evidences share a group when any of
these links them (transitively):

- the same URL family (``core.evidence.domains.url_family``: the
  registrable domain, or host plus owner on shared hosts). Derived from
  the URL, so a producer cannot split one site into two sources (B2);
- the same declared ``family`` or source name (one shared space);
- ``derived_from`` naming the other's source.

A declared family can only merge groups, never split them.

    independent_count() = distinct groups, not distinct names.

Callers pass evidence dicts (raw) or Evidence/Source models — both
shapes are read defensively.
"""

from __future__ import annotations

from typing import Any

from core.evidence.domains import url_family


def _source_of(evidence: Any) -> dict[str, Any]:
    if isinstance(evidence, dict):
        source = evidence.get("source", {})
        return source if isinstance(source, dict) else {}
    source = getattr(evidence, "source", None)
    if source is None:
        return {}
    if isinstance(source, dict):
        return source
    return {
        "name": getattr(source, "name", None),
        "url": getattr(source, "url", None),
        "family": getattr(source, "family", None),
        "derived_from": getattr(source, "derived_from", None),
    }


def _field(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if value:
            return value
    return None


def independent_count(evidences: list[Any]) -> int:
    """Distinct independent groups after linking shared sites and copies."""
    parent = list(range(len(evidences)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    first_with: dict[tuple[str, str], int] = {}
    names: dict[str, int] = {}
    sources = [_source_of(e) for e in evidences]
    for i, source in enumerate(sources):
        keys = [
            ("site", url_family(_field(source, "url"))),
            # Families and names share one space, as before B2: a family
            # "redis" and a source named "redis" are one group.
            ("label", _field(source, "family")),
            ("label", _field(source, "name")),
        ]
        if not any(value for _, value in keys):
            keys.append(("unknown", "?"))
        for kind, value in keys:
            if not value:
                continue
            key = (kind, str(value))
            if key in first_with:
                union(i, first_with[key])
            else:
                first_with[key] = i
        name = _field(source, "name")
        if name:
            names.setdefault(str(name), i)
    for i, source in enumerate(sources):
        derived = _field(source, "derived_from")
        if derived and str(derived) in names:
            union(i, names[str(derived)])
    return len({find(i) for i in range(len(evidences))})
