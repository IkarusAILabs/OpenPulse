# Conformance and differential results — TR-2026-01

Implementation: `main` at `f6e6ffc`. Run from the repository root:

```bash
python conformance/matrix.py
python conformance/versions_differential.py
```

Raw results are written to `conformance/results/`. Every disagreement is listed there; none is filtered out.

## Method

- **Oracle.** `conformance/oracle.py` implements Algorithm 1 and the membership tests of §5 from the report's text. It imports nothing from `core` or `analyzers`. Identity is an input to each case (ground truth, from the curated catalog's meaning), so the oracle tests matching and decision policy, not the identity resolver.
- **Matrix.** `conformance/matrix.py` crosses 17 scopes × 3 completeness states × 5 admissibility states with 13 image references and 4 package references.
  - **Scopes:** project; named example tag; repository; literal tag; `:<version>`; `:*`; object; namespace envelope; `namespace:<version>`; both together; another repository; two release lines; two package lists; two registries.
  - **Completeness:** partial; declared without basis; declared with basis.
  - **Admissibility:** current; contested; withdrawn; superseded; stale.
  - **References:** tag-pinned, digest-pinned and untagged images; Docker's `docker.io/<name>` spelling; a Docker Hub alias host; another project; unmapped references.

  This gives **3,995 cases**. Each runs through the oracle and through `check_dependency` on the equivalent `OSSEvent`.
- **Severity.** Each disagreement is classified from the implementation's side:
  - *unsafe* — the implementation clears, or drops an association, where the specification does not;
  - *false impact*;
  - *under-positive*;
  - *over-cautious*;
  - *label* — the two verdicts differ in name, but both are unresolved or both are non-blocking.

## Matrix results

**3,350 of 3,995 cases conform (83.9%).** All 645 disagreements fall into six mechanisms:

| Id | Mechanism | Cases | Severity | Where the fault lies |
|---|---|---:|---|---|
| **D12** | `docker.io/redis` parsed as namespace `docker.io`, not `library`, so it differs from `docker.io/library/redis` in location matching. Identity resolution is correct. | 37 | **8 unsafe clears**, 12 false impacts, 13 under-positive, 4 label | Implementation (open) |
| **D13** | An unmapped *package* (`zzzpkg`) gets "no applicable evidence" (UNKNOWN), not unresolved. This is the package-side twin of D10, which was fixed only for images. It can let another event's clearance headline. | 47 | unsafe (drops an association) | Implementation (open) |
| **D14** | A digest-pinned reference under a repository-wide element (`docker.io/library/redis`, `:*`) gets RELATED. The pinning-mix policy applies even though the element names no tag. | 12 | under-positive (safe direction) | Implementation (open) |
| **S1** | Algorithm 1's layer-1 guard returns RELATED for *every* dependency of a contested or stale event, including members and unrelated references. The report's own prose (§4.4; N4 and N5 as *negative*-admission conditions) withholds only negatives, and so does the implementation. | 482 | — | **Specification**: the algorithm contradicts its prose |
| **S2** | A dependency *curated as another project* (`mysql`) gets ? from the cross-kind rule and the package-inequality rule, so the specification says RELATED. The implementation says "no association". Under N2, a curated mapping to another project is exactly the evidence that justifies exclusion, so the rules should give 0. | 53 | — | **Specification**: the rules ignore a curated distinct identity |
| L1 | Project tie vs RELATED for a package against a registry scope, or against a project-wide event. | 14 | label: both unresolved | Neither (representation) |

### Unsafe cases

Only D12 makes the implementation clear a dependency the specification puts in scope. All 8 cases have the same shape: `docker.io/redis:7.2` against a complete scope naming `docker.io/library/redis` (repository, tag, `:<version>`, `:*`, object, the namespace envelope, or `namespace:<version>`). D13 drops an association, which affects summaries, not pair verdicts. No other mechanism yields an unsafe implementation result.

## Differential version results

| Check | Result |
|---|---|
| PEP 440 vs `packaging` 26.2 (PyPA), 233,289 ordered pairs over 483 generated versions | **224,676 agree, 0 disagree**; 6,685 abstain (OpenPulse undetermined: post, local, epoch, multi-marker forms); 1,928 pairs invalid in `packaging`, on all of which OpenPulse also abstains |
| OSV `ECOSYSTEM` ranges, PyPI, against intervals evaluated with `packaging` | **7,110 agree, 0 disagree**; 105 abstain |
| SemVer: semver.org §11 precedence vectors, plus antisymmetry and transitivity over a 16-version pool | 0 failures, 0 inconsistencies |

**What is not covered.**
- No independent SemVer library or Node runtime was available offline, so SemVer was checked against the specification's vectors and for consistency, not differentially.
- Debian, Maven and other ecosystems are not modelled. They compare plain numbers only and otherwise abstain, so they were not tested differentially.

## Consequences

1. **Fix in the implementation:** D12 (unsafe), D13 (summary-unsafe) and D14 (over-cautious). After the fixes, re-run the matrix, which should leave only S1, S2 and L1.
2. **Fix in the specification:**
   - S1: layer 1 withholds negatives only.
   - S2: a curated mapping to another project gives 0 for project-owned and cross-kind elements.

   Then update the oracle to the corrected text and re-run. The target is zero disagreements other than documented labels.
3. The matrix covers chosen dimensions, not every input. It is a conformance check of the specified semantics on that matrix, not a proof.
