# Research-readiness audit

**Scope.** Whether OpenPulse, as it stands, can support a peer-reviewed journal article on evidence-aware applicability of upstream changes to dependency references, and what blocks that.

**Status.** Audit of 2026-10-31, branch `pr-148`, commit `ddea292` (`v0.8.0-7-gddea292`, package version 0.8.0). The tracked tree was clean when the audit started. The untracked review files under `papers/tr-2026-01/` belong to the authors and were neither read as evidence nor modified.

**Method.**
- The source of `core/`, `evaluation/`, `conformance/`, `cli/mcp_server.py` and `core/agent_tools.py` was read directly.
- The 3,960-line technical report (`papers/tr-2026-01/main.tex`), its review responses, and the evaluation and conformance reports were read in full and cross-checked against the code and the committed result files.
- The full suite was run before any change: **1,164 passed, 5 skipped** (Python 3.14.6, Windows; CI uses 3.11 on Ubuntu and Windows).

Every finding below cites a file. Each finding is marked **fixed here**, **added here** or **open**.

---

## 1. What already exists (do not rebuild)

The repository is far more mature than a typical research prototype. Most of what a journal evaluation needs already exists, and this audit's main job was to find the gaps between it and a defensible paper.

| Requirement (brief) | Existing artefact | State |
|---|---|---|
| Applicability model with typed scope, completeness and identity | `core/risk/match.py`, `core/risk/check.py`, `core/verdict_meaning.py`; TR §5 (Algorithm 1, Lemmas 1–2, NotAffected contract N1–N5) | Implemented. Seven per-pair relationships summarise to four outcomes: affected, unresolved, cleared, no association. |
| Three outcomes; unresolved never silently cleared | `winning_cause` (`check.py`), `_exclusion` (`match.py`), `verdict_meaning` | Implemented, and regression-tested in `tests/test_false_clear.py` (70 tests before this audit). |
| Independent specification oracle | `conformance/oracle.py`. It imports nothing from `core`; identity is supplied as ground truth. | 6,195-case matrix and a 100,000-case randomised differential (seed 7) are committed. The same team wrote the oracle and the engine (TR §8). |
| Defect re-injection | `conformance/mutation.py` | 22 of 22 mutants caught before this audit. |
| Versioned dataset with provenance | `evaluation/retrospective/`: 27 events, 167 pairs, SHA-256-pinned. Each event has a `SOURCES.md`, and each label cites a dependent's file at a commit. | Frozen 2026-10-30. Labels are **developer-assigned (L1) only**. |
| Baselines | `evaluation/policies.py`: A naive, B conservative, V strong conservative, R OSV/OpenVEX re-encoding; plus four registered ablations of C | Implemented. R is evaluable on the development set only (6 of 12 events encoded). |
| Metrics with explicit denominators | `evaluation/metrics.py`, `evaluation/registration.py` (Clopper–Pearson, event-clustered bootstrap, Holm, TOST) | Implemented. |
| Pre-registered prospective protocol | `evaluation/REGISTRATION.md` | Written but **not run**. It needs independent annotators and the factorial cells L₀, L_K, X_K and T₀, which are not implemented. |
| MCP interface for coding agents | `cli/mcp_server.py`, `core/agent_tools.py`, `docs/MCP.md` | Read-only tools, root-confined file access, closed-vocabulary verdict meaning, and source status in every answer. |
| CI | `.github/workflows/ci.yml`, `retrospective.yml`, `paper.yml` | Unit and conformance gate, CodeQL, pip-audit, secret scan, deterministic SBOM, hash-locked installs. |

## 2. Findings

Priority classes follow the brief:
- **P0:** blocks reliable results or creates a misleading verdict.
- **P1:** essential for a credible evaluation.
- **P2:** reproducibility, clarity or adoption.
- **P3:** product work unrelated to the paper's claims.

### P0

**F-01 — D16: untrusted identity mappings drop associations. Fixed here.**
- **The defect.** A heuristic or REVIEW_REQUIRED mapping to another project was read as proof of that other project. Project-wide and package-scoped events on the image path, and release-line events on the package path, then returned "no association" (`UNKNOWN`). The TR requires undetermined (§5.3 tests; Appendix D16, listed as open).
- **Why it is P0.** A summary could show "cleared" over an association it should have kept. This is reachable with the shipped catalogue, for example `docker.io/bitnami/postgresql:16`.
- **Why the oracle missed it.** The oracle and the randomised generator have no untrusted identity.
- **The fix.** It is the one the TR specifies, applied in `_unresolved_identity` (`core/risk/match.py`) and `_scope_cause` (`core/risk/check.py`). Undetermined now holds unless the mapping is curated and VERIFIED.
- **Regression tests.** Six were added to `tests/test_false_clear.py`. Four fail on the old code; the other two are a curated-mapping control and the release-line case, which was already correct.
- **Effect.** No pair of either case set changes (`research/results/*/versions.json`).

**F-02 — No label is independent. Open, external blocker.**
- All 167 retrospective pairs and all 60 development pairs are labelled by the developer (`labelled_by: L1`, `independent_label: false`).
- The two "L2" rounds are an AI-assisted pilot. `round-2/L2-method.md` states that ChatGPT prepared the labels. The repository already reports both rounds as a pilot, not as inter-rater reliability.
- Consequence: every effectiveness number is agreement with the developer's own reading. This cannot be fixed in code. See `LABELING_GUIDE.md` and RESEARCH_PLAN step R4.

**F-03 — Review provenance. Open; needs the authors' decision.**
- `papers/tr-2026-01/review12/REVIEW.txt` carries citation artefacts of an AI tool.
- `main.tex` lines 3–4 hold an unrendered TODO about review provenance and venue AI policy.
- The response files call the reviews "external".
- Before any submission, the manuscript and cover letter must say how the reviews and labels were produced, and the venue's AI policy must be checked. Not doing so would be a research-integrity problem, not a style issue.

### P1

**F-04 — Holm adjustment applied to rounded p-values. Fixed here.**
- `registration.analyse` passed 4-decimal p-values to `holm()`. The smallest bootstrap p, 1/4001 = 0.00025, became 0.0002, and its Holm value became 0.0004 instead of 0.0005.
- That is why `evaluation/retrospective/REPORT.md` (0.0004) and the TR (0.0005) disagree.
- Unrounded p-values now feed Holm (`p_exact`, internal only). A regression test was added to `tests/test_registration.py`.
- REPORT.md is a frozen study report and still says 0.0004. The authors should append an erratum rather than have it silently rewritten.

**F-05 — An empty population was reported as valid. Fixed here.**
- The registered (independent-labels-only) analysis of the retrospective run says `valid: true` with `pairs: 0`.
- It now lists "no pairs in the population" as a validity problem. Test added.

**F-06 — The H1 rule text and code contradicted REGISTRATION.md. Fixed here.**
- REGISTRATION.md restated H1 as absolute (2026-10-31), but `registration.py` still subtracted B's share.
- There is no numeric effect, because B's share is 0 by construction. The code and its printed rule now match the registration. Test added.

**F-07 — The decision invariants were not executable properties. Added here.**
- The NotAffected contract and the dataflow invariant were checked by example tests and by oracle agreement, not as properties that hold on every input.
- **Added:** `conformance/invariants.py`, eight invariants I1–I8 checked on 12,000 seeded cases. Every invariant is exercised (1,025 to 12,928 checks each), with 0 violations.
- **Added:** `tests/test_decision_invariants.py`. Five targeted mutants each disable one safety rule and must be caught by the invariant written for it.
- **Mutation campaign:** D16 joins `conformance/mutation.py`, which now catches **23 of 23**. D16 is caught by the invariants and the regression test only; the matrix and the randomised differential miss it.
- **Still hand-checked:** the "completeness is never derived from a listing" dataflow invariant (TR §5.2). It needs a static or taint check; see RESEARCH_PLAN R7.

**F-08 — Ablations did not isolate the unresolved outcome or curated identity. Added here, post hoc.**
- The registered ablations remove completeness, freshness and identity conservatism.
- None removes the third outcome itself, or the curated identity knowledge.
- Three post-hoc configurations were added (`research/scripts/evaluate.py`, `BASELINES.md` §4). Because they were defined after the registered results were known, they are reported as exploratory.
- They change the attribution of H1 (§3 below).

**F-09 — Intervals were missing for most reported rates. Added here.**
- `evaluation/metrics.py` gives point rates plus a rule-of-three bound.
- `research/scripts/inference.py` adds, for every rate:
  - k/n with its named denominator;
  - an exact interval;
  - an event-clustered bootstrap interval (10,000 resamples, seed 20261031);
  - paired comparisons with C over the same resampled events;
  - an exact event-level sign test, labelled as within-sample.

**F-10 — Existing-format comparison (S3) cannot run as registered. Open.**
- X_K, L₀, L_K and T₀ are not implemented (REGISTRATION.md §2).
- R, the only existing-representation baseline, has no encodings for the retrospective events. On that set R is reported as *not evaluable*, never as 165 abstentions (F-08 of `BASELINES.md`).
- This is the reviewers' most persistent open criticism (RESPONSE_TO_REVIEW_13).

**F-11 — The committed results were not reproduced by CI. Added here.**
- `retrospective.yml` re-runs the study but does not compare with the committed results, and no test reads the retrospective case file.
- **Added:** `research/scripts/reproduce.py --check`, which regenerates every research output and fails on any difference, or when the committed outputs were produced from other source (a source SHA-256 in `research/results/MANIFEST.json`).
- **Added:** a `research` CI job.
- **Verified:** the current tree reproduces the freeze-tag and after-fixes results of A, V and C **pair for pair** on both case sets, offline (`research/tables/*_versions.md`).

**F-12 — Unverified references and a novelty risk. Open.**
- 15 of the TR's 62 bibliography entries were entered from memory without DOIs (`references.bib` around line 554; see `related_notes.md`, which documents the other 47).
- The TR claims that OSV, VEX/OpenVEX, CSAF and CycloneDX have no representation of affected-set completeness.
- SPDX 3.0 relationships carry a `completeness` property, and CycloneDX has `compositions[].aggregate`. Neither is discussed.
- A reviewer will raise this. `paper/LITERATURE_PROTOCOL.md` lists it as the first item to verify.

**F-17 — Agent/MCP answers could carry a verdict without its cause. Fixed here.**
- `core/agent_tools._assess` kept only causes whose event project equals the dependency's resolved slug. As a result, `docker.io/bitnami/redis:7.2` reached the agent as `AFFECTS_ARTIFACT` with no cause and no evidence URL: the affecting event's project is `bitnami`, the image's slug is `bitnami-redis-stack`.
- Seven of the ten dependencies in `tests/test_research_surfaces.py` had a verdict with no supporting cause.
- **The fix.** It keeps the intended noise filter, but shows another project's cause whenever it is affected or unresolved, or is the only support for the headline. Every verdict now arrives with the cause and evidence behind it (I8 on the agent surface). The existing agent and MCP tests pass unchanged.

**F-13 — Cross-surface consistency (invariant 5). Partly added.**
- I5 checks that the evidence contract states the engine's relationship and validates, on every generated case.
- `tests/test_research_surfaces.py` checks that the agent/MCP tool answer, the engine and the contract agree on the curated events.
- The CLI's text output and SARIF are not yet compared on generated cases.

### P2

**F-14 — Stale documents.** Verified mismatches:
- `evaluation/retrospective/DESIGN.md:3` and `SHORTLIST.md:3` still say "for approval".
- ROADMAP R-C0 is both "done" and "awaiting approval" (`docs/ROADMAP.md:80,82`).
- ROADMAP R-B5 quotes superseded rates.
- `conformance/REPORT.md` leads with 3,995 cases and 19 mutants (now 6,195 and 23).
- `docs/research/BACKLOG.md` and `RESEARCH_ALIGNMENT.md` predate the evaluation harness.

These were left for the authors, because each is a judgement about their own frozen records.

**F-15 — Two event taxonomies.**
- The development set uses `lifecycle`, `archival` and `breaking-change`; the retrospective set uses `eol` and others.
- Per-class results do not compare across the two sets.
- PROTOCOL.md says the development set has 13 events. The file has 12; the 13 counts event *combinations* (`metrics.summarise`).

**F-16 — Environment.**
- Locally there is no Node, Go or Java, so baseline V's pinned comparators are absent. The comparators decide no pair of either set, since all three versions agree pair for pair.
- The research pipeline therefore runs V without them deterministically, and records that (`--comparators off`). `--comparators required` remains the registered configuration.
- No TeX toolchain is present locally. The manuscript is built by CI (`paper.yml` pattern).

### P3 (out of scope for the paper)

Dependency-Track and DefectDojo exports, monthly reports, the GitHub Action, the observation store and the sweep. They were not touched.

## 3. What the existing evidence supports — and what it does not

These are retrospective, developer-labelled results (`research/tables/retro_outcomes.md`).

- **Supported, as an observation on this sample.**
  - C made 0 false clears on 103 in-scope pairs. The exact 95% bound is 0.035, pair-level, assuming independence.
  - Naive A made 35 false clears, across 10 of 27 events.
- **Attribution changes with the post-hoc ablations.**
  - C read as a binary tool, with the same engine but anything not affected reported as cleared, makes **26** false clears across 8 events.
  - So most of the reduction relative to A comes from **keeping the unresolved outcome**. Matching and scope semantics account for the rest (35 → 26).
  - The two components fail on different event classes:
    - A's false clears are in deprecation, EOL, licence and relocation;
    - binary C's are in compromised, licence and distribution (`retro_by_class.md`).
  - The per-pair reasons explain binary C's false clears:
    - most are compromised npm packages that OpenPulse cannot identify, because they are not in its catalogue and resolve only to themselves. Name matching gets these right, because there the name *is* the identity;
    - the rest are project ties without a version scope, and references inside registry-wide envelopes.
  - Neither component alone is safe here. Conservative identity costs usefulness exactly where names are reliable.
- **Not supported by these data.**
  - The completeness rule did not prevent a false clear: assuming completeness changes 7 correct negatives and introduces none.
  - Curated identity improves usefulness (16 more correct affected pairs) but changes no safety outcome.
  - Removing identity conservatism produces 17 silent misses (35 with name identity only), and no false clear.
- **Not claimable.**
  - Any population rate. The events were selected under quotas.
  - Statistical significance beyond this sample.
  - Agreement with an independent reading.
  - Any effect on AI coding agents. No agent experiment exists.

## 4. Priorities, complexity and dependencies

| # | Task | Priority | Complexity | Depends on | State |
|---|---|---|---|---|---|
| 1 | Fix D16 with regression tests | P0 | S (two functions) | — | done |
| 2 | Disclose review and label provenance; check venue AI policy | P0 | S (writing), needs the authors | — | open |
| 3 | Independent labels: 2 annotators and an adjudicator, κ before adjudication | P0 | L (people, about 30 h of labelling) | LABELING_GUIDE.md | open |
| 4 | Invariant properties, targeted mutants, D16 mutant | P1 | M | 1 | done |
| 5 | Post-hoc ablations and clustered intervals | P1 | M | — | done |
| 6 | Reproduction check in CI | P1 | M | 4, 5 | done |
| 7 | Holm, validity and H1 reporting fixes | P1 | S | — | done |
| 7a | Agent answers carry the cause behind every verdict (F-17) | P1 | S | — | done |
| 8 | Implement X_K, L₀, L_K, T₀; encode the retrospective events for R/X | P1 | L (encodings must be made by someone blind to the labels) | 3 | open |
| 9 | Verify the 15 references; position against SPDX 3.0 completeness and CycloneDX compositions | P1 | M | — | open |
| 10 | Static check for "completeness never derived from a listing" | P1 | M | — | open |
| 11 | CLI/SARIF consistency on generated cases | P2 | S | 4 | open |
| 12 | Update stale documents; one event taxonomy | P2 | S | — | open (authors) |
| 13 | Prospective held-out study (REGISTRATION.md) | P1 for a strong venue | XL | 3, 8 | open |
| 14 | Agent experiment (FURTHER_STUDIES.md) | P2 for this paper (future work) | L | API budget, a fixed model | open |
