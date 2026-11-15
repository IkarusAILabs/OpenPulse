# Research plan

This plan follows from the audit (`RESEARCH_READINESS_AUDIT.md`). Each step names the research question, threat or reproducibility requirement it serves, says what "done" means, and gives its state.

**Status legend**
- **done** — implemented, tested, and its result recorded in `research/`.
- **open** — not done.
- **blocked** — needs people, data or a decision this repository cannot supply.

## Research question and hypotheses

**RQ.** How can dependency-risk analysis decide whether an upstream change applies to a dependency reference without reading incomplete, ambiguous or insufficient evidence as proof that the reference is unaffected?

| Hypothesis | Measured by | Current evidence | Status |
|---|---|---|---|
| **H1.** An evidence-aware applicability model makes fewer false-clear decisions than a specified naive reading of the same records. | False clears / in-scope pairs, and events with a false clear, against A and the binary reading of C | Retrospective, developer-labelled: C 0/103, A 35/103 (10 of 27 events), binary C 26/103 (8 events) | Observed in a purposive, developer-labelled sample; **not independently evaluated** |
| **H2.** Representing completeness, identity, scope and unresolved outcomes explicitly makes the causes of decision errors observable and reproducible. | Every verdict traceable to rules and evidence (I8); every error categorised and replayable; results reproducible byte for byte | I1–I8 hold on 12,000 cases; 23 of 23 re-injected defects caught; all outputs reproduced; per-pair error tables | Supported as a property of the artefact. It is a design and engineering claim, not an effectiveness claim. |
| **H3.** The approach has measurable costs: unresolved outcomes, identity gaps, review effort. | Unresolved rate, silent misses, curated-identity ablation, by-class tables | C leaves 64/167 unresolved, versus B 97 and V 87. Without curated identity, 16 fewer correct-affected and 20 more unresolved. **Review effort: not measured.** | Partly measured. Review effort is blocked on annotators (W1–W3). |

## Steps

### R1 — Strengthen the applicability model (done)

- **Serves:** a misleading-verdict threat (D16), and H2.
- **Done when:**
  - D16 is fixed as the TR specifies, with regression tests that fail on the old code;
  - the agent surface carries the cause behind every verdict (F-17);
  - the conformance gate is unchanged.
- **Result:**
  - D16 fixed: 6 tests, of which 4 fail on the old code.
  - F-17 fixed: 10 tests, of which 7 fail on the old code.
  - No retrospective or development pair changes.

### R2 — Executable invariants and targeted mutation (done)

- **Serves:** H2, and the brief's §6.4.
- **Done when:**
  - eight invariants run as properties on seeded generated cases, including untrusted identity, which the oracle does not model;
  - every invariant is exercised;
  - each safety rule, disabled alone, is caught by its own invariant, and the run completes (no unrelated failure stands in for a detection);
  - the mutation campaign includes D16 and the invariant detector.
- **Result:**
  - `conformance/invariants.py`: 12,000 cases, 0 violations, 1,025–12,928 checks per invariant.
  - `tests/test_decision_invariants.py`: 5 targeted mutants, each caught by its target.
  - `conformance/results/mutation.json`: 23 of 23 caught, 14 of them by the invariants.

### R3 — Reproducible evaluation package (done)

- **Serves:** the brief's Contribution C/D and Principle 5.
- **Done when one command:**
  - validates the case sets;
  - re-runs the conformance checks against the committed counts;
  - runs every policy;
  - computes intervals;
  - compares implementation versions;
  - builds the tables and figures;
  - writes a manifest tying outputs to a source hash.
- **And:** `--check` reproduces them byte for byte in CI on Linux and Windows.
- **Result:** `research/scripts/reproduce.py`, with 34 outputs identical on regeneration, and the `research` CI job.

### R4 — Independent labels (blocked: people)

- **Serves:** P0 finding F-02, which bears on H1's credibility.
- **Done when:**
  - two annotators who did not build OpenPulse label the 167 retrospective pairs blind to all policy outputs, following `LABELING_GUIDE.md`;
  - Cohen's κ is computed before adjudication;
  - a third person adjudicates;
  - the labels are added as a **new dataset version**, never by overwriting L1;
  - `evaluate.py` reports the registered (independent-only) population with `valid: true`.
- **Estimate:** about 167 pairs × 2 annotators × 5–10 minutes, roughly 30–55 person-hours, plus adjudication.
- **Stand-in done (2026-11-01):** a blinded AI-panel round (`labelling/AI_PANEL_PROTOCOL.md`) and a label-sensitivity analysis (`scripts/label_sensitivity.py`). C's zero false clears and the direction of the comparison with A hold under every label set. R4 itself stays blocked: AI labels do not meet it.

### R5 — Existing-format comparison (open)

- **Serves:** review criticism 4 and audit F-10.
- **Done when:**
  - X_K, L₀, L_K and T₀ are implemented as in REGISTRATION.md §2;
  - an encoder blind to labels and results writes OSV/OpenVEX encodings for the 27 retrospective events, each hash-pinned;
  - S3 runs.
- **Until then:** R is reported as not evaluable on the retrospective set.

### R6 — Literature verification (open)

- **Serves:** novelty claims and Principle 2.
- **Done when:**
  - the 15 unverified references carry verified metadata;
  - SPDX 3.0 relationship completeness and CycloneDX `compositions` are read from their specifications and positioned in the manuscript;
  - the protocol in `paper/LITERATURE_PROTOCOL.md` is executed and logged.

### R7 — Static check for the dataflow invariant (open)

- **Serves:** TR §5.2 ("completeness is never derived from a listing"), which is still hand-checked.
- **Done when:** a test fails whenever code outside the curated-event loader sets `Scope.exhaustive` or `Scope.basis`.

### R8 — Prospective held-out study (blocked: R4, R5, people)

- **Serves:** H1 at a population level (REGISTRATION.md: at least 60 events at risk).
- **Done when:** the protocol is archived (OSF or Zenodo) and run by an independent team.

### R9 — Agent experiment (future work for this paper)

- **Serves:** the brief's Phase Eight.
- `evaluation/FURTHER_STUDIES.md` §4 already designs it. It needs:
  - a fixed model and version;
  - pre-registered tasks and scoring;
  - an injection arm;
  - several trials per cell.
- This paper does **not** claim any agent outcome.

## Methodological choices made here that need the authors' judgement (Principle 10)

1. **Post-hoc ablations.** Binary reading, no curated identity and name identity were defined *after* the registered results were known. They are reported as exploratory. The authors decide whether to register them for the prospective study.
2. **Comparators off.** The research pipeline runs baseline V without its pinned npm/Go/Maven comparators, for determinism across machines. On both case sets this changes no pair (versions tables). The registered configuration (`--comparators required`) stays authoritative.
3. **The D16 fix** changes engine behaviour for heuristic mappings. It follows the TR's own specification, but it changes the release's behaviour and needs a CHANGELOG entry and the authors' sign-off.
4. **The F-17 fix** changes which causes the MCP tool lists. It shows more causes than before. Whether that is too noisy for agents is an empirical question (R9).
5. **Target venue.** The format, page limit and AI policy depend on it. Candidates are listed in `paper/README.md`.
