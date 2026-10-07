# Evidence Contract v1

The evidence contract is OpenPulse's answer to a machine consumer's
question: *"what did OpenPulse establish about my dependency, and on
what basis?"* It is a **content contract** - a versioned JSON document
with provenance for every field - not a signature format (keys,
signatures and trust roots are a separate, later concern, per issue
#53).

- Schema: [`schemas/evidence-contract/v1/schema.json`](../schemas/evidence-contract/v1/schema.json)
  (JSON Schema draft 2020-12)
- Builder + standalone validator: [`core/evidence_contract.py`](../core/evidence_contract.py)
- Convergence layer (the v0.1.0 inward shape): [`core/attestation.py`](../core/attestation.py)
- CLI: `openpulse attest`

## What a document states

One document = one dependency's verdict against one upstream event.
Top-level blocks:

| Block | States | Provenance (current surface) |
|---|---|---|
| `contract_version` | schema shape semver | constant in `core/evidence_contract.py` |
| `event_context` | the upstream event being attested | `OSSEvent` id/type/slug/title/confidence/impact |
| `identity` | who the dependency is, how trusted the mapping is | `verdict.dependency`, `core/entities/identity.py` statuses and paths |
| `scope` | what the event's scope says, verbatim | `OSSEvent.scope` |
| `affected_dependency` | the verdict's match shape | `verdict.relationship/affected/match_strength/match_method` (`core/risk/check.py`) |
| `assessment` | what OpenPulse concluded, and how strongly | `verdict` decision-matrix output |
| `evidence_refs` | the sources behind the event claim | `OSSEvent.evidences[i]` |
| `temporal` | the four temporal roles, `null` = unknown | evidence dates, detection ledger, analyst findings |
| `unknowns` | what the contract does NOT establish | derived from the verdict - never backfilled |
| `recommendation` | one conditional next step | `analyzers/report_analyst.py` ADVICE keyed by impact |
| `provenance` | generator, timestamp, integrity digest | package version, contract version, UTC now, content hash |
| `signature` / `signing_key_id` / `trust_root` | planned, **always `null` in v1** | out of scope per issue #53 |

## Integrity: `provenance.content_hash`

`sha256:<hex>` over canonical JSON (sorted keys, compact separators)
of every top-level field except the planned (always-null) signature
family, with the two clock/hash-dependent provenance values pinned:

- `provenance.content_hash` -> `"sha256:pending"`
- `provenance.generation_timestamp` -> `"1970-01-01T00:00:00Z"`

Consequences:

- The same logical document built twice produces the **same hash**,
  even though the generation timestamps differ.
- Any content edit - a changed reason, a removed unknown, a
  downgraded confidence - changes the hash.
  `verify_v1_content_hash(doc)` recomputes it.
- Clock drift never breaks verification: only content matters.

## Validating without OpenPulse

The schema uses only this draft-2020-12 subset: `type`, `const`,
`enum`, `anyOf`, `$ref` (local `#/$defs/*`), `items`, `minItems`,
`required`, `properties`, `additionalProperties: false`, `minLength`,
`maxLength`, `pattern`, and the formats `date`, `date-time`, `uri`.
Any standard draft-2020-12 validator (e.g. the `jsonschema` package in
any language) can check a document against the schema file alone - the
hand-rolled validator below is a convenience, not a requirement.

`core/evidence_contract.py` ships a dependency-free validator for the
same subset. It is **fail-closed**: a schema using a keyword outside
the subset produces an explicit `unsupported keyword` error, never a
silent pass. Extending the schema and the validator must happen in the
same PR.

## Versioning policy

`contract_version` is semver for the **shape**, not the content.

- **Patch** (`1.0.x`): description/wording changes that alter no field
  set, no type, and no validation outcome.
- **Minor** (`1.x.0`): additive fields (a new optional block or
  property). Older documents remain valid.
- **Breaking** (`x.0.0`): removing/renaming fields, tightening
  validation, or changing `content_hash` computation. Requires a new
  `schemas/evidence-contract/vX/` directory and a migration note
  here.

The planned signature fields move from `null` to populated values only
in a future version, and that change is breaking by design - consumers
must not treat v1 documents as signed.

## Relationship to the v0.1.0 attestation shape

`core/attestation.py` (PR #60) converged OpenPulse's existing outputs
into an inward pydantic model. v1 is that model plus **outward names**:

| v0.1.0 (inward) | v1 (outward) |
|---|---|
| `contract_schema_version` | `contract_version` |
| `event` | `event_context` |
| `evidence_references` | `evidence_refs` |
| `dates` | `temporal` |

Every value path is shared: `build_v1_contract` calls the #60 builder,
renames blocks, stamps `1.0.0`, and recomputes the content hash over
the v1 shape. There is no second derivation path to keep in sync.

## CLI

```
openpulse attest --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json
openpulse attest --sbom data/fixtures/sbom/cyclonedx.json --event data/fixtures/bitnami/event.json --output contracts.jsonl
```

Emit mode is JSONL: one schema-valid contract document per line (one
per dependency x event pair). `--output` writes the JSONL to a file;
without it, stdout stays line-delimited for piping. Progress chatter
goes to stderr, so stdout is always exactly the documents. `--event`
is repeatable, and all five dependency sources (`--watchlist`,
`--sbom`, `--spdx`, `--images`, `--lockfile`) compose with each other
exactly as in `openpulse check`. `--raw-bundle-dir` enables the
security-correlation stream the same way check does.
