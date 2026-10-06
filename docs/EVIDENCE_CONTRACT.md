# Evidence Contract v1

OpenPulse v1 is a versioned machine-readable content contract for one dependency verdict against one upstream event.

- Schema: schemas/evidence-contract/v1/schema.json
- Builder/validator: core/evidence_contract.py
- Convergence layer: core/attestation.py
- CLI: openpulse attest

## Contract

The document exposes event_context, identity, scope, affected_dependency, assessment, evidence_refs, temporal, unknowns, recommendation and provenance. Planned signature, signing_key_id and trust_root fields are null in v1.

## Integrity

provenance.content_hash is a SHA-256 digest over canonical evidence content. The content hash and generation timestamp are pinned during hashing, so equivalent logical content has the same digest regardless of build time. Any evidence-content modification changes the digest.

## Validation

The shipped schema is JSON Schema draft 2020-12. The built-in validator is dependency-free and fail-closed for keywords outside its supported subset.

## Versioning

contract_version uses semver for the wire shape. Breaking field/validation/hash changes require a new v2 schema directory.

## CLI

openpulse attest --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json

openpulse attest --sbom data/fixtures/sbom/cyclonedx.json --event data/fixtures/bitnami/event.json --output contracts.jsonl

The command emits one JSON document per dependency x event pair. Output is JSONL and is suitable for machine consumers.
