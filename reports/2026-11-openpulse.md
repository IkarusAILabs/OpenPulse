# OpenPulse OSS Dependency Intelligence

## November 2026

In November 2026, OpenPulse identified 16 material upstream changes worth a software team's attention, including 9 non-lifecycle discoveries no lifecycle database records. Every item below names its evidence, its scope, and when it matters — and none of it speaks about your environment without a watchlist to prove it.

_Public report findings describe OSS ecosystem changes. They are not assertions that a particular user's environment is affected._

## Executive Summary

OpenPulse detected 16 material upstream changes across 107 monitored projects in 2026-11. That includes 9 non-lifecycle discoveries — changes no lifecycle database records. 1 change requires attention now; no upcoming changes carry warning windows.

- Projects monitored: 107
- Material changes (action + review): 16
- Changes requiring attention: 1
- Upcoming changes with warning: 0
- Non-lifecycle discoveries: 9
- Evidence confidence: 0 CONFIRMED, 0 CORROBORATED, 41 EMERGING, 1 UNVERIFIED
- Background findings (effective over 12 months ago): 63
- Data gaps: 15 projects with no signals, 1225 records held back
- What remains uncertain: 0 findings carry unknown dates, 1225 records were held back for weak evidence
- Sources that did not answer: endoflife for 4 projects — their findings for those projects are unknown, not absent

## Top Changes

### 1. **timescaledb** — CVE-2026-70634 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Announcement: 2026-08-06 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Source: https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
Evidence:
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-information-disclosure-via-dictionary-compression-reverse-iterator

### 2. **timescaledb** — CVE-2026-70635 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Announcement: 2026-08-06 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Source: https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
Evidence:
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-dos-via-bulk-dictionary-decompression-negative-index

### 3. **vitess** — CVE-2026-104252 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Announcement: 2026-10-13 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Source: https://github.com/vitessio/vitess/commit/3140c1846cd120db34f33b2083139b4ab638aed2
Evidence:
- https://github.com/vitessio/vitess/commit/976e1e0d78f9d29d02e5e31b4aa7e180648f08af
- https://github.com/vitessio/vitess/commit/c1ed96302e658190168c971afdac730cf70e43f7
- https://github.com/vitessio/vitess/pull/20255
- (+5 more in the appendix)

### 4. **timescaledb** — CVE-2026-70633 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Announcement: 2026-08-06 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Source: https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
Evidence:
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-dos-via-gorilla-compression-reverse-iterator

### 5. **vitess** — CVE-2026-65959 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Announcement: 2026-08-18 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Source: https://github.com/vitessio/vitess/commit/4c58cd70edc6b03d61cb65842c342ac08341e64f
Evidence:
- https://github.com/vitessio/vitess/commit/657662e78bde1c82df680e9cc43a686d619f8094
- https://github.com/vitessio/vitess/commit/d929225a450027406687d27af8dca45620945ceb
- https://github.com/vitessio/vitess/security/advisories/GHSA-mhc4-g3wh-cw7m

### 6. **bitnami** — bitnami mainline is latest-only; versioned tags live in bitnamilegacy

Category: Distribution · Evidence confidence: UNVERIFIED · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: distribution model change with high significance: action-oriented framing justified

Investigate: Confirm whether this is a removal or a rename (pull/mirror check); review pinned references.

### 7. **bitnami** — bitnamisecure/redis publishes latest-only tags

Category: Distribution · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `docker.io/bitnamisecure/redis`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: distribution observation without high significance: watch

Investigate: No action; track the repository for further changes.

### 8. **minio** — minio/minio is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/minio/minio

### 9. **react-native-fbsdk** — facebookarchive/react-native-fbsdk is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/facebookarchive/react-native-fbsdk

### 10. **jaeger** — jaeger 1 is end-of-life

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1`

Announcement: Unknown

Effective: 2025-12-31 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: EOL effective for scoped versions `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Source: https://endoflife.date/jaeger

## OpenPulse Discovery of the Month

OpenPulse detects upstream changes and connects them to dependency identity.

### bitnami mainline is latest-only; versioned tags live in bitnamilegacy

WHAT CHANGED

docker.io/bitnami serves only `latest` while docker.io/bitnamilegacy holds versioned tags with no updates. Pinned bitnami/* references need a migration plan.

WHY IT MATTERS

distribution model change with high significance: action-oriented framing justified

HOW OPENPULSE DETECTED IT

Namespace pattern analysis across registry probes (discovery heuristic — corroborate pulls and mirrors before acting).

WHAT WAS AFFECTED

- `docker.io/bitnami/redis:<version>`
- `docker.io/bitnamilegacy/redis:<version>`

WHAT WAS NOT AFFECTED

`latest`-tag consumers: latest-only publication continues; pinned version references need a migration plan.

EVIDENCE


ANNOUNCED

Unknown — no trustworthy upstream publication date on record.

OPENPULSE DETECTION

First detection unrecorded.

WARNING WINDOW

No trustworthy warning window — first detection unrecorded.

## Changes Requiring Attention

- **jaeger** — jaeger 1 is end-of-life
  Scope: 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

## Upcoming Changes

No upcoming changes with trustworthy dates this month.

## Changes by Category

| Category | Changes | Requiring attention |
|---|---|---|
| Security | 5 | 0 |
| Lifecycle | 33 | 1 |
| Distribution | 2 | 0 |
| Repository | 2 | 0 |
| Support | 0 | 0 |
| License | 0 | 0 |
| Ownership | 0 | 0 |
| Other | 0 | 0 |

## Evidence Quality

- CONFIRMED (0): official announcement from the source itself.
- CORROBORATED (0): confirmed by 2+ independent source families.
- EMERGING (41): single credible source.
- UNVERIFIED (1): weak or unconfirmed signal — never action-framed.

## What OpenPulse Watches

OpenPulse watches what can change underneath software dependencies: security disclosures, lifecycle and support ends, distribution and registry changes, repository archival, license and ownership changes. Findings above are grouped by these categories — not by CVE counts or EOL tables — because the question is always what changed, not how many records a database holds.

## Methodology

Findings rest on named sources with content hashes; confidence (CONFIRMED / CORROBORATED / EMERGING / UNVERIFIED) follows evidence strength, never match precision. Dependency identity is resolved before impact is assessed, and unknown scope stays unknown. Freshness states (NEW / UPCOMING / ACTIVE / RECENTLY_UPDATED / EXPIRED) derive from announcement, effective, detection, and verification dates — expired findings move to the Historical appendix, never deleted. Full model: `docs/METHODOLOGY.md`.

## What OpenPulse Added This Month

OpenPulse is designed to answer a question traditional dependency monitoring often does not answer: Something changed upstream. Does it affect what we depend on?

This month the report answers it with the findings below — detected upstream changes, explained in context, correlated across sources, attributed to dependency identity, with warning where dates allow. OpenPulse does not replace SCA, SBOM, vulnerability, or lifecycle databases — it is an intelligence layer across them.

### Upstream Change Detection

- Security (5): e.g. **timescaledb** — CVE-2026-70634 [AFFECTS_PACKAGE] tracked by nvd
- Lifecycle (33): e.g. **jaeger** — jaeger 1 is end-of-life
- Distribution (2): e.g. **bitnami** — bitnami mainline is latest-only; versioned tags live in bitnamilegacy
- Repository (2): e.g. **minio** — minio/minio is archived on GitHub

### Dependency Attribution

- Affected artifact: `docker.io/bitnamisecure/redis` — bitnamisecure/redis publishes latest-only tags
- Affected version: `1` — jaeger 1 is end-of-life
- Related project: bitnami — bitnami mainline is latest-only; versioned tags live in bitnamilegacy
- `docker.io/bitnami/redis:<version>` resolves to the Bitnami distribution identity, not the upstream project.
docker.io/bitnami/redis is not docker.io/redis: namespace-aware resolution keeps distribution packaging apart from upstream code.
- Not affected: `latest`-tag consumers: latest-only publication continues; pinned version references need a migration plan.

### Evidence-backed Intelligence

- Confirmation level: strongest finding this month is EMERGING; full breakdown in Evidence Quality. No opaque risk scores.
- 4 independent source families across 57 supporting references.
- Scope established for 34/42 findings.
- Effective date known for 33/42 findings.

### Early Warning

- No upcoming changes with trustworthy dates this month — nothing to warn about yet.

### Reference Case

Problem: bitnami mainline is latest-only; versioned tags live in bitnamilegacy

Signal: Distribution · namespace_heuristic · significance high.

Evidence: UNVERIFIED confidence · 0 references.

Identity: project.

Applicability: PROJECT_CHANGE (REVIEW) — distribution model change with high significance: action-oriented framing justified

Recommended investigation: Confirm whether this is a removal or a rename (pull/mirror check); review pinned references.

Warning window: unrecorded (first detection unknown).

### From Public Intelligence to Early Warning

- Public intelligence: “What is changing in OSS?” — this report.
- Dependency intelligence: “What is changing in the OSS projects I use?” — `openpulse check --watchlist <file>`.
- Dependency impact: “Does this affect my software?” — matched dependencies only.
- Early warning: “How much warning do I have?” — warning windows above.

## For Your Environment

This report describes open-source ecosystem intelligence. It does not establish that a specific user's environment is affected.

Dependency-aware impact requires a user's watchlist, inventory, or equivalent dependency context: public intelligence → dependency context (`openpulse check --watchlist <file>`) → affected dependency → actionable warning. Only that last step can speak about your environment.

## Appendix

### A. Historical findings

- **airflow** — CVE-2017-12614 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2017-15720 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2017-17835 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2017-17836 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2018-20244 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-02-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2018-20245 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2019-0216 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2019-0229 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2019-12398 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-01-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2019-12417 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-10-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-11981 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-11982 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-11983 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-13944 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-17511 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-12-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-17513 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-12-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-17515 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-12-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — CVE-2020-9485 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **airflow** — apache-airflow lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2, 1.10, 1.9, 1.8, 1.7)
  Status: EXPIRED · Announced: Unknown · Effective: 2017-03-19
  Note: EOL effective for scoped versions ['3.2', '3.1', '3.0', '2', '1.10', '1.9', '1.8', '1.7']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **angular** — angular lifecycle: reached end-of-life (19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-08-06
  Note: EOL effective for scoped versions ['19', '18', '17', '16', '15', '14', '13', '12', '11', '10', '9']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **ansible** — CVE-2013-2233 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-05-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2013-4259 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-09-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2013-4260 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-09-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2014-3498 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-06-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2015-3908 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-08-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2015-6240 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-06-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2016-3096 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-06-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2016-9587 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2017-7466 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2017-7550 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-11-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — CVE-2018-1000149 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-04-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ansible** — ansible lifecycle: reached end-of-life (13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2.10, 2.9)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-02-09
  Note: EOL effective for scoped versions ['13', '12', '11', '10', '9', '8', '7', '6', '5', '4', '3', '2.10', '2.9']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **argocd** — CVE-2020-8828 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2021-3557 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2023-22736 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-01-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2023-40584 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2024-28175 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2024-29893 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2025-59537 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — CVE-2025-59538 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **argocd** — argo-cd lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.14, 2.13, 2.12, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-11-13
  Note: EOL effective for scoped versions ['3.2', '3.1', '3.0', '2.14', '2.13', '2.12', '2.11', '2.10', '2.9', '2.8', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **bitnami** — CVE-2025-22248 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-05-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2023-26054 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2024-23650 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-01-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2024-23651 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-01-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2024-23652 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-01-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2024-23653 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-01-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-15788 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-15789 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-15791 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-15792 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-15793 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-33747 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **buildkit** — CVE-2026-33748 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2020-13597 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-06-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2022-28224 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-06-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2026-41184 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2026-41185 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2026-41186 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2026-41187 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — CVE-2026-6540 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **calico** — calico lifecycle: reached end-of-life (3.31, 3.30, 3.29, 3.28, 3.27, 3.26, 3.25)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-12-15
  Note: EOL effective for scoped versions ['3.31', '3.30', '3.29', '3.28', '3.27', '3.26', '3.25']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **cassandra** — CVE-2015-0225 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-04-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2018-8016 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2020-13946 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2020-17516 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-02-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2021-44521 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2023-30601 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-05-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2024-27137 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-02-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2025-23015 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-02-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2025-24860 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-02-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — CVE-2025-26467 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-08-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cassandra** — apache-cassandra lifecycle: reached end-of-life (3.11, 3.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-09-05
  Note: EOL effective for scoped versions ['3.11', '3.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **celery** — CVE-2011-4356 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2011-12-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **celery** — CVE-2021-23727 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-12-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cert-manager** — CVE-2024-36537 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-07-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cert-manager** — CVE-2026-25518 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cert-manager** — CVE-2026-62290 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cert-manager** — cert-manager lifecycle: reached end-of-life (1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-05-19
  Note: EOL effective for scoped versions ['1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **cilium** — CVE-2022-29178 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-05-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2022-29179 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-05-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-27593 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-27594 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-27595 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-29002 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-04-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-30851 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-05-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-34242 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-06-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-39347 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-41332 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2023-41333 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-25630 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-02-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-25631 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-02-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-28248 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-28249 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-28250 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-28860 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-37307 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-06-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — CVE-2024-42487 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cilium** — cilium lifecycle: reached end-of-life (1.17, 1.16, 1.15, 1.14, 1.13)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-07-24
  Note: EOL effective for scoped versions ['1.17', '1.16', '1.15', '1.14', '1.13']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **clickhouse** — CVE-2018-14668 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2018-14669 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2018-14670 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2018-14671 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2018-14672 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2019-15024 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2019-16535 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2019-18657 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-10-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-42387 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-42388 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-42389 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-42390 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-42391 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-43304 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2021-43305 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2022-44010 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2022-44011 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — CVE-2023-47118 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **clickhouse** — clickhouse lifecycle: reached end-of-life (26.7, 26.6, 26.5, 26.4, 26.2, 26.1, 25.12, 25.11, 25.10, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-04-22
  Note: EOL effective for scoped versions ['26.7', '26.6', '26.5', '26.4', '26.2', '26.1', '25.12', '25.11', '25.10', '25.9', '25.8', '25.7', '25.6', '25.5', '25.4', '25.3', '25.2', '25.1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **consul** — consul lifecycle: reached end-of-life (1.22, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-11-24
  Note: EOL effective for scoped versions ['1.22', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8', '1.7', '1.6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **containerd** — CVE-2020-15157 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-10-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2020-15257 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-12-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2021-21334 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-03-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2021-32760 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-07-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2021-41103 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-10-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2021-43816 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-01-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2022-23471 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-12-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2022-23648 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2022-31030 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-06-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2023-25153 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-02-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2023-25173 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-02-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2024-25621 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-11-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2024-40635 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2025-47290 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-05-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2025-47291 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-05-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2025-64329 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-11-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — CVE-2026-53488 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **containerd** — containerd lifecycle: reached end-of-life (2.1, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2018-12-05
  Note: EOL effective for scoped versions ['2.1', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **coredns** — CVE-2022-2835 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2022-2837 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2023-28452 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-09-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2023-30464 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-09-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2025-47950 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-06-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2025-68151 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-26017 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-26018 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-32934 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-32936 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-33190 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-33489 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-35579 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-05-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-62299 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-62309 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **coredns** — CVE-2026-62994 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-07-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2007-2232 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2007-04-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2007-2233 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2007-04-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2022-23649 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2022-35929 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-08-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2022-36056 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2023-46737 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2024-29902 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2024-29903 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2026-22703 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2026-24122 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cosign** — CVE-2026-39395 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-04-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2010-0009 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-04-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2010-2234 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-08-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2010-2953 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-09-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2010-3854 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2011-02-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2012-5641 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2012-5649 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-05-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2012-5650 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2014-2668 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2016-8742 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-02-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2017-12635 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-11-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2017-12636 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-11-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2018-11769 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2018-14889 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-09-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2018-17188 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2018-8007 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2020-1955 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-05-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — CVE-2021-38295 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-10-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **couchdb** — apache-couchdb lifecycle: reached end-of-life (3.3, 3.2)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-09-20
  Note: EOL effective for scoped versions ['3.3', '3.2']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **cpython** — CVE-2013-7440 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-06-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2014-9365 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-12-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2015-20107 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-04-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2016-0772 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-09-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2016-5636 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-09-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2016-5699 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-09-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2017-1000158 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-11-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2018-1000117 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2020-15523 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2022-42919 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-11-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2023-33595 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-06-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2023-38898 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — CVE-2023-6507 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **cpython** — python lifecycle: ended active support (3.13, 3.12, 3.11)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-04-01
  Note: active support ended: review support posture
- **cpython** — python lifecycle: reached end-of-life (3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 2.7, 3.1, 3.0, 2.6)
  Status: EXPIRED · Announced: Unknown · Effective: 2009-06-27
  Note: EOL effective for scoped versions ['3.10', '3.9', '3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '2.7', '3.1', '3.0', '2.6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **crossplane** — CVE-2023-27484 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **crossplane** — CVE-2023-37900 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **crossplane** — CVE-2023-38495 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2007-0404 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2007-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2007-0405 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2007-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2007-5712 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2007-10-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2007-5828 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2007-11-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2008-2302 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2008-05-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2008-3909 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2008-09-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2009-2659 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2009-08-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2009-3695 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2009-10-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2010-3082 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2010-09-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2010-4534 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-01-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2010-4535 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-01-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-0696 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-02-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-0697 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-02-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-0698 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-02-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-4136 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-4137 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-4138 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-4139 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2011-4140 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2011-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — CVE-2012-3442 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2012-07-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)
  Status: EXPIRED · Announced: Unknown · Effective: 2013-02-26
  Note: EOL effective for scoped versions ['5.1', '5.0', '4.2', '4.1', '4.0', '3.2', '3.1', '3.0', '2.2', '2.1', '2.0', '1.11', '1.10', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **elasticsearch** — CVE-2014-6439 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-10-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **elasticsearch** — CVE-2015-3337 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-05-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **elasticsearch** — CVE-2015-4165 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-08-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **elasticsearch** — CVE-2015-5377 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **elasticsearch** — CVE-2015-5531 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-08-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **elasticsearch** — CVE-2018-3826 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-09-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **elasticsearch** — elasticsearch lifecycle: reached end-of-life (9.3, 9.2, 9.1, 8.18, 9.0, 8.17, 8.16, 7, 6)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-02-10
  Note: EOL effective for scoped versions ['9.3', '9.2', '9.1', '8.18', '9.0', '8.17', '8.16', '7', '6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **envoy** — CVE-2019-15225 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-15226 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-10-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-18801 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-18802 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-18836 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-11-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-18838 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-7676 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-02-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-7677 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-02-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-7678 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-02-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-9900 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2019-9901 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2020-11767 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2020-8659 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-03-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2020-8660 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-03-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2020-8661 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-03-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — CVE-2020-8664 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-03-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **envoy** — envoy lifecycle: reached end-of-life (1.36, 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2016-11-30
  Note: EOL effective for scoped versions ['1.36', '1.35', '1.34', '1.33', '1.32', '1.31', '1.30', '1.29', '1.28', '1.27', '1.26', '1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **etcd** — CVE-2018-1098 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-04-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2018-1099 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-04-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2018-16886 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2020-15106 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-08-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2020-15112 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-08-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2020-15113 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-08-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2020-15114 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-08-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2020-15115 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-08-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2021-28235 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-04-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2022-34038 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — CVE-2023-32082 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-05-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **etcd** — etcd lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2017-01-20
  Note: EOL effective for scoped versions ['3.4', '3.3', '3.2', '3.1', '3.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **express** — express lifecycle: reached end-of-life (3, 2, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2011-03-01
  Note: EOL effective for scoped versions ['3', '2', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **falco** — CVE-2019-8339 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-05-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **falco** — CVE-2021-33505 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-07-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **fastapi** — CVE-2021-32677 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2021-06-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **flask** — CVE-2018-1000656 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **flask** — CVE-2019-1010083 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **flux** — flux lifecycle: reached end-of-life (2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.25)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-11-02
  Note: EOL effective for scoped versions ['2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.25']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **go** — go lifecycle: reached end-of-life (1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-02-25
  Note: EOL effective for scoped versions ['1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **gradle** — CVE-2016-6199 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-02-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **gradle** — CVE-2019-11065 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **gradle** — CVE-2019-15052 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **gradle** — CVE-2019-16370 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-09-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **gradle** — gradle lifecycle: ended active support (9, 8)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-07-31
  Note: active support ended: review support posture
- **gradle** — gradle lifecycle: reached end-of-life (7, 6, 5, 4, 3, 2, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2014-07-01
  Note: EOL effective for scoped versions ['7', '6', '5', '4', '3', '2', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **grafana** — CVE-2018-1000816 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2018-12099 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2018-15727 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2018-18623 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-06-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2018-18624 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-06-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2018-19039 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2019-13068 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-06-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2019-15043 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-09-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2019-15635 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-09-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2020-12052 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2020-12245 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2020-12458 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2020-12459 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — CVE-2020-13430 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-05-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **grafana** — grafana lifecycle: reached end-of-life (12.3, 12.2, 12.1, 12.0, 11.6, 11.5, 11.4, 11.3, 11.2, 11.1, 11.0, 10.4, 10.3, 10.2, 10.1, 10.0, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8, 7, 6)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-06-08
  Note: EOL effective for scoped versions ['12.3', '12.2', '12.1', '12.0', '11.6', '11.5', '11.4', '11.3', '11.2', '11.1', '11.0', '10.4', '10.3', '10.2', '10.1', '10.0', '9.5', '9.4', '9.3', '9.2', '9.1', '9.0', '8', '7', '6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **haproxy** — CVE-2012-2942 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-05-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2013-1912 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2013-2175 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-08-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2014-6269 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-09-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2015-3281 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-07-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2016-2102 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-08-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2016-5360 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-06-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2018-10184 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-05-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2018-11469 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-05-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2018-14645 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-09-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2018-20102 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2018-20103 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2018-20615 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-03-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2019-11323 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-05-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2019-14241 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2019-18277 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-10-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2019-19330 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-11-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — CVE-2019-8953 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-02-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **haproxy** — haproxy lifecycle: reached end-of-life (3.1, 2.9, 2.7, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2001-12-30
  Note: EOL effective for scoped versions ['3.1', '2.9', '2.7', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **helm** — CVE-2019-1000008 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-02-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2019-1010275 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2019-18658 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-11-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2020-11013 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2020-15184 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2020-15185 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2020-15186 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **helm** — CVE-2020-4053 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-06-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **influxdb** — CVE-2018-17572 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-03-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **influxdb** — CVE-2019-10329 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-05-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **influxdb** — CVE-2019-20933 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-11-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **influxdb** — CVE-2022-36640 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **influxdb** — influxdb lifecycle: reached end-of-life (3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-06-25
  Note: EOL effective for scoped versions ['3.9', '3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **istio** — CVE-2019-12243 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-06-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2019-12995 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-06-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2019-14993 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-08-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2019-18817 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-11-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2019-25014 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-01-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2020-10739 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-06-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2020-11767 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2020-16844 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2020-8595 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-02-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2020-8843 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-02-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2021-31920 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-05-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2021-31921 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-06-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2021-34824 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-06-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2021-39155 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-08-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2021-39156 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-08-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2022-21679 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-01-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2022-21701 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-01-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — CVE-2022-23635 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **istio** — istio lifecycle: reached end-of-life (1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-02-25
  Note: EOL effective for scoped versions ['1.29', '1.28', '1.27', '1.26', '1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8', '1.7']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **itext** — CVE-2017-9096 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-11-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **itext** — CVE-2021-43113 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-12-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **itext** — CVE-2022-24196 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **itext** — CVE-2022-24197 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **itext** — CVE-2022-24198 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **itext** — CVE-2023-6298 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **itext** — CVE-2023-6299 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jaeger** — CVE-2020-10750 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-06-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2011-4344 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2011-12-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2012-0324 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-03-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2012-0325 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-03-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2012-6072 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-02-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2012-6073 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-02-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2012-6074 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-02-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-0158 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-02-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-0327 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-03-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-0328 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-03-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-0329 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-03-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-0330 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-03-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-0331 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-03-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-2033 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2013-5573 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-12-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2014-2059 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — CVE-2014-2067 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **jenkins** — jenkins lifecycle: reached end-of-life (2.555, 2.541, 2.528, 2.516, 2.504, 2.492, 2.479, 2.462, 2.452, 2.440, 2.426, 2.414, 2.401, 2.387, 2.375, 2.361, 2.346)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-09-07
  Note: EOL effective for scoped versions ['2.555', '2.541', '2.528', '2.516', '2.504', '2.492', '2.479', '2.462', '2.452', '2.440', '2.426', '2.414', '2.401', '2.387', '2.375', '2.361', '2.346']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **junit** — CVE-2018-1000056 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-02-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **junit** — CVE-2018-1000411 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **junit** — CVE-2022-34176 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-06-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **junit** — CVE-2022-45380 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-11-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **junit** — CVE-2023-25761 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-02-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — CVE-2017-12610 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — CVE-2018-1288 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — CVE-2018-17196 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — CVE-2019-12399 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-01-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — CVE-2021-38153 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-09-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — CVE-2022-34917 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kafka** — apache-kafka lifecycle: reached end-of-life (3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.1, 1.0, 0.11, 0.10, 0.9, 0.8, 0.7)
  Status: EXPIRED · Announced: Unknown · Effective: 2013-12-03
  Note: EOL effective for scoped versions ['3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.8', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.1', '1.0', '0.11', '0.10', '0.9', '0.8', '0.7']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **keycloak** — CVE-2014-3651 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-12-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2014-3709 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2016-8609 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2016-8629 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-12158 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-12159 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-12160 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-12161 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-02-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-2582 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-2585 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2017-2646 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2018-10894 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2018-10912 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2018-14637 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-11-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2018-14655 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2018-14657 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — CVE-2018-14658 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **keycloak** — keycloak lifecycle: reached end-of-life (26.7, 26.6, 26.5, 26.4, 26.3, 26.2, 26.1, 26.0, 25.0, 24.0, 23.0, 22.0, 21.1, 21.0, 20.0, 19.0, 18.0, 17.0, 16.1, 16.0, 15.1, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-07-22
  Note: EOL effective for scoped versions ['26.7', '26.6', '26.5', '26.4', '26.3', '26.2', '26.1', '26.0', '25.0', '24.0', '23.0', '22.0', '21.1', '21.0', '20.0', '19.0', '18.0', '17.0', '16.1', '16.0', '15.1', '15.0', '14.0', '13.0', '12.0', '11.0', '10.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **kubernetes** — CVE-2015-7528 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-04-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2015-7561 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-08-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2016-1905 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2016-7075 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-09-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2017-1000056 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-07-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2017-1002100 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-09-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2017-1002101 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2017-1002102 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2018-1000187 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2018-1002100 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2018-1002101 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — CVE-2018-1999040 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kubernetes** — kubernetes lifecycle: reached end-of-life (1.34, 1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-08-04
  Note: EOL effective for scoped versions ['1.34', '1.33', '1.32', '1.31', '1.30', '1.29', '1.28', '1.27', '1.26', '1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **kyverno** — CVE-2022-47633 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-33191 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-05-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-34091 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-06-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-42813 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-42814 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-42815 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-42816 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2023-47630 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2024-48921 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-10-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2025-29778 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2025-46342 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-04-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2025-47281 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-07-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2026-22039 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2026-23881 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2026-40868 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-04-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — CVE-2026-4789 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **kyverno** — kyverno lifecycle: reached end-of-life (1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-11-10
  Note: EOL effective for scoped versions ['1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **langchain** — CVE-2023-29374 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-04-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-32786 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-34540 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-06-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-34541 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-06-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-36095 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-36188 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-36189 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-36258 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-36281 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-38860 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-38896 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-39631 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-39659 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2023-46229 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2024-1455 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2024-2057 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2024-28088 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **langchain** — CVE-2024-3571 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **linkerd** — CVE-2025-43915 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-05-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **loki** — CVE-2021-36156 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-08-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-2122 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-06-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-4414 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-01-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-5611 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-12-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-5612 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-12-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-5613 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-12-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-5614 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-12-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-5615 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-12-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2012-5627 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2013-1861 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-03-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2014-0001 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-01-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0505 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0546 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0596 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0597 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0598 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0600 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0606 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0608 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — CVE-2016-0609 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — mariadb lifecycle: reached end-of-life (12.2, 12.1, 12.0, 11.7, 11.6, 11.5, 11.3, 11.2, 11.1, 11.0, 10.10, 10.9, 10.8, 10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 5.5, 5.3, 5.2, 5.1)
  Status: EXPIRED · Announced: Unknown · Effective: 2015-02-01
  Note: EOL effective for scoped versions ['12.2', '12.1', '12.0', '11.7', '11.6', '11.5', '11.3', '11.2', '11.1', '11.0', '10.10', '10.9', '10.8', '10.7', '10.6', '10.5', '10.4', '10.3', '10.2', '10.1', '10.0', '5.5', '5.3', '5.2', '5.1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **maven** — CVE-2013-0253 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-04-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **maven** — CVE-2017-1000397 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-01-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **maven** — CVE-2019-10358 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **maven** — CVE-2019-16549 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **maven** — CVE-2019-16550 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **maven** — CVE-2019-9843 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-06-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **maven** — apache-maven lifecycle: reached end-of-life (3.8, 3.6, 3.5, 3.3, 3.2, 3.1, 3.0, 2, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2013-06-28
  Note: EOL effective for scoped versions ['3.8', '3.6', '3.5', '3.3', '3.2', '3.1', '3.0', '2', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **memcached** — CVE-2009-1255 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-04-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2009-1494 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-04-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2009-2415 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-08-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2010-1152 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-04-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2011-4971 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-12-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2013-0179 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-01-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2013-7239 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-01-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2013-7290 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-01-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2013-7291 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-01-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2016-8704 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-01-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — CVE-2016-8705 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-01-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **memcached** — memcached lifecycle: reached end-of-life (1.5, 1.4)
  Status: EXPIRED · Announced: Unknown · Effective: 2017-07-21
  Note: EOL effective for scoped versions ['1.5', '1.4']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **minio** — CVE-2018-1000538 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **minio** — CVE-2020-11012 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-04-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **minio** — CVE-2021-21287 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-02-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **minio** — CVE-2021-21362 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-03-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **minio** — CVE-2021-21390 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-03-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2012-6619 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2013-1892 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2013-2132 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2013-3969 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2013-4650 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-07-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2014-3971 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-12-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2014-8180 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-06-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2015-1609 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-03-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2016-3104 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-04-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2016-6494 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-10-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2017-14227 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-09-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2017-15535 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-11-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — CVE-2017-2665 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mongodb** — mongodb lifecycle: reached end-of-life (8.2, 8.1, 7.3, 7.2, 7.1, 6.3, 6.2, 6.1, 6.0, 5.3, 5.2, 5.1, 5.0, 4.4, 4.2, 4.0, 3.6, 3.4, 3.2, 3.0, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2010-08-31
  Note: EOL effective for scoped versions ['8.2', '8.1', '7.3', '7.2', '7.1', '6.3', '6.2', '6.1', '6.0', '5.3', '5.2', '5.1', '5.0', '4.4', '4.2', '4.0', '3.6', '3.4', '3.2', '3.0', '2.6', '2.4', '2.2', '2.0', '1.8', '1.6', '1.4', '1.2', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **mysql** — CVE-1999-1188 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 1998-12-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2000-0045 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-01-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2000-0148 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-02-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2000-0981 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-12-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2001-0407 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-06-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2001-1255 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-10-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2001-1274 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-01-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2001-1275 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-01-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2001-1453 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-02-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2001-1454 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-02-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2002-0969 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-10-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — CVE-2002-1373 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mysql** — mysql lifecycle: reached end-of-life (26.7, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.3, 8.2, 8.1, 8.0, 5.7, 5.6, 5.5, 5.1, 5.0, 4.1, 4.0, 3.23)
  Status: EXPIRED · Announced: Unknown · Effective: 2006-12-31
  Note: EOL effective for scoped versions ['26.7', '9.6', '9.5', '9.4', '9.3', '9.2', '9.1', '9.0', '8.3', '8.2', '8.1', '8.0', '5.7', '5.6', '5.5', '5.1', '5.0', '4.1', '4.0', '3.23']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **nats** — CVE-2019-13126 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2020-26521 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-11-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2020-26892 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-11-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2020-28466 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-03-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2021-3127 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-03-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2022-24450 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2022-26652 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2022-28357 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2023-46129 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2023-47090 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-27571 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-27889 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-29785 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-33215 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-33216 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-33217 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nats** — CVE-2026-33218 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2013-7259 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-04-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2018-18389 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-10-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2021-34371 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-08-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2024-34517 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-05-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2026-1337 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2026-1471 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2026-1497 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — CVE-2026-1524 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **neo4j** — neo4j lifecycle: reached end-of-life (2026.08, 2026.07, 2026.06, 2026.05, 2026.04, 2026.03, 2026.02, 2026.01, 2025.12, 2025.11, 2025.10, 2025.09, 2025.08, 2025.07, 2025.06, 2025.05, 2025.04, 2025.03, 2025.02, 2025.01, 5.25, 5.24, 5.23, 5.22, 5.21, 5.20, 5.19, 5.18, 5.17, 5.16, 5.15, 5.14, 5.13, 5.12, 5.11, 5.10, 5.9, 5.8, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.4, 4.3, 4.2, 4.1, 4.0, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2011-08-23
  Note: EOL effective for scoped versions ['2026.08', '2026.07', '2026.06', '2026.05', '2026.04', '2026.03', '2026.02', '2026.01', '2025.12', '2025.11', '2025.10', '2025.09', '2025.08', '2025.07', '2025.06', '2025.05', '2025.04', '2025.03', '2025.02', '2025.01', '5.25', '5.24', '5.23', '5.22', '5.21', '5.20', '5.19', '5.18', '5.17', '5.16', '5.15', '5.14', '5.13', '5.12', '5.11', '5.10', '5.9', '5.8', '5.7', '5.6', '5.5', '5.4', '5.3', '5.2', '5.1', '4.4', '4.3', '4.2', '4.1', '4.0', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.3', '2.2', '2.1', '2.0', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **nginx** — CVE-2009-2629 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-09-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2009-3896 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-11-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2009-3898 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-11-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2009-4487 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-01-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2010-2263 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-06-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2010-2266 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2010-06-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2011-4315 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2011-12-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2011-4963 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-07-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2012-1180 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-04-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2012-2089 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2012-04-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2013-0337 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-10-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2013-2028 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-07-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2013-2070 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-07-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2013-4547 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-11-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2014-0088 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-04-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2014-0133 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-03-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2014-3556 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-12-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2014-3616 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2014-12-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — CVE-2016-0742 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nginx** — nginx lifecycle: reached end-of-life (1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2012-04-23
  Note: EOL effective for scoped versions ['1.29', '1.28', '1.27', '1.26', '1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **nodejs** — CVE-2019-15606 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-02-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **nodejs** — nodejs lifecycle: ended active support (24, 22)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-10-21
  Note: active support ended: review support posture
- **nodejs** — nodejs lifecycle: reached end-of-life (25, 23, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2016-06-30
  Note: EOL effective for scoped versions ['25', '23', '21', '20', '19', '18', '17', '16', '15', '14', '13', '12', '11', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **numpy** — CVE-2014-1858 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-01-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2014-1859 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-01-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2017-12852 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-08-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2019-6446 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-01-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2021-33430 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-12-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2021-34141 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-12-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2021-41495 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-12-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — CVE-2021-41496 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-12-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **numpy** — numpy lifecycle: reached end-of-life (2.1, 2.0, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-01-07
  Note: EOL effective for scoped versions ['2.1', '2.0', '1.26', '1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **ollama** — CVE-2024-12055 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-28224 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-37032 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-05-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-39719 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-10-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-39720 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-10-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-39721 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-10-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-39722 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-10-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-45436 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-08-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2024-8063 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-0312 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-0315 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-0317 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-15514 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-1975 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-05-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-44779 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-08-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-51471 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-07-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-63389 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-66959 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ollama** — CVE-2025-66960 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-01-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-1999-0428 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 1999-03-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2000-0535 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-06-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2001-1141 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-07-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2002-0655 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-08-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2002-0656 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-08-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2002-0657 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-08-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2002-0659 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-08-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2002-1568 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-11-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0078 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-03-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0131 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-03-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0147 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-03-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0543 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-11-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0544 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-11-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0545 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-11-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2003-0851 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-12-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2004-0079 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2004-11-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2004-0081 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2004-11-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — CVE-2004-0112 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2004-11-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **openssl** — openssl lifecycle: reached end-of-life (3.6, 3.4, 3.3, 3.2, 3.1, 3.0, 1.1.1, 1.1.0, 1.0.2, 1.0.1, 1.0.0, 0.9.8)
  Status: EXPIRED · Announced: Unknown · Effective: 2015-12-31
  Note: EOL effective for scoped versions ['3.6', '3.4', '3.3', '3.2', '3.1', '3.0', '1.1.1', '1.1.0', '1.0.2', '1.0.1', '1.0.0', '0.9.8']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **opentelemetry** — CVE-2023-43810 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2023-45142 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2023-47108 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-11-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2025-58460 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-09-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2026-24051 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2026-29181 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-04-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2026-39882 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-04-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentelemetry** — CVE-2026-39883 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-04-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **opentofu** — opentofu lifecycle: reached end-of-life (1.11, 1.10, 1.9, 1.8, 1.7, 1.6)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-01-09
  Note: EOL effective for scoped versions ['1.11', '1.10', '1.9', '1.8', '1.7', '1.6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **pandas** — CVE-2020-13091 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-05-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-1999-0058 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 1997-04-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-1999-0068 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 1997-10-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-1999-0238 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 1997-08-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-2000-0059 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-01-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-2000-0860 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-11-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-2000-0967 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2000-12-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-2001-0108 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — CVE-2001-1385 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-01-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **php** — php lifecycle: ended active support (8.3, 8.2)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-12-31
  Note: active support ended: review support posture
- **php** — php lifecycle: reached end-of-life (8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.4, 5.0, 4.3, 4.2, 4.1, 4.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2001-06-23
  Note: EOL effective for scoped versions ['8.1', '8.0', '7.4', '7.3', '7.2', '7.1', '7.0', '5.6', '5.5', '5.4', '5.3', '5.2', '5.1', '4.4', '5.0', '4.3', '4.2', '4.1', '4.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **postgresql** — CVE-1999-0862 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 1999-12-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2000-1199 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2001-08-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-0802 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-08-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-0972 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-09-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1397 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-01-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1398 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-01-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1399 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-01-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1400 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-01-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1401 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-01-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1402 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-01-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1642 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-10-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2002-1657 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-12-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2003-0901 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2003-11-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2004-0547 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2004-08-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — CVE-2005-0245 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2005-02-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **postgresql** — postgresql lifecycle: reached end-of-life (13, 12, 11, 10, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.4, 8.3, 8.2, 8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 6.5, 6.4, 6.3, 6.2, 6.1, 6.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2003-03-01
  Note: EOL effective for scoped versions ['13', '12', '11', '10', '9.6', '9.5', '9.4', '9.3', '9.2', '9.1', '9.0', '8.4', '8.3', '8.2', '8.1', '8.0', '7.4', '7.3', '7.2', '7.1', '7.0', '6.5', '6.4', '6.3', '6.2', '6.1', '6.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **prometheus** — CVE-2002-1211 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2002-11-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **prometheus** — CVE-2019-3826 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-03-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **prometheus** — CVE-2021-29622 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-05-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **prometheus** — prometheus lifecycle: reached end-of-life (3.14, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.55, 2.54, 2.53, 2.52, 2.51, 2.50, 2.49, 2.48, 2.47, 2.46, 2.45, 2.44, 2.43, 2.42, 2.41, 2.40, 2.39, 2.38, 2.37, 2.36)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-07-11
  Note: EOL effective for scoped versions ['3.14', '3.12', '3.11', '3.10', '3.9', '3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.55', '2.54', '2.53', '2.52', '2.51', '2.50', '2.49', '2.48', '2.47', '2.46', '2.45', '2.44', '2.43', '2.42', '2.41', '2.40', '2.39', '2.38', '2.37', '2.36']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **pulsar** — CVE-2021-22160 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-05-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2021-41571 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2022-24280 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2022-33681 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2022-33682 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2022-33683 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-09-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2022-33684 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-11-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2022-34321 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2023-30428 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2023-30429 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2023-31007 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2023-37544 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2023-37579 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2023-51437 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-02-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2024-27135 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2024-27317 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — CVE-2024-27894 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pulsar** — apache-pulsar lifecycle: reached end-of-life (4.2, 4.1, 4.0, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-01-15
  Note: EOL effective for scoped versions ['4.2', '4.1', '4.0', '3.3', '3.2', '3.1', '3.0', '2.11', '2.10', '2.9', '2.8', '2.7', '2.6', '2.5']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **pytorch** — CVE-2022-45907 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-11-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2024-31580 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2024-31583 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2024-31584 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2024-48063 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-10-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2025-2148 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2025-2149 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **pytorch** — CVE-2025-2953 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-03-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **qdrant** — CVE-2023-38975 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-08-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **qdrant** — CVE-2024-2221 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **qdrant** — CVE-2024-3078 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **qdrant** — CVE-2024-3584 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-05-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **qdrant** — CVE-2024-3829 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-06-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **qdrant** — CVE-2026-25628 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2014-9494 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-01-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2014-9568 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-02-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2015-8786 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-12-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2016-0929 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-09-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2016-9877 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-12-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2017-4965 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-06-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2017-4966 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-06-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2017-4967 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-06-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2018-1279 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2019-11281 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-10-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — CVE-2019-11291 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-11-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rabbitmq** — rabbitmq lifecycle: reached end-of-life (4.2, 4.1, 4.0, 3.13, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2013-11-30
  Note: EOL effective for scoped versions ['4.2', '4.1', '4.0', '3.13', '3.12', '3.11', '3.10', '3.9', '3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **react** — CVE-2018-6341 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-12-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **react** — react lifecycle: ended active support (19, 18, 17, 16, 15)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-10-14
  Note: active support ended: review support posture
- **redis** — CVE-2013-7458 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-08-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — CVE-2015-4335 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-06-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — CVE-2015-8080 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-04-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — CVE-2016-10517 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — CVE-2016-8339 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-10-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — CVE-2017-15047 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — CVE-2018-12453 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-06-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis** — redis lifecycle: ended active support (8.10, 8.8, 8.6, 8.4, 8.2, 8.0, 7.4, 7.2, 6.2)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-04-27
  Note: active support ended: review support posture
- **redis** — redis lifecycle: reached end-of-life (7.0, 6.0, 5.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-04-27
  Note: EOL effective for scoped versions ['7.0', '6.0', '5.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **redis-py** — CVE-2023-28858 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2023-03-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redis-py** — CVE-2023-28859 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2023-03-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redpanda** — CVE-2023-24619 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-02-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redpanda** — CVE-2023-30450 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-04-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **redpanda** — CVE-2023-50976 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2004-0755 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2004-10-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2004-0983 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2005-03-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2005-1992 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2005-06-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2005-2337 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2005-10-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2006-1931 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2006-04-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2006-3694 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2006-07-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2006-5467 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2006-10-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2006-6303 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2006-12-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2007-5162 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2007-10-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — CVE-2007-5770 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2007-11-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **ruby** — ruby lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0.0, 1.9.3)
  Status: EXPIRED · Announced: Unknown · Effective: 2015-02-23
  Note: EOL effective for scoped versions ['3.2', '3.1', '3.0', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0.0', '1.9.3']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **rust** — CVE-2018-1000622 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rust** — CVE-2018-1000657 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rust** — CVE-2018-1000810 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-10-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rust** — CVE-2019-1010299 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-07-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rust** — CVE-2019-12083 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-05-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **rust** — rust lifecycle: reached end-of-life (1.98, 1.97, 1.96, 1.95, 1.94, 1.93, 1.92, 1.91, 1.90, 1.89, 1.88, 1.87, 1.86, 1.85, 1.84, 1.83, 1.82, 1.81, 1.80, 1.79, 1.78, 1.77, 1.76, 1.75, 1.74, 1.73, 1.72, 1.71, 1.70, 1.69, 1.68, 1.67, 1.66, 1.65, 1.64, 1.63, 1.62, 1.61, 1.60, 1.59, 1.58, 1.57, 1.56, 1.55, 1.54, 1.53, 1.52, 1.51, 1.50, 1.49, 1.48, 1.47, 1.46, 1.45, 1.44, 1.43, 1.42, 1.41, 1.40, 1.39, 1.38, 1.37, 1.36, 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29)
  Status: EXPIRED · Announced: Unknown · Effective: 2018-10-26
  Note: EOL effective for scoped versions ['1.98', '1.97', '1.96', '1.95', '1.94', '1.93', '1.92', '1.91', '1.90', '1.89', '1.88', '1.87', '1.86', '1.85', '1.84', '1.83', '1.82', '1.81', '1.80', '1.79', '1.78', '1.77', '1.76', '1.75', '1.74', '1.73', '1.72', '1.71', '1.70', '1.69', '1.68', '1.67', '1.66', '1.65', '1.64', '1.63', '1.62', '1.61', '1.60', '1.59', '1.58', '1.57', '1.56', '1.55', '1.54', '1.53', '1.52', '1.51', '1.50', '1.49', '1.48', '1.47', '1.46', '1.45', '1.44', '1.43', '1.42', '1.41', '1.40', '1.39', '1.38', '1.37', '1.36', '1.35', '1.34', '1.33', '1.32', '1.31', '1.30', '1.29']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **solr** — CVE-2009-3821 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2009-10-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2012-6612 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-12-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2013-6397 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-12-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2013-6407 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-12-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2013-6408 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2013-12-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2014-3628 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-01-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2015-8795 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2015-8796 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2015-8797 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2017-12629 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2017-3163 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-08-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2017-7660 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-07-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — CVE-2017-9803 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-09-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **solr** — solr lifecycle: reached end-of-life (8, 7, 6, 5, 4, 3, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2017-10-24
  Note: EOL effective for scoped versions ['8', '7', '6', '5', '4', '3', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **spark** — CVE-2015-6303 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2015-09-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2016-1322 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2016-1323 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2016-1324 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-02-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2016-9177 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-11-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2017-12269 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2017-12612 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-09-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2017-7678 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2018-11770 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2018-1334 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2018-8024 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-07-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — CVE-2018-9159 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spark** — apache-spark lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0, 2.4, 2.3, 2.2, 2.1, 2.0, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2014-09-03
  Note: EOL effective for scoped versions ['3.4', '3.3', '3.2', '3.1', '3.0', '2.4', '2.3', '2.2', '2.1', '2.0', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **spring-boot** — CVE-2022-27772 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spring-boot** — CVE-2026-40976 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-04-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **spring-boot** — spring-boot lifecycle: reached end-of-life (3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.5)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-03-01
  Note: EOL effective for scoped versions ['3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.5']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **tensorflow** — CVE-2018-10055 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2018-21233 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-05-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2018-7575 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2018-7576 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2018-7577 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2018-8825 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2019-16778 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2019-9635 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-04-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15190 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15191 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15192 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15193 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15194 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15195 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15196 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15197 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15198 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15199 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-15200 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-09-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tensorflow** — CVE-2020-5215 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-01-28 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **terraform** — CVE-2018-9057 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-03-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **terraform** — CVE-2019-19316 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-12-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **terraform** — CVE-2021-36230 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-07-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **terraform** — CVE-2023-4782 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-09-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **terraform** — terraform lifecycle: reached end-of-life (1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-05-18
  Note: EOL effective for scoped versions ['1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **tidb** — CVE-2022-31011 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-05-31 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tidb** — CVE-2022-34969 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-08-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tidb** — CVE-2024-33809 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-05-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tidb** — CVE-2024-35618 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-05-24 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tidb** — CVE-2024-41433 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-09-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **tidb** — CVE-2024-41434 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-09-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **timescaledb** — CVE-2022-24128 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-03-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **timescaledb** — CVE-2023-25149 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-02-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **timescaledb** — CVE-2026-29089 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-03-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2018-15598 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-08-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2019-12452 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-05-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2019-20894 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-02 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2020-15129 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-07-30 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2020-9321 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2020-03-16 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2021-27375 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-02-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2021-32813 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-08-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2022-23469 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-12-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2022-23632 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-02-17 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2022-39271 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-10-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2022-46153 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-12-08 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2023-29013 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-04-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2023-47106 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2023-47124 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2023-47633 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2024-28869 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-04-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2024-39321 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-07-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2024-45410 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-09-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2024-52003 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-11-29 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — CVE-2025-32431 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-04-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **traefik** — traefik lifecycle: reached end-of-life (3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.7)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-12-11
  Note: EOL effective for scoped versions ['3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.11', '2.10', '2.9', '2.8', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.7']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **transformers** — CVE-2024-11392 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-11-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2024-11393 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-11-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2024-11394 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-11-22 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-14920 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-14921 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-14924 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-14926 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-14927 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-14928 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-12-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-3263 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-07-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-3264 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-07-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-3777 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-07-07 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-3933 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-07-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-5197 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-08-06 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-6051 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-09-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **transformers** — CVE-2025-6638 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-09-12 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **trivy** — CVE-2026-54448 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-06-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **trivy** — CVE-2026-55092 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-06-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **valkey** — CVE-2025-67733 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **valkey** — CVE-2026-21863 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **valkey** — CVE-2026-27623 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vite** — CVE-2022-35204 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2022-08-18 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vite** — CVE-2023-34092 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-06-01 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vite** — CVE-2023-49293 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-12-04 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vite** — CVE-2024-23331 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-01-19 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vite** — CVE-2025-24010 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2025-01-20 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vitess** — CVE-2023-29194 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-04-14 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vitess** — CVE-2023-29195 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-05-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vitess** — CVE-2026-27965 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vitess** — CVE-2026-27969 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-26 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **vitess** — vitess lifecycle: reached end-of-life (22, 21, 20, 19, 18, 17, 16, 15, 14, 13)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-02-22
  Note: EOL effective for scoped versions ['22', '21', '20', '19', '18', '17', '16', '15', '14', '13']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **vue** — vue lifecycle: reached end-of-life (3.4, 3.3, 2.7, 3.2, 3.1, 3.0, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2016-11-22
  Note: EOL effective for scoped versions ['3.4', '3.3', '2.7', '3.2', '3.1', '3.0', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **webpack** — CVE-2023-28154 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-03-13 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **webpack** — CVE-2024-43788 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-08-27 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **webpack** — CVE-2025-68157 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **webpack** — CVE-2025-68458 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-02-05 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — CVE-2016-5017 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2016-09-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — CVE-2017-5637 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2017-10-10 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — CVE-2018-8012 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2018-05-21 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — CVE-2019-0201 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2019-05-23 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — CVE-2023-44981 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2023-10-11 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — CVE-2024-23944 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2024-03-15 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **zookeeper** — zookeeper lifecycle: reached end-of-life (3.7, 3.6, 3.5, 3.4)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-06-01
  Note: EOL effective for scoped versions ['3.7', '3.6', '3.5', '3.4']: evidence and scope justify action-oriented framing (applies only if you run these versions)

### B. All current findings

#### airflow

### **airflow** — apache-airflow 3.3 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.3`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/apache-airflow

#### bitnami

### **bitnami** — bitnami mainline is latest-only; versioned tags live in bitnamilegacy

Category: Distribution · Evidence confidence: UNVERIFIED · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: distribution model change with high significance: action-oriented framing justified

Investigate: Confirm whether this is a removal or a rename (pull/mirror check); review pinned references.

### **bitnami** — bitnamisecure/redis publishes latest-only tags

Category: Distribution · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `docker.io/bitnamisecure/redis`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: distribution observation without high significance: watch

Investigate: No action; track the repository for further changes.

#### clickhouse

### **clickhouse** — clickhouse 26.3 EOL approaching (2027-03-26)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `26.3`

Announcement: Unknown

Effective: 2027-03-26 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/clickhouse

#### containerd

### **containerd** — containerd lifecycle: approaching end-of-life (2.2, 2.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `2.2`, `2.0`

Announcement: Unknown

Effective: 2026-11-06 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/containerd

### **containerd** — containerd 2.0 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `2.0`

Announcement: Unknown

Effective: 2025-11-07 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/containerd

#### django

### **django** — django 6.0 EOL approaching (2027-04-30)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `6.0`

Announcement: Unknown

Effective: 2027-04-30 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/django

### **django** — django lifecycle: ended active support (6.0, 5.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `6.0`, `5.2`

Announcement: Unknown

Effective: 2025-12-03 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/django

#### envoy

### **envoy** — envoy lifecycle: approaching end-of-life (1.38, 1.37)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.38`, `1.37`

Announcement: Unknown

Effective: 2027-01-13 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/envoy

#### grafana

### **grafana** — grafana lifecycle: ended active support (13.3, 13.2, 13.1, 13.0, 12.4)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `13.3`, `13.2`, `13.1`, `13.0`, `12.4`

Announcement: Unknown

Effective: 2026-04-17 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/grafana

### **grafana** — grafana lifecycle: approaching end-of-life (13.1, 13.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `13.1`, `13.0`

Announcement: Unknown

Effective: 2027-01-09 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/grafana

#### haproxy

### **haproxy** — haproxy lifecycle: approaching end-of-life (3.3, 2.6)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.3`, `2.6`

Announcement: Unknown

Effective: 2027-01-01 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/haproxy

#### istio

### **istio** — istio lifecycle: approaching end-of-life (1.31, 1.30)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.31`, `1.30`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/istio

#### jaeger

### **jaeger** — jaeger 1 is end-of-life

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1`

Announcement: Unknown

Effective: 2025-12-31 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: EOL effective for scoped versions `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Source: https://endoflife.date/jaeger

#### kubernetes

### **kubernetes** — kubernetes 1.35 EOL approaching (2027-02-28)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.35`

Announcement: Unknown

Effective: 2027-02-28 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/kubernetes

#### mariadb

### **mariadb** — mariadb 13.0 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `13.0`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/mariadb

#### minio

### **minio** — minio/minio is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/minio/minio

#### mysql

### **mysql** — mysql 26.10 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `26.10`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/mysql

#### nodejs

### **nodejs** — nodejs 22 EOL approaching (2027-04-30)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `22`

Announcement: Unknown

Effective: 2027-04-30 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/nodejs

#### numpy

### **numpy** — numpy 2.2 EOL approaching (2026-12-09)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `2.2`

Announcement: Unknown

Effective: 2026-12-09 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/numpy

#### php

### **php** — php 8.2 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `8.2`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/php

#### postgresql

### **postgresql** — postgresql 14 EOL approaching (2026-11-12)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `14`

Announcement: Unknown

Effective: 2026-11-12 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/postgresql

#### prometheus

### **prometheus** — prometheus 3.15 EOL approaching (2026-11-06)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.15`

Announcement: Unknown

Effective: 2026-11-06 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/prometheus

#### rabbitmq

### **rabbitmq** — rabbitmq 4.3 EOL approaching (2027-01-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.3`

Announcement: Unknown

Effective: 2027-01-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/rabbitmq

#### react-native-fbsdk

### **react-native-fbsdk** — facebookarchive/react-native-fbsdk is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/facebookarchive/react-native-fbsdk

#### redis

### **redis** — redis lifecycle: approaching end-of-life (8.0, 6.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `8.0`, `6.2`

Announcement: Unknown

Effective: 2026-12-01 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/redis

#### ruby

### **ruby** — ruby 3.3 EOL approaching (2027-03-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.3`

Announcement: Unknown

Effective: 2027-03-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/ruby

#### spark

### **spark** — apache-spark 4.0 EOL approaching (2026-11-23)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.0`

Announcement: Unknown

Effective: 2026-11-23 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/apache-spark

#### spring-boot

### **spring-boot** — spring-boot 4.0 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.0`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/spring-boot

#### timescaledb

### **timescaledb** — CVE-2026-70633 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Announcement: 2026-08-06 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Source: https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
Evidence:
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-dos-via-gorilla-compression-reverse-iterator

### **timescaledb** — CVE-2026-70634 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Announcement: 2026-08-06 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Source: https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
Evidence:
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-information-disclosure-via-dictionary-compression-reverse-iterator

### **timescaledb** — CVE-2026-70635 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Announcement: 2026-08-06 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Source: https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
Evidence:
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-dos-via-bulk-dictionary-decompression-negative-index

#### traefik

### **traefik** — traefik 3.7 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.7`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/traefik

#### vitess

### **vitess** — vitess lifecycle: approaching end-of-life (24, 23)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `24`, `23`

Announcement: Unknown

Effective: 2026-11-04 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/vitess

### **vitess** — CVE-2026-104252 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Announcement: 2026-10-13 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Source: https://github.com/vitessio/vitess/commit/3140c1846cd120db34f33b2083139b4ab638aed2
Evidence:
- https://github.com/vitessio/vitess/commit/976e1e0d78f9d29d02e5e31b4aa7e180648f08af
- https://github.com/vitessio/vitess/commit/c1ed96302e658190168c971afdac730cf70e43f7
- https://github.com/vitessio/vitess/pull/20255
- https://github.com/vitessio/vitess/pull/20273
- https://github.com/vitessio/vitess/pull/20274
- https://github.com/vitessio/vitess/releases/tag/v23.0.5
- https://github.com/vitessio/vitess/releases/tag/v24.0.2
- https://github.com/vitessio/vitess/security/advisories/GHSA-v75v-6fpf-gvw8

### **vitess** — CVE-2026-65959 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Announcement: 2026-08-18 (official)

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: Unknown

Status: NEW

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Source: https://github.com/vitessio/vitess/commit/4c58cd70edc6b03d61cb65842c342ac08341e64f
Evidence:
- https://github.com/vitessio/vitess/commit/657662e78bde1c82df680e9cc43a686d619f8094
- https://github.com/vitessio/vitess/commit/d929225a450027406687d27af8dca45620945ceb
- https://github.com/vitessio/vitess/security/advisories/GHSA-mhc4-g3wh-cw7m

#### zookeeper

### **zookeeper** — zookeeper lifecycle: ended active support (3.9, 3.8)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.9`, `3.8`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/zookeeper

#### angular

### **angular** — angular lifecycle: ended active support (21, 20)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `21`, `20`

Announcement: Unknown

Effective: 2025-11-19 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/angular

### **angular** — angular 20 EOL approaching (2026-11-28)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `20`

Announcement: Unknown

Effective: 2026-11-28 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/angular

#### consul

### **consul** — consul 1.21 EOL approaching (2027-04-30)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.21`

Announcement: Unknown

Effective: 2027-04-30 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/consul

#### opentofu

### **opentofu** — opentofu 1.12 EOL approaching (2027-02-01)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.12`

Announcement: Unknown

Effective: 2027-02-01 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/opentofu

#### vue

### **vue** — vue 3.5 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.5`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-11-01

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/vue

### C. Source references

Finding source distribution: endoflife.date 78.6%, NVD 11.9%, Registry 4.8%, GitHub 4.8%
Independent source families observed: 4 (across 4 recorded source labels).

### D. Data gaps and limitations

**Sources that did not answer.** For these projects the named source returned an error (rate limit, timeout, outage), so the absence of its findings is unknown, not a clean result:

- endoflife (4): cockroach, loki, nest, vault

No signals observed for: bitnami-redis-stack, boto3, capa, cockroach, crio, k9s, kustomize, nest, node-redis, opa, pytest, requests, serde, typescript, vault.

1225 related-but-unconfirmed or below-bar records held back (see `openpulse analyze` for the full stream).

### E. Notes

- Collectors: endoflife.date, GitHub releases + repo metadata, NVD, CISA KEV, Docker Hub.
- GitHub calls authenticated (5000 req/hr budget).
- NVD queried without API key (5 req/30s); misses degrade to gaps, not findings.
- Keyword-associated CVE records without identity evidence are held back, not narrated.
- Public intelligence describes project-level change; whether it affects YOUR dependencies needs a watchlist (`openpulse check`).
- Lead times are not published: no history key was given, so first detections cannot be shown to be unedited. Set OPENPULSE_HISTORY_KEY (see `openpulse history-key generate`).
