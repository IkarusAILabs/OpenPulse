# OpenPulse OSS Dependency Intelligence

## November 2026

In November 2026, OpenPulse identified 16 material upstream changes worth a software team's attention, including 7 non-lifecycle discoveries no lifecycle database records. Every item below names its evidence, its scope, and when it matters — and none of it speaks about your environment without a watchlist to prove it.

_Public report findings describe OSS ecosystem changes. They are not assertions that a particular customer's environment is affected._

## Executive Summary

OpenPulse detected 16 material upstream changes across 107 monitored projects in 2026-11. That includes 7 non-lifecycle discoveries — changes no lifecycle database records. 2 changes require attention now; no upcoming changes carry warning windows.

- Projects monitored: 107
- Material changes (action + review): 16
- Changes requiring attention: 2
- Upcoming changes with warning: 0
- Non-lifecycle discoveries: 7
- Evidence confidence: 0 CONFIRMED, 0 CORROBORATED, 39 EMERGING, 1 UNVERIFIED
- Background findings (effective over 12 months ago): 63
- Data gaps: 35 projects with no signals, 591 records held back
- What remains uncertain: 0 finding carriess unknown dates, 591 records were held back for weak evidence

## Top Changes

### 1. **vitess** — CVE-2026-104252 [AFFECTS_PACKAGE] tracked by nvd

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

### 2. **vitess** — CVE-2026-65959 [AFFECTS_PACKAGE] tracked by nvd

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

### 3. **bitnami** — bitnami mainline is latest-only; versioned tags live in bitnamilegacy

Category: Distribution · Evidence confidence: UNVERIFIED · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: distribution model change with high significance: action-oriented framing justified

Investigate: Confirm whether this is a removal or a rename (pull/mirror check); review pinned references.

### 4. **bitnami** — bitnamisecure/redis publishes latest-only tags

Category: Distribution · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `docker.io/bitnamisecure/redis`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: distribution observation without high significance: watch

Investigate: No action; track the repository for further changes.

### 5. **react** — facebook/react moved to react/react on GitHub

Category: Ownership · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: ownership move is a project-level identity fact, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/react/react

### 6. **minio** — minio/minio is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/minio/minio

### 7. **react-native-fbsdk** — facebookarchive/react-native-fbsdk is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/facebookarchive/react-native-fbsdk

### 8. **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `5.1`, `5.0`, `4.2`, `4.1`, `4.0`, `3.2`, `3.1`, `3.0`, `2.2`, `2.1`, `2.0`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`

Announcement: Unknown

Effective: 2013-02-26 (already effective)

First detected by OpenPulse: 2026-10-21

Last verified: 2026-10-30

Status: NEW

Why it matters: EOL effective for scoped versions `5.1`, `5.0`, `4.2`, `4.1`, `4.0`, `3.2`, `3.1`, `3.0`, `2.2`, `2.1`, `2.0`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Source: https://endoflife.date/django

### 9. **jaeger** — jaeger 1 is end-of-life

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1`

Announcement: Unknown

Effective: 2025-12-31 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: EOL effective for scoped versions `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Source: https://endoflife.date/jaeger

### 10. **airflow** — apache-airflow 3.3 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.3`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/apache-airflow

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

- **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)
  Scope: 5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **jaeger** — jaeger 1 is end-of-life
  Scope: 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

## Upcoming Changes

No upcoming changes with trustworthy dates this month.

## Changes by Category

| Category | Changes | Requiring attention |
|---|---|---|
| Security | 2 | 0 |
| Lifecycle | 33 | 2 |
| Distribution | 2 | 0 |
| Repository | 2 | 0 |
| Support | 0 | 0 |
| License | 0 | 0 |
| Ownership | 1 | 0 |
| Other | 0 | 0 |

## Evidence Quality

- CONFIRMED (0): official announcement from the source itself.
- CORROBORATED (0): confirmed by 2+ independent source families.
- EMERGING (39): single credible source.
- UNVERIFIED (1): weak or unconfirmed signal — never action-framed.

## What OpenPulse Watches

OpenPulse watches what can change underneath software dependencies: security disclosures, lifecycle and support ends, distribution and registry changes, repository archival, license and ownership changes. Findings above are grouped by these categories — not by CVE counts or EOL tables — because the question is always what changed, not how many records a database holds.

## Methodology

Findings rest on named sources with content hashes; confidence (CONFIRMED / CORROBORATED / EMERGING / UNVERIFIED) follows evidence strength, never match precision. Dependency identity is resolved before impact is assessed, and unknown scope stays unknown. Freshness states (NEW / UPCOMING / ACTIVE / RECENTLY_UPDATED / EXPIRED) derive from announcement, effective, detection, and verification dates — expired findings move to the Historical appendix, never deleted. Full model: `docs/METHODOLOGY.md`.

## What OpenPulse Added This Month

OpenPulse is designed to answer a question traditional dependency monitoring often does not answer: Something changed upstream. Does it affect what we depend on?

This month the report answers it with the findings below — detected upstream changes, explained in context, correlated across sources, attributed to dependency identity, with warning where dates allow. OpenPulse does not replace SCA, SBOM, vulnerability, or lifecycle databases — it is an intelligence layer across them.

### Upstream Change Detection

- Security (2): e.g. **vitess** — CVE-2026-104252 [AFFECTS_PACKAGE] tracked by nvd
- Lifecycle (33): e.g. **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)
- Distribution (2): e.g. **bitnami** — bitnami mainline is latest-only; versioned tags live in bitnamilegacy
- Repository (2): e.g. **minio** — minio/minio is archived on GitHub
- Ownership (1): e.g. **react** — facebook/react moved to react/react on GitHub

### Dependency Attribution

- Affected artifact: `docker.io/bitnamisecure/redis` — bitnamisecure/redis publishes latest-only tags
- Affected version: `5.1` — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)
- Related project: bitnami — bitnami mainline is latest-only; versioned tags live in bitnamilegacy
- `docker.io/bitnami/redis:<version>` resolves to the Bitnami distribution identity, not the upstream project.
docker.io/bitnami/redis is not docker.io/redis: namespace-aware resolution keeps distribution packaging apart from upstream code.
- Not affected: `latest`-tag consumers: latest-only publication continues; pinned version references need a migration plan.

### Evidence-backed Intelligence

- Confirmation level: strongest finding this month is EMERGING; full breakdown in Evidence Quality. No opaque risk scores.
- 4 independent source families across 49 supporting references.
- Scope established for 34/40 findings.
- Effective date known for 33/40 findings.

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
- Customer impact: “Does this affect my software?” — matched dependencies only.
- Early warning: “How much warning do I have?” — warning windows above.

## For Your Environment

This report describes open-source ecosystem intelligence. It does not establish that a specific customer environment is affected.

Dependency-aware impact requires a customer watchlist, inventory, or equivalent dependency context: public intelligence → dependency context (`openpulse check --watchlist <file>`) → affected dependency → actionable warning. Only that last step can speak about your environment.

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
- **calico** — calico lifecycle: reached end-of-life (3.31, 3.30, 3.29, 3.28, 3.27, 3.26, 3.25)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-12-15
  Note: EOL effective for scoped versions ['3.31', '3.30', '3.29', '3.28', '3.27', '3.26', '3.25']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **cassandra** — apache-cassandra lifecycle: reached end-of-life (3.11, 3.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-09-05
  Note: EOL effective for scoped versions ['3.11', '3.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **cert-manager** — cert-manager lifecycle: reached end-of-life (1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-05-19
  Note: EOL effective for scoped versions ['1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **cilium** — cilium lifecycle: reached end-of-life (1.17, 1.16, 1.15, 1.14, 1.13)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-07-24
  Note: EOL effective for scoped versions ['1.17', '1.16', '1.15', '1.14', '1.13']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **clickhouse** — clickhouse lifecycle: reached end-of-life (26.7, 26.6, 26.5, 26.4, 26.2, 26.1, 25.12, 25.11, 25.10, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-04-22
  Note: EOL effective for scoped versions ['26.7', '26.6', '26.5', '26.4', '26.2', '26.1', '25.12', '25.11', '25.10', '25.9', '25.8', '25.7', '25.6', '25.5', '25.4', '25.3', '25.2', '25.1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **consul** — consul lifecycle: reached end-of-life (1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6)
  Status: EXPIRED · Announced: Unknown · Effective: 2020-11-24
  Note: EOL effective for scoped versions ['1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8', '1.7', '1.6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **containerd** — containerd lifecycle: reached end-of-life (2.1, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2018-12-05
  Note: EOL effective for scoped versions ['2.1', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **couchdb** — apache-couchdb lifecycle: reached end-of-life (3.3, 3.2)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-09-20
  Note: EOL effective for scoped versions ['3.3', '3.2']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **elasticsearch** — elasticsearch lifecycle: reached end-of-life (9.3, 9.2, 9.1, 8.18, 9.0, 8.17, 8.16, 7, 6)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-02-10
  Note: EOL effective for scoped versions ['9.3', '9.2', '9.1', '8.18', '9.0', '8.17', '8.16', '7', '6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **fastapi** — CVE-2021-32677 [AFFECTS_PACKAGE] tracked by osv, nvd
  Status: EXPIRED · Announced: 2021-06-09 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **flux** — flux lifecycle: reached end-of-life (2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.25)
  Status: EXPIRED · Announced: Unknown · Effective: 2022-11-02
  Note: EOL effective for scoped versions ['2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.25']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **go** — go lifecycle: reached end-of-life (1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-02-25
  Note: EOL effective for scoped versions ['1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19', '1.18', '1.17', '1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **gradle** — gradle lifecycle: ended active support (9, 8)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-07-31
  Note: active support ended: review support posture
- **gradle** — gradle lifecycle: reached end-of-life (7, 6, 5, 4, 3, 2, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2014-07-01
  Note: EOL effective for scoped versions ['7', '6', '5', '4', '3', '2', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **grafana** — grafana lifecycle: reached end-of-life (12.3, 12.2, 12.1, 12.0, 11.6, 11.5, 11.4, 11.3, 11.2, 11.1, 11.0, 10.4, 10.3, 10.2, 10.1, 10.0, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8, 7, 6)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-06-08
  Note: EOL effective for scoped versions ['12.3', '12.2', '12.1', '12.0', '11.6', '11.5', '11.4', '11.3', '11.2', '11.1', '11.0', '10.4', '10.3', '10.2', '10.1', '10.0', '9.5', '9.4', '9.3', '9.2', '9.1', '9.0', '8', '7', '6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **haproxy** — haproxy lifecycle: reached end-of-life (3.1, 2.9, 2.7, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2001-12-30
  Note: EOL effective for scoped versions ['3.1', '2.9', '2.7', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **kyverno** — kyverno lifecycle: reached end-of-life (1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8)
  Status: EXPIRED · Announced: Unknown · Effective: 2023-11-10
  Note: EOL effective for scoped versions ['1.16', '1.15', '1.14', '1.13', '1.12', '1.11', '1.10', '1.9', '1.8']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **loki** — CVE-2021-36156 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2021-08-03 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **mariadb** — mariadb lifecycle: reached end-of-life (12.2, 12.1, 12.0, 11.7, 11.6, 11.5, 11.3, 11.2, 11.1, 11.0, 10.10, 10.9, 10.8, 10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 5.5, 5.3, 5.2, 5.1)
  Status: EXPIRED · Announced: Unknown · Effective: 2015-02-01
  Note: EOL effective for scoped versions ['12.2', '12.1', '12.0', '11.7', '11.6', '11.5', '11.3', '11.2', '11.1', '11.0', '10.10', '10.9', '10.8', '10.7', '10.6', '10.5', '10.4', '10.3', '10.2', '10.1', '10.0', '5.5', '5.3', '5.2', '5.1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **maven** — apache-maven lifecycle: reached end-of-life (3.8, 3.6, 3.5, 3.3, 3.2, 3.1, 3.0, 2, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2013-06-28
  Note: EOL effective for scoped versions ['3.8', '3.6', '3.5', '3.3', '3.2', '3.1', '3.0', '2', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **memcached** — memcached lifecycle: reached end-of-life (1.5, 1.4)
  Status: EXPIRED · Announced: Unknown · Effective: 2017-07-21
  Note: EOL effective for scoped versions ['1.5', '1.4']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **mysql** — mysql lifecycle: reached end-of-life (26.7, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.3, 8.2, 8.1, 8.0, 5.7, 5.6, 5.5)
  Status: EXPIRED · Announced: Unknown · Effective: 2018-12-31
  Note: EOL effective for scoped versions ['26.7', '9.6', '9.5', '9.4', '9.3', '9.2', '9.1', '9.0', '8.3', '8.2', '8.1', '8.0', '5.7', '5.6', '5.5']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **neo4j** — neo4j lifecycle: reached end-of-life (2026.08, 2026.07, 2026.06, 2026.05, 2026.04, 2026.03, 2026.02, 2026.01, 2025.12, 2025.11, 2025.10, 2025.09, 2025.08, 2025.07, 2025.06, 2025.05, 2025.04, 2025.03, 2025.02, 2025.01, 5.25, 5.24, 5.23, 5.22, 5.21, 5.20, 5.19, 5.18, 5.17, 5.16, 5.15, 5.14, 5.13, 5.12, 5.11, 5.10, 5.9, 5.8, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.4, 4.3, 4.2, 4.1, 4.0, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2011-08-23
  Note: EOL effective for scoped versions ['2026.08', '2026.07', '2026.06', '2026.05', '2026.04', '2026.03', '2026.02', '2026.01', '2025.12', '2025.11', '2025.10', '2025.09', '2025.08', '2025.07', '2025.06', '2025.05', '2025.04', '2025.03', '2025.02', '2025.01', '5.25', '5.24', '5.23', '5.22', '5.21', '5.20', '5.19', '5.18', '5.17', '5.16', '5.15', '5.14', '5.13', '5.12', '5.11', '5.10', '5.9', '5.8', '5.7', '5.6', '5.5', '5.4', '5.3', '5.2', '5.1', '4.4', '4.3', '4.2', '4.1', '4.0', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.3', '2.2', '2.1', '2.0', '1.9', '1.8', '1.7', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **openssl** — openssl lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0, 1.1.1, 1.1.0, 1.0.2, 1.0.1, 1.0.0, 0.9.8)
  Status: EXPIRED · Announced: Unknown · Effective: 2015-12-31
  Note: EOL effective for scoped versions ['3.4', '3.3', '3.2', '3.1', '3.0', '1.1.1', '1.1.0', '1.0.2', '1.0.1', '1.0.0', '0.9.8']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **opentofu** — opentofu lifecycle: reached end-of-life (1.11, 1.10, 1.9, 1.8, 1.7, 1.6)
  Status: EXPIRED · Announced: Unknown · Effective: 2025-01-09
  Note: EOL effective for scoped versions ['1.11', '1.10', '1.9', '1.8', '1.7', '1.6']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **php** — php lifecycle: ended active support (8.3, 8.2)
  Status: EXPIRED · Announced: Unknown · Effective: 2024-12-31
  Note: active support ended: review support posture
- **php** — php lifecycle: reached end-of-life (8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 5.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2005-09-05
  Note: EOL effective for scoped versions ['8.1', '8.0', '7.4', '7.3', '7.2', '7.1', '7.0', '5.6', '5.5', '5.4', '5.3', '5.2', '5.1', '5.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **postgresql** — postgresql lifecycle: reached end-of-life (13, 12, 11, 10, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.4, 8.3, 8.2, 8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 6.5, 6.4, 6.3)
  Status: EXPIRED · Announced: Unknown · Effective: 2003-03-01
  Note: EOL effective for scoped versions ['13', '12', '11', '10', '9.6', '9.5', '9.4', '9.3', '9.2', '9.1', '9.0', '8.4', '8.3', '8.2', '8.1', '8.0', '7.4', '7.3', '7.2', '7.1', '7.0', '6.5', '6.4', '6.3']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **pulsar** — apache-pulsar lifecycle: reached end-of-life (4.2, 4.1, 4.0, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5)
  Status: EXPIRED · Announced: Unknown · Effective: 2021-01-15
  Note: EOL effective for scoped versions ['4.2', '4.1', '4.0', '3.3', '3.2', '3.1', '3.0', '2.11', '2.10', '2.9', '2.8', '2.7', '2.6', '2.5']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **rabbitmq** — rabbitmq lifecycle: reached end-of-life (4.2, 4.1, 4.0, 3.13, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2013-11-30
  Note: EOL effective for scoped versions ['4.2', '4.1', '4.0', '3.13', '3.12', '3.11', '3.10', '3.9', '3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **ruby** — ruby lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0.0, 1.9.3)
  Status: EXPIRED · Announced: Unknown · Effective: 2015-02-23
  Note: EOL effective for scoped versions ['3.2', '3.1', '3.0', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0.0', '1.9.3']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **rust** — rust lifecycle: reached end-of-life (1.98, 1.97, 1.96, 1.95, 1.94, 1.93, 1.92, 1.91, 1.90, 1.89, 1.88, 1.87, 1.86, 1.85, 1.84, 1.83, 1.82, 1.81, 1.80, 1.79, 1.78, 1.77, 1.76, 1.75, 1.74, 1.73, 1.72, 1.71, 1.70, 1.69, 1.68, 1.67, 1.66, 1.65, 1.64, 1.63, 1.62, 1.61, 1.60, 1.59, 1.58, 1.57, 1.56, 1.55, 1.54, 1.53, 1.52, 1.51, 1.50, 1.49, 1.48, 1.47, 1.46, 1.45, 1.44, 1.43, 1.42, 1.41, 1.40, 1.39, 1.38, 1.37, 1.36, 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29)
  Status: EXPIRED · Announced: Unknown · Effective: 2018-10-26
  Note: EOL effective for scoped versions ['1.98', '1.97', '1.96', '1.95', '1.94', '1.93', '1.92', '1.91', '1.90', '1.89', '1.88', '1.87', '1.86', '1.85', '1.84', '1.83', '1.82', '1.81', '1.80', '1.79', '1.78', '1.77', '1.76', '1.75', '1.74', '1.73', '1.72', '1.71', '1.70', '1.69', '1.68', '1.67', '1.66', '1.65', '1.64', '1.63', '1.62', '1.61', '1.60', '1.59', '1.58', '1.57', '1.56', '1.55', '1.54', '1.53', '1.52', '1.51', '1.50', '1.49', '1.48', '1.47', '1.46', '1.45', '1.44', '1.43', '1.42', '1.41', '1.40', '1.39', '1.38', '1.37', '1.36', '1.35', '1.34', '1.33', '1.32', '1.31', '1.30', '1.29']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **solr** — solr lifecycle: reached end-of-life (8, 7, 6, 5, 4, 3, 1)
  Status: EXPIRED · Announced: Unknown · Effective: 2017-10-24
  Note: EOL effective for scoped versions ['8', '7', '6', '5', '4', '3', '1']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **spark** — apache-spark lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0, 2.4, 2.3, 2.2, 2.1, 2.0, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Status: EXPIRED · Announced: Unknown · Effective: 2014-09-03
  Note: EOL effective for scoped versions ['3.4', '3.3', '3.2', '3.1', '3.0', '2.4', '2.3', '2.2', '2.1', '2.0', '1.6', '1.5', '1.4', '1.3', '1.2', '1.1', '1.0']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **spring-boot** — spring-boot lifecycle: reached end-of-life (3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.5)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-03-01
  Note: EOL effective for scoped versions ['3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.5']: evidence and scope justify action-oriented framing (applies only if you run these versions)
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
- **traefik** — traefik lifecycle: reached end-of-life (3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.7)
  Status: EXPIRED · Announced: Unknown · Effective: 2019-12-11
  Note: EOL effective for scoped versions ['3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3.0', '2.11', '2.10', '2.9', '2.8', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0', '1.7']: evidence and scope justify action-oriented framing (applies only if you run these versions)
- **trivy** — CVE-2026-54448 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-06-25 · Effective: Unknown
  Note: AFFECTS_PACKAGE from security correlation; placement follows analyst impact
- **trivy** — CVE-2026-55092 [AFFECTS_PACKAGE] tracked by nvd
  Status: EXPIRED · Announced: 2026-06-25 · Effective: Unknown
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

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: distribution model change with high significance: action-oriented framing justified

Investigate: Confirm whether this is a removal or a rename (pull/mirror check); review pinned references.

### **bitnami** — bitnamisecure/redis publishes latest-only tags

Category: Distribution · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `docker.io/bitnamisecure/redis`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: distribution observation without high significance: watch

Investigate: No action; track the repository for further changes.

#### istio

### **istio** — istio lifecycle: approaching end-of-life (1.31, 1.30)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.31`, `1.30`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/istio

#### kubernetes

### **kubernetes** — kubernetes 1.35 EOL approaching (2027-02-28)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.35`

Announcement: Unknown

Effective: 2027-02-28 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/kubernetes

#### minio

### **minio** — minio/minio is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: archived upstream is a project-level change, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/minio/minio

#### numpy

### **numpy** — numpy 2.2 EOL approaching (2026-12-09)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `2.2`

Announcement: Unknown

Effective: 2026-12-09 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/numpy

#### openssl

### **openssl** — openssl 3.6 EOL approaching (2026-11-01)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.6`

Announcement: Unknown

Effective: 2026-11-01 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/openssl

#### postgresql

### **postgresql** — postgresql 14 EOL approaching (2026-11-12)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `14`

Announcement: Unknown

Effective: 2026-11-12 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/prometheus

#### react

### **react** — facebook/react moved to react/react on GitHub

Category: Ownership · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: ownership move is a project-level identity fact, not proof any deployment is affected: review, never automatic action

Investigate: Review in the next planning cycle.

Source: https://github.com/react/react

#### react-native-fbsdk

### **react-native-fbsdk** — facebookarchive/react-native-fbsdk is archived on GitHub

Category: Repository · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/redis

#### vitess

### **vitess** — vitess 23 EOL approaching (2026-11-04)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `23`

Announcement: Unknown

Effective: 2026-11-04 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

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

Last verified: 2026-10-30

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

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/angular

#### clickhouse

### **clickhouse** — clickhouse 26.3 EOL approaching (2027-03-26)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `26.3`

Announcement: Unknown

Effective: 2027-03-26 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/clickhouse

#### consul

### **consul** — consul 1.22 EOL approaching (2026-10-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.22`

Announcement: Unknown

Effective: 2026-10-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/consul

#### containerd

### **containerd** — containerd lifecycle: approaching end-of-life (2.2, 2.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `2.2`, `2.0`

Announcement: Unknown

Effective: 2026-11-06 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/containerd

#### django

### **django** — django lifecycle: ended active support (6.0, 5.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `6.0`, `5.2`

Announcement: Unknown

Effective: 2025-12-03 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/django

### **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `5.1`, `5.0`, `4.2`, `4.1`, `4.0`, `3.2`, `3.1`, `3.0`, `2.2`, `2.1`, `2.0`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`

Announcement: Unknown

Effective: 2013-02-26 (already effective)

First detected by OpenPulse: 2026-10-21

Last verified: 2026-10-30

Status: NEW

Why it matters: EOL effective for scoped versions `5.1`, `5.0`, `4.2`, `4.1`, `4.0`, `3.2`, `3.1`, `3.0`, `2.2`, `2.1`, `2.0`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Source: https://endoflife.date/django

#### envoy

### **envoy** — envoy lifecycle: approaching end-of-life (1.38, 1.37)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.38`, `1.37`

Announcement: Unknown

Effective: 2027-01-13 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

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

Last verified: 2026-10-30

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

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/haproxy

#### jaeger

### **jaeger** — jaeger 1 is end-of-life

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1`

Announcement: Unknown

Effective: 2025-12-31 (already effective)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: EOL effective for scoped versions `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Source: https://endoflife.date/jaeger

#### mariadb

### **mariadb** — mariadb 13.0 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `13.0`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/mariadb

#### mysql

### **mysql** — mysql 26.10 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `26.10`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/mysql

#### opentofu

### **opentofu** — opentofu 1.12 EOL approaching (2027-02-01)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.12`

Announcement: Unknown

Effective: 2027-02-01 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/opentofu

#### php

### **php** — php 8.2 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `8.2`

Announcement: Unknown

Effective: 2026-12-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/php

#### rabbitmq

### **rabbitmq** — rabbitmq 4.3 EOL approaching (2027-01-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.3`

Announcement: Unknown

Effective: 2027-01-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/rabbitmq

#### ruby

### **ruby** — ruby 3.3 EOL approaching (2027-03-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.3`

Announcement: Unknown

Effective: 2027-03-31 (upcoming)

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

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

Last verified: 2026-10-30

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

Last verified: 2026-10-30

Status: UPCOMING

Why it matters: EOL upcoming but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Source: https://endoflife.date/spring-boot

#### traefik

### **traefik** — traefik 3.7 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.7`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/traefik

#### vue

### **vue** — vue 3.5 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.5`

Announcement: Unknown

Effective: Unknown

First detected by OpenPulse: Unknown

Last verified: 2026-10-30

Status: ACTIVE

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Source: https://endoflife.date/vue

### C. Source references

Finding source distribution: endoflife.date 82.5%, GitHub 7.5%, Registry 5.0%, NVD 5.0%
Independent source families observed: 4 (across 4 recorded source labels).

### D. Data gaps and limitations

No signals observed for: bitnami-redis-stack, boto3, buildkit, capa, celery, cockroach, coredns, crio, falco, flask, helm, k9s, kustomize, langchain, linkerd, nats, nest, node-redis, opa, opentelemetry, pandas, pytest, pytorch, qdrant, redpanda, requests, serde, tensorflow, timescaledb, transformers, typescript, valkey, vault, vite, webpack.

591 related-but-unconfirmed or below-bar records held back (see `openpulse analyze` for the full stream).

### E. Notes

- Collectors: endoflife.date, GitHub releases + repo metadata, NVD, CISA KEV, Docker Hub.
- GitHub calls authenticated (5000 req/hr budget).
- NVD queried without API key (5 req/30s); misses degrade to gaps, not findings.
- Keyword-associated CVE records without identity evidence are held back, not narrated.
- Public intelligence describes project-level change; whether it affects YOUR dependencies needs a watchlist (`openpulse check`).
