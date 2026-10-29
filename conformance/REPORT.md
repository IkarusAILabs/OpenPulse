# Conformance and differential results — TR-2026-01

Run from the repository root:

```bash
python conformance/matrix.py
python conformance/versions_differential.py
```

Results are written to `conformance/results/`: the counts and every disagreement. None is filtered out.

## Method

- **Oracle.** `conformance/oracle.py` implements Algorithm 1 and the membership tests of §5 from the report's text. It imports nothing from `core` or `analyzers`. Identity is an input to each case (ground truth, from the curated catalog's meaning), so the oracle tests matching and decision policy, not the identity resolver.
- **Matrix.** `conformance/matrix.py` crosses 17 scopes × 3 completeness states × 5 admissibility states with 13 image references and 4 package references.
  - **Scopes:** project; named example tag; repository; literal tag; `:<version>`; `:*`; object; namespace envelope; `namespace:<version>`; both together; another repository; two release lines; two package lists; two registries.
  - **Completeness:** partial; declared without basis; declared with basis.
  - **Admissibility:** current; contested; withdrawn; superseded; stale.

  This gives **3,995 cases**. Each runs through the oracle and through `check_dependency` on the equivalent `OSSEvent`.
- **Severity.** Each disagreement is classified from the implementation's side:
  - *unsafe* — the implementation clears, or drops an association, where the specification does not;
  - *false impact*;
  - *under-positive*;
  - *over-cautious*;
  - *label* — the verdicts differ in name, but both are unresolved or both are non-blocking.

## First run (implementation at `f6e6ffc`, report text as written)

3,350 of 3,995 cases conformed. The 645 disagreements fell into six mechanisms:

| Id | Mechanism | Cases | Fault |
|---|---|---:|---|
| **D12** | `docker.io/redis` parsed as namespace `docker.io`, not `library`. This gave **8 unsafe clears** against complete `docker.io/library/redis` scopes. | 37 | implementation |
| **D13** | An unmapped *package* was dropped as "no applicable evidence" instead of unresolved: the package-side twin of D10. | 47 | implementation |
| **D14** | A digest-pinned reference under a repository-wide element got RELATED, though a repository element covers every pin. | 12 | implementation |
| **S1** | Algorithm 1's layer-1 guard made *every* verdict RELATED for contested or stale events. The prose (§4.4; N4 and N5) and the code withhold only negatives. | 482 | specification |
| **S2** | A dependency *curated as another project* got ? from the cross-kind and package-inequality rules. A curated mapping to another project is the evidence that justifies "no association" (N2). | 53 | specification |
| L1 | Project tie vs RELATED | 14 | label |

## What was changed

**Implementation**

| Id | Change |
|---|---|
| D12 | A first segment with a dot, port or `localhost` is a registry host also in a two-segment reference, so `docker.io/redis` is `docker.io/library/redis`. Single-name repositories go under `library` only on Docker Hub. The registry sweep's bare-namespace rule, which had relied on the old parse, is now stated explicitly. |
| D13 | An unmapped package is RELATED against project-wide, release-line and package scopes. It has no association with container-image and registry scopes, since a package is never one of those. `boto3` and `serde` are now curated as their own projects. Four tests had used them as "a dependency nothing applies to". |
| D14 | A repository element without a tag or digest (or with `:*`) covers digest-pinned references to the repository. |

**Specification** (the corrections the oracle now implements; the report's text is to be updated to match)

| Id | Correction |
|---|---|
| S1 | Layer 1 drops withdrawn and superseded events, and withholds *negatives* from contested or stale events. It does not change positives. |
| S2 | A dependency curated as another project gives 0 (no association) for project-owned elements (project, release line, package) and across reference kinds. This exclusion needs no complete scope. |
| S3 | Across kinds, a package reference has no association with container-image, object or registry elements, whatever its identity. It is ? against a source-repository element (a Go module path may name the repository), and ? whenever identity is the event's own project or unresolved. |
| S4 | A named example artefact illustrates a change and never bounds it. Non-membership in an example gives 0, not N. Another tag of a named repository gives ?. |

## Final run

The implementation has D12–D15 fixed and the image path aligned with S2; the oracle includes S1–S4 and the example rule.

**Matrix: 3,947 of 3,995 cases conform (98.8%).** The 48 remaining cases are one documented label difference. For a package of the event's own project, against a registry scope or a project-wide event, the specification gives a project tie (AFFECTS_PROJECT) and the code gives RELATED. Both are unresolved, and both block a clearance. There are no unsafe, false-impact, under-positive or over-cautious cases.

## Randomised differential testing

`conformance/randomized.py` generates cases that combine everything at once:
- one to three events per dependency, from two projects;
- each event with a scope of one to four elements of mixed kinds, random named examples, random completeness, basis and admissibility;
- a random dependency: tag-pinned, digest-pinned or untagged image, or a package with or without a version, of either project, a curated third project, or unmapped.

Each case compares both the per-event verdicts and the cross-event summary. The generator is seeded, so every run is reproducible.

| Seed | Cases | Summaries conform | Per-event verdicts conform |
|---|---:|---:|---:|
| 2026 | 20,000 | 20,000 | all |
| 7 | 100,000 | 100,000 | 200,272 of 200,272 |

The first randomised run found:
- **D15, an implementation defect.** When a named example left a reference undetermined, the event's scope was never evaluated, so a release-line member was only RELATED (24 under-positive cases).
- **S2 on the image path.** An image curated as another project was turned into an identity exclusion that needed a complete scope, instead of "no association" (7,446 per-event cases). The version branch now decides identity before reading the tag.
- **Two oracle errors, both corrected.** The generator labelled `docker.io/bitnami/redis` unmapped, though it is curated as `bitnami-redis-stack`. And the oracle let a package match a named example image; examples never bound a scope, and a package is never an image.

## Defect re-injection

`conformance/mutation.py` re-introduces each historical defect (D1, D3, D4, D7–D15) and disables each enforced rule (N3, N4 withdrawn, N4 stale, N5, element roles, the package-name rule, S2). Each mutant is a single-function patch of the running code. Four detectors then run against it:
- **A:** the matrix (any change from the clean baseline);
- **B:** 5,000 randomised cases;
- **C:** the false-clear regression tests;
- **D:** the version differential tests.

**All 19 mutants are caught, and all 19 are caught even without the regression tests (C).** The oracle detectors (A, B) catch the matching and policy mutants. The version detector (D) catches the comparator mutants D8 and D11. D2, D5 and D6 are not re-injected, because none is a single-function change of the current code: D2 is a multi-line walk, D5 is subsumed by D10 and S2, and D6 is rejected by the closed grammar before any comparison.

## Continuous enforcement

`tests/test_conformance_gate.py` runs in the normal test suite, in about 3 seconds. It fails the build on:
- any matrix disagreement other than the documented label;
- any disagreement on 5,000 seeded random cases;
- any disagreement with `packaging`, or with the SemVer vectors, comparator and ranges alike.

## Differential version results

| Check | Result |
|---|---|
| PEP 440 vs `packaging` 26.2 (PyPA), 233,289 ordered pairs over 483 generated versions | **224,676 agree, 0 disagree**; 6,685 abstain (OpenPulse undetermined: post, local, epoch, multi-marker forms); 1,928 pairs invalid in `packaging`, on all of which OpenPulse also abstains |
| OSV `ECOSYSTEM` ranges, PyPI, against intervals evaluated with `packaging` | **7,110 agree, 0 disagree**; 105 abstain |
| SemVer: semver.org §11 precedence vectors, antisymmetry and transitivity over a 16-version pool, and OSV `SEMVER` ranges built from the vectors | 0 failures, 0 inconsistencies, 0 range failures |

**What is not covered.**
- No independent SemVer library or Node runtime was available offline, so SemVer was checked against the specification's vectors and for consistency, not differentially.
- Ecosystems the comparator does not model compare plain numbers only and otherwise abstain, so they were not tested differentially.

## Limits

The matrix covers chosen dimensions, not every input. It checks the specified semantics on that matrix and is not a proof. Identity is supplied as ground truth, so resolver errors are outside it. The oracle and the implementation were written by the same team, which limits independence. An external re-implementation of the oracle would strengthen the result.
