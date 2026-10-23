# Next Phases — v0.6.1 → v0.7.0 development plan (2026-10-21)

Source: the 2026-10-21 security architecture review (finding matrix in `docs/ARCHITECTURE_REVIEW.md`). The plan sequences that review against `docs/ROADMAP.md`. Each item names its conceptual layer (1–10) and finding ID. Status words: DONE, ACTIVE, NEXT, LATER.

## Where we are

- `main` @ `b82aaf0` (2026-10-21): Phase A merged (#112, #113, #115–#120); intelligence schema 0.5.0, evidence contract v1.1. 747 offline tests; CI green on Linux and Windows.
- Release: v0.6.1 is prepared in `CHANGELOG.md`. The last tagged release is v0.5.0: v0.6.0 was never tagged, so v0.6.1 ships both lines.
- Phase A leftovers: A6b (collector response caps) and A9 (tag and publish the release).
- Still open from v0.6.0: item **C** (finding F5) is referenced in the #100 commit (workstreams A, B, D) but documented nowhere. Either record what it was and add it to this plan, or mark it deferred.

## Rules for every phase

The standing roadmap principles apply. In practice, for each PR:

- **Shape.** One finding per PR. Each PR description covers the threat, the fix, a test that fails without the fix, and whether any golden flipped, with justification for the flip.
- **Dependencies and tests.** No new runtime dependencies without explicit sign-off. All tests stay offline. Every CI addition carries a `# Threat:` comment.
- **Unknown stays unknown.** A parse failure, a skip or partial coverage never becomes "no dependencies" or `NOT_AFFECTED`.
- **Schema and contract changes are additive only.** A new minor version goes in a sibling schema directory, and the previous one stays untouched.
- **Ask before** changing public verdict semantics, bumping the contract major version, or renaming packages.

## Phase A — v0.6.1 "Correctness & leak fixes" (patch, no schema change)

| # | Item | Layer | Finding | Status |
|---|---|---|---|---|
| A1 | Namespaced pom.xml; DOCTYPE refused; depth/element caps | 8 | H1 | DONE #112 |
| A2 | Registry ports kept out of image identity | 3 | M3 | DONE #113 |
| A3 | Webhook errors report status + host only (see detail below) | 7 | M4, L6 | DONE #115 |
| A4 | Lock correctness: OS advisory locks (see detail below) | 1, 6 | M6 | DONE #116 |
| A5 | GitHub-discovered SBOM/SPDX go through `load_sbom_doc`/`load_spdx_doc` with a size check | 8 | M7 | DONE #117 |
| A6 | Bounded input handling (see detail below) | 8 | L1, L2, L4 | DONE #118 (file reads) |
| A6b | Stream collector HTTP responses with a byte cap (all seven collectors; their tests mock `httpx.get` and need reworking) | 1 | L4 | NEXT |
| A7 | Strict charset validation for GitHub owner/repo and Docker namespace/repo; reject `.`, `..`, `?`, `#` | 1, 8 | L5 | DONE #119 |
| A8 | `SECURITY.md`: disclosure via GitHub private vulnerability reporting (enabled), supported versions, scope | — | — | DONE #120 |
| A9 | Release v0.6.1: version bump in `pyproject.toml` and `core/version.py`, `CHANGELOG.md`, tag + GitHub release | — | — | ACTIVE (bump + changelog done; tag after merge) |

**A3 detail:**
- Webhook delivery errors report the status code and host only; the URL path is never printed.
- `redact()` covers `Bearer <token>`, `ghp_`/`gho_`/`github_pat_` tokens, and the paths of known webhook hosts.
- Add `OPENPULSE_WEBHOOK_URL` and `GITHUB_TOKEN` environment-variable inputs as an alternative to argv.

**A4 detail (as shipped):**
- `fcntl.flock` / `msvcrt.locking` on a persistent lock file; the OS releases it when the holder dies, so there is no stale-reclaim heuristic.
- A first revision with owner tokens and rename-based reclaim double-acquired on the Linux CI runner; plain lock files cannot close that window.
- Busy locks raise TimeoutError at the deadline; the lock file is never unlinked.

**A6 detail:**
- Replace `getsize()` followed by an unbounded read with `read(MAX+1)`.
- Handle `RecursionError` with a clean exit.
- Make the package-lock v1 walk iterative.
- Stream collector bodies with a byte cap (split out as A6b).
- Set `MAX_BLOB_BYTES` no higher than the parser cap.

**Exit criteria:**
- CI is green on both operating systems.
- `demo-bitnami` output is unchanged.
- Goldens are unchanged, or any flip is justified.
- A 404 from a Slack-style webhook never prints the secret path segment.

## Phase B — v0.7.0 "Anchored Trust" (layers 2 and 6)

Goal: authority, independence and history integrity are derived from verifiable facts or keyed secrets, never from strings the caller supplies. ROADMAP M1 says not to expand without a concrete requirement. The concrete requirement here is that lead time, the headline metric, rests on this history.

| # | Item | Finding |
|---|---|---|
| B1 | Derived source authority (see detail below) | M1 |
| B2 | Derived independence: source family comes from the registrable domain when `family` is absent | M2 |
| B3 | Keyed integrity (see detail below) | H2, L1 |
| B4 | Rollback and downgrade detection (see detail below) | H2 |
| B5 | `openpulse anchor`: signed checkpoint of all tips plus a Merkle root of the ledger, stored as a git commit or CI artifact; `verify` compares against the last anchor | H2 |
| B6 | Clock trust (see detail below) | L7 |
| B7 | Evidence contract v1.2 (see detail below) | L8 |

**B1 detail:**
- Add `official_domains` per project in `canonical_projects.yaml`.
- `Source.authority` becomes a fail-closed Literal.
- A source counts as `official` only when its URL is https and the host is on the allowlist, either as an exact match or a dot-boundary subdomain.
- Anything else is downgraded, and the reason is recorded.

**B3 detail:**
- HMAC-SHA256 over chain fields and ledger entries, using a key held outside `.openpulse/`.
- Verification states: VALID_KEYED, VALID_UNKEYED, BROKEN, UNKNOWN.
- `first_detected_at` is added to the chained fields.
- Only VALID_KEYED history backs a published lead time.

**B4 detail:**
- Once a chained record exists, a missing tip means ROLLBACK_SUSPECTED.
- Chained-to-legacy downgrades are refused.
- Re-baselining requires `--rebaseline --reason`, and the reason is recorded.

**B6 detail:**
- Reject ledger stamps earlier than the entry's creation, or too far from UTC wall-clock time.
- Remove the naive `datetime.now()` fallback.

**B7 detail:**
- The content hash is computed over RFC 8785 (JCS) canonical JSON.
- Ship a documented Node or Go verification snippet.
- The v1.1 schema stays untouched.
- Signature fields stay null.

**Exit criteria:**
- Without the key, an edited record whose hashes were recomputed is not VALID_KEYED.
- Deleting the tip plus the newest records is reported as rollback.
- A forged `official` cannot reach CONFIRMED.
- Same-domain sources cannot reach CORROBORATED.
- Reports cite lead times from keyed-valid detections only.
- README, METHODOLOGY and ROADMAP move from "corruption-detecting" to "tamper-evident (keyed)" only once all of the above hold.

## Phase C — v0.7.0 M6 operationalization (layers 7 and 8)

Phase C builds on Phase B: alerts cite keyed-valid detections.

| # | Item | Finding |
|---|---|---|
| C1 | Persistent delivery state (see detail below) | — |
| C2 | DNS-pinned webhook transport (see detail below) | M5 |
| C3 | GitHub Action, `integrations/github-action/` (see detail below) | — |
| C4 | `openpulse bench`: per-scenario expected vs actual verdicts, identity/applicability precision and recall, as a reproducibility JSON uploaded by CI (numbers are not marketed) | — |

**C1 detail:**
- Deterministic alert identity: `sha256(event_id, dependency identity, assessment, contract hash)`.
- Deduplication across runs.
- Retry with backoff, a maximum attempt count, and a dead-letter record.
- Stored in the same atomic, locked JSON store.

**C2 detail:**
- Resolve once and check every address.
- Unwrap IPv4-mapped, 6to4 and NAT64 addresses before checking.
- Connect to the validated IP while keeping SNI and Host on the original name.
- Test with a resolver that changes its answer between calls.

**C3 detail:**
- Runs `check` / `attest` on the PR's manifests, lockfiles and SBOMs, and produces a step summary plus SARIF.
- Fails only on ACTION/CRITICAL causes backed by keyed-valid evidence.
- Non-COMPLETE coverage produces a warning, never a pass.
- Uses least-privilege `permissions:`.
- Status: first cut ACTIVE (action, `attest --sarif/--summary/--fail-on`, CI dogfooding). The gate counts ACTION/CRITICAL causes today; "backed by keyed-valid evidence" is added once B3 ships.

## Phase D — Release supply chain (in parallel with B and C)

| # | Item | Finding |
|---|---|---|
| D1 | Hash-pinned dependency install (see detail below) | L9 |
| D2 | Tag-triggered release workflow (see detail below) | L9 |
| D3 | `persist-credentials: false` on checkouts; ruff `S` rules with justified ignores | L9 |
| D4 | `scan_secrets.py` self-skip limited to its canonical path; a decision recorded on scanning `*.lock`; CycloneDX `serialNumber` as a valid deterministic `urn:uuid` | L11 |
| D5 | Catalog alias-collision test; legacy flat identity keys respect `confidence` | Info |
| D6 | Namespace the top-level packages under `openpulse.*` with a deprecation shim, in one dedicated PR after Phases A–C merge (ask first) | L10 |

**D1 detail:**
- `requirements.lock` carries `--hash` entries.
- CI runs `pip install --require-hashes -r requirements.lock`, then `pip install --no-deps -e .`.
- `check_lock.py` fails on packages that are installed but not locked.

**D2 detail:**
- Triggered by a signed tag.
- Builds the sdist and wheel.
- Publishes to PyPI with Trusted Publishing (OIDC).
- Creates sigstore signatures and SLSA build-provenance attestations.
- Attaches the SBOM to the release.

## Still on the roadmap, outside this plan

These are the M2/M4 research work items from `docs/research/BACKLOG.md`:

- A live namespace-move pair for `split_moves`.
- Repository/archive-change detection beyond the archived flag.
- Support-model and license-change candidates.
- An optional AI/ML golden.
- First external consumer of the evidence contract (M9 design only).

Schedule them alongside Phase C. They compete for the same reviewer time, not the same files.

## Kickoff prompt for the next session

> Work in the OpenPulse repo. Read `docs/NEXT_PHASES.md`, `docs/ARCHITECTURE_REVIEW.md` (2026-10-21 addendum), `docs/ROADMAP.md` and `CHANGELOG.md`. First finish Phase A item A6b: stream every collector's HTTP response with a byte cap, and rework the collector tests that mock `httpx.get`. Then start Phase B with B1 (derived source authority) and B2 (derived independence), one PR each, under the "Rules for every phase". For each item: re-verify the finding against the code, write a test that fails, then fix it, and justify any golden flip in the PR description. Ask me before adding `official_domains` to more than the projects that have curated official events today. Do not start B3 (keyed integrity) until B1 and B2 have merged, and propose the key-management design to me first.
