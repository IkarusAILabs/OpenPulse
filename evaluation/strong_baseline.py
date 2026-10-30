"""Policy V: the strong conservative baseline (TR-2026-01 §10 baseline v).

It isolates what OpenPulse's verdict engine adds beyond conservative
abstention plus ordinary ecosystem-aware version comparison. It receives
what OpenPulse receives (the same typed scopes, the same admissibility,
the same curated identity mappings) and decides with none of the
engine's matching code:

- references are parsed with the specification oracle's parser
  (``conformance/oracle.py``);
- identity is exact: only a curated, VERIFIED mapping (explicit,
  catalog, or a curated (ecosystem, name) package mapping) ties a
  dependency to a project or to another project. A heuristic or
  self-resolution is unresolved;
- versions are compared by the ecosystem's own comparator where one is
  pinned (PyPI: ``packaging``). Elsewhere only plain dotted numbers are
  compared, and anything else is undetermined;
- every relation it cannot decide is undetermined, and undetermined
  never clears.

Negatives need a scope declared complete with a recorded basis, a
current event, evidence within the freshness bound, and no contradicting
evidence: the admissibility OpenPulse applies, restated here.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

import oracle  # noqa: E402
from packaging.version import InvalidVersion, Version  # noqa: E402

from core.entities.catalog import package_name_key  # noqa: E402
from core.entities.identity import package_trust, resolution_trust  # noqa: E402
from core.schema.models import OSSEvent  # noqa: E402

M, N, U, P, Z = oracle.M, oracle.N, oracle.U, oracle.P, oracle.Z
COMPARATORS = {"pypi": f"packaging {__import__('packaging').__version__}"}

_PACKAGE_PREFIXES = ("pypi:", "npm:", "pkg:", "maven:", "cargo:", "go:")
_NUMERIC = re.compile(r"\d+(?:\.\d+)*")


# --- identity: curated and exact only -------------------------------------


def _identity(dep: dict[str, Any]) -> tuple[str, str | None]:
    """("project", slug) for a curated VERIFIED mapping, else ("unresolved", None)."""
    if dep["kind"] == "image":
        trust = resolution_trust(str(dep["ref"]))
    else:
        trust = package_trust(str(dep["package"]), dep.get("ecosystem"))
    if trust["via"] in ("explicit", "catalog") and trust["identity_status"] == "VERIFIED":
        return "project", str(trust["slug"])
    return "unresolved", None


def _relation(dep: dict[str, Any], project: str) -> str:
    """ "project" | "other" | "unresolved" relative to the event's project."""
    status, slug = _identity(dep)
    if status == "unresolved":
        return "unresolved"
    return "project" if slug == project else "other"


# --- versions: ecosystem comparators ---------------------------------------


def _in_line(version: str, line: str, ecosystem: str) -> bool | None:
    """Is ``version`` in release line ``line``? None when not decidable."""
    if ecosystem == "pypi":
        try:
            v, prefix = Version(version), Version(line)
        except InvalidVersion:
            return None
        if v.epoch != prefix.epoch:
            return None
        width = len(prefix.release)
        return v.release[:width] == prefix.release
    # No pinned comparator: plain dotted numbers only.
    if not (_NUMERIC.fullmatch(version) and _NUMERIC.fullmatch(line)):
        return None
    parts, prefix = version.split("."), line.split(".")
    return [int(x) for x in parts[: len(prefix)]] == [int(x) for x in prefix]


# --- membership tests -------------------------------------------------------


def _image_vs_artifact(ref: str, value: str, example: bool) -> str:
    d, e = oracle.parse_ref(ref), oracle.parse_ref(value)
    namespace = e.name == "*"
    if namespace:
        if (d.registry, d.namespace) != (e.registry, e.namespace):
            return N
    elif (d.registry, d.namespace, d.name) != (e.registry, e.namespace, e.name):
        return Z if example else N
    if e.digest is not None:
        return M if d.digest == e.digest else U
    if namespace and e.tag is None:
        return U  # an envelope: membership is not a positive
    if e.tag in (None, oracle.TAG_ANY):
        return M
    tag = d.tag if d.tag is not None else (None if d.digest else "latest")
    if tag is None:
        return U
    member = oracle.version_like(tag) if e.tag == oracle.TAG_VERSION else tag == e.tag
    if member:
        return M
    return U if example else N


def _test(dep: dict[str, Any], event: OSSEvent) -> set[str]:
    """Every element's result for one event (layer 2)."""
    results: set[str] = set()
    is_image = dep["kind"] == "image"
    relation = _relation(dep, event.project_slug)
    ecosystem = str(dep.get("ecosystem") or "").lower()
    for artifact in event.affected_artifacts:  # named examples
        if artifact.ref.startswith(_PACKAGE_PREFIXES):
            results.add(Z if relation == "other" else U if relation == "unresolved" else P)
        elif is_image:
            results.add(_image_vs_artifact(str(dep["ref"]), artifact.ref, example=True))
        else:
            results.add(Z if relation == "other" else U)
    scope = event.scope
    kind = scope.kind if scope is not None else "project"
    if kind == "project":
        results.add({"project": P, "other": Z}.get(relation, U))
    elif kind == "artifact":
        for value in scope.artifacts:
            if is_image:
                results.add(_image_vs_artifact(str(dep["ref"]), value, example=False))
            else:
                results.add(Z if relation == "other" else U)
    elif kind == "registry":
        for value in scope.registries:
            if is_image:
                same = oracle.parse_ref(str(dep["ref"])).registry == value.lower()
                results.add(U if same else N)
            else:
                results.add(Z if relation == "other" else U)
    elif kind == "package":
        if is_image:
            results.add(Z if relation == "other" else U)
        else:
            mine = package_name_key(ecosystem or "generic", str(dep["package"]))[1]
            names = {package_name_key(ecosystem or "generic", p)[1] for p in scope.packages}
            if mine in names:
                results.add(M)
            else:
                results.add(Z if relation == "other" else U)
    elif kind == "version":
        if relation != "project":
            results.add(Z if relation == "other" else U)
        else:
            if is_image:
                version = oracle.parse_ref(str(dep["ref"])).tag
                ecosystem = ""  # an image tag follows no package ecosystem
            else:
                version = dep.get("version")
            if not version:
                results.add(U)
            for line in scope.versions if version else []:
                within = _in_line(str(version), str(line), ecosystem)
                results.add(U if within is None else M if within else N)
    else:
        results.add(U)
    return results


# --- layer 1 and aggregation -------------------------------------------------


def _admissible_negative(
    event: OSSEvent, as_of: datetime | None, max_evidence_age: timedelta | None
) -> bool:
    if event.scope is None or not event.scope.admits_negative():
        return False
    if any(e.relation == "contradicts" for e in event.evidences):
        return False
    if as_of is not None and max_evidence_age is not None:
        newest = max(e.source.fetched_at for e in event.evidences)
        if as_of - newest > max_evidence_age:
            return False
    return True


def per_event(
    dep: dict[str, Any],
    event: OSSEvent,
    as_of: datetime | None = None,
    max_evidence_age: timedelta | None = None,
) -> str:
    results = _test(dep, event)
    if M in results:
        return "affected"
    if U in results:
        return "unresolved"
    if N in results:
        if results <= {N, Z} and _admissible_negative(event, as_of, max_evidence_age):
            return "cleared"
        return "unresolved"
    if P in results:
        return "unresolved"
    return "no_association"


def strong_conservative(
    dep: dict[str, Any],
    events: list[OSSEvent],
    *,
    as_of: datetime | None = None,
    max_evidence_age: timedelta | None = None,
) -> dict[str, Any]:
    """Policy V over every current event, summarised as in TR Table 8."""
    outcomes = {per_event(dep, e, as_of, max_evidence_age) for e in events if e.is_current_record()}
    for outcome in ("affected", "unresolved", "cleared"):
        if outcome in outcomes:
            return {"outcome": outcome}
    return {"outcome": "no_association"}
