"""Watchlist checking — Dependency Early Warning.

A watchlist names the dependencies a team actually runs (image refs
and/or packages with versions). Checking keeps two reasoning streams
separate — event-based intelligence (explicit upstream events) and
security correlation (CVE/package/version applicability) — and
combines them only at the final verdict, retaining each cause.

Decision matrix (final relationship):
  AFFECTS_ARTIFACT > AFFECTS_VERSION > AFFECTS_PACKAGE
  > NOT_AFFECTED > RELATED > AFFECTS_PROJECT > UNKNOWN
except that a clearance from one event never outranks an unresolved
association (RELATED / AFFECTS_PROJECT) from another
(``winning_cause``).
`affected` is True only for ARTIFACT/VERSION/PACKAGE. A project-only
tie (AFFECTS_PROJECT) is contextual, never impact. Pure functions.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from analyzers.security_analyst import correlate
from core.detections import ledger
from core.entities.catalog import is_qualified, package_name_key, qualified_package
from core.entities.identity import UNRESOLVED_IDENTITY, package_trust, resolution_trust
from core.risk.match import event_affects_ref
from core.schema.models import OSSEvent
from core.versions import in_release_line

_RANK = {
    "UNKNOWN": 0,
    "RELATED": 1,
    "AFFECTS_PROJECT": 2,
    "NOT_AFFECTED": 3,
    "AFFECTS_PACKAGE": 4,
    "AFFECTS_VERSION": 5,
    "AFFECTS_ARTIFACT": 6,
}

_AFFECTED = ("AFFECTS_ARTIFACT", "AFFECTS_VERSION", "AFFECTS_PACKAGE")

#: Associations that are neither impact nor clearance: while any cause
#: holds one, a NOT_AFFECTED from another event cannot headline.
_UNRESOLVED = ("RELATED", "AFFECTS_PROJECT")

#: Match strength answers "what matches" — never "how trustworthy is
#: the underlying claim". The ceiling below is what a match *alone*
#: can justify; the verdict confidence is the conservative minimum of
#: this ceiling and the evidence behind the event.
_MATCH_CEILING = {
    "AFFECTS_ARTIFACT": "CONFIRMED",
    "AFFECTS_VERSION": "CORROBORATED",
    "AFFECTS_PACKAGE": "EMERGING",
    "NOT_AFFECTED": "CORROBORATED",
    "AFFECTS_PROJECT": "EMERGING",
    "RELATED": "UNVERIFIED",
    "UNKNOWN": "UNVERIFIED",
}

_MATCH_STRENGTH = {
    "AFFECTS_ARTIFACT": "exact",
    "AFFECTS_VERSION": "scoped",
    "AFFECTS_PACKAGE": "scoped",
    "NOT_AFFECTED": "exclusion",
    "AFFECTS_PROJECT": "contextual",
    "RELATED": "contextual",
    "UNKNOWN": "none",
}

_CONFIDENCE_ORDER = {"UNVERIFIED": 0, "EMERGING": 1, "CORROBORATED": 2, "CONFIRMED": 3}

#: Identity statuses that must not silently elevate impact. Exact
#: artifact equality (self-identity) is exempt — see identity.py.
_UNTRUSTED_IDENTITY = ("REVIEW_REQUIRED", "UNVERIFIED")
_IDENTITY_CAP = "EMERGING"


def _weaker(first: str, second: str) -> str:
    order = _CONFIDENCE_ORDER
    return first if order.get(first, 0) <= order.get(second, 0) else second


class DependencyVerdict(BaseModel):
    """One dependency, fully explained. `affected` derives from evidence."""

    dependency: str
    affected: bool
    relationship: str
    confidence: str = "UNVERIFIED"
    match_strength: str = "none"
    evidence_confidence: str = "UNVERIFIED"
    identity_status: str = "VERIFIED"
    match_method: str | None = None
    evidence: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    reason: str = ""
    verdicts: list[dict[str, Any]] = Field(
        default_factory=list, description="Retained per-cause verdicts (streams stay separate)"
    )
    first_detected: str | None = Field(
        default=None,
        description=(
            "Earliest durable ledger detection across this verdict's recorded "
            "lifecycle/security causes; None when nothing is recorded (never a guess)"
        ),
    )
    inspection_coverage: str = Field(
        default="COMPLETE",
        description=(
            "Coverage of the repository inspection behind this dependency: "
            "COMPLETE (every file read), PARTIAL (something skipped/capped/failed) "
            "or FAILED (repository not enumerable). Non-GitHub inputs are COMPLETE."
        ),
    )
    inspection_coverage_reasons: list[str] = Field(
        default_factory=list,
        description="Downgrade causes for inspection_coverage (tree truncated, caps, fetch errors)",
    )


def load_watchlist_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate a parsed watchlist document into normalized dep entries.

    Optional passthrough (never required): source, environment, owner.
    """
    if not isinstance(doc, dict):
        raise ValueError("watchlist must be a mapping")
    deps = doc.get("dependencies", [])
    if not isinstance(deps, list) or not deps:
        raise ValueError("watchlist needs a non-empty `dependencies` list")
    normalized = []
    for i, dep in enumerate(deps):
        if not isinstance(dep, dict):
            raise ValueError(f"dependency #{i} must be a mapping")
        extra = {}
        for key in ("source", "environment", "owner"):
            if dep.get(key) is not None:
                if not isinstance(dep[key], str):
                    raise ValueError(f"dependency #{i} field `{key}` must be a string")
                extra[key] = dep[key]
        if dep.get("ref"):
            normalized.append({"kind": "image", "ref": str(dep["ref"]), **extra})
        elif dep.get("package"):
            normalized.append(
                {
                    "kind": "package",
                    "package": str(dep["package"]),
                    "ecosystem": str(dep.get("ecosystem", "")),
                    "version": str(dep["version"]) if dep.get("version") else None,
                    **extra,
                }
            )
        else:
            raise ValueError(f"dependency #{i} needs `ref` or `package`")
    return normalized


def _dep_label(dep: dict[str, Any]) -> str:
    if dep["kind"] == "image":
        return str(dep["ref"])
    version = dep.get("version")
    return f"{dep['package']}=={version}" if version else str(dep["package"])


def _event_scope_cause(dep: dict[str, Any], event: OSSEvent) -> dict[str, Any] | None:
    """Package dep vs one event's scope. None when the event says nothing usable.

    A negative stands only against a declared-complete scope; outside
    a partial or unspecified one the cause is RELATED (see ``_exclusion``).
    """
    cause = _scope_cause(dep, event)
    if cause is None or cause["relationship"] != "NOT_AFFECTED":
        return cause
    if event.scope is not None and event.scope.admits_negative():
        return cause
    why = (
        "scope completeness has no recorded basis"
        if event.scope is not None and event.scope.exhaustive
        else "scope is not exhaustive"
    )
    return {
        **cause,
        "relationship": "RELATED",
        "match_method": "project_scope",
        "reason": f"{cause['reason']}; {why}, so not a clearance",
    }


def _qualified_results(dep: dict[str, Any], event: OSSEvent) -> list[str]:
    """Element results for ecosystem-qualified package-scope values (F3).

    A purl value names exactly one package, so it decides by (ecosystem,
    canonical name) before identity: M when equal; N when the dependency
    is a package of a different ecosystem (never the same object); ?
    when the dependency states no ecosystem, the value does not parse,
    or only the name differs (names are not fully canonical).
    """
    scope = event.scope
    if scope is None or scope.kind != "package":
        return []
    ecosystem = str(dep.get("ecosystem") or "").strip()
    mine = package_name_key(ecosystem, str(dep["package"])) if ecosystem else None
    results = []
    for value in scope.packages:
        if not is_qualified(value):
            continue
        key = qualified_package(str(value))
        if key is None or mine is None or ecosystem.lower() == "generic":
            results.append("?")
        elif key == mine:
            results.append("M")
        elif key[0] != mine[0]:
            results.append("N")
        else:
            results.append("?")
    return results


def _go_module_repository(dep: dict[str, Any], event: OSSEvent) -> str | None:
    """The event's source-repository artifact a Go module lives in, or None.

    The module path equals the repository path or extends it by a
    subdirectory or major-version suffix (`github.com/o/r/v3`). Compared
    case-insensitively, as code hosts resolve repository paths.
    """
    if str(dep.get("ecosystem") or "").strip().lower() not in ("go", "golang"):
        return None
    module = str(dep["package"]).strip().lower()
    for artifact in event.affected_artifacts:
        if artifact.kind != "source-repository":
            continue
        repo = re.sub(r"^[a-z][a-z0-9+.-]*://", "", str(artifact.ref).strip().lower()).rstrip("/")
        if repo and (module == repo or module.startswith(repo + "/")):
            return str(artifact.ref)
    return None


def _scope_cause(dep: dict[str, Any], event: OSSEvent) -> dict[str, Any] | None:
    trust = package_trust(str(dep["package"]), dep.get("ecosystem"))
    slug = trust["slug"]
    qualified = _qualified_results(dep, event)
    exact = {
        "cause": "upstream_change",
        "event_id": event.id,
        "event_type": event.event_type.value,
        "project": event.project_slug,
        "impact": event.impact.value,
        "evidence": [e.source.name for e in event.evidences],
        "evidence_confidence": event.confidence.value,
        "match_method": "event_scope_package",
    }
    if "M" in qualified:
        # The event names this exact (ecosystem, package): self-identity,
        # no mapping involved, whatever the catalog says.
        return {
            **exact,
            "identity_status": "VERIFIED",
            "identity_via": "exact-artifact",
            "relationship": "AFFECTS_PACKAGE",
            "affected": True,
            "reason": f"{dep['ecosystem']} package {dep['package']} is named in event scope "
            f"packages {event.scope.packages}",
        }
    repository = _go_module_repository(dep, event)
    if repository is not None:
        # A Go module path is a repository locator: a module at or below a
        # named source repository lives in it (go.mod requires are what a
        # relocation's repository artifact exists to reach). Self-identity,
        # like the M case above. Positive only: a module outside the named
        # paths may still be that repository under a vanity import path, so
        # it is never cleared here.
        return {
            **exact,
            "identity_status": "VERIFIED",
            "identity_via": "exact-artifact",
            "relationship": "AFFECTS_ARTIFACT",
            "affected": True,
            "match_method": "event_scope:artifact",
            "reason": f"Go module {dep['package']} lives in affected source repository "
            f"{repository}",
        }
    # A self-resolved package is unresolved even when its name is the event's
    # project (F4): a name is not identity, as D10 holds for images.
    unresolved = trust["via"] == "self"
    if (slug != event.project_slug or unresolved) and (
        not unresolved or UNRESOLVED_IDENTITY.get() == "unrelated"
    ):
        return None  # curated as another project: no association
    bare = [p for p in (event.scope.packages if qualified else []) if not is_qualified(p)]
    if qualified and not bare and set(qualified) == {"N"}:
        # Every value names a package of another ecosystem: an exclusion by
        # object kind, not by identity, so it needs no resolved identity.
        # Admissibility (complete scope, basis, currency) is applied by
        # _event_scope_cause.
        return {
            **exact,
            "identity_status": trust["identity_status"],
            "identity_via": trust["via"],
            "relationship": "NOT_AFFECTED",
            "affected": False,
            "reason": f"{dep['ecosystem']} package {dep['package']} is not a package of the "
            f"ecosystems named in event scope packages {event.scope.packages}",
        }
    if slug != event.project_slug or unresolved:
        if event.scope is not None and event.scope.kind in ("artifact", "registry"):
            # Container-image and registry scopes name locations a package
            # reference never is: no association, whatever its identity.
            return None
        # An unmapped package resolves only to itself. That is not
        # evidence of another project, so against the project, its
        # release lines or its packages the association is undetermined,
        # never dropped (TR-2026-01 D13; D10 for images).
        return {
            "cause": "upstream_change",
            "event_id": event.id,
            "event_type": event.event_type.value,
            "project": event.project_slug,
            "impact": event.impact.value,
            "evidence": [e.source.name for e in event.evidences],
            "evidence_confidence": event.confidence.value,
            "identity_status": trust["identity_status"],
            "identity_via": trust["via"],
            "relationship": "RELATED",
            "affected": False,
            "match_method": "project_scope",
            "reason": (
                f"{dep['package']} resolves only to itself; identity unresolved, so it is "
                f"neither excluded from nor unrelated to project {event.project_slug}"
            ),
        }
    scope = event.scope
    version = dep.get("version")
    base: dict[str, Any] = {
        "cause": "upstream_change",
        "event_id": event.id,
        "event_type": event.event_type.value,
        "project": event.project_slug,
        "impact": event.impact.value,
        "evidence": [e.source.name for e in event.evidences],
        "evidence_confidence": event.confidence.value,
        "identity_status": trust["identity_status"],
        "identity_via": trust["via"],
    }
    if scope is None:
        return {
            **base,
            "relationship": "RELATED",
            "affected": False,
            "match_method": "project_scope",
            "reason": f"{dep['package']} belongs to event project {slug}; impact not established",
        }
    kind = scope.kind
    if kind == "version" and scope.versions:
        if not version:
            return {
                **base,
                "relationship": "RELATED",
                "affected": False,
                "match_method": "project_scope",
                "reason": f"event is version-scoped to {scope.versions}; dep version unknown",
            }
        comparable = True
        for scoped in scope.versions:
            within = in_release_line(str(version), str(scoped))
            if within is None:
                comparable = False
            elif within:
                return {
                    **base,
                    "relationship": "AFFECTS_VERSION",
                    "affected": True,
                    "match_method": "event_scope_version",
                    "reason": f"{dep['package']}=={version} is within event scope version {scoped}",
                }
        if not comparable:
            # Never a clear: an unparseable version is not "outside" a scope.
            return {
                **base,
                "relationship": "RELATED",
                "affected": False,
                "match_method": "project_scope",
                "reason": (
                    f"{dep['package']}=={version} is not comparable with scope versions "
                    f"{scope.versions}"
                ),
            }
        return {
            **base,
            "relationship": "NOT_AFFECTED",
            "affected": False,
            "match_method": "event_scope_version",
            "reason": (f"{dep['package']}=={version} is outside scope versions {scope.versions}"),
        }
    if kind == "package" and scope.packages:
        # Names compare in canonical form: lowercase, PEP 503 folding for
        # PyPI, Maven groupId:artifactId = groupId/artifactId.
        ecosystem = str(dep.get("ecosystem") or "generic")
        names = {
            package_name_key(ecosystem, str(p))[1] for p in scope.packages if not is_qualified(p)
        }
        if package_name_key(ecosystem, str(dep["package"]))[1] in names:
            return {
                **base,
                "relationship": "AFFECTS_PACKAGE",
                "affected": True,
                "match_method": "event_scope_package",
                "reason": f"{dep['package']} is inside event scope packages {scope.packages}",
            }
        # A project package element (TR-2026-01 F2): a listed value that is
        # the event's own project denotes every package a curated mapping
        # assigns to it. The slug equals the project only through such a
        # mapping here, since an unmapped package resolves to itself.
        if event.project_slug.lower() in {str(p).lower() for p in scope.packages}:
            return {
                **base,
                "relationship": "AFFECTS_PACKAGE",
                "affected": True,
                "match_method": "event_scope_package",
                "reason": (
                    f"{dep['package']} is a curated package of project {slug}, which event "
                    f"scope packages {scope.packages} name as a whole"
                ),
            }
        # Canonical folding covers PyPI and Maven spelling only (npm scopes,
        # Go module paths and other forms are not modelled), so a name that
        # differs from every listed one may still be the same package:
        # inequality is undetermined, never an exclusion.
        return {
            **base,
            "relationship": "RELATED",
            "affected": False,
            "match_method": "event_scope_package",
            "reason": (
                f"{dep['package']} is not listed in event scope packages {scope.packages}; "
                "package names are not canonicalised, so not a clearance"
            ),
        }
    if kind == "artifact":
        return {
            **base,
            "relationship": "RELATED",
            "affected": False,
            "match_method": "project_scope",
            "reason": "event is artifact-scoped; a package ref cannot match artifacts",
        }
    return {
        **base,
        "relationship": "AFFECTS_PROJECT",
        "affected": False,
        "match_method": "project_scope",
        "reason": (f"{dep['package']} belongs to {slug}; project ties are contextual, not impact"),
    }


Cause = dict[str, Any]


def _security_causes(dep: dict[str, Any], bundles: dict[str, dict[str, Any]]) -> list[Cause]:
    """CVE/package/version applicability stream (independent of events)."""
    if dep["kind"] != "package":
        return []
    trust = package_trust(str(dep["package"]), dep.get("ecosystem"))
    slug = trust["slug"]
    raw = bundles.get(slug)
    if raw is None:
        return []
    context = {
        "slug": slug,
        "package": dep["package"],
        "ecosystem": dep.get("ecosystem", ""),
        "version": dep.get("version"),
    }
    causes = []
    for finding in correlate(raw, context):
        relationship = str(finding.get("relationship", "UNKNOWN"))
        if relationship == "UNKNOWN":
            continue
        causes.append(
            {
                "cause": "security_vulnerability",
                "relationship": relationship,
                "affected": relationship in ("AFFECTS_VERSION", "AFFECTS_PACKAGE"),
                "match_method": finding.get("match_method"),
                "event_id": finding.get("cve_id"),
                "event_type": "SECURITY",
                "project": slug,
                "impact": finding.get("impact"),
                "evidence": list(finding.get("sources", [])),
                "evidence_confidence": str(finding.get("confidence") or "UNVERIFIED"),
                "identity_status": trust["identity_status"],
                "identity_via": trust["via"],
                "reason": (
                    f"{finding.get('cve_id')} [{relationship}] via {finding.get('match_method')}"
                ),
            }
        )
    return causes


def winning_cause(causes: list[Cause]) -> Cause:
    """The cause that headlines a verdict (non-empty ``causes``).

    The highest-ranked cause, except that a clearance never outranks
    an unresolved association from another event: when any cause is
    RELATED or AFFECTS_PROJECT, NOT_AFFECTED cannot headline. UNKNOWN
    causes ("matches nothing in this event") assert no association and
    do not block a clearance. Per-cause verdicts stay retained either
    way, and ``affected`` is unchanged -- neither side is affected.
    """
    top = max(causes, key=lambda c: _RANK.get(str(c.get("relationship", "")), 0))
    if str(top.get("relationship")) != "NOT_AFFECTED":
        return top
    unresolved = [c for c in causes if str(c.get("relationship")) in _UNRESOLVED]
    if not unresolved:
        return top
    return max(unresolved, key=lambda c: _RANK.get(str(c.get("relationship", "")), 0))


def _combine(dep: dict[str, Any], causes: list[Cause]) -> DependencyVerdict:
    """Explicit decision matrix over retained causes.

    Final confidence is the conservative minimum of what the match
    alone justifies (match ceiling) and the evidence behind the
    winning cause — a precise match on a weak claim stays weak.
    Verdicts that rely on untrusted identity mappings (anything but
    exact artifact equality through REVIEW_REQUIRED/UNVERIFIED
    mappings) are capped at EMERGING.
    """
    label = _dep_label(dep)
    coverage = str(dep.get("inspection_coverage") or "COMPLETE")
    coverage_reasons = [str(r) for r in (dep.get("inspection_coverage_reasons") or [])]
    if not causes:
        return DependencyVerdict(
            dependency=label,
            affected=False,
            relationship="UNKNOWN",
            reason="no applicable evidence",
            inspection_coverage=coverage,
            inspection_coverage_reasons=coverage_reasons,
        )
    for cause in causes:
        cause.setdefault("detail", cause.get("reason", ""))
        cause.setdefault("evidence_confidence", "UNVERIFIED")
        cause.setdefault("identity_status", "VERIFIED")
    top = winning_cause(causes)
    relationship = str(top["relationship"])
    affected = relationship in _AFFECTED
    match_strength = _MATCH_STRENGTH.get(relationship, "none")
    evidence_confidence = str(top.get("evidence_confidence") or "UNVERIFIED")
    confidence = _weaker(_MATCH_CEILING.get(relationship, "UNVERIFIED"), evidence_confidence)
    identity_status = str(top.get("identity_status") or "VERIFIED")
    via_artifact_exact = str(top.get("match_method") or "") == "event_scope:artifact"
    capped_identity = False
    if affected and not via_artifact_exact and identity_status in _UNTRUSTED_IDENTITY:
        confidence = _weaker(confidence, _IDENTITY_CAP)
        capped_identity = True
    evidence: list[str] = []
    events: list[str] = []
    for cause in causes:
        for item in cause.get("evidence", []) or []:
            if item not in evidence:
                evidence.append(str(item))
        event_id = cause.get("event_id")
        if event_id and event_id not in events:
            events.append(str(event_id))
    if affected:
        reason = "; ".join(c.get("reason", "") for c in causes if c.get("affected")) or top.get(
            "reason", ""
        )
    else:
        reason = top.get("reason", "") or f"evaluated {label}: no established impact"
    if capped_identity:
        reason = (
            f"{reason} [identity {identity_status} via "
            f"{top.get('identity_via', '?')}: confidence capped at {_IDENTITY_CAP}]"
        )
    return DependencyVerdict(
        dependency=label,
        affected=affected,
        relationship=relationship,
        confidence=confidence,
        match_strength=match_strength,
        evidence_confidence=evidence_confidence,
        identity_status=identity_status,
        match_method=top.get("match_method"),
        evidence=evidence,
        events=events,
        reason=reason,
        verdicts=causes,
        inspection_coverage=coverage,
        inspection_coverage_reasons=coverage_reasons,
    )


_ACTION_IMPACTS = ("ACTION", "CRITICAL")


def fail_on_threshold(results: list[DependencyVerdict], threshold: str) -> bool:
    """Return whether a deterministic CI policy threshold is breached.

    ``affected`` gates any affected dependency; ``review`` includes REVIEW,
    ACTION and CRITICAL causes; ``action`` preserves the historical strict
    semantics; ``critical`` gates only CRITICAL causes. UNKNOWN and RELATED
    never fail a threshold by themselves.
    """
    threshold = str(threshold).lower()
    if threshold not in {"affected", "review", "action", "critical"}:
        raise ValueError(f"unknown fail-on threshold: {threshold}")
    if threshold == "affected":
        return any(result.affected for result in results)
    minimum = {
        "review": {"REVIEW", "ACTION", "CRITICAL"},
        "action": {"ACTION", "CRITICAL"},
        "critical": {"CRITICAL"},
    }[threshold]
    return any(
        result.affected
        and any(
            str(cause.get("impact", "")).upper() in minimum
            for cause in result.verdicts
            if cause.get("affected")
        )
        for result in results
    )


def strict_affected(results: list[DependencyVerdict]) -> bool:
    """Whether --strict should fail: an affected verdict carried by an
    ACTION-level cause. REVIEW/WATCH-level affected verdicts (e.g. weak
    evidence capped findings) never trip the gate on their own."""
    for result in results:
        if not result.affected:
            continue
        for cause in result.verdicts:
            if cause.get("affected") and str(cause.get("impact", "")).upper() in _ACTION_IMPACTS:
                return True
    return False


Verdict = DependencyVerdict


def inadmissible_reason(
    event: OSSEvent,
    as_of: datetime | None = None,
    max_evidence_age: timedelta | None = None,
) -> str | None:
    """Why ``event`` may not support a negative, or None if it may.

    Layer 1 of the applicability policy (TR-2026-01 N4, N5): an event
    whose extent is contested by its own evidence, or whose newest
    evidence is older than the caller's freshness bound, can still
    associate a dependency but never clear one. Withdrawn and
    superseded events are dropped before evaluation (``check_dependency``).
    The freshness bound is opt-in: replaying recorded evidence offline
    would otherwise make every negative stale.
    """
    if any(e.relation == "contradicts" for e in event.evidences):
        return "the event's extent is contested by contradicting evidence"
    if as_of is not None and max_evidence_age is not None:
        newest = max(e.source.fetched_at for e in event.evidences)
        if newest.tzinfo is None:
            newest = newest.replace(tzinfo=timezone.utc)
        if as_of - newest > max_evidence_age:
            return (
                f"newest evidence was fetched {newest.date()}, older than the "
                f"{max_evidence_age.days}-day freshness bound (stale)"
            )
    return None


def _admit(
    cause: Cause, event: OSSEvent, as_of: datetime | None, max_age: timedelta | None
) -> Cause:
    """Turn a negative from an inadmissible event into RELATED."""
    if cause.get("relationship") != "NOT_AFFECTED":
        return cause
    why = inadmissible_reason(event, as_of, max_age)
    if why is None:
        return cause
    return {
        **cause,
        "relationship": "RELATED",
        "reason": f"{cause['reason']}; {why}, so not a clearance",
    }


def check_dependency(
    dep: dict[str, Any],
    events: list[OSSEvent],
    bundles: dict[str, dict[str, Any]] | None = None,
    *,
    as_of: datetime | None = None,
    max_evidence_age: timedelta | None = None,
    unresolved_identity: Literal["undetermined", "unrelated"] = "undetermined",
) -> DependencyVerdict:
    """One dep vs events (+ optional raw bundles) -> explicit verdict.

    Withdrawn and superseded events are not evaluated. With ``as_of``
    and ``max_evidence_age`` both given, a negative from an event whose
    newest evidence is older than the bound becomes RELATED (stale).
    ``unresolved_identity="unrelated"`` is the evaluation's identity
    ablation (``core.entities.identity.UNRESOLVED_IDENTITY``): unsound by
    design, never for production use.
    """
    if unresolved_identity not in ("undetermined", "unrelated"):
        raise ValueError(f"unresolved_identity: {unresolved_identity!r}")
    token = UNRESOLVED_IDENTITY.set(unresolved_identity)
    try:
        return _check_dependency(dep, events, bundles, as_of, max_evidence_age)
    finally:
        UNRESOLVED_IDENTITY.reset(token)


def _check_dependency(
    dep: dict[str, Any],
    events: list[OSSEvent],
    bundles: dict[str, dict[str, Any]] | None,
    as_of: datetime | None,
    max_evidence_age: timedelta | None,
) -> DependencyVerdict:
    bundles = bundles or {}
    events = [event for event in events if event.is_current_record()]
    causes: list[Cause] = []
    if dep["kind"] == "image":
        trust = resolution_trust(str(dep["ref"]))
        for event in events:
            match = event_affects_ref(event, dep["ref"])
            exact = match["via"] == "artifact"
            cause = _admit(
                {
                    "cause": "upstream_change",
                    "relationship": match["relationship"],
                    "affected": bool(match["affected"]),
                    "match_method": f"event_scope:{match['via']}"
                    if match["via"]
                    else "project_scope",
                    "event_id": event.id,
                    "event_type": event.event_type.value,
                    "project": event.project_slug,
                    "impact": event.impact.value,
                    "evidence": [e.source.name for e in event.evidences],
                    "evidence_confidence": event.confidence.value,
                    # Exact artifact equality is self-identity (no
                    # mapping involved); anything coarser relies on the
                    # slug resolution and inherits its trust.
                    "identity_status": "VERIFIED" if exact else trust["identity_status"],
                    "identity_via": "exact-artifact" if exact else trust["via"],
                    "reason": str(match["detail"]),
                },
                event,
                as_of,
                max_evidence_age,
            )
            causes.append(cause)
    else:
        for event in events:
            cause = _event_scope_cause(dep, event)
            if cause is not None:
                causes.append(_admit(cause, event, as_of, max_evidence_age))
        causes.extend(_security_causes(dep, bundles))
    return _combine(dep, causes)


def check_watchlist(
    deps: list[dict[str, Any]],
    events: list[OSSEvent],
    bundles: dict[str, dict[str, Any]] | None = None,
    *,
    as_of: datetime | None = None,
    max_evidence_age: timedelta | None = None,
) -> list[DependencyVerdict]:
    """Whole watchlist -> one verdict per dependency."""
    return [
        check_dependency(dep, events, bundles, as_of=as_of, max_evidence_age=max_evidence_age)
        for dep in deps
    ]


#: Durable lifecycle fact types: one set, owned by the ledger (the
#: identity contract), so the writer and the reader can never diverge.
_LIFECYCLE_EVENT_TYPES = ledger.LIFECYCLE_EVENT_TYPES

#: Relationships asserting the dependency is implicated: the only
#: ones that start (or continue) a durable detection record.
_AFFECTED_RELATIONSHIPS = frozenset({"AFFECTS_VERSION", "AFFECTS_PACKAGE", "AFFECTS_ARTIFACT"})


def durable_fact_from_cause(
    cause: Cause,
    events_by_id: dict[str, OSSEvent],
) -> dict[str, Any] | None:
    """Durable detection fact for ONE impact-asserting cause, or None.

    The single derivation of cause -> ledger identity: fact key
    (project, class, subject, scope). Both callers - the writer
    (``detections_from_verdicts`` -> ``ledger.record_detection``)
    and any reader that needs to look a fact up (the alert digest)
    - go through this function, so a cause can never be recorded
    under one identity and read back under another. Causes that
    assert no impact, carry no stable project, or name no durable
    event type yield None: nothing durable to remember.
    """
    if str(cause.get("relationship", "")) not in _AFFECTED_RELATIONSHIPS:
        return None
    project = str(cause.get("project") or "")
    if not project:
        return None  # no stable project -> nothing durable
    if cause.get("cause") == "security_vulnerability":
        subject = str(cause.get("event_id") or "")
        if not subject:
            return None
        return {
            "project": project,
            "finding_class": ledger.SECURITY,
            "subject": subject,
            "scope": [],
        }
    if cause.get("cause") != "upstream_change":
        return None
    event_type = str(cause.get("event_type") or "")
    if event_type not in _LIFECYCLE_EVENT_TYPES:
        return None  # distribution changes keep observation-history detection
    event = events_by_id.get(str(cause.get("event_id") or ""))
    if event is None or event.scope is None:
        return None
    versions = sorted({str(v) for v in event.scope.versions or []})
    if not versions:
        return None
    return {
        "project": project,
        "finding_class": ledger.LIFECYCLE,
        "subject": event_type,
        "scope": versions,
    }


def detections_from_verdicts(
    verdicts: list[DependencyVerdict],
    events: list[OSSEvent] | None = None,
) -> list[dict[str, Any]]:
    """Durable detection facts carried by check verdicts.

    Pure function - verdicts in, ledger-shaped fact descriptors out
    (project, finding_class, subject, scope terms); no writes here.
    The fact identity is deliberately announcement-independent:
    lifecycle facts key as (project, event_type, cycle versions) and
    security facts as (project, CVE id), so the same underlying fact
    reported by different events/sources across runs maps to ONE
    ledger entry. `events` supplies the scope versions for lifecycle
    causes (the cause carries the event id). Identity derivation is
    delegated to ``durable_fact_from_cause`` - one derivation path,
    shared with the alert-digest reader, never a second one. Only
    impact-asserting relationships contribute: a RELATED tie is
    context, not a detection worth remembering, and UNKNOWN means no
    evidence. Never invents: causes without a usable identity are
    skipped.
    """
    events_by_id = {e.id: e for e in events or []}
    facts: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, tuple[str, ...]]] = set()
    for verdict in verdicts:
        for cause in verdict.verdicts:
            fact = durable_fact_from_cause(cause, events_by_id)
            if fact is None:
                continue
            key = (
                str(fact["project"]),
                str(fact["finding_class"]),
                str(fact["subject"]),
                tuple(str(v) for v in fact["scope"]),
            )
            if key in seen:
                continue
            seen.add(key)
            facts.append(fact)
    return facts
