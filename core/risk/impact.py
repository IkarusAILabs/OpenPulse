"""Impact eligibility — from analyst proposal to reportable assessment.

An analyst's ``impact`` is a proposal made without customer context.
This module decides what a finding *is eligible for* in a report:

- ``assessment``: PROJECT_SIGNAL | PROJECT_CHANGE | AFFECTS_DEPENDENCY
  | ACTION_REQUIRED — what kind of claim this finding supports.
- ``eligibility``: INFORMATIONAL | WATCH | REVIEW | ACTION — where it
  may appear. ACTION here means "evidence and scope justify
  action-oriented framing (with disclaimer)"; ACTION_REQUIRED
  additionally needs a linked, affected dependency plus policy.

Central rule: ``EOL detected`` never equals ``ACTION_REQUIRED``.
Without a dependency inventory, lifecycle findings are at most
PROJECT_CHANGE — never customer impact. Pure functions.
"""

from __future__ import annotations

from datetime import date
from typing import Any

#: Assessment vocabulary (§2-§4): claim kinds, weakest first.
#: NOT_AFFECTED is the explicit negative: the dependency was checked
#: against the scope and is outside it. It is informational/cleared
#: semantics — never combinable with an AFFECTS_* assessment.
PROJECT_SIGNAL = "PROJECT_SIGNAL"
PROJECT_CHANGE = "PROJECT_CHANGE"
AFFECTS_DEPENDENCY = "AFFECTS_DEPENDENCY"
ACTION_REQUIRED = "ACTION_REQUIRED"
NOT_AFFECTED = "NOT_AFFECTED"

#: Eligibility ladder for report placement.
INFORMATIONAL = "INFORMATIONAL"
WATCH = "WATCH"
REVIEW = "REVIEW"
ACTION = "ACTION"

_ELIGIBILITY = (INFORMATIONAL, WATCH, REVIEW, ACTION)

#: Verdicts that establish dependency impact (shared with check.py).
_AFFECTED = ("AFFECTS_ARTIFACT", "AFFECTS_VERSION", "AFFECTS_PACKAGE")

#: Confidence sufficient for action-oriented conclusions.
_STRONG_CONFIDENCE = ("CONFIRMED", "CORROBORATED")


def _parse_day(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _analyst_impact(finding: dict[str, Any]) -> str:
    return str(finding.get("impact", "INFORMATIONAL")).upper()


def _scope(finding: dict[str, Any]) -> dict[str, Any]:
    scope = finding.get("scope")
    if not isinstance(scope, dict):
        return {}
    return scope


def _scoped(finding: dict[str, Any]) -> bool:
    """True when the finding narrows applicability beyond the project."""
    scope = _scope(finding)
    if not scope:
        return False
    if scope.get("kind") in ("version", "artifact", "package", "registry"):
        return bool(
            scope.get("versions") or scope.get("artifacts")
            or scope.get("packages") or scope.get("registries")
        )
    return False


def _state(finding: dict[str, Any]) -> str:
    return str(finding.get("lifecycle_state") or "").upper()


def _significance(finding: dict[str, Any]) -> str:
    return str(finding.get("significance") or "").lower()


def evaluate_impact(
    finding: dict[str, Any],
    dependency_context: dict[str, Any] | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Assess one finding -> {assessment, eligibility, reasons}.

    ``dependency_context`` is None for public reports, else a mapping
    with ``verdict`` (relationship), ``affected`` (bool), and
    ``confidence``. ``today`` defaults to the current date.
    """
    today = today or date.today()
    finding = finding or {}
    reasons: list[str] = []

    if dependency_context is not None:
        return _with_context(finding, dependency_context, today, reasons)
    return _public(finding, today, reasons)


def _with_context(
    finding: dict[str, Any],
    context: dict[str, Any],
    today: date,
    reasons: list[str],
) -> dict[str, Any]:
    verdict = str(context.get("verdict") or "UNKNOWN")
    affected = bool(context.get("affected"))
    confidence = str(context.get("confidence") or "UNVERIFIED")
    if verdict in _AFFECTED and affected:
        # Weak evidence caps the dependency path too: a precise match
        # on a heuristic claim is AFFECTS at most, never ACTION.
        if str(finding.get("evidence_strength") or "").lower() == "weak":
            reasons.append("weak evidence strength: match established, action withheld")
            return _result(AFFECTS_DEPENDENCY, REVIEW, reasons)
        effective = _effective(finding, today)
        if effective and confidence in _STRONG_CONFIDENCE:
            reasons.append(
                f"{verdict} with {confidence} confidence and "
                f"effective {effective}: action required"
            )
            return _result(ACTION_REQUIRED, ACTION, reasons)
        reasons.append(
            f"{verdict} established but action policy not met "
            f"(confidence={confidence}, effective={effective})"
        )
        # Weak evidence never enters ACTION channels: at most REVIEW.
        if confidence in _STRONG_CONFIDENCE:
            return _result(AFFECTS_DEPENDENCY, ACTION, reasons)
        return _result(AFFECTS_DEPENDENCY, REVIEW, reasons)
    if verdict == "NOT_AFFECTED" and not affected:
        reasons.append(str(context.get("reason") or "dependency outside event scope"))
        return _result(NOT_AFFECTED, INFORMATIONAL, reasons)
    if verdict == "RELATED":
        reasons.append(str(context.get("reason") or "contextual tie, impact not established"))
        return _result(PROJECT_SIGNAL, WATCH, reasons)
    reasons.append("no established impact for this dependency")
    return _result(PROJECT_SIGNAL, INFORMATIONAL, reasons)


def _effective(finding: dict[str, Any], today: date) -> str | None:
    """Effective date when the change already applies (else None)."""
    if _state(finding) == "EFFECTIVE":
        return str(finding.get("effective_at") or finding.get("event_date") or "past")
    day = _parse_day(finding.get("effective_at") or finding.get("event_date"))
    if day is not None and day <= today:
        return str(day)
    return None


def _public(
    finding: dict[str, Any], today: date, reasons: list[str]
) -> dict[str, Any]:
    analyst = _analyst_impact(finding)
    event_type = str(finding.get("event_type", ""))
    signal = str(finding.get("signal", ""))
    if signal == "security" or finding.get("relationship"):
        result = _public_security(finding, analyst, reasons)
    else:
        result = _public_change(finding, event_type, analyst, reasons)
    return _apply_evidence_cap(finding, result)


#: Explicit weak evidence never rises above REVIEW, however strong the
#: analyst proposal. Missing evidence_strength means the producer
#: predates strength labeling — legacy tolerance, no cap.
_WEAK_EVIDENCE_CEILING = REVIEW


def _apply_evidence_cap(
    finding: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    if str(finding.get("evidence_strength") or "").lower() != "weak":
        return result
    order = {name: rank for rank, name in enumerate(_ELIGIBILITY)}
    if order.get(result["eligibility"], 0) > order[_WEAK_EVIDENCE_CEILING]:
        capped = dict(result)
        capped["eligibility"] = _WEAK_EVIDENCE_CEILING
        capped["reasons"] = list(result.get("reasons") or []) + [
            "weak evidence strength caps placement at REVIEW"
        ]
        return capped
    return result


def _public_security(
    finding: dict[str, Any], analyst: str, reasons: list[str]
) -> dict[str, Any]:
    relationship = str(finding.get("relationship") or "")
    if relationship in _AFFECTED:
        reasons.append(
            f"{relationship} from security correlation; placement follows analyst impact"
        )
        return _result(PROJECT_CHANGE, _cap(analyst), reasons)
    reasons.append("security finding without established dependency impact")
    return _result(PROJECT_SIGNAL, _cap(analyst), reasons)


def _public_change(
    finding: dict[str, Any], event_type: str, analyst: str, reasons: list[str]
) -> dict[str, Any]:
    state = _state(finding)
    significance = _significance(finding)
    scoped = _scoped(finding)
    if event_type == "EOL":
        if state == "EFFECTIVE" and scoped:
            versions = (_scope(finding).get("versions") or [])
            reasons.append(
                f"EOL effective for scoped versions {versions}: "
                "evidence and scope justify action-oriented framing "
                "(applies only if you run these versions)"
            )
            return _result(PROJECT_CHANGE, ACTION, reasons)
        if state == "UPCOMING":
            reasons.append("EOL upcoming but not yet effective: watch")
            return _result(PROJECT_CHANGE, WATCH, reasons)
        reasons.append("EOL proposal without usable scope/state: review at most")
        return _result(PROJECT_SIGNAL, REVIEW, reasons)
    if event_type == "EOS":
        reasons.append("active support ended: review support posture")
        return _result(PROJECT_CHANGE, REVIEW, reasons)
    if event_type == "PROJECT_ARCHIVED":
        reasons.append(
            "archived upstream is a project-level change, not proof any "
            "deployment is affected: review, never automatic action"
        )
        return _result(PROJECT_CHANGE, REVIEW, reasons)
    if event_type == "REGISTRY_CHANGE":
        reasons.append(
            "registry disappearance needs pull/mirror confirmation: "
            "high-significance candidate, review"
        )
        return _result(PROJECT_CHANGE, REVIEW, reasons)
    if event_type == "OWNERSHIP_CHANGE":
        reasons.append(
            "ownership move is a project-level identity fact, not proof "
            "any deployment is affected: review, never automatic action"
        )
        return _result(PROJECT_CHANGE, REVIEW, reasons)
    if event_type == "DISTRIBUTION_CHANGE":
        if significance == "high" and finding.get("distribution_model_change"):
            reasons.append(
                "distribution model change with high significance: "
                "action-oriented framing justified"
            )
            return _result(PROJECT_CHANGE, ACTION, reasons)
        if significance == "high":
            reasons.append("high-significance distribution change: review")
            return _result(PROJECT_CHANGE, REVIEW, reasons)
        reasons.append("distribution observation without high significance: watch")
        return _result(PROJECT_CHANGE, WATCH, reasons)
    if event_type == "PACKAGE_REMOVAL":
        if significance == "high":
            reasons.append(
                "package removal from registry is high significance: "
                "action-oriented framing justified"
            )
            return _result(PROJECT_CHANGE, ACTION, reasons)
        reasons.append("package removal from registry: review")
        return _result(PROJECT_CHANGE, REVIEW, reasons)
    reasons.append(f"unclassified change ({event_type or 'unknown'}): "
                   "no action framing without evidence")
    return _result(PROJECT_SIGNAL, _cap(analyst, ceiling=REVIEW), reasons)


def _cap(analyst: str, ceiling: str = ACTION) -> str:
    order = {name: rank for rank, name in enumerate(_ELIGIBILITY)}
    capped = min(order.get(analyst, 0), order[ceiling])
    return _ELIGIBILITY[capped]


def _result(assessment: str, eligibility: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "assessment": assessment,
        "eligibility": eligibility,
        "reasons": list(reasons),
    }
