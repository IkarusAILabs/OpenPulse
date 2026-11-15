"""Lookalike-name indicators (track T, T-A2).

A package name that closely resembles a well-known one may be a typosquat,
or a hallucinated name someone registered (threats T1, T2). This check
compares a candidate PyPI or npm name with two references and names every
rule that fires:

- the curated catalog's packages for that ecosystem;
- a pinned, separately licensed snapshot of popular names
  (``data/reference/``, built by ``scripts/refresh_reference_names.py``):
  npm-high-impact (MIT) for npm, a dated PyPI download query (CC BY 4.0)
  for PyPI once a maintainer has run it.

Rules, each reported with the reference it matched:

- ``separator``: equal once ``-``, ``_`` and ``.`` are removed;
- ``edit_distance``: within one edit (names of 5+ characters) or two
  (10+), counting a swap of neighbours as one edit;
- ``confusable``: equal under the UTS #39 skeleton restricted to ASCII
  (``1``/``I``/``|`` as ``l``, ``0`` as ``O``, ``m`` as ``rn``);
- ``scope``: an npm ``@scope/name`` whose ``name`` is a reference.

A fired rule is SUSPICIOUS_INCONCLUSIVE: an indicator, never a typosquat
verdict, and never evidence of intent. A name that is itself a reference
is VERIFIED_RELATIONSHIP. Nothing firing is MISSING_EVIDENCE: no indicator
is not evidence that a name is authentic (roadmap, track T). Local data
only: no network, no budget. Nothing here feeds a verdict.
"""

from __future__ import annotations

import functools
import json
import re
from typing import Any

from core.registry_existence import (
    _NPM_NAME,
    _PYPI_NAME,
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    SUSPICIOUS_INCONCLUSIVE,
    VERIFIED_RELATIONSHIP,
    ecosystem_of,
)
from core.resources import data_path

CHECK = "lookalike"
MAX_INDICATORS = 10
_SEPARATORS = re.compile(r"[-_.]+")

_STATEMENTS = {
    SUSPICIOUS_INCONCLUSIVE: (
        "the name resembles {n} reference name(s) under the rules listed; an indicator to "
        "check, never a typosquat verdict and never evidence of intent"
    ),
    VERIFIED_RELATIONSHIP: "the name is itself a reference name",
    MISSING_EVIDENCE: (
        "no indicator fired against the reference names; this is not evidence that the "
        "name is authentic"
    ),
    NOT_PERFORMED: "lookalike indicators not computed: {why}",
}
_WHY = {
    "unsupported": "computed for PyPI and npm package names only",
    "invalid": "the name does not match the ecosystem's grammar",
}


def _normalize(ecosystem: str, name: str) -> str:
    return _SEPARATORS.sub("-", name).lower() if ecosystem == "PyPI" else name.lower()


@functools.lru_cache(maxsize=1)
def _confusables() -> dict[str, str]:
    files = sorted(data_path("reference").glob("uts39-confusables-ascii-*.json"))
    if not files:
        return {}
    return json.loads(files[-1].read_text(encoding="utf-8"))["mappings"]


@functools.lru_cache(maxsize=4)
def references(ecosystem: str) -> tuple[frozenset[str], tuple[dict[str, Any], ...]]:
    """(normalized reference names, [{source, version, names}]) for one ecosystem."""
    from core.entities.catalog import load_catalog

    names: set[str] = set()
    curated = {
        _normalize(ecosystem, str(p.get("name")))
        for entry in load_catalog()
        for p in entry.get("packages") or []
        if isinstance(p, dict) and p.get("ecosystem") == ecosystem and p.get("name")
    }
    names |= curated
    sources = [{"source": "OpenPulse curated catalog", "version": None, "names": len(curated)}]
    prefix = {"npm": "npm-high-impact-", "PyPI": "pypi-top-"}[ecosystem]
    snapshots = sorted(data_path("reference").glob(f"{prefix}*.json"))
    if snapshots:
        snapshot = json.loads(snapshots[-1].read_text(encoding="utf-8"))
        popular = {_normalize(ecosystem, n) for n in snapshot["names"]}
        names |= popular
        sources.append(
            {"source": snapshot["source"], "version": snapshot["version"], "names": len(popular)}
        )
    else:
        sources.append({"source": "popular-name list", "version": None, "names": 0})
    return frozenset(names), tuple(sources)


@functools.lru_cache(maxsize=65536)
def _skeleton(name: str) -> str:
    mappings = _confusables()
    return "".join(mappings.get(char, char) for char in name).lower()


def _within(a: str, b: str, limit: int) -> bool:
    """Optimal string alignment distance <= limit (adjacent swap = 1 edit)."""
    if abs(len(a) - len(b)) > limit:
        return False
    previous2: list[int] = []
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                current[j] = min(current[j], previous2[j - 2] + 1)
        if min(current) > limit:
            return False
        previous2, previous = previous, current
    return previous[-1] <= limit


def _indicators(ecosystem: str, name: str, refs: frozenset[str]) -> list[dict[str, str]]:
    candidate = _normalize(ecosystem, name)
    stripped = _SEPARATORS.sub("", candidate)
    skeleton = _skeleton(name)
    found: list[dict[str, str]] = []
    for ref in sorted(refs):
        rule = None
        if _SEPARATORS.sub("", ref) == stripped:
            rule = "separator"
        elif _skeleton(ref) == skeleton:
            rule = "confusable"
        elif len(ref) >= 5 and _within(candidate, ref, 2 if len(ref) >= 10 else 1):
            rule = "edit_distance"
        if rule:
            found.append({"rule": rule, "reference": ref})
    if ecosystem == "npm" and candidate.startswith("@") and "/" in candidate:
        bare = candidate.split("/", 1)[1]
        if bare in refs:
            found.append({"rule": "scope", "reference": bare})
    return found


def check(ecosystem: str | None, name: str) -> dict[str, Any]:
    """One T-F1 record for one candidate name."""
    eco = ecosystem_of(ecosystem)
    if eco is None:
        return _record(NOT_PERFORMED, why="unsupported")
    grammar = _PYPI_NAME if eco == "PyPI" else _NPM_NAME
    if not grammar.fullmatch(name if eco == "PyPI" else name.lower()):
        return _record(NOT_PERFORMED, why="invalid")
    refs, sources = references(eco)
    evidence: dict[str, Any] = {"references": [dict(s) for s in sources]}
    if _normalize(eco, name) in refs:
        return _record(VERIFIED_RELATIONSHIP, **evidence)
    indicators = _indicators(eco, name, refs)
    if indicators:
        evidence["indicators"] = indicators[:MAX_INDICATORS]
        evidence["indicators_total"] = len(indicators)
        return _record(SUSPICIOUS_INCONCLUSIVE, n=len(indicators), **evidence)
    return _record(MISSING_EVIDENCE, **evidence)


def _record(status: str, *, why: str = "", n: int = 0, **evidence: Any) -> dict[str, Any]:
    return {
        "check": CHECK,
        "status": status,
        "statement": _STATEMENTS[status].format(n=n, why=_WHY.get(why, "")),
        "evidence": evidence,
    }


__all__ = ["CHECK", "check", "references"]
