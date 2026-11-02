# Implementation plan — v0.7 → v0.10 (2026-10-28)

The living build plan. It sequences the 2026-10-21 security review (finding matrix in `docs/ARCHITECTURE_REVIEW.md`), the distribution work since, and the open issues against `docs/ROADMAP.md`. Every item names its conceptual layer (1–10) where one applies, its finding ID or issue, a size (S ≈ a day, M ≈ 2–4 days, L ≈ a week or more) and who should build it.

Status words: DONE, ACTIVE, NEXT, LATER, BLOCKED (waiting on a decision).

## Where we are (verified against `main` @ `a461bc9`, 2026-10-28)

- **Update 2026-11-02 (v0.15 released):** v0.15.0 "Pre-Install Gates" is released (Phase 9, Z1–Z4: #295–#298). T-E2's exit is met: the policy that fails CI also fails a commit and a pre-install CI step, with no model involved, and the pre-install bypass routes are tested and documented. Track T Phase 4 (T-E1, T-E2) is complete. Still open: the PyPI popular-name list (decision 9). Next in track T: Phase 2's T-C reputation indicators (need labelled data).
- **Update 2026-11-02 (v0.15 plan):** v0.15.0 "Pre-Install Gates" is Phase 9 below: track T Phase 4's T-E2, the trust policy enforced where dependencies enter (a pre-commit hook on dependency files, and a CI step before `pip install` or `npm ci`), through one new `openpulse gate` command. Started on the owner's "continue building next steps" (2026-11-02); scope open to change.
- **Update 2026-11-02 (v0.14 released):** v0.14.0 "Enforced Trust" is released (Phase 8, Y1–Y6: #287–#292). T-E1's exit is met: prohibited conditions fail CI with no model involved, and the bypass tests pass with the uncovered routes documented. Two pull-request bypasses found by Y5 were fixed. Still open: the PyPI popular-name list (decision 9). Next in track T: T-E2 pre-installation controls (P2) and Phase 2's T-C reputation indicators (need labelled data).
- **Update 2026-11-02 (v0.14 plan, owner-approved):** v0.14.0 "Enforced Trust" is Phase 8 below: track T Phase 4's T-E1 (a policy file evaluated without any model, the Action on pull requests, trust in SARIF), preceded by a measurement harness whose false-positive results the owner accepted as Phase 4's prerequisite, and the scheduled removal of the deprecated v0.12 fields.
- **Update 2026-11-02 (v0.13 released):** v0.13.0 "Agent Trust Evidence" is released (Phase 7, X1–X6: #279–#284). Track T Phase 3's exit is met: agent answers carry the trust block and contract 2.2.0 is published beside 2.1. Still open: the PyPI popular-name list (decision 9). Next in track T: Phase 2 (T-C, needs a measured false-positive rate) and Phase 4 (T-E1 enforcement).
- **Update 2026-11-02 (v0.13 plan, owner-approved):** v0.13.0 "Agent Trust Evidence" is Phase 7 below: track T Phase 3 (the `trust` block for agents, the T-F2 contract block, M8 recording) with three checks that hold or fail rather than score: known-malicious records, dependency confusion against the user's own list, and repository linkage.
- **Update 2026-11-02 (v0.12 released):** v0.12.0 "Trusted Inputs" is released (Phase 6, U1–U5: #260–#264, #272–#276). The Action part of U5 moved to T-E1. Still open: the PyPI popular-name list for lookalike indicators (an owner-run BigQuery query, or another approved source).
- **Update 2026-11-01 (v0.12 plan):** v0.12.0 "Trusted Inputs" is Phase 6 below: track T Phase 1 (untrusted-text fixes, digest integrity, PyPI provenance, lookalike indicators, trust checks on added dependencies).
- **Update 2026-11-01 (v0.11 released):** v0.11.0 "Early Warning Operations" is released (Phase 5, W1–W5), together with track T's first milestone T-M1 (#257).
- **Update 2026-11-01 (v0.11 plan):** v0.11.0 "Early Warning Operations" is Phase 5 below: persistent alert delivery (C1), a severity gate on `warnings`, signed webhooks, MCP hardening (C5), and track T Phase 0 (design only).
- **Update 2026-11-01 (later):** v0.10.0 "Verified Releases & Safe Gates" is released (Phase 3). The owner decided that product development continues alongside track R rather than waiting for the paper submission (`docs/ROADMAP.md`), so Phase 5 (M6 operations) is no longer paused.
- **Update 2026-11-01:** v0.9.0 "Anchored Trust" is released (Phase 2, all exit criteria met). v0.10.0 is rescoped from M6 operations, which `docs/ROADMAP.md` pauses until after R-D, to "Verified Releases & Safe Gates" (Phase 3 below), approved by the owner on 2026-11-01. The bullets below are the 2026-10-28 snapshot.
- **Released:** v0.7.0 "Channels" (2026-10-28): wheel data packaging (#132), the release-line verdict fix (#133, **changes verdicts**), `openpulse mcp`, DefectDojo export and Dependency-Track upload (#134–#137), `python -I -m cli` (#146, #150), the CycloneDX serial fix (#147), shared GitHub auth options (#149) and the install name `ikarus-openpulse` (#154). The Action is not on the Marketplace yet (R4).
- **Next patch, v0.7.1:** collector response caps (#155, H11) and hash-locked installs everywhere (#156, H12).
- **Phase A** (correctness and leak fixes) is done, including A6b.
- **Phases B–D:** none of Phase B is started. Phase C has only the Action (C3). Phase D has only the serial fix (part of D4).
- **Contributor PRs waiting on changes:**
  - #148 (Tejas5405): it claims `Fixes #103` but changes no behaviour;
  - #151 (SatriaBagusNurhadianto): its collision error is swallowed by one caller and crashes another.
- **Distribution blocker found in this review:** the PyPI name `openpulse` belongs to an unrelated project, OpenQASM's "Reference OpenPulse AST". Our README and `docs/MCP.md` say `pip install "openpulse[mcp]"`, which installs *that* package. See Phase 0.

## Rules for every phase

The standing roadmap principles apply. In practice, for each PR:

- **Shape.** One finding per PR. Each PR description covers the threat, the fix, a test that fails without the fix, and whether any golden flipped, with justification for the flip.
- **Dependencies and tests.** No new runtime dependencies without explicit sign-off. All tests stay offline. Every CI addition carries a `# Threat:` comment.
- **Unknown stays unknown.** A parse failure, a skip or partial coverage never becomes "no dependencies" or `NOT_AFFECTED`.
- **Schema and contract changes are additive only.** A new minor version goes in a sibling schema directory, and the previous one stays untouched.
- **Test where users hit it.** Entry points are tested the way users run them: from outside the checkout, through the CLI or MCP, not only by calling the inner function. #146 and #151 both shipped green suites over real bugs.
- **Ask before** changing public verdict semantics, bumping the contract major version, renaming packages or distributions, or publishing anywhere.

## Sequencing

```text
Phase 0 (release + distribution)  ──►  v0.7.0 release
        │
        ├──► Phase 1 (hardening, mostly contributors)  ── runs alongside everything below
        │
        ├──► Phase 2 (Anchored Trust, v0.9.0)
        │        B1 ─► B2 ─► B3* ─► B4 ─► B5        (* key-management design approved first)
        │        B6, B7 independent
        │
        ├──► Phase 3 (Verified Releases & Safe Gates, v0.10.0; rescoped 2026-11-01)
        │        V1 (= D2) ─► tag v0.10.0 through it;  V2, V4, V5 any time
        │        V3 after the contract 2.1.0 sign-off
        │
        ├──► Phase 4 (release supply chain)
        │        D1 any time;  D2 is V1;  D6 needs D2 + the name
        │
        └──► Phase 5 (Early Warning Operations, v0.11.0; M6 un-paused 2026-11-01)
                 C1 after B3 (done);  C2 moved to V4;  C4 superseded by the R-B1 harness
```

## Phase 0 — Release and distribution (now, before any new feature)

The work on `main` reaches users only through a release, and the documented install command installs someone else's package. Fix both first.

| # | Item | Size | Who | Status |
|---|---|---|---|---|
| R1 | **Install docs fix (urgent).** Replace `pip install "openpulse[mcp]"` in README and `docs/MCP.md` with a pinned git install, `pip install "ikarus-openpulse[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v0.7.0"`, until a PyPI name exists. Add a test that greps the docs for a bare `pip install openpulse`. | S | maintainer | DONE (#154) |
| R2 | **Distribution name decision.** Choose an available PyPI name, e.g. `openpulse-intel` or `ikarus-openpulse`, keeping the `openpulse` CLI command. Reserve it on PyPI with a placeholder through Trusted Publishing only. | S | **owner** | DECIDED 2026-10-28: `ikarus-openpulse` (CLI command stays `openpulse`; later import namespace `ikarus_openpulse`). The rename ships in the v0.7.0 release PR; reserving it on PyPI happens with D2's first Trusted Publishing upload |
| R3 | **Release v0.7.0 "Channels".** Version bump, CHANGELOG `Unreleased` → `0.7.0`, tag, GitHub release. The release notes must lead with #133's verdict change, because gates may start failing. Minor (not patch) because of that semantic change and the three new commands. | S | maintainer | DONE: tagged and released 2026-10-28 |
| R4 | **Publish the Action to the Marketplace** from the v0.7.0 tag (the description is already under the limit). | S | **owner** | NEXT |
| R5 | **Triage:** close #79 (GitHub repo input shipped in v0.6.0); rescope #78 to "delivery state + dedup" (C1); confirm Dependabot closed #130 after #131; follow up on #148 and #151, or take them over if the contributors go quiet. | S | maintainer | DONE 2026-10-28 (#148 and #151 await their contributors) |
| R6 | **Record or retire v0.6.0 item "C" (finding F5).** It's named in the #100 commit and documented nowhere. | S | **owner** | DONE: retired 2026-10-28 (scope unknown, nothing depends on it) |

**Exit:** v0.7.0 is tagged and released; the docs install OpenPulse and not the quantum-pulse package; the Action is on the Marketplace; the issue list matches the code.

## Phase 1 — Hardening (v0.7.x patches, mostly good first issues)

Each item has an issue with acceptance criteria, so it can go to contributors. Maintainers review and merge, applying the "test where users hit it" rule.

| # | Item | Issue | Size | Who |
|---|---|---|---|---|
| H1 | `check --fail-on` must fail on FAILED repository coverage | #101 | S | contributor |
| H2 | Digest/warnings show non-COMPLETE coverage in the body (and the webhook) | #102 | S | contributor |
| H3 | Per-file blob cap below the total budget (25 MB), so one file can't use the whole budget | #103, #148 | S | contributor (#148) |
| H4 | CI guard also catches `--deselect`, `-k "not …"`, `collect_ignore`, `addopts` | #104 | S | contributor |
| H5 | Token file: first non-empty line, validate the token, reuse `bounded_io` | #138 | S | contributor |
| H6 | Token file: warn when other users can read it | #139 | S | contributor |
| H7 | `persist-credentials: false` on the `test` and `codeql` checkouts, plus a policy test | #141 | S | contributor |
| H8 | `scan_secrets`: canonical self-skip, skip virtualenvs, decide on `*.lock` | #142 | S | contributor |
| H9 | Catalog collisions fail loudly **at every caller** (resolver and trust) | #144, #151 | S | contributor (#151) |
| H10 | Standalone evidence-contract consumer (no OpenPulse imports) | #108 | M | contributor |
| H11 | **A6b:** stream every collector's HTTP response with a byte cap; rework the tests that mock `httpx.get` | — | M | DONE (#155, v0.7.1) |
| H12 | **D1:** hash-pinned locks (`--require-hashes`), `--no-deps -e .`, and `check_lock.py` failing on unlocked installs | #110 | M | DONE (#156, v0.7.1) |
| H13 | **D3 (rest):** ruff `S` rules with justified per-line ignores | — | S | maintainer |

**Exit:** all of the above merged, then a v0.7.1 patch release. A6b closes the last unbounded input channel.

## Phase 2 — v0.9.0 "Anchored Trust" (layers 2 and 6) — DONE, released 2026-11-01

Goal: authority, independence and history integrity are derived from verifiable facts or keyed secrets, never from strings the caller supplies. ROADMAP M1 says not to expand without a concrete requirement. The concrete requirement here is that lead time, the headline metric, rests on this history.

| # | Item | Finding | Size | Depends on |
|---|---|---|---|---|
| B1 | Derived source authority (detail below) — DONE (#224; `Literal` step deferred) | M1 | M | — |
| B2 | Derived independence: source family from the registrable domain when `family` is absent — DONE (#227) | M2 | S | B1 (shared domain helper) |
| B3 | Keyed integrity (detail below) — design APPROVED 2026-11-01 (`docs/KEYED_INTEGRITY.md`); B3a (key, MACs, keyed states) DONE (#229); B3b rotation DONE (#230); B3c keyed adoption and lead-time clamp DONE (#231; sweep first detections keyed-only since 2026-11-01); B3d rescoped to CI documentation (the Action runs `attest`, which keeps no history, so an Action key input would do nothing) | H2, L1 | L | **owner-approved key-management design** |
| B4 | Rollback and downgrade detection (detail below) — DONE (#233) | H2 | M | B3 |
| B5 | DONE (#234) — `openpulse anchor`: signed checkpoint of all tips plus a Merkle root of the ledger, stored as a git commit or CI artifact; `verify` compares against the last anchor | H2 | M | B3, B4 |
| B6 | Clock trust (detail below) — DONE (#223) | L7 | S | — |
| B7 | Evidence contract v2.0 (JCS hash; detail below) — DONE (#236; #109 `NOT_APPLICABLE` coverage left for its own decision) | L8 | M | — |

**B1 detail:**
- Add `official_domains` per project in `canonical_projects.yaml`, starting with the projects that have curated official events today (`bitnami`, `bitnami-spark`, `django`, `itext`). More only with owner sign-off.
- `Source.authority` becomes a fail-closed `Literal`.
- A source counts as `official` only when its URL is https and the host is on the allowlist, either as an exact match or a dot-boundary subdomain.
- Anything else is downgraded, and the reason is recorded on the event.
- Tests: lookalike hosts (`evil-redis.io`, `redis.io.evil.com`), `http://`, punycode hosts. A forged `official` can't reach CONFIRMED.

**B3 detail (design first):**
- HMAC-SHA256 over chain fields and ledger entries, with a key held outside `.openpulse/`.
- **Decision needed before code:** where the key lives (environment variable, OS keyring, CI secret), how it's rotated, and what happens to histories created before the key.
- Verification states: VALID_KEYED, VALID_UNKEYED, BROKEN, UNKNOWN.
- `first_detected_at` is added to the chained fields.
- Only VALID_KEYED history backs a published lead time.

**B4 detail:**
- Once a chained record exists, a missing tip means ROLLBACK_SUSPECTED.
- Chained-to-legacy downgrades are refused.
- Re-baselining requires `--rebaseline --reason`, and the reason is recorded.

**B6 detail:**
- Reject ledger stamps earlier than the entry's creation, or too far from UTC wall-clock time.
- Remove the naive `datetime.now()` fallback in `core/observations/store.py`.

**B7 detail:**
- The content hash is computed over RFC 8785 (JCS) canonical JSON, in `schemas/evidence-contract/v2/`. Renumbered 2026-10-30: a change to hash computation is breaking under the contract's versioning policy, so it is 2.0.0, not 1.2. Contract 1.2.0 shipped the additive verdict-meaning fields (ROADMAP R-B6).
- Ship a documented Node or Go verification snippet.
- The v1.0 and v1.1 schemas stay untouched.
- Signature fields stay null.
- Pairs naturally with #109 (`NOT_APPLICABLE` coverage for non-repository inputs).

**Exit:**
- Without the key, an edited record whose hashes were recomputed is not VALID_KEYED.
- Deleting the tip plus the newest records is reported as rollback.
- A forged `official` can't reach CONFIRMED.
- Same-domain sources can't reach CORROBORATED.
- Reports cite lead times from keyed-valid detections only.
- README, METHODOLOGY and ROADMAP move from "corruption-detecting" to "tamper-evident (keyed)" only once all of the above hold.

All exit criteria hold as of v0.9.0 (2026-11-01), and the wording has moved.

## Phase 3 — v0.10.0 "Verified Releases & Safe Gates" (rescoped 2026-11-01) — DONE, released 2026-11-01

Goal: a release anyone can verify back to its commit, lock and SBOM, and no CI gate that passes on an input OpenPulse did not fully read. Why this and not M6: `docs/ROADMAP.md` pauses M6 until after R-D, and track R needs a verifiable tagged release for its reproducibility package (R-D2). Nothing here changes the frozen evaluation.

| # | Item | Finding / issue | Size | Depends on |
|---|---|---|---|---|
| V1 | DONE (#241) — Tag-triggered release workflow (= D2): build sdist and wheel from the tag, fail when the tag differs from `openpulse --version`, regenerate the deterministic SBOM, attach all three to the GitHub release, and add build-provenance attestations (`actions/attest-build-provenance`, SHA-pinned, least-privilege per job). PyPI publishing only after decision 7 | #111 | M | — |
| V2 | DONE (#240) — `check --fail-on` fails when repository coverage is FAILED, as `--strict` already does | #101 | S | — |
| V3 | DONE (#248, #249) — `NOT_APPLICABLE` inspection coverage for inputs with no repository scan (evidence contract 2.1.0, sibling schema), and `digest` / `warnings` show non-COMPLETE coverage in the body | #109, #102 | M | decision 8 |
| V4 | DNS-pinned webhook transport (= C2; detail under Phase 5) | M5 | M | — · DONE (#242) |
| V5 | DONE (#243–#247) — Hardening good first issues: CI guard for `--deselect` and friends, token-file handling and permissions, `persist-credentials: false`, secret-scan skips | #104, #138, #139, #141, #142 | S each | — |

**Exit:**
- `v0.10.0` is tagged through V1, and `gh attestation verify` passes on its wheel.
- No `--fail-on` or `--strict` run exits 0 on FAILED repository coverage.
- A contract never says COMPLETE for an input that had no repository scan.
- A rebinding resolver can't steer webhook delivery to a private address.

**Not in v0.10.0:** C1 persistent delivery state (#78) and C5 MCP hardening (M6, paused); C4 `bench` (superseded by the R-B1 harness); D6 namespace move (its own release); more lockfile readers (#153, contributors any time); track T code (waits for its Phase 0).

## Phase 5 — v0.11.0 "Early Warning Operations" (layers 7 and 8) — DONE, released 2026-11-01

Goal: scheduled alerts an operator can leave running. An alert is delivered once, a failed delivery is retried and never lost silently, a receiver can check that a payload came from OpenPulse, and a CI job can gate on deadlines. M6 is un-paused (`docs/ROADMAP.md`, amendment 2026-11-01). Nothing here changes a verdict or the frozen evaluation.

| # | Item | From | Size | Depends on |
|---|---|---|---|---|
| W1 | DONE (#252) — Persistent alert delivery state for `check --webhook` (= C1, detail below) | #78, C1 | M | B3 (done) |
| W2 | DONE (#253) — `warnings --fail-on {overdue,critical,high,medium,low}`: exit 1 when a deadline at or above the severity is in the window | #78 | S | — |
| W3 | DONE (#254) — Signed webhook payloads: HMAC-SHA256 over timestamp and body with a secret from the environment or a file, sent as headers a receiver can verify; replay window documented | #78 | S | W1 |
| W4 | DONE (#255) — MCP hardening (= C5): per-session lookup budget and timeout surfaced to the agent; `project_lifecycle` cached across sessions with the same TTL rules | C5 | S | — |
| W5 | DONE (#256; approved by the owner 2026-11-01, `docs/research/TRACK_T_PHASE0.md`) — Track T Phase 0, docs only: re-verified threat-model references, registry API and attestation feasibility with dates, reference-list sources and licences, design notes for T-F1 and T-F3 | ROADMAP track T | M | — |

**Exit:**
- A scheduled `check --webhook` run never sends the same alert twice, retries a failed delivery on the next run, and dead-letters it after the attempt limit.
- `warnings --fail-on critical` fails a CI job on a CRITICAL or OVERDUE deadline and passes otherwise.
- A receiver can verify a payload's signature and reject a replay outside the window.
- An MCP agent is told when its lookup budget is spent instead of getting a silent partial answer.
- Track T Phase 0's exit criteria in `docs/ROADMAP.md` are met.

**Not in v0.11.0:** C4 `bench` (superseded by the R-B1 harness); PagerDuty/Teams-specific payload formats and hosted dashboards (M6 hosted surfaces, later); more readers (#153, contributors any time); track T code (follows its Phase 0).

Earlier item list (kept for the IDs used above):

| # | Item | Finding / issue | Size | Depends on |
|---|---|---|---|---|
| C1 | Persistent delivery state (detail below) — v0.11.0 W1 | #78 | M | B3 (alerts cite keyed-valid detections) |
| C2 | DNS-pinned webhook transport (detail below) — moved to v0.10.0 as V4, DONE (#242) | M5 | M | — |
| C3 | GitHub Action | — | — | DONE (v0.6.2/v0.6.3). Remaining: its gate counts only keyed-valid evidence once B3 ships |
| C4 | SUPERSEDED by the R-B1 evaluation harness — `openpulse bench`: per-scenario expected vs actual verdicts, identity/applicability precision and recall, as a reproducibility JSON uploaded by CI (numbers are not marketed) | M4 | M | — |
| C5 | v0.11.0 W4 — MCP hardening: per-session lookup budget and timeout surfaced to the agent; `project_lifecycle` cached across sessions with the same TTL rules | — | S | — |

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

**Exit:**
- A scheduled `check --webhook` run never sends the same alert twice and retries failed deliveries with a dead-letter record.
- A rebinding resolver can't steer delivery to a private address.
- `bench` publishes a reproducibility JSON from CI.

## Phase 6 — v0.12.0 "Trusted Inputs" (track T Phase 1; planned 2026-11-01) — DONE, released 2026-11-02

Goal: track T Phase 1's exit from `docs/ROADMAP.md`, "PyPI and npm answers carry existence, digest and provenance statuses; no verdict changes", built on the owner-approved Phase 0 note (`docs/research/TRACK_T_PHASE0.md`, section 8). Every new field uses the T-F1 vocabulary and the T-F3 rule. Nothing here changes a verdict, a contract or the frozen evaluation.

| # | Item | Track T | Size | Depends on |
|---|---|---|---|---|
| U1 | Untrusted-text fixes A–E from the Phase 0 audit, one PR each: A MCP inputs validated against ecosystem grammars; B event scope strings bounded when events are built; C `safe_message` strips control and bidi characters; D OSV ids validated before URLs; E repository `full_name` validated | T-F3 | S each | — |
| U2 | Digest integrity: lockfile hashes (`poetry.lock`, `package-lock.json` `integrity`, pip `--hash`) compared with registry digests; a mismatch is VERIFIED_FAILURE | T-B4 | M | T-M1 |
| U3 | PyPI provenance: PEP 740 attestations from the Integrity API, verified with `pypi-attestations` in a new optional, hash-locked `[provenance]` extra (approved 2026-11-01); without the extra, NOT_PERFORMED | T-B1 | M | U2 |
| U4 | Lookalike indicators against pinned, separately licensed name snapshots (PyPI BigQuery CC BY 4.0, npm-high-impact MIT) and UTS #39 v18.0.0 confusables; SUSPICIOUS_INCONCLUSIVE, never a verdict | T-A2 | M | U1 |
| U5 | Trust checks in file checks on added dependencies only (`check_dependency_file` against a base, and the Action on pull requests), within the W4 budget | T-A1, T-D | M | U2 |

**Exit:**
- `dependency_status` answers for PyPI and npm carry existence, digest and (PyPI) provenance records.
- No caller or upstream string reaches an agent-facing field outside a labelled, capped field (injection fixtures pass).
- No verdict changes (tested by running each check against agreeing and disagreeing stub registries).

**U5 scope (2026-11-02):** `check_dependency_file(base_path=...)` (MCP) and `openpulse trust --base` (CLI). The Action part moves to T-E1: a pull-request job has no base file without a deeper checkout and `git show`, and gating on trust statuses is T-E1's job by design.

**Not in v0.12.0:** T-B2 npm provenance (sigstore-python cannot verify npm bundles yet, Phase 0 section 2); T-C reputation indicators (Phase 2); the T-F2 contract block (Phase 3).

## Phase 7 — v0.13.0 "Agent Trust Evidence" (track T Phase 3; approved 2026-11-02) — DONE, released 2026-11-02

Goal: track T Phase 3's exit from `docs/ROADMAP.md`, "agent answers carry the trust block; the contract minor is published beside the previous one", plus the Phase 2 checks that need no false-positive study because each one holds or fails against a cited source. Every record uses T-F1 and T-F3. No verdict changes.

| # | Item | Track T | Size | Depends on |
|---|---|---|---|---|
| X1 | Known-malicious records: OSV `MAL-` entries for any PyPI or npm name (not only catalogued ones). CONFIRMED_MALICIOUS only with the cited record; otherwise MISSING_EVIDENCE, never "safe". Within the W4 budget | T-F1 | M | — |
| X2 | Dependency confusion: the user lists private names; OpenPulse reports which exist publicly (reuses T-A1). Nothing is inferred about unlisted names | T-A3 | S | — |
| X3 | Repository linkage: does the repository named in registry metadata name the package back, or does verified provenance bind the artifact to it (starjacking, T4) | T-A4 | M | — |
| X4 | One `trust` block in `dependency_status` gathering the T-A, T-B and X1–X3 records; optional caller-supplied `selection_context`, recorded verbatim, labelled agent-supplied and never used in a status. The separate v0.12 fields stay one minor release, marked deprecated | T-D | S–M | X1–X3 |
| X5 | Evidence contract 2.2.0: an additive `trust_assurance` block in a sibling schema directory, emitted by `openpulse attest`; hash rule unchanged, 2.1 untouched | T-F2 | M | X4 |
| X6 | `openpulse mcp --record DIR`: opt-in, local-only JSONL of questions and answers, the data source for RQ1 and RQ4 | M8 | S–M | — |

**Exit:**
- `dependency_status` answers carry one `trust` block with every T-F1 record, and `attest` emits contract 2.2.0 that validates beside 2.1.
- CONFIRMED_MALICIOUS appears only with a cited record (tested with stub OSV answers).
- No verdict changes (tested).

**Not in v0.13.0:** T-C reputation indicators (Phase 2 needs a measured false-positive rate first); T-E1 policy enforcement and the Action's pull-request trust step (Phase 4, after those results); T-B2 npm provenance (no verifier yet); the PyPI popular-name list (owner decision 9).

## Phase 8 — v0.14.0 "Enforced Trust" (track T Phase 4, T-E1; approved 2026-11-02) — DONE, released 2026-11-02

Goal: track T Phase 4's exit from `docs/ROADMAP.md`, "prohibited conditions block in CI without any model involved; bypass tests pass", for T-E1. Phase 4 depends on "the false-positive results of the evaluation": the owner approved (2026-11-02, decision 11) that Y1's measurements on synthetic and organic sets meet that dependency for T-E1, with the separately registered study (RQ1–RQ5) still to come. Fail closed only for conditions the user's policy prohibits; nothing new blocks without a policy.

| # | Item | Track T | Size | Depends on |
|---|---|---|---|---|
| Y1 | Measurement harness (offline, synthetic, evaluation-plan categories 1–5 and 7, each also degraded): a stub registry world, detection, false-positive and unresolved rates per check and status, and an organic control (leave-one-out lookalike over the pinned popular-name list). Results in `docs/research/TRACK_T_MEASUREMENTS.md`; a check without a measured false-positive rate is labelled experimental | evaluation plan | M | — |
| Y2 | `.openpulse/policy.yml`: prohibited conditions (confirmed malicious, a failed digest or provenance check, not found in the registry, a user blocklist, provenance required for named packages, a status prohibited for a named scope), evaluated deterministically by `check` and `attest`, extending `--fail-on` | T-E1 | M | Y1 |
| Y3 | The GitHub Action on pull requests: trust checks on dependencies added against the base branch's copy of each file, gated by the policy (deferred from U5) | T-E1 | M | Y2 |
| Y4 | T-F1 statuses in SARIF and DefectDojo: error only when the policy prohibits the condition, otherwise warning or note; no risk score (Phase 0 open question) | T-E1 | S | Y2 |
| Y5 | Bypass tests (evaluation-plan category 8): edited lockfiles, additions outside the gate, an agent ignoring a warning; what the gate catches and what it cannot | T-E1 | S | Y3 |
| Y6 | Remove the deprecated v0.12 top-level `registry_existence`, `provenance` and `lookalike` from `dependency_status` (announced for 0.14.0) | T-D | S | — |

**Exit:**
- A prohibited condition fails `check`, `attest` and the Action with no model involved; with no policy, gates behave as in v0.13.
- Every condition a policy can prohibit has a measured false-positive rate, or is labelled experimental.
- Bypass tests pass, and the routes the gate cannot cover are documented.

**Not in v0.14.0:** T-E2 pre-installation controls (P2); T-C reputation indicators (need star history and labelled data); the registered study itself; the PyPI popular-name list (decision 9).

## Phase 9 — v0.15.0 "Pre-Install Gates" (track T Phase 4, T-E2; planned 2026-11-02) — DONE, released 2026-11-02

Goal: T-E2 from `docs/ROADMAP.md`: the T-E1 trust policy enforced at the existing integration points where dependencies enter, before anything is installed. A registry proxy or firewall stays out of scope.

| # | Item | Track T | Size | Depends on |
|---|---|---|---|---|
| Z1 | `openpulse gate FILE...`: the trust policy on the dependencies added or changed since a git ref (`--base-ref`, read with `git show`) or a base file, with no events needed; exit 0 pass, 1 violation, 2 usage. Built from the T-E1 pieces (policy, trust checks, base comparison, digest changes) | T-E2 | M | v0.14.0 |
| Z2 | Pre-commit hook: `.pre-commit-hooks.yaml` runs `openpulse gate --base-ref HEAD` on staged manifests and lockfiles | T-E2 | S | Z1 |
| Z3 | CI before install: a documented workflow step (`openpulse gate --base-ref origin/main` before `pip install` / `npm ci`), and the Action's dogfood of it | T-E2 | S | Z1 |
| Z4 | Bypass tests for the pre-install routes (`git commit --no-verify`, a lockfile regenerated after the gate, an install from an ungated file), each covered or documented | T-E2 | S | Z2, Z3 |

**Exit:** the same policy that fails CI (T-E1) also fails a commit and a pre-install CI step, with no model involved; the pre-install bypass routes are tested and documented.

**Not in v0.15.0:** a registry proxy or firewall (out of scope by design); T-C reputation indicators (need labelled data); the PyPI popular-name list (decision 9).

## Phase 4 — Release supply chain (alongside Phases 2–3)

| # | Item | Issue | Size | Depends on |
|---|---|---|---|---|
| D2 | (v0.10.0 V1) Tag-triggered release workflow: build the sdist and wheel; publish to PyPI with Trusted Publishing (OIDC) **as `ikarus-openpulse`** (R2); sigstore signatures and SLSA build-provenance attestations; attach the SBOM | #111 | M | R2 |
| D5 (rest) | Legacy flat identity keys respect `confidence` | — | S | H9 |
| D6 | Move the top-level packages (`core`, `cli`, `collectors`, `analyzers`, `reports`) under one namespace with a deprecation shim. **The namespace can't be `openpulse`:** the PyPI `openpulse` package imports as `openpulse`, so both installed together would collide. Use the R2 name: `ikarus_openpulse`. Keep `python -I -m cli` working through the shim for one minor release. | — | L | R2, D2 (ask first) |

**Exit:** `pip install <R2 name>` installs a signed, attested OpenPulse with an SBOM, and no OpenPulse module shadows or is shadowed by another distribution.

## Research track (M2 / M4 / M8 / M9, alongside Phase 3)

These compete for reviewer time, not for the same files:

- A live namespace-move pair for `split_moves` (M2).
- Repository/archive-change detection beyond the archived flag; support-model and license-change candidates (M2).
- An optional AI/ML golden scenario (M4, doubles as the M8 entry point), which `bench` (C4) then measures.
- First external consumer of the evidence contract (M9 design only; builds on H10/#108).
- M8: how coding agents actually use `openpulse mcp`. Record the questions agents ask and the verdicts they get (opt-in, local only) before designing further tools.

## Decisions needed from the owner

| # | Decision | Blocks |
|---|---|---|
| 1 | PyPI distribution name (R2) — **decided: `ikarus-openpulse`** | R1's final wording, D2, D6 |
| 2 | Release as v0.7.0 now — **decided: yes** | R3 |
| 3 | Publish the Action to the Marketplace | R4 |
| 4 | Keep or retire v0.6.0 item "C" / F5 — **decided: retired** | R6 |
| 5 | B3 key management: storage, rotation, pre-key histories — **decided 2026-11-01:** as proposed in `docs/KEYED_INTEGRITY.md` | B3–B5, C1 |
| 6 | Which projects get `official_domains` first | B1 scope |
| 7 | Publish `ikarus-openpulse` to PyPI from the V1 workflow (needs the owner to register a Trusted Publisher on PyPI) — open; until then V1 attaches signed artifacts to the GitHub release only | V1's PyPI step |
| 8 | Evidence contract 2.1.0: `NOT_APPLICABLE` coverage status — **decided 2026-11-01: approved** | V3 |
| 9 | PyPI popular-name list for lookalike indicators: run the dated BigQuery query (CC BY 4.0), or approve another source — open | U4's PyPI reference |
| 10 | v0.13.0 scope, including the additive evidence contract 2.2.0 (`trust_assurance`) — **decided 2026-11-02: approved** | X1–X6 |
| 11 | v0.14.0 scope, and that Y1's synthetic and organic false-positive measurements meet track T Phase 4's "false-positive results" dependency for T-E1 (the registered study still to come) — **decided 2026-11-02: approved** | Y1–Y6 |

## Risks

- **Verdict churn after v0.7.0.** #133 makes end-of-life gates fire on real lockfiles for the first time. Lead the release notes with it, and keep `--fail-on` defaults unchanged.
- **Name squatting.** Until R2 is registered, someone else can take the chosen PyPI name. Reserve it as soon as it's decided.
- **Contributor PRs with green-but-wrong tests** (#146, #151). Apply the "test where users hit it" rule in review, and keep good-first-issue acceptance criteria phrased at the user's level.
- **Phase B touches the trust core.** One finding per PR, goldens re-justified on any flip, and B3 strictly after its design is approved.

## Kickoff prompt for the next session

> Work in the OpenPulse repo. Read `docs/NEXT_PHASES.md`, `docs/ARCHITECTURE_REVIEW.md` (2026-10-21 addendum), `docs/ROADMAP.md` and `CHANGELOG.md`. Do Phase 0 first. R1: replace every `pip install openpulse` in the docs with the pinned git install and add a docs test. R3: prepare the v0.7.0 release PR (version bump, CHANGELOG `Unreleased` → `0.7.0` with #133's verdict change first). R5: the issue triage. Ask me for decisions R2, R4 and R6 before acting on them, and don't publish anything. Then take Phase 1 items H11 (A6b) and H12 (D1) one PR each, under the "Rules for every phase", while reviewing contributor PRs for H1–H10. Don't start Phase 2 until v0.7.0 is released, and propose the B3 key-management design to me before writing B3 code.
