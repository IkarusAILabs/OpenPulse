# Advisory-path benchmark: design

**Status: design, written 2026-10-31 in response to the twelfth review (§3.3.5, Priority 3).** No snapshot, case or label exists yet. Like the event-scope study, this needs a registration of its own (`evaluation/REGISTRATION.md` §1 excludes this path), archived before any label. This document fixes the design so that the registration can be drafted from it.

## 1. Why a separate study

OpenPulse has two decision paths:
- the **event-scope path** reads typed upstream-change events (relocation, archival, distribution, lifecycle). The registered study evaluates it;
- the **advisory path** (`core/risk/check.py`, `_security_causes`, and `correlate`) correlates OSV and NVD advisories by package identity and version range.

The advisory path is the only one where a false clear has been observed. In the retrospective study, OSV advisories without a CVE identifier were dropped or merged by CVE, so `node-ipc` 9.2.2 was not reported affected (D-S1). Two false impacts followed from the range and version-only semantics (D-S2, D-S3). All three are fixed and regression-tested, but no study has measured this path. No result of the event-scope study is claimed for it.

## 2. Question

> Given the advisories as they stood on a date, does OpenPulse's advisory path report a package version as affected exactly when the advisory data then available places it in range? How often do its decisions differ from those of the reference consumer, and why?

Two kinds of error are kept apart, because they have different owners:
- **Correlation errors.** OpenPulse's decision differs from what the snapshot it was given says. These are OpenPulse's defects.
- **Data errors.** The snapshot was wrong or incomplete at that date, and a later correction shows it. OpenPulse is not wrong to follow the data, but a consumer is harmed either way. These are reported, never counted as OpenPulse's errors.

## 3. Reconstructing the advisory state at a date

Advisory databases change: records are added, ranges corrected, and records withdrawn. Today's state must not be used to judge a past decision. Use only sources whose own history shows each record's state at a date:

| Source | How the state at date *t* is reconstructed |
|---|---|
| GitHub Advisory Database (`github/advisory-database`, OSV format) | The repository at its last commit before *t* |
| PyPA advisory database (`pypa/advisory-database`) | The same |
| Go vulnerability database (`golang/vulndb`, OSV reports) | The same |
| RustSec (`rustsec/advisory-db`) | The same, converted to OSV by its published tooling |
| NVD | Only where an archived JSON feed for that date exists; otherwise NVD is excluded for that date, and the exclusion is reported |

The snapshot for each date is frozen with its source commits and a SHA-256 of the extracted records, before OpenPulse runs on it.

## 4. Cases

A case is (package, ecosystem, version, date). The population is the advisories in the reconstructed sources for a set of dates, over PyPI, npm, Go and Maven. The strata are fixed before sampling, and each must be represented:

| Stratum | Why |
|---|---|
| Advisories with no CVE identifier (GHSA-, PYSEC-, GO-, RUSTSEC-only) | D-S1's class |
| Multi-package advisories (several `affected` entries) | D-S2's class: another package's range must not decide |
| Version-only entries (`versions` with no `ranges`) | D-S3's class |
| Multiple ranges, `last_affected`, `limit` | Range semantics |
| Pre-release and build-metadata boundaries | D8 and D11's class |
| `ECOSYSTEM` ranges for Maven and PyPI; `SEMVER` for npm and Go | Comparator per scheme |
| Withdrawn advisories (`withdrawn` set at *t*) | Must not associate |
| Advisories later corrected (range or package changed after *t*) | Data errors (§2) |
| Packages with no advisory | Negative controls |

For each sampled advisory, versions are drawn at the boundaries: just inside and just outside each range end, a pre-release of each boundary, and one version far from any boundary.

## 5. Ground truth and the reference consumer

- **Correlation truth at *t*.** This is what the snapshot says under the OSV schema. It is computed by a reference consumer that shares no code with OpenPulse: `osv-scanner` (pinned version), or the OSV schema's own range-evaluation algorithm with the pinned ecosystem comparators that the registered study uses (`evaluation/ecosystem_versions.py`). Where the reference consumer and the schema disagree, the case is adjudicated by hand and reported.
- **Data truth.** This is the latest available state of the same advisory, and its correction history. A version affected under the corrected record but not under the record at *t* is a data-error case.
- **Labels for data truth** need an annotator independent of OpenPulse's development, as in the registered study. Correlation truth is computed, not labelled.

## 6. Policies

- **OpenPulse's advisory path** (`check_dependency` with the snapshot as `bundles`).
- **The reference consumer** (§5).
- **A CVE-keyed merger**: advisories merged by CVE identifier, with CVE-less records dropped. This is the pre-D-S1 behaviour, and shows what the fix prevents.

## 7. Measures

Each is reported per stratum and per ecosystem, with exact intervals per advisory. The bootstrap is clustered by advisory, because many cases share one.
- **False clears:** affected at *t*, but OpenPulse reports no association or not affected.
- **False impacts:** not affected at *t*, but OpenPulse reports affected.
- **Unresolved decisions:** an undetermined comparison or identity.
- **Disagreements with the reference consumer**, each explained.
- **Data errors:** decisions that followed the snapshot, but that the later correction shows were wrong.
- **Regression coverage:** for each fixed defect class (D-S1 to D-S3, D8, D11), whether a case of that class is present and passes.

## 8. Freeze and leakage

As for the registered study:
- OpenPulse is frozen at a tag;
- snapshots and cases are frozen with their hashes before any run;
- a defect found and fixed afterwards is reported as a separate run, never merged into the frozen result.

The cases come from dates and packages outside the retrospective study.

## 9. Not covered

- **Advisory discovery.** Whether OpenPulse fetches the right advisories at all is a collection question, measured separately.
- **Advisory quality beyond its own corrections.** An advisory that stays wrong is undetectable here.
- **Exploitability, reachability and severity.** OpenPulse does not assess them.
