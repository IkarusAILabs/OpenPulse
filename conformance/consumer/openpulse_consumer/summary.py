"""An outcome summary that keeps every outcome apart (v0.19.0 P4).

A contract states several things that a consumer is tempted to fold into
one "pass": the relationship OpenPulse found, how completely the repository
was inspected, and what the trust checks returned. They are independent:

- **Relationship** (``assessment.relationship``) is counted as stated, all
  seven values, zeros included. NOT_AFFECTED, RELATED and UNKNOWN are three
  different outcomes, and ``affected: false`` is true of all three.
- **Inspection coverage** (``inspection_coverage.status``) is counted on
  its own. Contract 1.0 has no coverage field: it is NOT_REPORTED, never
  COMPLETE.
- **Trust** (``trust_assurance``) is counted per record, from the records
  themselves. A document whose run did not check trust is "not checked",
  which is not the same as a check that found nothing. MISSING_EVIDENCE and
  NOT_PERFORMED are counted, not dropped.

There is no pass, clean or safe field, on purpose. Each document instead
lists what it leaves open (``Outcome.open``): an UNKNOWN or RELATED
relationship, a NOT_AFFECTED whose scope does not admit a negative or that
had no freshness bound, coverage other than COMPLETE or NOT_APPLICABLE,
and every trust record other than VERIFIED_RELATIONSHIP. A document with
nothing open is still only what it states, read by its own fields.

Only documents that pass ``check`` (schema and content hash) are
summarised; the others are counted as invalid and contribute no outcome.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any

from openpulse_consumer.contract import check

RELATIONSHIPS = (
    "AFFECTS_ARTIFACT",
    "AFFECTS_VERSION",
    "AFFECTS_PACKAGE",
    "AFFECTS_PROJECT",
    "RELATED",
    "NOT_AFFECTED",
    "UNKNOWN",
)
#: NOT_REPORTED: contract 1.0, which has no inspection_coverage field.
COVERAGE = ("COMPLETE", "PARTIAL", "FAILED", "NOT_APPLICABLE", "NOT_REPORTED")
TRUST_STATUSES = (
    "CONFIRMED_MALICIOUS",
    "VERIFIED_FAILURE",
    "SUSPICIOUS_INCONCLUSIVE",
    "MISSING_EVIDENCE",
    "VERIFIED_RELATIONSHIP",
    "NOT_PERFORMED",
)
_SETTLED_COVERAGE = {"COMPLETE", "NOT_APPLICABLE"}


@dataclass(frozen=True)
class Outcome:
    """What one valid document states, axis by axis, and what it leaves open."""

    contract_version: str
    event: str
    dependency: str
    relationship: str
    affected: bool
    #: verdict_meaning.direct_scope; None before contract 1.2
    direct_scope: str | None
    coverage: str
    coverage_reasons: tuple[str, ...]
    #: {status: records}, every status present; None when trust was not checked
    trust: dict[str, int] | None
    #: scope.completeness.admits_negative; None before contract 1.2
    negative_admitted: bool | None
    #: evaluation_context.freshness_bound_applied; None before contract 1.2
    freshness_bound_applied: bool | None
    unknowns: tuple[str, ...]
    limitations: tuple[str, ...]
    open: tuple[str, ...]


def _trust(doc: dict[str, Any]) -> tuple[dict[str, int] | None, list[str]]:
    assurance = doc.get("trust_assurance")
    if assurance is None:
        return None, []
    counts = dict.fromkeys(TRUST_STATUSES, 0)
    for record in assurance["checks"]:
        counts[record["status"]] += 1
    problems = []
    if counts != assurance["summary"]:
        problems.append(
            "trust_assurance.summary disagrees with its records; the records are counted"
        )
    return counts, problems


def outcome(doc: dict[str, Any]) -> Outcome:
    """The outcome of one document that already passed ``check``."""
    assessment = doc["assessment"]
    relationship = assessment["relationship"]
    coverage_field = doc.get("inspection_coverage")
    coverage = coverage_field["status"] if coverage_field else "NOT_REPORTED"
    completeness = doc["scope"].get("completeness")
    negative_admitted = completeness["admits_negative"] if completeness else None
    context = doc.get("evaluation_context")
    fresh = context["freshness_bound_applied"] if context else None
    meaning = doc.get("verdict_meaning")
    trust, open_items = _trust(doc)

    if relationship == "UNKNOWN":
        open_items.insert(0, "relationship UNKNOWN: the evidence did not decide")
    elif relationship == "RELATED":
        open_items.insert(0, "relationship RELATED: tied to the event, not established as affected")
    elif relationship == "NOT_AFFECTED":
        if negative_admitted is None:
            open_items.append(
                "NOT_AFFECTED, but this contract version does not report"
                " whether the scope admits a negative"
            )
        elif not negative_admitted:
            open_items.append("NOT_AFFECTED, but the scope does not admit a negative")
        if not fresh:
            open_items.append(
                "NOT_AFFECTED with no freshness bound: the evidence may be of any age"
            )
    if coverage not in _SETTLED_COVERAGE:
        open_items.append(f"inspection coverage {coverage}")
    if trust is not None:
        for status in TRUST_STATUSES:
            if status != "VERIFIED_RELATIONSHIP" and trust[status]:
                open_items.append(f"trust: {trust[status]} {status}")

    return Outcome(
        contract_version=doc["contract_version"],
        event=doc["event_context"]["id"],
        dependency=doc["identity"]["dependency"],
        relationship=relationship,
        affected=assessment["affected"],
        direct_scope=meaning["direct_scope"] if meaning else None,
        coverage=coverage,
        coverage_reasons=tuple(coverage_field["reasons"]) if coverage_field else (),
        trust=trust,
        negative_admitted=negative_admitted,
        freshness_bound_applied=fresh,
        unknowns=tuple(doc["unknowns"]["unknowns"]),
        limitations=tuple(doc["unknowns"]["limitations"]),
        open=tuple(open_items),
    )


@dataclass
class Summary:
    """Counts per axis over valid documents; no axis is folded into another."""

    valid: int = 0
    invalid: int = 0
    relationships: dict[str, int] = field(default_factory=lambda: dict.fromkeys(RELATIONSHIPS, 0))
    coverage: dict[str, int] = field(default_factory=lambda: dict.fromkeys(COVERAGE, 0))
    trust_records: dict[str, int] = field(default_factory=lambda: dict.fromkeys(TRUST_STATUSES, 0))
    trust_not_checked: int = 0
    with_open_items: int = 0
    outcomes: list[Outcome] = field(default_factory=list)

    def add(self, doc: Any) -> Outcome | None:
        """Count one document; an invalid one is counted and not read."""
        if not isinstance(doc, dict) or not check(doc).valid:
            self.invalid += 1
            return None
        result = outcome(doc)
        self.valid += 1
        self.relationships[result.relationship] += 1
        self.coverage[result.coverage] += 1
        if result.trust is None:
            self.trust_not_checked += 1
        else:
            for status, count in result.trust.items():
                self.trust_records[status] += count
        if result.open:
            self.with_open_items += 1
        self.outcomes.append(result)
        return result

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize(documents: Iterable[Any]) -> Summary:
    summary = Summary()
    for doc in documents:
        summary.add(doc)
    return summary


__all__ = [
    "COVERAGE",
    "RELATIONSHIPS",
    "TRUST_STATUSES",
    "Outcome",
    "Summary",
    "outcome",
    "summarize",
]
