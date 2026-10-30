"""OpenPulse Intelligence Schema v0.7.0 — pydantic models (source of truth)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from .enums import Confidence, EventType, Impact

SCHEMA_VERSION = "0.7.0"


class Source(BaseModel):
    name: str  # e.g. "bitnami/official-blog", "endoflife.date", "osv.dev"
    url: HttpUrl
    authority: str = Field(description="official | primary | secondary | tertiary")
    fetched_at: datetime
    # Provenance (all optional — v0.1.0 documents still validate).
    family: str | None = Field(
        default=None,
        description="Independent-source family (e.g. 'bitnami'); "
        "republished copies share the originator's family",
    )
    derived_from: str | None = Field(
        default=None, description="Source name this evidence derives from, if any"
    )
    acquisition_method: str | None = Field(
        default=None, description="e.g. 'https-collector', 'manual-curation'"
    )
    parser_version: str | None = Field(default=None, description="Parser that produced this record")
    content_hash: str | None = Field(
        default=None, description="sha256:<hex> over canonical source content"
    )


class Evidence(BaseModel):
    source: Source
    excerpt: str = Field(max_length=2000)
    effective_date: date | None = None
    announcement_date: date | None = None
    relation: Literal["supports", "context", "contradicts"] = Field(
        default="supports",
        description="How this evidence relates to the event claim",
    )


class CanonicalProject(BaseModel):
    """Entity resolution root: one project, many names/packages."""

    slug: str  # e.g. "bitnami", "redis", "postgresql"
    display_name: str
    github_repo: str | None = None  # "org/repo"
    website: HttpUrl | None = None
    purls: list[str] = []
    cpes: list[str] = []
    aliases: list[str] = []  # e.g. ["redis", "redis-server", "docker.io/redis", "bitnami/redis"]
    docker_images: list[str] = []


class Artifact(BaseModel):
    kind: str  # docker-image | helm-chart | npm | pypi | maven | ...
    ref: str  # e.g. "docker.io/bitnami/redis:7.2"


class Claim(BaseModel):
    """One checkable assertion with named supporting evidence (no graph)."""

    id: str
    type: str = Field(description="Event type or 'vulnerability'")
    subject: str = Field(description="What the claim is about")
    statement: str = Field(description="The checkable assertion")
    evidence_refs: list[str] = Field(default_factory=list, description="Supporting source names")


class Attribution(BaseModel):
    """What the evidence establishes — populate only what is known."""

    affected_project: str | None = None
    affected_package: str | None = None
    affected_artifact: str | None = None
    affected_version: str | None = None


class Scope(BaseModel):
    """Event applicability scope — additive, all fields optional.

    Absent scope means project-wide (legacy behavior). Populated scope
    narrows matching: version lists, explicit artifacts/packages, or
    registries. A dependency outside a populated scope is NOT_AFFECTED
    only when the producer declares the scope complete
    (``exhaustive=True``); otherwise -- including when unspecified -- it
    is RELATED (the list names known members only).
    """

    kind: Literal["project", "package", "artifact", "version", "registry"] = "project"
    versions: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    packages: list[str] = Field(
        default_factory=list,
        description=(
            "Package-scope values. A purl without a version (pkg:pypi/redis) names "
            "exactly one package of one ecosystem; a bare name (redis) carries no "
            "ecosystem and is read through the dependency's curated identity. A bare "
            "value equal to the event's project covers every package curated as it "
            "(TR-2026-01 F2, F3)."
        ),
    )
    registries: list[str] = Field(default_factory=list)
    exhaustive: bool = Field(
        default=False,
        description=(
            "Producer declaration that the listed elements are every member of "
            "the scope (declared completeness; nothing verifies it). Default "
            "False: unspecified completeness is partial, so exclusion is never "
            "a clearance."
        ),
    )
    basis: Literal["definitional", "announced", "corroborated", "verified"] | None = Field(
        default=None,
        description=(
            "Why the scope is complete: 'definitional' (the scope is the event "
            "itself, e.g. one release line's EOL), 'announced' (a named source "
            "states the extent), 'corroborated' (an independent source family "
            "states the same extent), 'verified' (established by a verifier). "
            "A declaration without a basis is not admissible: exhaustive=True "
            "with no basis never clears (TR-2026-01 N3)."
        ),
    )

    def admits_negative(self) -> bool:
        """Declared complete *and* the declaration's basis is recorded."""
        return self.exhaustive and self.basis is not None


class OSSEvent(BaseModel):
    id: str
    schema_version: str = SCHEMA_VERSION
    project_slug: str
    event_type: EventType
    title: str
    summary: str
    confidence: Confidence
    impact: Impact
    affected_versions: list[str] = []
    affected_artifacts: list[Artifact] = []
    evidences: list[Evidence] = Field(min_length=1)
    claims: list[Claim] = Field(default_factory=list)
    attribution: Attribution | None = None
    scope: Scope | None = None
    withdrawn: bool = Field(
        default=False,
        description="Retracted by its source: asserts nothing and is not evaluated",
    )
    superseded_by: str | None = Field(
        default=None,
        description="Id of the event that corrects or replaces this one; not evaluated",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def requires_action(self) -> bool:
        return self.impact in (Impact.ACTION, Impact.CRITICAL)

    def is_current_record(self) -> bool:
        """Neither withdrawn nor superseded (TR-2026-01 N4)."""
        return not self.withdrawn and self.superseded_by is None
