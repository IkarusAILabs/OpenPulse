"""Decision policies compared by the evaluation (PROTOCOL.md, section 2).

Every policy receives the same replayed events and the same dependency,
and returns one outcome class for the pair:

    affected        a decisive positive
    cleared         a decisive negative (NotAffected)
    unresolved      an association that is not established (abstention)
    no_association  nothing relates the dependency to any event

The baselines are written from the protocol's text. They use the
specification oracle's reference parser (``conformance/oracle.py``),
which imports nothing from the engine, so they share OpenPulse's inputs
but none of its matching code. OpenPulse itself is the production
``check_dependency``; its ablations change the *input* events, never the
code, so an ablation is reproducible from the event transform alone.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

import oracle  # noqa: E402

from core.risk.check import check_dependency  # noqa: E402
from core.schema.models import OSSEvent  # noqa: E402

AFFECTED, CLEARED, UNRESOLVED, NONE = "affected", "cleared", "unresolved", "no_association"
OUTCOMES = (AFFECTED, CLEARED, UNRESOLVED, NONE)

#: Named-artefact prefixes that denote packages, not container references.
_PACKAGE_PREFIXES = ("pypi:", "npm:", "pkg:", "maven:", "cargo:", "go:")
_RELEASE = re.compile(r"v?(\d+(?:\.\d+)*)")


# --- the affected-set listing shared by both baselines -------------------


def _release(version: str | None) -> list[int] | None:
    match = _RELEASE.match(version or "")
    return [int(n) for n in match.group(1).split(".")] if match else None


def _in_line(version: str | None, line: str) -> bool:
    release, prefix = _release(version), _release(line)
    return release is not None and prefix is not None and release[: len(prefix)] == prefix


def _image_listed(ref: str, value: str) -> bool:
    d, e = oracle.parse_ref(ref), oracle.parse_ref(value)
    tag = d.tag if d.tag is not None else (None if d.digest else "latest")
    if e.name == "*":
        if (d.registry, d.namespace) != (e.registry, e.namespace):
            return False
    elif (d.registry, d.namespace, d.name) != (e.registry, e.namespace, e.name):
        return False
    if e.digest is not None:
        return d.digest == e.digest
    if e.tag in (None, oracle.TAG_ANY):
        return True
    if tag is None:
        return False
    if e.tag == oracle.TAG_VERSION:
        return oracle.version_like(tag)
    return tag == e.tag


def _package_name(value: str) -> tuple[str, str | None]:
    """``pypi:leftpad:0.0.1`` / ``npm:react@18.0.0`` / ``pkg:maven/g/a``."""
    body = value.split(":", 1)[1] if ":" in value else value
    body = body.lstrip("/")
    if "@" in body:
        name, version = body.rsplit("@", 1)
        return name.lower(), version
    if ":" in body:
        name, version = body.split(":", 1)
        return name.lower(), version
    return body.lower(), None


def _name_owner(dep: dict[str, Any]) -> str:
    """Name-based identity: the repository's or package's own name."""
    if dep["kind"] == "image":
        return oracle.parse_ref(str(dep["ref"])).name
    return str(dep.get("package", "")).lower()


def listed(dep: dict[str, Any], event: OSSEvent) -> bool:
    """Is ``dep`` named by the event's affected set, read literally?

    The listing is the union of the scope's values and the named affected
    artefacts. Container references compare after the reference
    canonicalisation (Docker Hub aliases, ``library``); identity is by
    name, the way an affected-product list is commonly read; versions
    compare by numeric release-line prefix.
    """
    scope = event.scope
    kind = scope.kind if scope is not None else "project"
    is_image = dep["kind"] == "image"
    own_project = _name_owner(dep) == event.project_slug.lower()
    for artifact in event.affected_artifacts:
        ref = artifact.ref
        if ref.startswith(_PACKAGE_PREFIXES):
            if is_image:
                continue
            name, version = _package_name(ref)
            if name.split("/")[-1] == _name_owner(dep).split("/")[-1] and (
                version is None or version == dep.get("version")
            ):
                return True
        elif is_image and _image_listed(str(dep["ref"]), ref):
            return True
    if scope is None or kind == "project":
        return own_project
    if kind == "artifact":
        return is_image and any(_image_listed(str(dep["ref"]), v) for v in scope.artifacts)
    if kind == "registry":
        return is_image and oracle.parse_ref(str(dep["ref"])).registry in {
            r.lower() for r in scope.registries
        }
    if kind == "package":
        return not is_image and _name_owner(dep) in {p.lower() for p in scope.packages}
    if kind == "version":
        names = {p.lower() for p in scope.packages} or {event.project_slug.lower()}
        if _name_owner(dep) not in names:
            return False
        if is_image:
            version = oracle.parse_ref(str(dep["ref"])).tag
        else:
            version = dep.get("version")
        return any(_in_line(version, line) for line in scope.versions)
    return False


# --- policies ------------------------------------------------------------


def naive(dep: dict[str, Any], events: list[OSSEvent], **_: Any) -> dict[str, Any]:
    """Policy A: an unlisted dependency is unaffected."""
    hit = any(listed(dep, e) for e in events if e.is_current_record())
    return {"outcome": AFFECTED if hit else CLEARED}


def conservative(dep: dict[str, Any], events: list[OSSEvent], **_: Any) -> dict[str, Any]:
    """Policy B: an unlisted dependency is unknown (an abstention)."""
    current = [e for e in events if e.is_current_record()]
    if any(listed(dep, e) for e in current):
        return {"outcome": AFFECTED}
    return {"outcome": UNRESOLVED if current else NONE}


_OPENPULSE_OUTCOME = {
    "AFFECTS_ARTIFACT": AFFECTED,
    "AFFECTS_VERSION": AFFECTED,
    "AFFECTS_PACKAGE": AFFECTED,
    "NOT_AFFECTED": CLEARED,
    "RELATED": UNRESOLVED,
    "AFFECTS_PROJECT": UNRESOLVED,
    "UNKNOWN": NONE,
}


def openpulse(
    dep: dict[str, Any],
    events: list[OSSEvent],
    *,
    as_of: datetime | None = None,
    max_evidence_age: timedelta | None = None,
) -> dict[str, Any]:
    """Policy C: the production verdict engine, freshness bound set."""
    verdict = check_dependency(dep, events, as_of=as_of, max_evidence_age=max_evidence_age)
    outcome = _OPENPULSE_OUTCOME.get(verdict.relationship, UNRESOLVED)
    justification = _justification(verdict, events)
    return {
        "outcome": outcome,
        "relationship": verdict.relationship,
        "confidence": verdict.confidence,
        "reason": verdict.reason,
        "justification": justification,
    }


def _justification(verdict: Any, events: list[OSSEvent]) -> dict[str, bool]:
    """What a decisive verdict carries to justify itself (metric E)."""
    by_id = {e.id: e for e in events}
    cited = [by_id[i] for i in verdict.events if i in by_id]
    return {
        "sources_named": bool(verdict.evidence),
        "acquisition_time": any(ev.source.fetched_at for e in cited for ev in e.evidences),
        "completeness_basis": any(e.scope is not None and e.scope.basis for e in cited),
    }


# --- ablations: OpenPulse on transformed inputs ---------------------------


def _assume_complete(events: list[OSSEvent]) -> list[OSSEvent]:
    """Every populated scope declared complete, as a list read as closed."""
    out = []
    for e in events:
        if e.scope is not None and not e.scope.admits_negative():
            scope = e.scope.model_copy(
                update={"exhaustive": True, "basis": e.scope.basis or "announced"}
            )
            e = e.model_copy(update={"scope": scope})
        out.append(e)
    return out


def openpulse_no_completeness(dep, events, **kw):
    """Ablation: completeness is assumed rather than required (N3 off)."""
    return openpulse(dep, _assume_complete(events), **kw)


def openpulse_no_freshness(dep, events, **_):
    """Ablation: no freshness bound (N4 freshness off)."""
    return openpulse(dep, events)


def openpulse_no_completeness_no_freshness(dep, events, **_):
    """Ablation: both admission premises off, since either alone can mask the other."""
    return openpulse(dep, _assume_complete(events))


Policy = Callable[..., dict[str, Any]]

#: Registered before any case is run (PROTOCOL.md). Order is report order.
POLICIES: dict[str, Policy] = {
    "A-naive": naive,
    "B-conservative": conservative,
    "C-openpulse": openpulse,
    "C-ablate-completeness": openpulse_no_completeness,
    "C-ablate-freshness": openpulse_no_freshness,
    "C-ablate-both": openpulse_no_completeness_no_freshness,
}
