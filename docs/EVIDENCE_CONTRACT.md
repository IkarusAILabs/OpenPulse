# Evidence Contract

The evidence contract is OpenPulse's answer to a machine consumer's
question: *"what did OpenPulse establish about my dependency, and on
what basis?"* It is a **content contract** - a versioned JSON document
with provenance for every field - not a signature format (keys,
signatures and trust roots are a separate, later concern, per issue
#53).

- Schema (current, 2.4): [`schemas/evidence-contract/v2.4/schema.json`](../schemas/evidence-contract/v2.4/schema.json)
  (JSON Schema draft 2020-12); 2.3, 2.2, 2.1, 2.0, 1.2, 1.1 and 1.0 stay published beside it
- Hash verifier with no OpenPulse code (Node 18+): [`conformance/evidence-contract/verify.mjs`](../conformance/evidence-contract/verify.mjs)
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
| `inspection_coverage` (1.1) | how completely a source repository was read | `verdict.inspection_coverage` |
| `verdict_meaning` (1.2) | what the verdict asserts and does not, as closed vocabularies | `core/verdict_meaning.py` |
| `evaluation_context` (1.2) | freshness bound and identity policy the verdict was computed under | builder arguments |
| `scope.completeness` (1.2) | declared or partial, its basis, and whether it admits a negative | `OSSEvent.scope.exhaustive/basis` |
| `signature` / `signing_key_id` / `trust_root` | planned, **always `null` in v1** | out of scope per issue #53 |

## Integrity: `provenance.content_hash`

### 2.0.0: RFC 8785 (JCS)

`provenance.content_hash_method` is `jcs-sha256`, and `content_hash` is

    "sha256:" + hex(SHA-256(JCS(body)))

where `body` is the document with these removed:

- the planned signature fields `signature`, `signing_key_id` and `trust_root`;
- `provenance.content_hash` and `provenance.generation_timestamp`.

JCS is RFC 8785: members sorted by the UTF-16 code units of their names, numbers written as ECMAScript does, strings escaped as `JSON.stringify` does, no whitespace. Every other field is covered, including any field a later 2.x minor adds. A consumer recomputes the hash with any JCS library, without OpenPulse's serializer:

- Python: `core.evidence_contract.verify_content_hash(doc)` (any contract version; the JCS encoder is `core/jcs.py`, stdlib only).
- Node: `node conformance/evidence-contract/verify.mjs contracts.jsonl` (exit 1 when a document fails).

The same logical document still hashes identically at any build time, and any content edit changes the hash. A document whose `content_hash_method` is not `jcs-sha256` does not verify as 2.x.

### 1.x


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
  property). Newer documents are published in a new sibling schema
  directory (e.g. `schemas/evidence-contract/v1.1/schema.json`) while
  the previous minor schema stays untouched, so a consumer pinned to
  `1.0` keeps validating `1.0` documents. Older documents are not
  retroactively valid against the newer schema.
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
renames blocks, stamps the current `contract_version`, adds the
`inspection_coverage` block, and recomputes the content hash over the
v1 shape. There is no second derivation path to keep in sync.

### 1.1.0 - inspection coverage (v0.6.0)

Minor, additive: a new required top-level `inspection_coverage` block
carries the repository-inspection outcome that produced the verdict -
`{"status": COMPLETE|PARTIAL|FAILED, "reasons": [...]}`. Non-repository
inputs (`--watchlist`, `--sbom`, `--lockfile`, `--manifest`, `--images`)
are always `COMPLETE` in 1.1 through 2.0 (2.1 says `NOT_APPLICABLE`, below). A `PARTIAL` or `FAILED` status means OpenPulse
did not read every discovered dependency file, so the absence of an
AFFECTED verdict is not a clean bill of health. The producer version
continues to be `provenance.openpulse_version`.

The 1.1 schema is published at
`schemas/evidence-contract/v1.1/schema.json`; `v1/schema.json` is left
byte-for-byte at 1.0 and remains the schema for 1.0 documents. A
consumer pinned to 1.0 can keep validating 1.0 output; upgrading to 1.1
means adopting the file with the higher `contract_version`.

### 1.2.0 - verdict meaning (TR-2026-01 sections 5.1-5.2)

Minor, additive. A bare relationship label invites over-reading. An agent may take NOT_AFFECTED as permission to proceed, and AFFECTS_ARTIFACT as a finding that a dependency is broken. 1.2 states what a verdict does and does not assert, in fields a consumer can decide on without reading free text:

- **`verdict_meaning`:** `direct_scope` is one of `member`, `excluded`, `undetermined`, `project_tie` or `no_association`, derived from `assessment.relationship`.
  - `embedded_components`, `availability`, `maintenance_or_support` and `security_consequence` are always `not_evaluated`. OpenPulse establishes none of them.
  - `statement` is a fixed template per `direct_scope` and contains no upstream text.
- **`scope.completeness`:** `state` is `partial` or `declared` (`verified` is reserved for a future verifier). It also carries the declaration's `basis` and `admits_negative`, which is true only for a declaration with a recorded basis (N3). NOT_AFFECTED can only follow from such a scope.
- **`evaluation_context`:** the `as_of` time and `max_evidence_age_days` given to the freshness check, and whether a bound was applied at all. Without a bound, a negative may rest on evidence of any age, so compare `temporal.last_verified` or `evidence_refs[].fetched_at` with your own bound. `unresolved_identity` is the constant `undetermined`: an evaluation ablation can never be emitted as a contract.

The content hash is computed exactly as in 1.1, over 1.1's fields plus the two new top-level blocks. `verify_v1_content_hash` picks the field set from the document's own `contract_version`, so 1.1 documents keep verifying. The 1.1 schema stays byte-for-byte at `schemas/evidence-contract/v1.1/schema.json`.

**Canonical (RFC 8785, JCS) hashing is a 2.0.0 change.** It changes how `content_hash` is computed, which the versioning policy above classes as breaking. It was planned as "v1.2" in `docs/NEXT_PHASES.md` (B7) and is renumbered there.

### 2.0.0 - canonical content hash (v0.9.0, B7)

Major, because the hash computation changed. The shape is 1.2's plus one field:

- **`provenance.content_hash_method`:** the constant `jcs-sha256`, required.
- **`provenance.content_hash`:** SHA-256 over the JCS form of the document, as described under *Integrity* above. 1.x hashed a Python-specific serialization over a fixed field list with placeholders; 2.0 hashes RFC 8785 bytes of everything except the hash, the build time and the signature fields.

Every value is the 1.2 builder's: `build_contract` builds the 1.2 document and restamps it. `openpulse attest` emits 2.0.0. `build_v1_contract` still emits 1.2.0 unchanged (the frozen evaluation uses it), and 1.2, 1.1 and 1.0 documents keep validating against their own schemas and verifying with `verify_v1_content_hash`. `validate_contract` and `verify_content_hash` dispatch on the document's own `contract_version`.

**Upgrading a consumer:** validate against `schemas/evidence-contract/v2/schema.json` (a 2.0 document fails the 1.2 schema's `contract_version` const), and recompute the hash with JCS as above. The signature fields stay `null`.

### 2.1.0 - NOT_APPLICABLE coverage (v0.10.0, V3, #109)

Minor, additive. Up to 2.0, a run that inspected no repository (`--watchlist`, `--sbom`, `--spdx`, `--lockfile`, `--manifest`, `--images` only) stamped every contract `inspection_coverage.status: COMPLETE`, so a consumer could not tell "fully scanned" from "no scan happened". 2.1 adds one enum value:

- **`NOT_APPLICABLE`:** the run inspected no repository. `reasons` is empty. It is not a clean bill of health and not a failure: there is no repository coverage to report.
- **Unchanged:** a run with `--github-repo` stamps every contract with the run's `COMPLETE`, `PARTIAL` or `FAILED` status, as before (including contracts for dependencies from other inputs in the same run, so a partly read repository never makes them look clean).
- **Gates:** `NOT_APPLICABLE` counts as `COMPLETE`. `--fail-on` decides on verdicts alone, and SARIF and the GitHub Action raise no coverage warning.

Shape and hash are 2.0's: the content hash is the same JCS rule, and `content_hash_method` stays `jcs-sha256`. `openpulse attest` emits 2.1.0. The 2.0 schema stays byte-for-byte, so a 2.0 validator rejects `NOT_APPLICABLE`.

**Upgrading a consumer:** validate against `schemas/evidence-contract/v2.1/schema.json`, and treat `NOT_APPLICABLE` as "no repository in this run". A consumer that switches on the status must accept the fourth value.

### 2.2.0 - trust assurance (v0.13.0, X5, track T T-F2)

Minor, additive. One new required top-level field, `trust_assurance`:

- **`null`:** the run did not check trust. This is `openpulse attest` without `--trust`, and it is not a clean result: nothing was checked.
- **An object**, from `openpulse attest --trust`, which looks the dependency up live:
  - **`checks`:** one record per trust check, in a fixed shape: `check`, `status`, `statement`, `checked_at` and `references`.
    - `check` is one of `malicious` (OSV `MAL-` records), `registry_existence` (T-A1), `provenance` (T-B1), `repository_linkage` (T-A4), `dependency_confusion` (T-A3) or `lookalike` (T-A2).
    - `status` is the closed T-F1 vocabulary.
    - `statement` is a fixed template, never upstream text, and at most 500 characters.
    - `checked_at` is a date-time, or null for local checks.
    - `references` are the https URIs the record cites: the registry URL, the OSV record, the claimed repository.
  - **`summary`:** counts for all six statuses.
  - **`used_in_verdict`:** always `false`. Trust records never change `assessment`, `affected_dependency`, `recommendation` or `verdict_meaning` (tested).

| Status | Meaning |
|---|---|
| `CONFIRMED_MALICIOUS` | A cited authoritative record says so (an OSV `MAL-` record). OpenPulse never assigns it on its own indicators |
| `VERIFIED_FAILURE` | A check ran and failed: a digest or signature that doesn't verify, a provenance identity that differs from the claimed repository |
| `SUSPICIOUS_INCONCLUSIVE` | An indicator fired without confirmation |
| `MISSING_EVIDENCE` | The check ran but there was nothing to verify. Not evidence of authenticity |
| `VERIFIED_RELATIONSHIP` | The check ran and the binding holds. It binds an identity; it does not say the package is benign |
| `NOT_PERFORMED` | The check did not run (unsupported ecosystem, offline, source unreachable, budget, a private package) |

There is no `SAFE` value. Each check's own free-form evidence stays in the MCP answers and out of the contract, so this public shape does not change when a check's internals do.

The hash rule is 2.1's: `trust_assurance` is inside the JCS content hash like any other field, so `verify.mjs` and `verify_content_hash` cover it unchanged. The 2.1 schema stays byte-for-byte, and a 2.1 validator rejects a 2.2 document (`trust_assurance` is an unexpected property). `openpulse attest` emits 2.2.0.

**Upgrading a consumer:** validate against `schemas/evidence-contract/v2.2/schema.json`. Treat a null `trust_assurance` as "not checked", and never read a missing status as safe.

### 2.3.0 - reputation indicators (v0.16.0, Q5, track T T-C)

Minor, additive. `trust_assurance.checks[].check` may also be one of three reputation indicators. Each is an indicator only: it reports `SUSPICIOUS_INCONCLUSIVE` at most, never `VERIFIED_FAILURE` or `CONFIRMED_MALICIOUS`, and indicators are never summed into a score.

| `check` | `SUSPICIOUS_INCONCLUSIVE` when | `references` |
|---|---|---|
| `publisher_change` (threat T6) | The release was published by an npm account, or a PyPI provenance publisher, that the earlier releases did not use; or trusted publishing or attestations stopped | none |
| `repository_moved` | The claimed GitHub repository answers under another name (renamed or transferred) | the repository it answers as |
| `young_popular_repository` (threat T5) | The claimed repository is younger than 180 days and has at least 1000 stars. Stars are inputs, never trust evidence, so this check is never `VERIFIED_RELATIONSHIP` | the repository |

Their firing rates on legitimate packages are in [`docs/research/TRACK_T_MEASUREMENTS.md`](research/TRACK_T_MEASUREMENTS.md). Nothing else changes: same fields, statuses, summary and hash rule. The 2.2 schema stays byte-for-byte, and a 2.2 validator rejects a 2.3 document that names a new check. `openpulse attest` emitted 2.3.0 in v0.16-v0.17.

**Upgrading a consumer:** validate against `schemas/evidence-contract/v2.3/schema.json`. A consumer that switches on `check` must accept the three new names, or ignore names it does not know.

### 2.4.0 - discovery scope (v0.18.0, S3)

Minor, additive. `inspection_coverage` has a required `scope`: what the repository inspection searched, so a consumer can tell what COMPLETE was complete *over*. It is null when the run inspected no repository (`NOT_APPLICABLE`) or the repository could not be enumerated (`FAILED` before the tree was read).

| Field | Meaning |
|---|---|
| `repository`, `ref`, `commit` | The repository, the branch read, and the commit every file was read at |
| `file_patterns` | The dependency file names and patterns that were read (`requirements.txt`, `requirements*.txt`, `*.csproj`, ...) |
| `recognised_not_read` | Dependency file names recognised but not read (`yarn.lock`, `uv.lock`, ...); each one present makes coverage PARTIAL |
| `skipped_directories` | `[{directory, files}]`: directories not searched (`node_modules`, `vendor`, hidden directories, ...) and how many files each held, most first. At most 50 are named; `directory: null` sums the rest and any name outside `[A-Za-z0-9._-]` |
| `tree_entries` | Entries in the repository tree |
| `limits` | `max_tree_entries`, `max_files`, `max_file_bytes`, `max_total_bytes` |
| `limits_reached` | Which applied: `tree_truncated`, `max_files`, `max_file_bytes`, `max_total_bytes` |
| `files_found`, `files_read` | Dependency files discovered, and how many were read and parsed |

Coverage is only as complete as this search: a file outside `file_patterns`, under a skipped directory or past a limit was not read. The hash rule is unchanged; `scope` is inside the content hash. The 2.3 schema stays byte-for-byte, and a 2.3 validator rejects a 2.4 document (`scope` is an unexpected property). `openpulse attest` emits 2.4.0, and prints the same scope as one line (`searched owner/repo main@<commit>: ...`), as does `check --github-repo`.

**Upgrading a consumer:** validate against `schemas/evidence-contract/v2.4/schema.json`. Treat a null `scope` as "no repository searched", never as "everything searched".

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
security-correlation stream the same way check does. `--trust` also
checks each PyPI and npm dependency once per run (live lookups, at most
4 per dependency and 2000 per run) and records the result in every
contract's `trust_assurance`; `--private-names` names the private-name
list (default `.openpulse/private-packages.txt` when present).
