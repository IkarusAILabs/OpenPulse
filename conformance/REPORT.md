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

## Final run (implementation with D12–D14 fixed, oracle with S1–S4)

**3,935 of 3,995 cases conform (98.5%).**

| Severity | Cases |
|---|---:|
| unsafe (clears or drops an association) | **0** |
| false impact | **0** |
| under-positive | **0** |
| over-cautious | 16 |
| label: both unresolved | 42 |
| label: both non-blocking | 2 |

The 60 remaining disagreements come from two mechanisms, both safe:
- **42 labels.** For a package of the event's own project against a registry scope or a project-wide event, the code reports the project tie (AFFECTS_PROJECT) where the specification says RELATED, or the other way round. Both are unresolved, and both block a clearance.
- **18 over-cautious or non-blocking cases.** For an *image* curated as another project, against a release-line scope, the code makes an identity exclusion that still needs a complete scope, so it gives RELATED under a partial scope and NOT_AFFECTED under a complete one. The specification gives "no association" in both. Package references already follow the specification here.

## Differential version results

| Check | Result |
|---|---|
| PEP 440 vs `packaging` 26.2 (PyPA), 233,289 ordered pairs over 483 generated versions | **224,676 agree, 0 disagree**; 6,685 abstain (OpenPulse undetermined: post, local, epoch, multi-marker forms); 1,928 pairs invalid in `packaging`, on all of which OpenPulse also abstains |
| OSV `ECOSYSTEM` ranges, PyPI, against intervals evaluated with `packaging` | **7,110 agree, 0 disagree**; 105 abstain |
| SemVer: semver.org §11 precedence vectors, plus antisymmetry and transitivity over a 16-version pool | 0 failures, 0 inconsistencies |

**What is not covered.**
- No independent SemVer library or Node runtime was available offline, so SemVer was checked against the specification's vectors and for consistency, not differentially.
- Ecosystems the comparator does not model compare plain numbers only and otherwise abstain, so they were not tested differentially.

## Limits

The matrix covers chosen dimensions, not every input. It checks the specified semantics on that matrix and is not a proof. Identity is supplied as ground truth, so resolver errors are outside it. The oracle and the implementation were written by the same team, which limits independence. An external re-implementation of the oracle would strengthen the result.
