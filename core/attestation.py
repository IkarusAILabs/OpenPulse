"""Evidence contract minimal schema - attestation precursor (issue #53).

Machine-readable dependency intelligence another system can consume
without understanding OpenPulse internals. This module is the
CONVERGENCE step, not an invention step: every field below already
exists somewhere in current outputs, and each field's docstring names
its current source. Fields with no current source are marked
``planned`` and are never populated by the builder.

Scope (deliberate):
- Built from (event, verdict[, finding]) triples the verdict engine
  already produces - no re-derivation, no second opinion.
- Verdict-level documents: one contract document per dependency
  verdict, carrying the event context that produced it.
- Round-trip: dump -> re-validate -> byte-identical document.
- No CLI surface yet. No signing, keys, signatures, or trust roots -
  those are a separate, later issue (#53's own Out of scope).
- Not a policy decision: consumers decide what to do with the
  assessment; the contract only states what OpenPulse established.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.evidence.provenance import hash_content
from core.leadtime import event_effective_day, parse_day
from core.schema.models import OSSEvent

#: Bump when the contract's field set or semantics change.
CONTRACT_SCHEMA_VERSION = "0.1.0"

#: Fields accepted by the contract but NOT populated today. The
#: builder never writes these; their presence in the model documents
#: the planned shape and keeps consumers from inventing them.
PLANNED_FIELDS: frozenset[str] = frozenset(
    {
        "signature",
        "signing_key_id",
        "trust_root",
    }
)


class IdentityBlock(BaseModel):
    """Identity of the affected entity, with trust status.

    Sources: verdict.dependency / verdict.identity_status
    (core/risk/check.py); identity trust states and mapping paths
    come from core/entities/identity.py (resolution_trust).
    """

    model_config = ConfigDict(extra="forbid")

    dependency: str = Field(description="Verdict dependency label (verdict.dependency)")
    identity_status: str = Field(
        description="VERIFIED | REVIEW_REQUIRED | UNVERIFIED (verdict.identity_status)"
    )
    identity_via: str | None = Field(
        default=None,
        description=(
            "How the slug was reached: explicit | catalog | namespace_rule | self | "
            "exact-artifact (winning cause identity_via)"
        ),
    )


class ScopeBlock(BaseModel):
    """What the event scope says, verbatim.

    Source: event.scope (core/schema/models.py Scope).
    """

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(description="project | package | artifact | version | registry")
    versions: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    packages: list[str] = Field(default_factory=list)
    registries: list[str] = Field(default_factory=list)


class AffectedDependencyBlock(BaseModel):
    """The dependency the verdict is about.

    Source: verdict.dependency + verdict.relationship / affected /
    match_strength / match_method (core/risk/check.py _combine).
    """

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Verdict dependency label")
    relationship: str = Field(
        description=(
            "AFFECTS_ARTIFACT | AFFECTS_VERSION | AFFECTS_PACKAGE | NOT_AFFECTED | "
            "RELATED | AFFECTS_PROJECT | UNKNOWN (verdict.relationship)"
        )
    )
    affected: bool = Field(description="True only for ARTIFACT/VERSION/PACKAGE (verdict.affected)")
    match_strength: str = Field(
        description="exact | scoped | exclusion | contextual | none (verdict.match_strength)"
    )
    match_method: str | None = Field(
        default=None, description="Winning cause match_method (verdict.match_method)"
    )


class AssessmentBlock(BaseModel):
    """What OpenPulse concluded and how strongly.

    Sources: verdict.affected / relationship / confidence /
    match_strength / evidence_confidence / reason
    (core/risk/check.py _combine).
    """

    model_config = ConfigDict(extra="forbid")

    relationship: str
    affected: bool
    confidence: str = Field(description="Verdict confidence after identity cap")
    match_strength: str
    evidence_confidence: str
    reason: str = Field(description="Verdict reason, verbatim")


class EvidenceReference(BaseModel):
    """One supporting evidence source, with authority.

    Source: event.evidences[i] (core/schema/models.py Evidence/Source).
    """

    model_config = ConfigDict(extra="forbid")

    source_name: str
    url: str
    authority: str
    fetched_at: datetime
    relation: str = Field(default="supports")
    excerpt: str = Field(max_length=2000)


class DateRoles(BaseModel):
    """The four temporal roles, parsed; None means unknown, never a guess.

    Sources: announcement/effective from event evidence dates;
    first_detected from verdict.first_detected (detection ledger);
    last_verified from finding.last_observed_at / observed_at.
    Parsed through core.leadtime.parse_day.
    """

    model_config = ConfigDict(extra="forbid")

    announcement_date: str | None = None
    effective_date: str | None = None
    first_detected: str | None = Field(
        default=None,
        description=("Earliest durable ledger detection (verdict.first_detected); None = unknown"),
    )
    last_verified: str | None = Field(
        default=None,
        description=(
            "Most recent re-observation (finding last_observed_at/observed_at); None = unknown"
        ),
    )


class UnknownsBlock(BaseModel):
    """What the contract does NOT establish - unknown stays unknown.

    Derived from the verdict itself: a None date, an UNKNOWN
    relationship, or untrusted identity metadata is stated, never
    backfilled. Roadmap principle 8.
    """

    model_config = ConfigDict(extra="forbid")

    unknowns: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RecommendationBlock(BaseModel):
    """One conditional next step, in report vocabulary.

    Source: analyzers/report_analyst.py ADVICE, keyed by the event
    impact. Conditional wording only - instructions, never claims
    about the consumer environment.
    """

    model_config = ConfigDict(extra="forbid")

    text: str


class ProvenanceBlock(BaseModel):
    """Who generated this, when, under which schema.

    Sources: package version via importlib.metadata (same approach
    as reports/generate.py); schema version constant here; UTC now.
    """

    model_config = ConfigDict(extra="forbid")

    openpulse_version: str
    contract_schema_version: str = Field(default=CONTRACT_SCHEMA_VERSION)
    generation_timestamp: datetime
    event_id: str
    content_hash: str = Field(
        description=(
            "sha256 over the contract body: every field below except the hash "
            "itself and the generation timestamp, both pinned during hashing so "
            "the same logical document always hashes identically"
        )
    )


class EvidenceContract(BaseModel):
    """One dependency verdict as a consumable evidence document.

    Round-trip guarantee: ``dump_contract`` output re-validates
    byte-identically through ``EvidenceContract.model_validate_json``.
    ``provenance.content_hash`` covers the document body (everything
    except the hash itself and the generation timestamp, both pinned
    during hashing) so a consumer can verify integrity without
    understanding the fields, and so the same logical document built
    twice hashes identically.
    """

    model_config = ConfigDict(extra="forbid")

    contract_schema_version: str = Field(default=CONTRACT_SCHEMA_VERSION)
    event: dict[str, Any] = Field(
        description=("Event context: id, event_type, project_slug, title, confidence, impact")
    )
    identity: IdentityBlock
    scope: ScopeBlock
    affected_dependency: AffectedDependencyBlock
    assessment: AssessmentBlock
    evidence_references: list[EvidenceReference] = Field(min_length=1)
    dates: DateRoles
    unknowns: UnknownsBlock
    recommendation: RecommendationBlock
    provenance: ProvenanceBlock

    # Planned (never populated by the builder):
    signature: str | None = Field(
        default=None,
        description="planned: cryptographic signature over content_hash (separate issue)",
    )
    signing_key_id: str | None = Field(
        default=None, description="planned: key identifier for the above signature"
    )
    trust_root: str | None = Field(
        default=None, description="planned: where the signing key is anchored"
    )


#: Fields covered by the content hash. The two clock/hash-dependent
#: provenance values (content_hash, generation_timestamp) are pinned
#: to placeholders during hashing: the digest is a function of the
#: evidence content only, so the same logical document built twice
#: hashes identically. verify_content_hash reproduces this shape.
_HASH_BODY_FIELDS = (
    "contract_schema_version",
    "event",
    "identity",
    "scope",
    "affected_dependency",
    "assessment",
    "evidence_references",
    "dates",
    "unknowns",
    "recommendation",
    "provenance",
)

_HASH_PLACEHOLDER = "sha256:pending"
_TIMESTAMP_PLACEHOLDER = "1970-01-01T00:00:00Z"


def _openpulse_version() -> str:
    """Installed package version, or unknown (same fallback as reports)."""
    try:
        from importlib.metadata import version as _pkg_version

        return str(_pkg_version("openpulse"))
    except Exception:
        return "unknown"


def _event_context(event: OSSEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "event_type": event.event_type.value,
        "project_slug": event.project_slug,
        "title": event.title,
        "confidence": event.confidence.value,
        "impact": event.impact.value,
    }


def _scope_block(event: OSSEvent) -> ScopeBlock:
    scope = event.scope
    if scope is None:
        return ScopeBlock(kind="project")
    return ScopeBlock(
        kind=scope.kind,
        versions=list(scope.versions or []),
        artifacts=list(scope.artifacts or []),
        packages=list(scope.packages or []),
        registries=list(scope.registries or []),
    )


def _winning_cause(verdict: Any) -> dict[str, Any] | None:
    """The highest-ranked recorded cause, or None when there are none."""
    causes = list(getattr(verdict, "verdicts", None) or [])
    if not causes:
        return None
    from core.risk.check import _RANK

    return max(causes, key=lambda c: _RANK.get(str(c.get("relationship", "")), 0))


def _evidence_references(event: OSSEvent) -> list[EvidenceReference]:
    return [
        EvidenceReference(
            source_name=e.source.name,
            url=str(e.source.url),
            authority=e.source.authority,
            fetched_at=e.source.fetched_at,
            relation=e.relation,
            excerpt=e.excerpt,
        )
        for e in event.evidences
    ]


def _dates_block(event: OSSEvent, verdict: Any, finding: dict[str, Any] | None) -> DateRoles:
    """Temporal roles from their real homes; unknown stays unknown."""
    announced: str | None = None
    for e in event.evidences:
        day = parse_day(e.announcement_date)
        if day is not None:
            announced = str(day)
            break
    effective_day = event_effective_day(event)
    effective: str | None = str(effective_day) if effective_day is not None else None
    first_detected = getattr(verdict, "first_detected", None)
    first_detected = str(first_detected) if first_detected else None
    last_verified: str | None = None
    if finding:
        for key in ("last_observed_at", "observed_at"):
            day = parse_day(finding.get(key))
            if day is not None:
                last_verified = str(day)
                break
    return DateRoles(
        announcement_date=announced,
        effective_date=effective,
        first_detected=first_detected,
        last_verified=last_verified,
    )


def _unknowns_block(verdict: Any, dates: DateRoles, identity_block: IdentityBlock) -> UnknownsBlock:
    unknowns: list[str] = []
    limitations: list[str] = []
    if not dates.announcement_date:
        unknowns.append("announcement date unknown")
    if not dates.effective_date:
        unknowns.append("effective date unknown")
    if not dates.first_detected:
        unknowns.append("first detection unknown (no durable ledger record)")
    if not dates.last_verified:
        unknowns.append("last verification unknown (no re-observation recorded)")
    if str(getattr(verdict, "relationship", "")) == "UNKNOWN":
        unknowns.append("relationship unknown: no applicable evidence")
    if identity_block.identity_status != "VERIFIED":
        limitations.append(
            "identity mapping is "
            + identity_block.identity_status
            + ": conclusions capped at EMERGING"
        )
    return UnknownsBlock(unknowns=unknowns, limitations=limitations)


def _recommendation(event: OSSEvent) -> RecommendationBlock:
    from analyzers.report_analyst import ADVICE

    return RecommendationBlock(text=ADVICE.get(event.impact.value, ""))


def _identity_block(verdict: Any, winning_cause: dict[str, Any] | None) -> IdentityBlock:
    identity_via = None
    if winning_cause is not None:
        identity_via = winning_cause.get("identity_via") or None
    return IdentityBlock(
        dependency=str(getattr(verdict, "dependency", "")),
        identity_status=str(getattr(verdict, "identity_status", "VERIFIED")),
        identity_via=identity_via,
    )


def build_contract(
    event: OSSEvent,
    verdict: Any,
    finding: dict[str, Any] | None = None,
) -> EvidenceContract:
    """(event, verdict[, finding]) -> one evidence-contract document.

    Pure: no I/O, no side effects. Every field is copied from an
    existing surface (event, verdict, or the optional analyst
    finding); nothing is inferred, estimated, or backfilled. The only
    clock read is the provenance generation timestamp.
    """
    winning = _winning_cause(verdict)
    identity_block = _identity_block(verdict, winning)
    dates = _dates_block(event, verdict, finding)
    contract = EvidenceContract(
        event=_event_context(event),
        identity=identity_block,
        scope=_scope_block(event),
        affected_dependency=AffectedDependencyBlock(
            label=str(getattr(verdict, "dependency", "")),
            relationship=str(getattr(verdict, "relationship", "UNKNOWN")),
            affected=bool(getattr(verdict, "affected", False)),
            match_strength=str(getattr(verdict, "match_strength", "none")),
            match_method=getattr(verdict, "match_method", None),
        ),
        assessment=AssessmentBlock(
            relationship=str(getattr(verdict, "relationship", "UNKNOWN")),
            affected=bool(getattr(verdict, "affected", False)),
            confidence=str(getattr(verdict, "confidence", "UNVERIFIED")),
            match_strength=str(getattr(verdict, "match_strength", "none")),
            evidence_confidence=str(getattr(verdict, "evidence_confidence", "UNVERIFIED")),
            reason=str(getattr(verdict, "reason", "")),
        ),
        evidence_references=_evidence_references(event),
        dates=dates,
        unknowns=_unknowns_block(verdict, dates, identity_block),
        recommendation=_recommendation(event),
        provenance=ProvenanceBlock(
            openpulse_version=_openpulse_version(),
            generation_timestamp=datetime.now(timezone.utc),
            event_id=event.id,
            content_hash=_HASH_PLACEHOLDER,
        ),
    )
    object.__setattr__(
        contract,
        "provenance",
        contract.provenance.model_copy(update={"content_hash": _hash_body(contract)}),
    )
    return contract


def dump_contract(contract: EvidenceContract) -> str:
    """Canonical JSON dump. Byte-stable for the same logical document
    (the only clock-dependent field is the provenance timestamp)."""
    return contract.model_dump_json()


def round_trip(contract: EvidenceContract) -> EvidenceContract:
    """dump -> validate -> back. Byte-identical by construction."""
    return EvidenceContract.model_validate_json(dump_contract(contract))


def _hash_body(contract: EvidenceContract) -> str:
    """Digest over the contract body with the two non-evidence values
    (the hash itself and the generation timestamp) pinned: the digest
    depends on the evidence content only, never on build time."""
    body: dict[str, Any] = {}
    dumped = contract.model_dump()
    for field_name in _HASH_BODY_FIELDS:
        body[field_name] = dumped[field_name]
    body["provenance"]["content_hash"] = _HASH_PLACEHOLDER
    body["provenance"]["generation_timestamp"] = _TIMESTAMP_PLACEHOLDER
    return hash_content(body)


def verify_content_hash(contract: EvidenceContract) -> bool:
    """Recompute the body hash; True when it matches provenance.content_hash."""
    return _hash_body(contract) == contract.provenance.content_hash
