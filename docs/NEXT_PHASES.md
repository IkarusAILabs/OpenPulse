# Implementation plan — v0.7 → v0.10 (2026-10-28)

The living build plan. It sequences the 2026-10-21 security review (finding matrix in `docs/ARCHITECTURE_REVIEW.md`), the distribution work since, and the open issues against `docs/ROADMAP.md`. Every item names its conceptual layer (1–10) where one applies, its finding ID or issue, a size (S ≈ a day, M ≈ 2–4 days, L ≈ a week or more) and who should build it.

Status words: DONE, ACTIVE, NEXT, LATER, BLOCKED (waiting on a decision).

## Where we are (verified against `main` @ `a461bc9`, 2026-10-28)

- **Update 2026-11-08 (v0.20 plan, owner-approved):** v0.20.0 "Change Evidence Beyond Lifecycle" is Phase 14 below (decision 19): M2's change classes that the schema names but nothing detects. Build order: C1 repository history, C2 repository changes, C3 per-release licenses, C4 deprecation, C5 evidence rules, C6 verified cases.
- **Update 2026-11-08 (v0.19 released):** v0.19.0 "Evidence Consumer and Portability" is released (Phase 13, P1–P5: #336–#341). The exit holds: a consumer with no OpenPulse code validates every released contract version, 1.0 to 2.4, on documents written by each version's own release. After the release: D5's rest (#344) and H13 (#345) are on `main` under Unreleased, which completes Phase 1. What is left needs the owner: decisions 3, 6, 7, 9, 15, 17 and 18, D6 (ask first), and the scope of any Phase 14.
- **Update 2026-11-07 (v0.18 released):** v0.18.0 "Inspection Coverage Assurance" is released (Phase 12, S2–S5: #331–#334; S1 shipped in v0.16.0). The exit holds: coverage is COMPLETE only when every dependency file in the recorded search was read, anything else is PARTIAL with each category named, and no summary reads as an all-clear over PARTIAL. Decision 15 (`--fail-on` on PARTIAL by default) stays open. Next: Phase 13 (v0.19.0).
- **Update 2026-11-06 (v0.17 built):** G1–G6 are on `main` (#315, #322, #323, #325, #326 and the G6 docs). The exit condition holds: the bypass routes "a file changed after the gate" and "a lockfile regenerated after the gate" are "Yes" in `docs/TRUST_POLICY.md`, pinned by `tests/test_gate_bypass.py` and run end to end in `tests/test_e2e_install.py`. Still not covered, and documented: an install from a file the gate was not given, a lockfile the install command itself rewrites, a receipt written by hand, a skipped verification. v0.17.0 released 2026-11-06. Next: Phase 12 (v0.18.0).
- **Update 2026-11-03 (track T research):** the owner asked an AI assistant to take on the star-history indicators and track T's study. Started as "Track T research" below: TR1 (star-history recorder) and TR2 (draft protocol) are done. GitHub's stargazer listings and GraphQL `starredAt` are closed to third parties (verified 2026-11-03), so star history comes from the counts-only star-history endpoint. Labels come from StarScout and OSV, never from an AI. Decisions 17 and 18 are new. R-C stays with an independent team.
- **Update 2026-11-03 (v0.17 plan, owner-approved):** the owner asked to plan and start the next versions (2026-11-03). Decisions 13, 14 and 16 are approved, so v0.17.0 "Gate-to-Install Integrity" (Phase 11) is ACTIVE and v0.18.0 and v0.19.0 follow in that order. Build order for v0.17: G1 receipts, G3 digests in the gate, G2 verification, G4 generated files, G5 end-to-end install tests, G6 docs. Decision 15's scope is approved; whether `--fail-on` fails on PARTIAL coverage by default stays open until S4 is built. Writing G1's tests found a gate crash on `main` since v0.15.0 (a private-name list passed as loaded names where a path was expected), fixed separately as a v0.16.1 candidate.
- **Update 2026-11-03 (v0.16 released):** v0.16.0 "Reputation Evidence" is released (Phase 10, Q1–Q6: #301–#307, #311). T-C's indicators that need no star history ship measured, or experimental where the organic set could not measure them (`young_popular_repository`), and none is a verdict. Q6's adversarial cases found and fixed one over-strong status (npm trusted publishing read as publisher continuity). Also in the release: the security review fixes (#306) and Phase 12's S1 defect fix (#310). Next: decisions 13–16 (v0.17–v0.19 scopes).
- **Update 2026-11-02 (v0.16 plan, owner-approved):** v0.16.0 "Reputation Evidence" is Phase 10 below: track T Phase 2's T-C, the transparent reputation indicators that need no star history (a publisher change, a moved repository, a young repository claiming popularity), each measured on recorded organic projects before it ships. It needs evidence contract 2.3.0 for the new check names. Approved by the owner 2026-11-02 (decision 12).
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

| # | Item | Issue | Size | Status |
|---|---|---|---|---|
| H1 | `check --fail-on` must fail on FAILED repository coverage | #101 | S | DONE (#240) |
| H2 | Digest/warnings show non-COMPLETE coverage in the body (and the webhook) | #102 | S | DONE (#249) |
| H3 | Per-file blob cap below the total budget (25 MB), so one file can't use the whole budget | #103, #148 | S | DONE (#220; #148 closed) |
| H4 | CI guard also catches `--deselect`, `-k "not …"`, `collect_ignore`, `addopts` | #104 | S | DONE (#244) |
| H5 | Token file: first non-empty line, validate the token, reuse `bounded_io` | #138 | S | DONE (#245) |
| H6 | Token file: warn when other users can read it | #139 | S | DONE (#246) |
| H7 | `persist-credentials: false` on the `test` and `codeql` checkouts, plus a policy test | #141 | S | DONE (#243) |
| H8 | `scan_secrets`: canonical self-skip, skip virtualenvs, decide on `*.lock` | #142 | S | DONE (#247) |
| H9 | Catalog collisions fail loudly **at every caller** (resolver and trust) | #144, #151 | S | DONE (#219; #151 closed) |
| H10 | Standalone evidence-contract consumer (no OpenPulse imports) | #108 | M | DONE (v0.19.0 P1–P5, #336–#341) |
| H11 | **A6b:** stream every collector's HTTP response with a byte cap; rework the tests that mock `httpx.get` | — | M | DONE (#155, v0.7.1) |
| H12 | **D1:** hash-pinned locks (`--require-hashes`), `--no-deps -e .`, and `check_lock.py` failing on unlocked installs | #110 | M | DONE (#156, v0.7.1) |
| H13 | **D3 (rest):** ruff `S` rules with justified per-line ignores (done: 4 asserts became explicit checks, two `urlopen` clients refuse non-https URLs, every other finding carries its reason on the line; tests exempt from S101/S105/S106/S603/S607 only) | — | S | DONE (#345) |

**Exit:** all of the above merged, then a v0.7.1 patch release. A6b closes the last unbounded input channel. **Met 2026-11-08:** every row is done; H13 (#345) was the last.

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

## Phase 10 — v0.16.0 "Reputation Evidence" (track T Phase 2, T-C; approved 2026-11-02) — DONE, released 2026-11-03

Goal: T-C from `docs/ROADMAP.md`, limited to the indicators that need no star history. Each indicator has a written rule, its inputs and its source. Indicators are reported one by one and never summed into a score. None is a verdict or changes one, and the absence of an indicator is never evidence of authenticity. Each ships with a firing rate measured on recorded organic projects, or is labelled experimental. Builds on T-B1 provenance, T-A4 repository linkage and the v0.14 measurement harness (`benchmarks/trust.py`).

| # | Item | Track T | Size | Depends on |
|---|---|---|---|---|
| Q1 | Organic reputation fixtures, measured first: a recorded, dated set of real popular PyPI and npm packages (registry metadata for recent releases, verified provenance where published, GitHub repository metadata), a recorder script, and offline replay. `benchmarks/trust.py` reports each new indicator's firing rate on it before the indicator ships | T-C | M | v0.15.0 |
| Q2 | `publisher_change` (threat T6): a release published by someone the package's earlier releases were not. PyPI: the verified provenance publisher (repository, workflow) differs from the previous attested release's, or attestations stop after attested releases. npm: the version's publishing account (`_npmUser`) published no earlier version. `SUSPICIOUS_INCONCLUSIVE`, naming both publishers; handovers are legitimate, so never a verdict | T-C, T-B | M | Q1 |
| Q3 | `repository_moved`: the claimed repository answers under another name (a GitHub transfer or rename redirect). `SUSPICIOUS_INCONCLUSIVE`, naming the old and new names. Reuses the linkage check and the collector's redirect handling | T-C | S | Q1 |
| Q4 | `young_popular_repository` (threat T5): a repository younger than a set age with a star count above a set threshold. Experimental unless Q1 measures it; star counts are inputs, never trust evidence | T-C | S | Q1 |
| Q5 | Wiring: the `trust` block, evidence contract 2.3.0 (additive: the three check names; 2.2 published unchanged beside it), trust-policy conditions (scoped indicators that must name packages; experimental where Q1 measured no organic rate), SARIF and DefectDojo, MCP docs | T-D, T-F2, T-E1 | M | Q2–Q4 |
| Q6 | Echo and degraded-run tests: hostile publisher and repository names are never echoed (T-F3); an unreachable source is `NOT_PERFORMED`; adversarial identity cases (a claimed repository that is a GitHub page, a claim of someone else's popular repository, a transfer to an unrelated owner, a publisher change hidden behind a trusted-publishing switch) each get the status their rule defines and no stronger; the measurements document is regenerated | T-C | S | Q5 |

**Exit:** each indicator is documented with its rule, inputs, source and a measured organic firing rate (or an experimental label). None changes a verdict, and prohibiting one requires named packages. Track T Phase 2's exit ("each indicator is documented, with a measured false-positive rate on the organic fixture set") is met for these three.

**Acceptance, restated (advisory review 2026-11-02):** each indicator has an explicit meaning and source (its module docstring, `docs/MCP.md` and `docs/EVIDENCE_CONTRACT.md` 2.3.0); none reaches a status stronger than `SUSPICIOUS_INCONCLUSIVE` or establishes trust (`young_popular_repository` never verifies anything); organic false-positive rates are measured (Q1–Q4); verdict semantics are unchanged (trust checks are never verdict inputs, tested).

**Not in v0.16.0:** star-history bursts and stars inconsistent with downloads or dependents (GitHub's API budget makes them on-demand only, and they need labelled data; LATER); any statistical or ML detection (needs the evaluation plan's labelled data); a registry proxy; the PyPI popular-name list (decision 9).

## Phase 11 — v0.17.0 "Gate-to-Install Integrity" (track T Phase 4, T-E2; approved 2026-11-03) — DONE, released 2026-11-06

Goal: prove that what `openpulse gate` checked is what gets installed. Today the gate judges files as they are when it runs and records nothing about them. A file changed between the gate and the install step, or a lockfile regenerated after the gate, is installed unchecked: `docs/TRUST_POLICY.md` lists both routes as not covered. In-place lockfile hash edits are caught only when the policy prohibits `digest_mismatch`.

| # | Item | Track T | Size | Depends on |
|---|---|---|---|---|
| G1 | ✅ **Gate receipt.** `openpulse gate --receipt PATH` writes what was gated: the SHA-256 of each input file, the policy and the private-name list, their paths, the base ref or base files, the OpenPulse version, the decision, and every violation and unchecked check. Fixed shape, documented, never upstream text (T-F3) | T-E2 | M | v0.16.0 |
| G2 | ✅ **Verify before install** (done: `--verify-receipt`, the Action's `receipts` output; tests in `tests/test_gate_verify.py`). `openpulse gate --verify-receipt PATH FILE...` re-hashes the files about to be installed and exits 1 if any differs from the receipt, is missing from it, or the receipt is not a passing one. The Action's `gate` input writes the receipt, and a documented step verifies it immediately before `pip install` / `npm ci`. Changed means reinspect: run the gate again | T-E2 | M | G1 |
| G3 | ✅ **Lockfile digests always checked by the gate** (done: `trust_policy.with_gate_implied`; bypass tests in `tests/test_gate_bypass.py`). For every lockfile entry the change adds or whose locked digests changed, the gate compares the digests with the registry whatever the policy says, and a mismatch fails the gate (`digest_mismatch` becomes implied in `gate`; `check` and `attest` keep needing it in the policy). Needs decision 14 | T-B4, T-E2 | S | v0.16.0 |
| G4 | ✅ **Generated dependency files** (done: `--require-receipt-for`; the generate-then-gate order in `docs/TRUST_POLICY.md`). A lockfile the build regenerates (`poetry lock`, `npm install`, `uv lock`) after the gate fails G2's verification. Document the generate-then-gate order, and add a `gate` mode for the CI step after generation (`--require-receipt-for` named files) so a regenerated file cannot reach install without passing the gate | T-E2 | S | G2 |
| G5 | ✅ **Adversarial end-to-end CI tests** (done: `tests/test_e2e_install.py`). In CI, offline, against a local hash-pinned wheel index: a clean change is gated and installs; a lockfile swapped after the gate is refused by G2; an in-place hash edit is refused by G3; a regenerated lockfile is refused until gated again; `pip install --require-hashes` installs exactly the gated digests. Both the accepted and the rejected installs are asserted | T-E2 | M | G1–G4 |
| G6 | ✅ Docs (done: the CI order, receipt limits and bypass rows in `docs/TRUST_POLICY.md`, `docs/GITHUB_ACTION.md`, README): the bypass table in `docs/TRUST_POLICY.md` and `docs/GITHUB_ACTION.md` updated with what is now covered, and what still is not (an install from outside the gated files) | T-E2 | S | G5 |

**Exit:** every install a gated pipeline performs is either of the exact bytes the gate passed, with the receipt to show it, or refused. The bypass routes "a file changed after the gate" and "a lockfile regenerated after the gate" move from "No" to "Yes" in `docs/TRUST_POLICY.md`.

**Not in v0.17.0:** signing receipts (they are integrity records within one pipeline run; a signed, portable receipt waits for the contract signature work); intercepting installers (a pip or npm plugin); a registry proxy.

## Phase 12 — v0.18.0 "Inspection Coverage Assurance" (M5/M6; approved 2026-11-03; the `--fail-on` default in decision 15 still open) — DONE, released 2026-11-07

Goal: repository-wide coverage that never overstates itself. `--github-repo` reports COMPLETE, PARTIAL or FAILED, but discovery recognises only exact file names: a repository whose dependencies are in `requirements-dev.txt`, `yarn.lock`, `pnpm-lock.yaml`, `uv.lock`, `Pipfile.lock` or a bare `package.json` is not told about them, and can be reported COMPLETE. That breaks the standing rule "unknown stays unknown" (Rules for every phase), so S1 is a defect fix and can ship earlier as a patch.

| # | Item | Layer | Size | Depends on |
|---|---|---|---|---|
| S1 | ✅ **No silent omissions (defect; fixed on `main`, unreleased).** A recognised dependency file OpenPulse cannot read (`yarn.lock`, `pnpm-lock.yaml`, `uv.lock`, `Pipfile`, `Pipfile.lock`, `package.json` without a lockfile, `bun.lockb`, `gradle.lockfile`, `environment.yml`, `setup.py`, `setup.cfg`) is listed with the reason "dependency file not supported", and makes coverage PARTIAL | M5 | S | — |
| S2 | ✅ **Requirements variants read** (done: `core/github_reader.py`, with `-r`/`-c` includes accounted for; tests in `tests/test_github_reader.py`). `requirements-*.txt`, `requirements/*.txt` and `constraints*.txt` go through the existing requirements parser, matching the pre-commit hook's pattern | M5 | S | S1 |
| S3 | ✅ **Discovery scope recorded** (done: `RepoInspection.scope`, evidence contract 2.4.0, one line in `check` and `attest`; tests in `tests/test_discovery_scope.py`). Coverage states what was searched: the ref and commit, the file-name patterns, the directories skipped (`node_modules`, `vendor`, ...) with counts, and the caps that applied. Additive in the evidence contract (a 2.4.0 minor) | M5 | M | S1 |
| S4 | ✅ **No unjustified all-clear** (done: `core/coverage.py` categories in every summary, SARIF `inspection_coverage_categories`; decision 15 still open). Every summary that can read as clear (`check`, `digest`, `warnings`, the job summary, SARIF, webhooks) states PARTIAL coverage and names the uninspected categories (unsupported files, capped files, truncated tree, fetch errors). Whether `--fail-on` should also fail on PARTIAL by default is decision 15 (today it needs `--fail-on-partial`) | M6 | M | S3 |
| S5 | ✅ **Monorepos and nested workspaces** (done: `packages/` searched, npm workspace members covered by their lockfile, Cargo virtual manifests read; tests in `tests/test_monorepos.py`). Tests and fixes for npm/pnpm workspaces, Cargo workspaces, Poetry and uv projects in subdirectories, Go multi-module repositories and Maven multi-module builds: every member is found or listed as uninspected | M5 | M | S1, S2 |

**Exit:** a repository's coverage is COMPLETE only when every dependency file in it was read; anything else is PARTIAL with each uninspected file and category named, and no output reads as all-clear over a PARTIAL run.

## Phase 13 — v0.19.0 "Evidence Consumer and Portability" (M9 preparation, T-F2; approved 2026-11-03) — DONE, released 2026-11-08

Goal: show that an evidence contract means the same thing outside OpenPulse. `conformance/evidence-contract/verify.mjs` already recomputes the content hash with no OpenPulse code, but it accepts any `2.x` version string, does not validate the schema, and says nothing about the document's outcomes.

| # | Item | Size | Depends on |
|---|---|---|---|
| P1 | ✅ **Standalone consumer** (done: `conformance/consumer/`, `requirements.lock` from `scripts/compile_locks.py`, the `consumer` CI job). `conformance/consumer/`: a small Python package with no OpenPulse imports (one pinned, hash-locked dependency: `jsonschema`), tested in CI from outside the checkout | M | — |
| P2 | ✅ **Exact versions** (done: consumer version, provenance and format rules; `verify.mjs` `VERSIONS`). Accepts only versions with a published schema and validates against exactly that schema; rejects unknown versions (`2.9.0`), a `provenance.contract_version` that differs from the top level, and unknown fields where the schema is closed. `verify.mjs` rejects unknown versions too | S | P1 |
| P3 | ✅ **Hash verification** (done: `openpulse_consumer.hashes`, 1.x per-version fields, own JCS; 1.0 verification fixed in OpenPulse) for 1.x and 2.x documents, matching `verify.mjs` | S | P1 |
| P4 | ✅ **Outcomes preserved** (done: `openpulse_consumer.summary`, `openpulse-consumer summary [--json]`, open items per document, no pass field). The consumer's summary keeps NOT_AFFECTED, RELATED and UNKNOWN apart, keeps `inspection_coverage` and `trust_assurance` statuses (MISSING_EVIDENCE and NOT_PERFORMED included), and never folds a negative or incomplete outcome into "pass". Tested with documents built to tempt that mistake | S | P1 |
| P5 | ✅ **Released-contract corpus** (done: 24 documents and 61 negatives; 1.0 from the untagged commit `d68f533`, 1.1 from v0.6.1, 1.2 from v0.8.0, 2.4 from v0.18.0; `regenerate.py --check` in the `consumer` CI job). `conformance/contracts/<version>/`: documents produced by each released contract version (2.0 from v0.9.0, 2.1 from v0.10.0, 2.2 from v0.13.0, 2.3 from v0.16.0, and the 1.x builder), regenerated by a script from the release tags, plus mutated negatives. CI runs the consumer over all of them | M | P1–P4 |

**Exit:** a third party can validate, verify and read any released OpenPulse contract without OpenPulse, and gets the same outcomes OpenPulse reported, including every unknown.

## Phase 14 — v0.20.0 "Change Evidence Beyond Lifecycle" (M2; approved 2026-11-08) — DONE, released 2026-11-09

Goal: detect the upstream changes the schema already names but nothing produces. `LICENSE_CHANGE` and `DEPRECATION` have no detector; repository facts (archived, moved, license) were judged from the current snapshot only, so a license *change* could not be seen, and only container registries kept a verifiable history. M2's rule applies: formalisation and verification, not more mechanisms.

| # | Item | Size | Depends on |
|---|---|---|---|
| C1 | ✅ **Repository observation history** (done: `core/observations/repository.py`, `openpulse observe-github`). GitHub repository facts (the queried path and the path GitHub answers with, `archived`, GitHub's license id, the last push, the default branch, and `missing` for a 404) kept as a hash-chained history beside the registry histories (`github.com/<owner>/<name>/`), with the same lock, tip pointer, ROLLBACK/DOWNGRADE/BROKEN refusals, reasoned re-baseline, history-key MACs and anchor coverage. Any failure other than a 404 records nothing | M | — |
| C2 | ✅ **Repository changes become findings** (done: `diff_repository_observations`, `analyze_repository_changes`, `observe-github` and `report --with-sweep`; unarchived, a 404 and lost license evidence are changes, not findings; the history finding replaces the snapshot's restatement in a report): `LICENSE_CHANGE` (from one license id to another), archived, unarchived and moved to a new owner, each with the time it was first observed. "No license detected" or `NOASSERTION` is lost evidence, never a relicense. The snapshot rules stay for repositories with no history | M | C1 |
| C3 | ✅ **License changes between releases** (done: `core/release_license.py`, `openpulse release-license`, `report --with-sweep` for catalog packages, changes published in the last 365 days; releases ordered by version, PyPI's two spellings never a change): npm and PyPI record a license per release, so a change between two releases is verifiable today, without waiting for history to build up. Reuses the existing registry fetchers and their host allowlist | M | — |
| C4 | ✅ **Deprecated and withdrawn packages** (done: `core/registry_deprecation.py`, `openpulse deprecation`, `report --with-sweep` for catalog packages' package-level flags; npm read through version documents, so very large packages are still checked): npm `deprecated`, PyPI yanked releases (PEP 592) and the "Development Status :: 7 - Inactive" classifier become `DEPRECATION` findings. npm and PyPI only | M | — |
| C5 | ✅ **Evidence rules** (done: each C2–C4 finding carries `confidence` and `evidence_basis`; `corroborate_repository_license` asks the registry only when GitHub reports a license change; `finding_lead_time` is lifecycle-only): a difference OpenPulse observed is moderate evidence (EMERGING); a flag the publisher set on the registry is the publisher's own statement; GitHub's license detection is a heuristic and needs the registry's license to agree before it is corroborated. First detection is recorded; lead time stays defined for lifecycle events only | S | C2–C4 |
| C6 | ✅ **Verified cases before support is claimed** (done: Cases 11–16 in `docs/DISCOVERIES.md` replay recorded registry responses; `VERIFIED_CASES` and each finding's `support`; repository history ships experimental): each new class needs at least one replayable, verified case in `docs/DISCOVERIES.md`; until then it ships as experimental | S | C2–C5 |

No contract version change: `LICENSE_CHANGE` and `DEPRECATION` are already in every contract schema's vocabulary. Not in v0.20.0: `MAINTAINER_CHANGE` (npm maintainer lists are noisy; v0.16's publisher-change indicator covers the risky case), `MAJOR_RELEASE` (a release, not a risk), a live firing for `split_moves` (cannot be forced), and new lockfile ecosystems (#153, #343).

**Exit:** a license change, an archive or ownership transition and a package deprecation are each reported from verifiable evidence, with the time OpenPulse first saw it and an evidence strength that says how it was seen; each class has a verified case or is labelled experimental.

## Phase 15 — v0.21.0 "Your Dependencies, Watched" (M6; approved 2026-11-09) — ACTIVE

Goal: the v0.20.0 checks reach the dependencies people actually use, and a scheduled run remembers what it saw. Two gaps after v0.20.0: deprecation and license-change detection ran only on catalog packages (`report --with-sweep`), never on a project's own lockfile, the Action, the gate or the agent tools; and repository history needs repeated observations, but the Action kept nothing between runs, so even a weekly schedule could not see a change. This closes M6's remaining "scheduling and CI/PR integration".

| # | Item | Size | Depends on |
|---|---|---|---|
| W1 | ✅ **Your dependencies get the v0.20 checks** (done: `check`/`attest --registry-changes`, the Action's `registry-changes` input, the agent tools with live lookups; `analyzers/registry_events.py` builds each event for one dependency): deprecations and yanks for the version you use and license changes after it, as `REVIEW` results in the output, contracts, SARIF and the digest. Advisory: they fail a run only under an explicit `--fail-on review` or `affected` | M | — |
| W2 | ✅ **The Action keeps history between runs** (done: inputs `history`, `history-key`, `history-previous-keys`, `history-id`; `openpulse history-audit`; saved only from the default branch after a passed audit). An opt-in `history` input restores and saves the observation history and the detection ledger through the Actions cache, keyed by a history key from a secret. A tampered, rolled-back or foreign cache is refused, never adopted silently | M | — |
| W3 | ✅ **The Action observes your GitHub repositories** (done: `check`/`attest --observe-repositories`, the Action's `observe-repositories` input; `core/dependency_repositories.py`; a first observation reports what a repository already is, by the snapshot rules). For each repository your dependencies link to, a scheduled run records license, archive and owner changes in the W2 history | M | W2 |
| W4 | **Only what is new.** A scheduled run reports changes first seen since the previous run, with the time OpenPulse first saw each, from the existing detection ledger | S | W2 |
| W5 | **Delivery from the Action.** New findings in the job summary, and optionally a signed webhook (existing) or one updated issue | S | W4 |
| W6 | **Docs and an end-to-end test.** A weekly-watch example in `docs/GITHUB_ACTION.md`; two scheduled runs over recorded responses, where the second reports the change exactly once | S | W1–W5 |

No contract version change is planned: evidence contract 2.4.0 already carries every field. If an item needs a new field it is an additive 2.5.0, raised in that item's PR first. Not in v0.21.0: new lockfile ecosystems (#153, with contributor PR #343), contract v2 signatures (#80), the `--fail-on` PARTIAL default (decision 15), the namespace move D6 (ask first), and forcing a live repository change (one cannot be forced; W2 and W3 make one likely to be seen).

**Exit:** a deprecated, yanked or relicensed dependency in a project's own files is reported from verifiable registry evidence, and a weekly scheduled run of the Action reports a repository or registry change once, when it is first seen, with the history it was seen in.

## Track T research — star-history indicators and the track T study (author-run, AI-assisted; started 2026-11-03) — ACTIVE

Goal: the two track T items that needed data or a study, done by an AI assistant where that is sound (owner, 2026-11-03). Independence is not claimed: labels come from published third-party records, thresholds are frozen on organic data before any positive is read, and the protocol is registered by a named author before the run. R-C (track R's held-out evaluation) stays with an independent human team; AI only prepares it.

| # | Item | Size | Depends on | Status |
|---|---|---|---|---|
| TR1 | **Star-history recorder.** `benchmarks/record_star_history.py`: weekly star counts from GitHub's star-history endpoint (the stargazer listings are closed to third parties since 2026), for the organic set (committed) and a fixed-seed sample of StarScout's flagged repositories (local only) | S | — | DONE (this change) |
| TR2 | **Study protocol.** `docs/research/TRACK_T_STUDY_PROTOCOL.md`: questions, hypotheses, data, calibration and freezing, metrics, stopping rule, ethics. Part A (measurement) now; Part B (agents, enforcement) registered separately | S | — | DRAFT (this change) |
| TR3 | **Young organic set.** `benchmarks/record_young_set.py`: GitHub repositories created in the last 12 months with ≥ 50 stars, kept only when the PyPI or npm package of the same name claims them back, with no OSV malicious record and no StarScout flag; 500 recorded (`stars-young-2026-11-03.json`). The StarScout positives are recorded locally too | S | TR1 | DONE |
| TR4 | **Calibration.** `benchmarks/track_t_study.py calibrate`: both organic sets split 50/50 by name; SH1–SH3 thresholds from the 300 eligible calibration repositories (SH1 0.7956, SH2 0.9921, SH3 2581; 3 of 300 above each), written into the protocol and `star-calibration-2026-11-03.json` | S | TR1, TR3 | DONE |
| TR5 | **Registration** of Part A by the responsible author (decision 17), and the freeze tag. Steps in `docs/research/TRACK_T_REGISTRATION.md`; `track_t_study.py package` builds the archive (protocol, code, inputs, SHA-256 manifest) and refuses until the protocol is filled, the tree is clean and the commit is tagged | — | TR4 | NEXT (owner) |
| TR6 | **The run:** positives, held-out organic, OSV-malicious packages; results in `docs/research/` with every bias of §4 reported. **Ready before registration:** `track_t_study.py run` (H-A1, H-A2, H-B1, Q-B metadata, Q-C provenance; Wilson and Newcombe intervals; aggregates only), tested end to end on synthetic files and refusing to run until the protocol is archived; Q-B's frame pinned (`malicious-frame-2026-11-03.json`: samples from 222,726 npm and 11,953 PyPI OSV `MAL-` names) | M | TR5 | code ready; run after TR5 |
| TR7 | **Ship or drop** each SH indicator from the measured rates: a `star_burst` trust check (experimental or indicator), or a recorded negative result | M | TR6 | after TR6 |
| TR8 | **R-C package for an external team:** packets, codebook and a one-command run, so the independent evaluation costs a team as little as possible. No AI labels count as R-C labels | M | — | LATER |

**Exit:** each star-history indicator is either shipped with rates measured under a registered protocol, or dropped with the negative result published; and the track T study's Part A results are published with their limits.

## Phase 4 — Release supply chain (alongside Phases 2–3)

| # | Item | Issue | Size | Depends on |
|---|---|---|---|---|
| D2 | (v0.10.0 V1) Tag-triggered release workflow: build the sdist and wheel; publish to PyPI with Trusted Publishing (OIDC) **as `ikarus-openpulse`** (R2); sigstore signatures and SLSA build-provenance attestations; attach the SBOM | #111 | M | R2 |
| D5 (rest) | ✅ Legacy flat identity keys respect `confidence` (done: VERIFIED only with `confidence: high`; the shipped catalog uses none) | — | S | H9 |
| D6 | Move the top-level packages (`core`, `cli`, `collectors`, `analyzers`, `reports`) under one namespace with a deprecation shim. **The namespace can't be `openpulse`:** the PyPI `openpulse` package imports as `openpulse`, so both installed together would collide. Use the R2 name: `ikarus_openpulse`. Keep `python -I -m cli` working through the shim for one minor release. | — | L | R2, D2 (ask first) |

**Exit:** `pip install <R2 name>` installs a signed, attested OpenPulse with an SBOM, and no OpenPulse module shadows or is shadowed by another distribution.

## Research track (M2 / M4 / M8 / M9, alongside Phase 3)

These compete for reviewer time, not for the same files:

- A live namespace-move pair for `split_moves` (M2).
- Repository/archive-change detection beyond the archived flag; support-model and license-change candidates (M2).
- An optional AI/ML golden scenario (M4, doubles as the M8 entry point), which `bench` (C4) then measures.
- First external consumer of the evidence contract (M9 design only; builds on H10/#108).
- M8: how coding agents actually use `openpulse mcp`. Record the questions agents ask and the verdicts they get (opt-in, local only) before designing further tools.

**R-C runs in parallel with every product phase, and is the critical dependency for any empirical claim** (advisory review 2026-11-02, agreeing with `docs/ROADMAP.md` R-C). No document claims that OpenPulse is more accurate than an alternative until the independent evaluation is complete. The external team, the archived protocol, held-out cases, independent labels and the baseline comparison come before adding more internally curated examples: a larger internal set does not substitute for any of them.

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
| 12 | v0.16.0 scope (Phase 10), including the additive evidence contract 2.3.0 for the three new check names — **decided 2026-11-02: approved** | Q1–Q6 |
| 13 | v0.17.0 scope (Phase 11): gate receipts and verification before install — **decided 2026-11-03: approved** | G1–G6 |
| 14 | `openpulse gate` checks changed lockfile digests whatever the policy says (G3), so a hash edit cannot pass a policy that forgot `digest_mismatch` — **decided 2026-11-03: approved** | G3 |
| 15 | v0.18.0 scope (Phase 12), including evidence contract 2.4.0 for the recorded discovery scope, and whether `--fail-on` fails on PARTIAL coverage by default (a gate-semantics change) — **scope approved 2026-11-03**; the `--fail-on` default stays open until S4. S1 shipped in v0.16.0 | S1–S5 |
| 16 | v0.19.0 scope (Phase 13), including the consumer's one runtime dependency (`jsonschema`) — **decided 2026-11-03: approved** | P1–P5 |
| 17 | Approve the track T study protocol (Part A) and register it under your name on OSF or Zenodo before the held-out data is read; an AI cannot be the accountable author — open | TR5 |
| 18 | Use StarScout's flagged-repository lists as fake-star labels, kept local (git-ignored) and published only as aggregates, as its authors ask — open | TR1's positives, TR6 |
| 19 | v0.20.0 scope (Phase 14): change evidence beyond lifecycle (repository history, license changes, deprecation), no contract version change — **decided 2026-11-08: approved** | C1–C6 |
| 20 | v0.21.0 scope (Phase 15): the v0.20 checks for a project's own dependencies, Action history between runs, scheduled repository observation, new-only reporting and delivery; no contract version change planned — **decided 2026-11-09: approved** | W1–W6 |

## Risks

- **Verdict churn after v0.7.0.** #133 makes end-of-life gates fire on real lockfiles for the first time. Lead the release notes with it, and keep `--fail-on` defaults unchanged.
- **Name squatting.** Until R2 is registered, someone else can take the chosen PyPI name. Reserve it as soon as it's decided.
- **Contributor PRs with green-but-wrong tests** (#146, #151). Apply the "test where users hit it" rule in review, and keep good-first-issue acceptance criteria phrased at the user's level.
- **Phase B touches the trust core.** One finding per PR, goldens re-justified on any flip, and B3 strictly after its design is approved.

## Kickoff prompt for the next session

> Work in the OpenPulse repo. Read `docs/NEXT_PHASES.md`, `docs/ARCHITECTURE_REVIEW.md` (2026-10-21 addendum), `docs/ROADMAP.md` and `CHANGELOG.md`. Do Phase 0 first. R1: replace every `pip install openpulse` in the docs with the pinned git install and add a docs test. R3: prepare the v0.7.0 release PR (version bump, CHANGELOG `Unreleased` → `0.7.0` with #133's verdict change first). R5: the issue triage. Ask me for decisions R2, R4 and R6 before acting on them, and don't publish anything. Then take Phase 1 items H11 (A6b) and H12 (D1) one PR each, under the "Rules for every phase", while reviewing contributor PRs for H1–H10. Don't start Phase 2 until v0.7.0 is released, and propose the B3 key-management design to me before writing B3 code.
