# Implementation plan — v0.7 → v0.10 (2026-10-28)

The living build plan. It sequences the 2026-10-21 security review (finding matrix in `docs/ARCHITECTURE_REVIEW.md`), the distribution work since, and the open issues against `docs/ROADMAP.md`. Every item names its conceptual layer (1–10) where one applies, its finding ID or issue, a size (S ≈ a day, M ≈ 2–4 days, L ≈ a week or more) and who should build it.

Status words: DONE, ACTIVE, NEXT, LATER, BLOCKED (waiting on a decision).

## Where we are (verified against `main` @ `a461bc9`, 2026-10-28)

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
        ├──► Phase 3 (M6 operations, v0.10.0)
        │        C2 any time;  C1 after B3 (alerts cite keyed-valid detections)
        │        C4 (bench) any time
        │
        └──► Phase 4 (release supply chain)
                 D1 any time;  D2 needs the Phase 0 name decision;  D6 needs D2 + the name
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

## Phase 2 — v0.9.0 "Anchored Trust" (layers 2 and 6)

Goal: authority, independence and history integrity are derived from verifiable facts or keyed secrets, never from strings the caller supplies. ROADMAP M1 says not to expand without a concrete requirement. The concrete requirement here is that lead time, the headline metric, rests on this history.

| # | Item | Finding | Size | Depends on |
|---|---|---|---|---|
| B1 | Derived source authority (detail below) — ACTIVE (PR open; `Literal` step deferred) | M1 | M | — |
| B2 | Derived independence: source family from the registrable domain when `family` is absent | M2 | S | B1 (shared domain helper) |
| B3 | Keyed integrity (detail below) — design APPROVED 2026-11-01 (`docs/KEYED_INTEGRITY.md`); B3a (key, MACs, keyed states) DONE (#229); B3b rotation DONE (#230); B3c keyed adoption and lead-time clamp DONE (#231); B3d rescoped to CI documentation (the Action runs `attest`, which keeps no history, so an Action key input would do nothing) | H2, L1 | L | **owner-approved key-management design** |
| B4 | Rollback and downgrade detection (detail below) | H2 | M | B3 |
| B5 | ACTIVE (PR open) — `openpulse anchor`: signed checkpoint of all tips plus a Merkle root of the ledger, stored as a git commit or CI artifact; `verify` compares against the last anchor | H2 | M | B3, B4 |
| B6 | Clock trust (detail below) — DONE (Unreleased, v0.9.0) | L7 | S | — |
| B7 | Evidence contract v2.0 (JCS hash; detail below) | L8 | M | — |

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

## Phase 3 — v0.10.0 M6 operations (layers 7 and 8)

| # | Item | Finding / issue | Size | Depends on |
|---|---|---|---|---|
| C1 | Persistent delivery state (detail below) | #78 | M | B3 (alerts cite keyed-valid detections) |
| C2 | DNS-pinned webhook transport (detail below) | M5 | M | — |
| C3 | GitHub Action | — | — | DONE (v0.6.2/v0.6.3). Remaining: its gate counts only keyed-valid evidence once B3 ships |
| C4 | `openpulse bench`: per-scenario expected vs actual verdicts, identity/applicability precision and recall, as a reproducibility JSON uploaded by CI (numbers are not marketed) | M4 | M | — |
| C5 | MCP hardening: per-session lookup budget and timeout surfaced to the agent; `project_lifecycle` cached across sessions with the same TTL rules | — | S | — |

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

## Phase 4 — Release supply chain (alongside Phases 2–3)

| # | Item | Issue | Size | Depends on |
|---|---|---|---|---|
| D2 | Tag-triggered release workflow: build the sdist and wheel; publish to PyPI with Trusted Publishing (OIDC) **as `ikarus-openpulse`** (R2); sigstore signatures and SLSA build-provenance attestations; attach the SBOM | #111 | M | R2 |
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

## Risks

- **Verdict churn after v0.7.0.** #133 makes end-of-life gates fire on real lockfiles for the first time. Lead the release notes with it, and keep `--fail-on` defaults unchanged.
- **Name squatting.** Until R2 is registered, someone else can take the chosen PyPI name. Reserve it as soon as it's decided.
- **Contributor PRs with green-but-wrong tests** (#146, #151). Apply the "test where users hit it" rule in review, and keep good-first-issue acceptance criteria phrased at the user's level.
- **Phase B touches the trust core.** One finding per PR, goldens re-justified on any flip, and B3 strictly after its design is approved.

## Kickoff prompt for the next session

> Work in the OpenPulse repo. Read `docs/NEXT_PHASES.md`, `docs/ARCHITECTURE_REVIEW.md` (2026-10-21 addendum), `docs/ROADMAP.md` and `CHANGELOG.md`. Do Phase 0 first. R1: replace every `pip install openpulse` in the docs with the pinned git install and add a docs test. R3: prepare the v0.7.0 release PR (version bump, CHANGELOG `Unreleased` → `0.7.0` with #133's verdict change first). R5: the issue triage. Ask me for decisions R2, R4 and R6 before acting on them, and don't publish anything. Then take Phase 1 items H11 (A6b) and H12 (D1) one PR each, under the "Rules for every phase", while reviewing contributor PRs for H1–H10. Don't start Phase 2 until v0.7.0 is released, and propose the B3 key-management design to me before writing B3 code.
