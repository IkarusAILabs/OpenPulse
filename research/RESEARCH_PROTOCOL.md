# Research protocol

This protocol specifies what is evaluated and how. It is the reference for the model (§1–2), the invariants (§3), the conditions a negative result rests on (§4), and the experimental design (§5).

The formal treatment, with Algorithm 1, the lemmas and the NotAffected contract, is in TR-2026-01 §5 (`papers/tr-2026-01/main.tex`). This file does not restate it. It maps it to code and tests, and states what is checked and what is assumed.

## 1. Unit of analysis

A **pair** (d, e) is:
- a **dependency reference** d, either a container reference (`docker.io/bitnami/redis:7.2`, a digest pin) or a package (ecosystem, name, version); and
- an **upstream event** e: a recorded change to a project, such as a distribution change, licence change, end of life, deprecation, relocation or compromise. Each event carries evidence items with provenance.

A **case** is one reference evaluated against one or more events. Pairs of one event share that event's evidence, so the **event is the statistical cluster** (METRICS.md §4).

## 2. The applicability model, dimension by dimension

| Dimension (brief §4A) | Representation | Code |
|---|---|---|
| Dependency identity | Resolved slug plus *how* it was reached: `explicit`, `catalog`, `namespace_rule` or `self` | `core/entities/identity.py:resolution_trust`, `package_trust` |
| Canonical identity and aliases | Curated explicit aliases, catalogue aliases and images; Docker Hub host folding; PEP 503 / Maven name folding | `core/entities/resolve.py`, `core/entities/catalog.py` |
| Ecosystem and namespace | Registry, namespace and name triple for images; (ecosystem, name) and purl for packages | `match.split_image_ref`, `catalog.package_name_key` |
| Version or release-line scope | Release-line prefix membership; uncomparable versions are undetermined | `core/versions.py:in_release_line` |
| Event type | `OSSEvent.event_type` | `core/schema/models.py` |
| Event scope | Typed elements (artifact, version, package, registry; project if none). Roles: exact or envelope. Named artefacts are examples, never bounds. | `match._scope_result`, `_artifact_candidates`, `element_role` |
| Evidence provenance | Each evidence item has a source, URL, authority tier, `fetched_at` and relation (supports or contradicts) | `Evidence`, `Source` in `core/schema/models.py`; contract `evidence_refs` |
| Evidence freshness | The newest evidence item must be within a bound (default 90 days) for a negative | `check._admit`, `inadmissible_reason` |
| Evidence completeness | `Scope.exhaustive` plus `Scope.basis`. A negative needs both. `verified` is reserved and never produced. | `Scope.admits_negative`, `verdict_meaning.scope_completeness` |
| Confidence or ambiguity | Match ceiling ∧ evidence confidence; capped at EMERGING for untrusted identity | `check._combine` |
| Decision outcome | Seven relationships, summarised to four outcomes: affected, unresolved, cleared, no association | `check.winning_cause`, `policies._OPENPULSE_OUTCOME` |

**Outcomes.**
- **Affected:** `AFFECTS_ARTIFACT`, `AFFECTS_VERSION` or `AFFECTS_PACKAGE`.
- **Unresolved:** `RELATED`, or `AFFECTS_PROJECT` (a project tie without established scope membership).
- **Cleared:** `NOT_AFFECTED`, which means "outside the directly named scope of a complete, current, uncontested event". It is never a statement that the dependency is safe (`core/verdict_meaning.py`).
- **No association:** `UNKNOWN`, which means "nothing relates this reference to the event". It is not a clearance either.

## 3. Decision invariants

Each invariant is checked as a property of the production engine's outputs on seeded generated cases, in `conformance/invariants.py`:
- the randomised generator of `conformance/randomized.py`, widened with heuristic identity mappings;
- 3 seeds × 4,000 cases;
- results in `conformance/results/invariants.json`.

`tests/test_decision_invariants.py` re-runs 3 × 1,500 cases on every CI run.

| # | Invariant (brief §6.4) | Executable statement | Checks / violations |
|---|---|---|---|
| I1 | An unknown identity cannot produce a negative because no match was found | Unresolved (self-resolved) identity, identity-dependent scope (project, release line, bare package values) ⇒ per-event verdict ∉ {NOT_AFFECTED, UNKNOWN} | 2,481 / 0 |
| I2 | Incomplete scope is not proof of non-applicability | Per-event NOT_AFFECTED ⇒ scope declared complete ∧ basis recorded ∧ event current (not stale, contested, withdrawn or superseded) | 1,393 / 0 |
| I3 | Ambiguous mappings cannot silently produce a negative | As I1, for a heuristic or REVIEW_REQUIRED mapping to another project | 1,112 / 0 |
| I4 | Unresolved outcomes stay unresolved in reports and machine-readable interfaces | Any per-event RELATED or AFFECTS_PROJECT ⇒ summary ∉ {NOT_AFFECTED, UNKNOWN}; the meaning block reads it as undetermined or project tie, and says "Not a clearance"; so does the evidence contract | 7,235 / 0 |
| I5 | The result is consistent across surfaces | The v1.2 evidence contract validates and states the engine's relationship and meaning. `tests/test_research_surfaces.py` adds: the agent/MCP answer, the engine, the contract and the evaluation mapping agree on curated events, in both modes. | 12,928 / 0 |
| I6 | A known applicable event is not excluded by a misleading name match | Affected ⇒ still affected after look-alike elements are placed first in the event (same name in another registry or namespace, similar package names) | 1,351 / 0 |
| I7 | A negative is justified by the documented model | Per-event NOT_AFFECTED ⇒ the specification oracle (`conformance/oracle.py`) also says NOT_AFFECTED; summary NOT_AFFECTED ⇒ at least one clearing event and none unresolved | 1,025 / 0 |
| I8 | Every verdict is traceable to evidence and rules | Non-UNKNOWN verdict ⇒ names its events (a subset of the input events), each cause has a relationship and a reason, and cited evidence exists. On the agent surface: every verdict arrives with a supporting cause and its evidence URLs. | 8,480 / 0 |

**Sensitivity.** Each targeted mutant disables one safety rule (`tests/test_decision_invariants.py`). The run must complete, and the target invariant must fire.

| Disabled rule | Fired (600 cases, seed 11) |
|---|---|
| Unresolved identity read as unrelated (D10) | I1 55, I3 57 |
| Heuristic mapping read as proof of another project (D16) | I3 57 |
| Completeness not required for a clearance (D4/N3) | I2 111, I7 75 |
| Clearance headlines over an unresolved event (D3) | I4 35, I7 35 |
| Same-named repository elsewhere excludes | I6 19 |

In the full campaign (`conformance/mutation.py`), the invariants catch 14 of 23 re-injected defects. D16 is caught **only** by the invariants and its regression test: the oracle has no untrusted identity, so neither the matrix nor the randomised differential sees it.

**What this is not.** It is not formal verification. The properties are checked on generated inputs from a finite vocabulary of projects, references and tags (`randomized.py`). The same team wrote the generator, the oracle and the engine.

## 4. Which conditions are verified, which are assumed

The brief separates five questions. A NOT_AFFECTED verdict is sound **only under the assumptions marked A** below.

| Question | Status in OpenPulse | How |
|---|---|---|
| Was a relevant event discovered? | **A: assumed**, not verified | Discovery recall was measured once: 0/15 as shipped, 8/15 after fixes (`evaluation/retrospective/REPORT.md`). A verdict covers only the events supplied, and the meaning block says "other events were not considered". |
| Was the event represented accurately (elements, completeness, basis)? | **A: assumed.** The curated event, including its completeness declaration, is trusted. | TR Table `tab:premises`: P1 is "never verified". Measuring declaration reliability (D1) is in REGISTRATION.md, not run. |
| Was the dependency identity resolved correctly? | **Checked in part** | Heuristic and unmapped identities can never exclude or disassociate (I1, I3). A wrong *curated VERIFIED* mapping is trusted and not detected (A). |
| Was the event's scope evaluated correctly? | **Checked** against the specification | Oracle matrix (6,195), randomised differential (100,000), invariants (12,000), version differentials against `packaging` and pinned ecosystem comparators |
| Was the result communicated correctly? | **Checked** for the contract and agent surfaces | I4, I5, I8; `tests/test_research_surfaces.py`. CLI text and SARIF are not compared on generated cases (audit F-13). |

## 5. Evaluation design

- **Case sets.**
  - `openpulse-retro-2026-11` v1: 27 events, 167 pairs, frozen and hash-pinned. This is the evidence set.
  - `openpulse-dev-2026-10`: 12 events, 60 pairs, used for development. It is illustrative only, never evidence.
  - Both are described in `DATASET_CARD.md`.
- **Labels.** The developer's (L1), assigned by written per-event rules before any policy ran (`evaluation/retrospective/DESIGN.md` §6). They are **not independent**: see `LABELING_GUIDE.md`.
- **Policies.** Registered: A, B, R, V, C, and C's four ablations. Post hoc: three further ablations of C. All are defined in `BASELINES.md`. Every policy receives the same replayed events and the same reference.
- **Knowledge cut.** Each event is replayed as known on its `as_of` date (`evaluation/replay.py`). The freshness bound is 90 days.
- **Metrics.** Defined in `METRICS.md`, with every denominator named.
- **Separation.** There is no tuning set. The retrospective set was frozen before any policy ran on it. The engine fixes made after it ran are reported as "after fixes", separately (`research/tables/retro_versions.md`), and a pair-by-pair transition table shows exactly which pairs changed. Development and evaluation sets share no event.
  - With 27 events, the set is not split further. Event-level clustering is handled in the statistics, not by a random split that would leave about 5 events per fold.
- **Registered prospective study.** `evaluation/REGISTRATION.md`. Not run (RESEARCH_PLAN R8).
