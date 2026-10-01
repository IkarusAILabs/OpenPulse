"""Registry observations — immutable, digest-aware facts about a repository.

A tag is NOT an identity: `latest` today may resolve to a different
digest tomorrow. Observations persist tag→digest mappings so change
detection compares facts against facts, never a snapshot against a
hunch. No observation, no change claim: a first sighting is a
baseline, not an event.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from core.observations.base import ObservationBase
from core.observations.chain import verify_link


class RegistryObservation(ObservationBase):
    source: str = "docker-hub"
    collector: str = "registries"
    registry: str = "docker.io"
    namespace: str
    repository: str
    tags: dict[str, list[str]] = Field(
        default_factory=dict, description="tag -> sorted image digests (multi-arch aware)"
    )
    tag_count: int | None = None
    missing: bool = False

    def integrity_body(self) -> dict:
        return {
            "registry": self.registry,
            "namespace": self.namespace,
            "repository": self.repository,
            "tags": self.tags,
            "missing": self.missing,
        }

    def seal(self, body: dict | None = None) -> RegistryObservation:  # type: ignore[override]
        """Attach content hash + observation id. Returns a new frozen copy."""
        staged = self.model_copy(
            update={
                "entity_reference": self.entity_reference
                or f"{self.registry}/{self.namespace}/{self.repository}"
            }
        )
        return staged.model_copy(update=staged._seal_update(body or staged.integrity_body()))


def _raw_body(record: dict) -> dict:
    """Content-covered facts straight from the stored mapping (no coercion)."""
    return {
        "registry": record.get("registry"),
        "namespace": record.get("namespace"),
        "repository": record.get("repository"),
        "tags": record.get("tags") or {},
        "missing": bool(record.get("missing")),
    }


def verify_registry_observation(record: dict, previous_link: str | None = None) -> str:
    """VALID/BROKEN/UNKNOWN for one persisted registry record.

    Recomputes the content hash from the stored facts (catches body
    edits that keep the hash fields), then checks the chain link
    against ``previous_link`` — the predecessor's chain hash, or None
    for a genesis record. Records that predate chaining verify
    UNKNOWN, never VALID. Prefer ``verify_registry_history`` for
    whole histories.
    """
    from core.evidence.provenance import hash_content

    if not isinstance(record, dict):
        return "BROKEN"
    try:
        body_hash = hash_content(_raw_body(record))
    except Exception:
        return "BROKEN"
    if record.get("content_hash") != body_hash:
        return "BROKEN"
    if not record.get("chain_hash"):
        return "UNKNOWN"
    return verify_link(record, previous_link)


def verify_registry_history(records: list[dict]) -> dict:
    """Content + chain verification over oldest->newest stored records."""
    from core.observations.chain import (
        BROKEN as _BROKEN,
    )
    from core.observations.chain import (
        UNKNOWN as _UNKNOWN,
    )
    from core.observations.chain import (
        VALID as _VALID,
    )
    from core.observations.chain import (
        verify_observation_chain,
    )

    content_breaks = [
        i
        for i, record in enumerate(records)
        if not isinstance(record, dict) or _content_hash_of(record) is None
    ]
    chain = verify_observation_chain(records)
    if content_breaks or chain["status"] == _BROKEN:
        return {
            "status": _BROKEN,
            "breaks": sorted(set(content_breaks) | set(chain["breaks"])),
            "unknowns": chain["unknowns"],
        }
    if chain["status"] == _UNKNOWN:
        return {"status": _UNKNOWN, "breaks": [], "unknowns": chain["unknowns"]}
    return {"status": _VALID, "breaks": [], "unknowns": []}


def _content_hash_of(record: dict) -> str | None:
    """Recomputed content hash, or None when the stored body is corrupt."""
    from core.evidence.provenance import hash_content

    try:
        recomputed = hash_content(_raw_body(record))
    except Exception:
        return None
    return recomputed if record.get("content_hash") == recomputed else None


class Change(BaseModel):
    """One detected difference between two observations of the same repository."""

    model_config = ConfigDict(frozen=True)

    type: str = Field(
        description="tag_appeared | tag_disappeared | tag_digest_changed | "
        "latest_moved | repo_missing | repo_restored"
    )
    registry: str = "docker.io"
    namespace: str
    repository: str
    tag: str | None = None
    previous: list[str] | None = None
    current: list[str] | None = None
    previous_observation_id: str | None = Field(
        default=None, description="Observation the 'before' facts come from"
    )
    current_observation_id: str | None = Field(
        default=None, description="Observation the 'after' facts come from"
    )
    previous_observed_at: datetime | None = None
    previous_hash: str | None = Field(default=None, description="Previous observation content_hash")
    current_hash: str | None = Field(default=None, description="Current observation content_hash")
    previous_chain: str | None = Field(
        default=None, description="Previous observation chain_hash (tamper-evident link)"
    )
    current_chain: str | None = Field(
        default=None, description="Current observation chain_hash (tamper-evident link)"
    )
    tags_present: list[str] | None = Field(
        default=None,
        description="Tags present in the current observation (grounds NOT-AFFECTED scope)",
    )
    first_detected_at: datetime | None = Field(
        default=None, description="First history scan that surfaced this change"
    )
    parser_version: str | None = Field(default=None, description="Parser that read the probe")
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


#: Upper bound on tags per observation. A hostile or corrupted
#: registry response must not exhaust memory/disk via an unbounded
#: tag map (legitimate Hub repos stay orders of magnitude below).
MAX_OBSERVATION_TAGS = 10_000


def to_observation(probe: dict, observed_at: datetime | None = None) -> RegistryObservation:
    """Registry probe dict (from the docker collector) -> sealed observation."""
    digests = probe.get("digests", {})
    if not isinstance(digests, dict):
        raise ValueError("probe digests must be a tag->digests mapping")
    if len(digests) > MAX_OBSERVATION_TAGS:
        raise ValueError(f"probe carries {len(digests)} tags (limit {MAX_OBSERVATION_TAGS})")
    tags = {}
    for tag, values in digests.items():
        if not isinstance(values, list):
            raise ValueError(f"probe digests for tag {tag!r} must be a list")
        tags[str(tag)] = [str(d) for d in values]
    return RegistryObservation(
        registry=probe.get("registry", "docker.io"),
        namespace=probe.get("namespace", ""),
        repository=probe.get("repo", ""),
        observed_at=observed_at or datetime.now(timezone.utc),
        tags=tags,
        tag_count=probe.get("count"),
        missing=bool(probe.get("missing")),
    ).seal()


def diff_observations(prev: RegistryObservation | None, curr: RegistryObservation) -> list[Change]:
    """Compare two observations. No previous observation -> baseline -> no changes."""
    if prev is None:
        return []
    if prev.content_hash == curr.content_hash and prev.missing == curr.missing:
        return []
    changes: list[Change] = []
    common = {
        "registry": curr.registry,
        "namespace": curr.namespace,
        "repository": curr.repository,
        "previous_observation_id": prev.observation_id or None,
        "current_observation_id": curr.observation_id or None,
        "previous_observed_at": prev.observed_at,
        "previous_hash": prev.content_hash,
        "current_hash": curr.content_hash,
        "previous_chain": prev.chain_hash,
        "current_chain": curr.chain_hash,
        "tags_present": sorted(curr.tags or {}),
        "parser_version": curr.parser_version,
    }
    if curr.missing and not prev.missing:
        return [Change(type="repo_missing", observed_at=curr.observed_at, **common)]
    if not curr.missing and prev.missing:
        return [Change(type="repo_restored", observed_at=curr.observed_at, **common)]
    prev_tags, curr_tags = prev.tags or {}, curr.tags or {}
    for tag in sorted(set(curr_tags) - set(prev_tags)):
        changes.append(
            Change(
                type="tag_appeared",
                tag=tag,
                current=curr_tags[tag],
                observed_at=curr.observed_at,
                **common,
            )
        )
    for tag in sorted(set(prev_tags) - set(curr_tags)):
        changes.append(
            Change(
                type="tag_disappeared",
                tag=tag,
                previous=prev_tags[tag],
                observed_at=curr.observed_at,
                **common,
            )
        )
    for tag in sorted(set(prev_tags) & set(curr_tags)):
        if prev_tags[tag] != curr_tags[tag]:
            changes.append(
                Change(
                    type="latest_moved" if tag == "latest" else "tag_digest_changed",
                    tag=tag,
                    previous=prev_tags[tag],
                    current=curr_tags[tag],
                    observed_at=curr.observed_at,
                    **common,
                )
            )
    return changes
