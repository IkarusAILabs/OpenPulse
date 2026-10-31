# Final implementation report: research-readiness round 1

**Date:** 2026-10-31.

**Base:** branch `pr-148`, commit `ddea292` (`v0.8.0-7-gddea292`).

**Commit state:** all changes are in the working tree, **uncommitted and unpushed**. Nothing was released, published or pushed.

## 1. What was inspected

- **Source.** The decision engine (`core/risk/match.py`, `core/risk/check.py`, `core/verdict_meaning.py`), identity resolution (`core/entities/`), the evidence contract, and the agent and MCP surface (`core/agent_tools.py`, `cli/mcp_server.py`).
- **Evaluation and conformance tooling.** The evaluation harness (`evaluation/`: policies, metrics, registration, run, replay) and the conformance tooling (`conformance/`: oracle, matrix, randomised, mutation, independent kit).
- **Data.** Both case sets, and the frozen and after-fixes results.
- **Process.** The CI workflows, and the TR (`papers/tr-2026-01/main.tex`, 3,960 lines) with its review responses.
- **Baseline before any change:** 1,164 passed, 5 skipped.

## 2. What was changed

Engine behaviour:

| Change | Files | Why |
|---|---|---|
| D16 fixed: a heuristic or unreviewed identity mapping no longer removes an association | `core/risk/match.py`, `core/risk/check.py` | P0. A summary could show "cleared" over a kept association. The TR specifies the fix. |
| Agent and MCP answers carry the cause behind every verdict (F-17) | `core/agent_tools.py`, `docs/MCP.md` | 7 of 10 tested dependencies got a verdict with no supporting cause |

Statistics:

| Change | Files | Why |
|---|---|---|
| Holm adjusts unrounded p; an empty population is invalid; the H1 rule text is absolute | `evaluation/registration.py` | Reporting defects (F-04 to F-06) |

Conformance and tests:

| Change | Files | Why |
|---|---|---|
| Decision invariants I1–I8 as properties | `conformance/invariants.py`, `conformance/results/invariants.json` | Brief §6.4 |
| D16 mutant, D10 anchor update, invariant detector | `conformance/mutation.py`, `conformance/results/mutation.json` | Mutation campaign covers the new rule and detector |
| Regression, property, mutation-sensitivity, surface and pipeline tests | `tests/test_false_clear.py`, `test_registration.py`, `test_decision_invariants.py`, `test_research_surfaces.py`, `test_research_pipeline.py` | — |

Research package and process:

| Change | Files | Why |
|---|---|---|
| Research package | `research/` (9 documents, 6 scripts, schema, results, tables, figures, draft manuscript) | Brief §13, §17 |
| CI | `.github/workflows/ci.yml` (job `research`), `paper.yml` (job `manuscript`) | Brief §15 |
| CHANGELOG upgrade note | `CHANGELOG.md` | D16 changes verdicts |

**Not changed:**
- the frozen case files and frozen results;
- the TR and its review files;
- the stale documents listed in audit F-14, which are left for the authors.

## 3. What was tested, with exact results

| Check | Result |
|---|---|
| Full suite (`pytest -q`), after all changes | **1,228 passed, 5 skipped** (107.8 s; baseline 1,164 passed, 5 skipped) |
| `ruff check .` | All checks passed |
| D16 tests on the pre-fix code | 4 of 6 fail (the 2 that pass are a curated-mapping control and the already-correct release-line case) |
| Agent-cause tests on the pre-fix code | 7 of 10 fail |
| Decision invariants, 3 seeds × 4,000 cases | 0 violations. Checks per invariant: I1 2,481, I2 1,393, I3 1,112, I4 7,235, I5 12,928, I6 1,351, I7 1,025, I8 8,480. |
| Invariants on the pre-D16 code (1,000 cases) | I3: 66 violations, no other invariant fires |
| Targeted mutants (5) | Each caught by its target invariant (RESEARCH_PROTOCOL.md §3) |
| Mutation campaign | 23 of 23 caught, 14 by the invariants. D16 is caught only by the invariants and its regression test. |
| Oracle matrix | 6,195 cases, unchanged from the committed result (6,123 conform, 72 label-only) |
| Reproduction check (`reproduce.py --check`) | **34 outputs identical**, source hash `d938c63de420` |
| Cross-version | Current tree vs after-fixes: 0 of 167 pairs change for C. Vs the frozen run: 0 of 167 change for A, B and V. Development set: 0 of 60. |

Not run here:
- the CI jobs themselves (Linux and Windows, Python 3.11);
- the LaTeX build, because no TeX is installed locally;
- the npm, Go and Maven comparators, because no toolchains are installed locally;
- the 100,000-case `--full` check.

## 4. Experiments

**Completed** (retrospective, developer-labelled; `research/tables/`):
- every registered policy;
- three post-hoc ablations;
- intervals and clustering;
- version comparison.

**Not completed:**
- independent labelling;
- the S3 and existing-format comparison: R is not evaluable on the retrospective set, and X_K, L₀, L_K and T₀ do not exist;
- the prospective held-out study;
- the discovery study;
- review-burden measurement;
- the agent experiment.

## 5. Remaining defects

- **Dataflow invariant.** "Completeness is never derived from a listing" is still hand-checked (plan R7).
- **CLI text and SARIF** are not compared with the engine on generated cases (F-13).
- **Latent package/source-repository gap.** The TR §8 gap is unchanged.
- **Wrong curated mappings.** A wrong curated VERIFIED mapping is trusted and not detected (by design; it is assumed).

## 6. Remaining methodological weaknesses

- All labels are the developer's.
- The 27 events are a purposive sample.
- Only npm, Go and images are covered.
- 138 of 167 pairs have unresolved identity.
- Post-hoc ablations.
- The same team built the oracle, generator, invariants and engine.
- Review effort is not measured.
- The completeness rule prevented no false clear on this set.

## 7. Claims the evidence supports

- On this developer-labelled retrospective sample:
  - OpenPulse made 0 false clears on 103 in-scope pairs, where a naive reading of the same records made 35, across 10 of 27 events;
  - its unresolved outcome accounts for most of the difference, since the same engine read as binary makes 26;
  - the cost is 64 of 167 unresolved outcomes.
- The implementation conforms to its specification on the oracle grid and the randomised and generated cases, and satisfies eight decision invariants on 12,000 generated cases. The checks detect 23 of 23 re-injected defects.
- Every result reproduces byte for byte from one offline command, tied to a source hash.

## 8. Claims that must not yet be made

- Any false-clear or error rate for real-world use, other ecosystems or other events.
- "Independently labelled", "ground truth", or inter-rater reliability.
- Statistical significance beyond the sample.
- That the completeness rule improves safety (not observed here).
- Novelty or "first", until the literature protocol is done. SPDX 3.0 and CycloneDX completeness must be addressed.
- Superiority over existing formats or tools (S3 not run).
- Any effect on AI coding agents, or protection against malicious packages, hallucinated packages or prompt injection.
- Formal verification.

## 9. Most important next steps before journal submission

1. **Disclose AI assistance.** Decide and disclose how the TR reviews and the pilot labels were produced, and check the venue's AI policy (audit F-03).
2. **Independent labels.** Obtain them for the 167 pairs: two annotators and an adjudicator, following `LABELING_GUIDE.md`.
3. **Literature protocol.** Execute it, verify the 4 flagged references, and position the work against SPDX 3.0 and CycloneDX completeness.
4. **Blind encodings.** Have the 27 retrospective events encoded blind for R and X_K, and implement the missing factorial cells, so the existing-format comparison can run.
5. **Review and commit.** Review and commit this round. Let CI run the `research` and `manuscript` jobs, read the PDF, and choose a venue.
6. **Archive.** Archive a tagged release with a DOI.
