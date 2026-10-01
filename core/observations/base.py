"""Shared observation metadata — one envelope for every source kind.

RegistryObservation, GitHubRepositoryObservation and
LifecycleObservation all carry: observation_id, source,
entity_reference, observed_at, first_detected_at, content_hash,
parser_version, previous_observation_hash, chain_hash. Source-specific
facts live in each subclass payload. Future collectors emit these
instead of inventing new shapes.

Sealed observations are frozen: ``seal()`` and ``link()`` return new
instances, and mutating a sealed record raises. Trust comes from
``verify_record()`` (content + chain recompute), not from the type
system alone.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.evidence.provenance import PARSER_VERSION, hash_content
from core.observations.chain import (
    GENESIS_PREVIOUS,
    chain_hash,
    link_hash_for,
)


class ObservationBase(BaseModel):
    model_config = ConfigDict(frozen=True)

    observation_id: str = ""
    source: str = "unknown"
    entity_reference: str = ""
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    first_detected_at: datetime | None = Field(
        default=None,
        description="First trustworthy detection of this entity (inherited along the chain)",
    )
    content_hash: str | None = None
    parser_version: str = PARSER_VERSION
    previous_observation_hash: str | None = Field(
        default=None, description="Predecessor chain hash, or 'genesis' for the first sighting"
    )
    chain_hash: str | None = None

    def integrity_body(self) -> dict[str, Any]:
        """Payload covered by content_hash — subclass facts, nothing else."""
        return {}

    def _seal_update(self, body: dict[str, Any]) -> dict[str, Any]:
        """Update dict for sealing — model_copy preserves the subclass."""
        content = hash_content(body)
        short = content.split(":")[1][:12]
        observation_id = self.observation_id or f"{self.source}:{self.entity_reference}:{short}"
        return {"content_hash": content, "observation_id": observation_id}

    def seal(self, body: dict[str, Any]) -> ObservationBase:
        """Return a sealed copy: content hash + stable id. The original is untouched."""
        return self.model_copy(update=self._seal_update(body))

    def link(
        self,
        previous: dict[str, Any] | ObservationBase | None,
    ) -> ObservationBase:
        """Return a chain-linked copy. None previous = explicit genesis baseline.

        ``first_detected_at`` is inherited from the predecessor (the
        entity was first seen then); a genesis record detects now.
        Requires a sealed record (content_hash must exist).
        """
        if self.content_hash is None:
            raise ValueError("link() requires a sealed observation (seal first)")
        if previous is None:
            prev_link: str | None = GENESIS_PREVIOUS
            first: datetime | None = self.observed_at
        else:
            raw = previous.model_dump(mode="json") if isinstance(previous, BaseModel) else previous
            prev_link = link_hash_for(raw)
            if prev_link is None:
                raise ValueError("link() predecessor carries no verifiable hash")
            first_raw = raw.get("first_detected_at") or raw.get("observed_at")
            first = _coerce_dt(first_raw) or self.observed_at
        chained = self.model_copy(
            update={"previous_observation_hash": prev_link, "first_detected_at": first}
        )
        digest = chain_hash(chained.model_dump(mode="json"), str(prev_link))
        return chained.model_copy(update={"chain_hash": digest})

    def verify_record(self) -> str:
        """VALID/BROKEN/UNKNOWN: content recompute, then chain-link self-check.

        The chain link is checked against this record's own stated
        predecessor (recompute consistency); full-history verification
        is ``verify_observation_chain`` over the stored files.
        """
        if self.content_hash != hash_content(self.integrity_body()):
            return "BROKEN"
        dumped = self.model_dump(mode="json")
        if not self.chain_hash:
            return "UNKNOWN"  # sealed but never chained (legacy shape)
        prev = self.previous_observation_hash
        if prev is None:
            return "BROKEN"
        if prev == GENESIS_PREVIOUS:
            if self.chain_hash != chain_hash(dumped, GENESIS_PREVIOUS):
                return "BROKEN"
            return "VALID"
        # Non-genesis: the stored link must at least be a hash-shaped
        # value and the digest must recompute; whether the predecessor
        # file still exists is the chain walk's job, not this record's.
        if not isinstance(prev, str) or not prev.startswith("sha256:"):
            return "BROKEN"
        if self.chain_hash != chain_hash(dumped, prev):
            return "BROKEN"
        return "VALID"

    @property
    def integrity(self) -> str:
        """Shorthand for verify_record() (VALID | BROKEN | UNKNOWN)."""
        return self.verify_record()


def _coerce_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


# Re-export chain verification at the envelope level for callers that
# work in plain dicts (store, sweep, CLI).
def verify_observation_chain(records: list[dict[str, Any]]) -> dict[str, Any]:
    from core.observations.chain import verify_observation_chain as _verify

    return _verify(records)


class GitHubRepositoryObservation(ObservationBase):
    source: str = "github"
    repo: str = ""
    archived: bool = False
    pushed_at: str | None = None
    default_branch: str | None = None
    license: str | None = None

    def integrity_body(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "archived": self.archived,
            "pushed_at": self.pushed_at,
            "license": self.license,
        }

    def seal(self, body: dict[str, Any] | None = None) -> GitHubRepositoryObservation:  # type: ignore[override]
        staged = self.model_copy(update={"entity_reference": self.entity_reference or self.repo})
        return staged.model_copy(update=staged._seal_update(body or staged.integrity_body()))


class LifecycleObservation(ObservationBase):
    source: str = "endoflife"
    product: str = ""
    cycle: str = ""
    eol: Any = None
    support: Any = None
    latest: str | None = None

    def integrity_body(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "cycle": self.cycle,
            "eol": self.eol,
            "support": self.support,
            "latest": self.latest,
        }

    def seal(self, body: dict[str, Any] | None = None) -> LifecycleObservation:  # type: ignore[override]
        staged = self.model_copy(
            update={"entity_reference": self.entity_reference or f"{self.product}:{self.cycle}"}
        )
        return staged.model_copy(update=staged._seal_update(body or staged.integrity_body()))
