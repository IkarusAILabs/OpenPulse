# OpenPulse Monthly Intelligence — 2026-10

Reporting period: 2026-10.

_Public report findings describe OSS ecosystem changes. They are not assertions that a particular customer's environment is affected._

## Executive Summary

OpenPulse detected 120 material upstream changes across 100 monitored projects in 2026-10. That includes 102 non-lifecycle discoveries — changes no lifecycle database records. 57 changes require attention now; no upcoming changes carry warning windows.

- Projects monitored: 100
- Material changes (action + review): 120
- Changes requiring attention: 57
- Upcoming changes with warning: 0
- Non-lifecycle discoveries: 102
- Evidence confidence: 0 CONFIRMED, 0 CORROBORATED, 195 EMERGING, 0 UNVERIFIED
- Data gaps: 37 projects with no signals, 317 records held back

## Top Changes

### 1. **bitnami** — CVE-2025-22248 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/bitnami/charts/security/advisories/GHSA-mx38-x658-5fwj

### 2. **gradle** — CVE-2016-6199 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://discuss.gradle.org/t/a-security-issue-about-gradle-rce/17726
- https://philwantsfish.github.io/security/java-deserialization-github

### 3. **gradle** — CVE-2019-15052 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/gradle/gradle/issues/10278
- https://github.com/gradle/gradle/pull/10176
- https://github.com/gradle/gradle/security/advisories/GHSA-4cwg-f7qc-6r95

### 4. **grafana** — CVE-2018-15727 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/105184
- https://access.redhat.com/errata/RHSA-2018:3829
- https://access.redhat.com/errata/RHSA-2019:0019
- (+1 more in the appendix)

### 5. **grafana** — CVE-2019-15043 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://lists.opensuse.org/opensuse-security-announce/2020-06/msg00060.html
- http://lists.opensuse.org/opensuse-security-announce/2020-07/msg00083.html
- http://lists.opensuse.org/opensuse-security-announce/2020-10/msg00009.html
- (+7 more in the appendix)

### 6. **influxdb** — CVE-2019-10329 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.openwall.com/lists/oss-security/2019/05/31/2
- http://www.securityfocus.com/bid/108540
- https://jenkins.io/security/advisory/2019-05-31/#SECURITY-1403

### 7. **influxdb** — CVE-2019-20933 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/influxdata/influxdb/commit/761b557315ff9c1642cf3b0e5797cd3d983a24c0
- https://github.com/influxdata/influxdb/compare/v1.7.5...v1.7.6
- https://github.com/influxdata/influxdb/issues/12927
- (+2 more in the appendix)

### 8. **influxdb** — CVE-2022-36640 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.krsecu.com/CVE/409b5310045bd6b9a984a5fb63bd8786d5c5681a8ad5b1c815c84b2b90002ad7.docx
- https://dl.influxdata.com/influxdb/releases/influxdb_1.8.10_amd64.deb
- https://portal.influxdata.com/downloads/
- (+1 more in the appendix)

### 9. **kafka** — CVE-2018-17196 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/109139
- https://lists.apache.org/thread.html/519eb0fd45642dcecd9ff74cb3e71c20a4753f7d82e2f07864b5108f%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/b0656d359c7d40ec9f39c8cc61bca66802ef9a2a12ee199f5b0c1442%40%3Cdev.drill.apache.org%3E
- (+8 more in the appendix)

### 10. **kafka** — CVE-2019-12399 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.openwall.com/lists/oss-security/2020/01/14/1
- https://lists.apache.org/thread.html/r0e3a613705d70950aca2bfe9a6265c87503921852d9a3dbce512ca9f%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r2d390dec5f360ec8aa294bef18e1a4385e2a3698d747209216f5a48b%40%3Ccommits.druid.apache.org%3E
- (+21 more in the appendix)

## Changes Requiring Attention

- **airflow** — apache-airflow lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2, 1.10, 1.9, 1.8, 1.7)
  Scope: 3.2, 3.1, 3.0, 2, 1.10, 1.9, 1.8, 1.7 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **angular** — angular lifecycle: reached end-of-life (19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9)
  Scope: 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **ansible** — ansible lifecycle: reached end-of-life (13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2.10, 2.9)
  Scope: 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2.10, 2.9 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **argocd** — argo-cd lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.14, 2.13, 2.12, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 3.2, 3.1, 3.0, 2.14, 2.13, 2.12, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **calico** — calico lifecycle: reached end-of-life (3.30, 3.29, 3.28, 3.27, 3.26, 3.25)
  Scope: 3.30, 3.29, 3.28, 3.27, 3.26, 3.25 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **cassandra** — apache-cassandra lifecycle: reached end-of-life (3.11, 3.0)
  Scope: 3.11, 3.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **cert-manager** — cert-manager lifecycle: reached end-of-life (1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)
  Scope: 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **cilium** — cilium lifecycle: reached end-of-life (1.17, 1.16, 1.15, 1.14, 1.13)
  Scope: 1.17, 1.16, 1.15, 1.14, 1.13 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **clickhouse** — clickhouse lifecycle: reached end-of-life (26.6, 26.5, 26.4, 26.2, 26.1, 25.12, 25.11, 25.10, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1)
  Scope: 26.6, 26.5, 26.4, 26.2, 26.1, 25.12, 25.11, 25.10, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **consul** — consul lifecycle: reached end-of-life (1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6)
  Scope: 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **containerd** — containerd lifecycle: reached end-of-life (2.1, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 2.1, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **couchdb** — apache-couchdb lifecycle: reached end-of-life (3.3, 3.2)
  Scope: 3.3, 3.2 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **cpython** — python lifecycle: reached end-of-life (3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 2.7, 3.1, 3.0, 2.6)
  Scope: 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 2.7, 3.1, 3.0, 2.6 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)
  Scope: 5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **elasticsearch** — elasticsearch lifecycle: reached end-of-life (9.3, 9.2, 9.1, 8.18, 9.0, 8.17, 8.16, 7, 6)
  Scope: 9.3, 9.2, 9.1, 8.18, 9.0, 8.17, 8.16, 7, 6 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **envoy** — envoy lifecycle: reached end-of-life (1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **etcd** — etcd lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0)
  Scope: 3.4, 3.3, 3.2, 3.1, 3.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **express** — express lifecycle: reached end-of-life (3, 2, 1)
  Scope: 3, 2, 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **flux** — flux lifecycle: reached end-of-life (2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.25)
  Scope: 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.25 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **go** — go lifecycle: reached end-of-life (1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)
  Scope: 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **gradle** — gradle lifecycle: reached end-of-life (7, 6, 5, 4, 3, 2, 1)
  Scope: 7, 6, 5, 4, 3, 2, 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **grafana** — grafana lifecycle: reached end-of-life (12.3, 12.2, 12.1, 12.0, 11.6, 11.5, 11.4, 11.3, 11.2, 11.1, 11.0, 10.4, 10.3, 10.2, 10.1, 10.0, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8, 7, 6)
  Scope: 12.3, 12.2, 12.1, 12.0, 11.6, 11.5, 11.4, 11.3, 11.2, 11.1, 11.0, 10.4, 10.3, 10.2, 10.1, 10.0, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8, 7, 6 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **haproxy** — haproxy lifecycle: reached end-of-life (3.1, 2.9, 2.7, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 3.1, 2.9, 2.7, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **influxdb** — influxdb lifecycle: reached end-of-life (3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)
  Scope: 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **istio** — istio lifecycle: reached end-of-life (1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7)
  Scope: 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **jaeger** — jaeger 1 is end-of-life
  Scope: 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **jenkins** — jenkins lifecycle: reached end-of-life (2.555, 2.541, 2.528, 2.516, 2.504, 2.492, 2.479, 2.462, 2.452, 2.440, 2.426, 2.414, 2.401, 2.387, 2.375, 2.361, 2.346)
  Scope: 2.555, 2.541, 2.528, 2.516, 2.504, 2.492, 2.479, 2.462, 2.452, 2.440, 2.426, 2.414, 2.401, 2.387, 2.375, 2.361, 2.346 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **kafka** — apache-kafka lifecycle: reached end-of-life (3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.1, 1.0, 0.11, 0.10, 0.9, 0.8, 0.7)
  Scope: 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.1, 1.0, 0.11, 0.10, 0.9, 0.8, 0.7 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **keycloak** — keycloak lifecycle: reached end-of-life (26.6, 26.5, 26.4, 26.3, 26.2, 26.1, 26.0, 25.0, 24.0, 23.0, 22.0, 21.1, 21.0, 20.0, 19.0, 18.0, 17.0, 16.1, 16.0, 15.1, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0)
  Scope: 26.6, 26.5, 26.4, 26.3, 26.2, 26.1, 26.0, 25.0, 24.0, 23.0, 22.0, 21.1, 21.0, 20.0, 19.0, 18.0, 17.0, 16.1, 16.0, 15.1, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **kubernetes** — kubernetes lifecycle: reached end-of-life (1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16)
  Scope: 1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **kyverno** — kyverno lifecycle: reached end-of-life (1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8)
  Scope: 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **mariadb** — mariadb lifecycle: reached end-of-life (12.2, 12.1, 12.0, 11.7, 11.6, 11.5, 11.3, 11.2, 11.1, 11.0, 10.10, 10.9, 10.8, 10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 5.5, 5.3, 5.2, 5.1)
  Scope: 12.2, 12.1, 12.0, 11.7, 11.6, 11.5, 11.3, 11.2, 11.1, 11.0, 10.10, 10.9, 10.8, 10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 5.5, 5.3, 5.2, 5.1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **maven** — apache-maven lifecycle: reached end-of-life (3.8, 3.6, 3.5, 3.3, 3.2, 3.1, 3.0, 2, 1)
  Scope: 3.8, 3.6, 3.5, 3.3, 3.2, 3.1, 3.0, 2, 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **memcached** — memcached lifecycle: reached end-of-life (1.5, 1.4)
  Scope: 1.5, 1.4 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **mongodb** — mongodb lifecycle: reached end-of-life (8.2, 8.1, 7.3, 7.2, 7.1, 6.3, 6.2, 6.1, 6.0, 5.3, 5.2, 5.1, 5.0, 4.4, 4.2, 4.0, 3.6, 3.4, 3.2, 3.0, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0)
  Scope: 8.2, 8.1, 7.3, 7.2, 7.1, 6.3, 6.2, 6.1, 6.0, 5.3, 5.2, 5.1, 5.0, 4.4, 4.2, 4.0, 3.6, 3.4, 3.2, 3.0, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **mysql** — mysql lifecycle: reached end-of-life (9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.3, 8.2, 8.1, 8.0, 5.7, 5.6, 5.5)
  Scope: 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.3, 8.2, 8.1, 8.0, 5.7, 5.6, 5.5 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **neo4j** — neo4j lifecycle: reached end-of-life (2026.08, 2026.07, 2026.06, 2026.05, 2026.04, 2026.03, 2026.02, 2026.01, 2025.12, 2025.11, 2025.10, 2025.09, 2025.08, 2025.07, 2025.06, 2025.05, 2025.04, 2025.03, 2025.02, 2025.01, 5.25, 5.24, 5.23, 5.22, 5.21, 5.20, 5.19, 5.18, 5.17, 5.16, 5.15, 5.14, 5.13, 5.12, 5.11, 5.10, 5.9, 5.8, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.4, 4.3, 4.2, 4.1, 4.0, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 2026.08, 2026.07, 2026.06, 2026.05, 2026.04, 2026.03, 2026.02, 2026.01, 2025.12, 2025.11, 2025.10, 2025.09, 2025.08, 2025.07, 2025.06, 2025.05, 2025.04, 2025.03, 2025.02, 2025.01, 5.25, 5.24, 5.23, 5.22, 5.21, 5.20, 5.19, 5.18, 5.17, 5.16, 5.15, 5.14, 5.13, 5.12, 5.11, 5.10, 5.9, 5.8, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.4, 4.3, 4.2, 4.1, 4.0, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **nginx** — nginx lifecycle: reached end-of-life (1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.16, 1.14, 1.12, 1.10, 1.8, 1.6, 1.4, 1.2, 1.0)
  Scope: 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.16, 1.14, 1.12, 1.10, 1.8, 1.6, 1.4, 1.2, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **nodejs** — nodejs lifecycle: reached end-of-life (25, 23, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)
  Scope: 25, 23, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **numpy** — numpy lifecycle: reached end-of-life (2.1, 2.0, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14)
  Scope: 2.1, 2.0, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **openssl** — openssl lifecycle: reached end-of-life (3.3, 3.2, 3.1, 3.0, 1.1.1, 1.1.0, 1.0.2, 1.0.1, 1.0.0, 0.9.8)
  Scope: 3.3, 3.2, 3.1, 3.0, 1.1.1, 1.1.0, 1.0.2, 1.0.1, 1.0.0, 0.9.8 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **php** — php lifecycle: reached end-of-life (8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 5.0)
  Scope: 8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 5.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **postgresql** — postgresql lifecycle: reached end-of-life (13, 12, 11, 10, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.4, 8.3, 8.2, 8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 6.5, 6.4, 6.3)
  Scope: 13, 12, 11, 10, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.4, 8.3, 8.2, 8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 6.5, 6.4, 6.3 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **prometheus** — prometheus lifecycle: reached end-of-life (3.14, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.55, 2.54, 2.53, 2.52, 2.51, 2.50, 2.49, 2.48, 2.47, 2.46, 2.45, 2.44, 2.43, 2.42, 2.41, 2.40, 2.39, 2.38, 2.37, 2.36)
  Scope: 3.14, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.55, 2.54, 2.53, 2.52, 2.51, 2.50, 2.49, 2.48, 2.47, 2.46, 2.45, 2.44, 2.43, 2.42, 2.41, 2.40, 2.39, 2.38, 2.37, 2.36 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **pulsar** — apache-pulsar lifecycle: reached end-of-life (4.2, 4.1, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5)
  Scope: 4.2, 4.1, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **rabbitmq** — rabbitmq lifecycle: reached end-of-life (4.2, 4.1, 4.0, 3.13, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)
  Scope: 4.2, 4.1, 4.0, 3.13, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **redis** — redis lifecycle: reached end-of-life (7.0, 6.0, 5.0)
  Scope: 7.0, 6.0, 5.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **ruby** — ruby lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0.0, 1.9.3)
  Scope: 3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0.0, 1.9.3 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **rust** — rust lifecycle: reached end-of-life (1.97, 1.96, 1.95, 1.94, 1.93, 1.92, 1.91, 1.90, 1.89, 1.88, 1.87, 1.86, 1.85, 1.84, 1.83, 1.82, 1.81, 1.80, 1.79, 1.78, 1.77, 1.76, 1.75, 1.74, 1.73, 1.72, 1.71, 1.70, 1.69, 1.68, 1.67, 1.66, 1.65, 1.64, 1.63, 1.62, 1.61, 1.60, 1.59, 1.58, 1.57, 1.56, 1.55, 1.54, 1.53, 1.52, 1.51, 1.50, 1.49, 1.48, 1.47, 1.46, 1.45, 1.44, 1.43, 1.42, 1.41, 1.40, 1.39, 1.38, 1.37, 1.36, 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29)
  Scope: 1.97, 1.96, 1.95, 1.94, 1.93, 1.92, 1.91, 1.90, 1.89, 1.88, 1.87, 1.86, 1.85, 1.84, 1.83, 1.82, 1.81, 1.80, 1.79, 1.78, 1.77, 1.76, 1.75, 1.74, 1.73, 1.72, 1.71, 1.70, 1.69, 1.68, 1.67, 1.66, 1.65, 1.64, 1.63, 1.62, 1.61, 1.60, 1.59, 1.58, 1.57, 1.56, 1.55, 1.54, 1.53, 1.52, 1.51, 1.50, 1.49, 1.48, 1.47, 1.46, 1.45, 1.44, 1.43, 1.42, 1.41, 1.40, 1.39, 1.38, 1.37, 1.36, 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **solr** — solr lifecycle: reached end-of-life (8, 7, 6, 5, 4, 3, 1)
  Scope: 8, 7, 6, 5, 4, 3, 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **spark** — apache-spark lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0, 2.4, 2.3, 2.2, 2.1, 2.0, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 3.4, 3.3, 3.2, 3.1, 3.0, 2.4, 2.3, 2.2, 2.1, 2.0, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **spring-boot** — spring-boot lifecycle: reached end-of-life (3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.5)
  Scope: 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.5 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **terraform** — terraform lifecycle: reached end-of-life (1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)
  Scope: 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **traefik** — traefik lifecycle: reached end-of-life (3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.7)
  Scope: 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.7 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **vitess** — vitess lifecycle: reached end-of-life (22, 21, 20, 19, 18, 17, 16, 15, 14, 13)
  Scope: 22, 21, 20, 19, 18, 17, 16, 15, 14, 13 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **vue** — vue lifecycle: reached end-of-life (3.4, 3.3, 2.7, 3.2, 3.1, 3.0, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1)
  Scope: 3.4, 3.3, 2.7, 3.2, 3.1, 3.0, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.
- **zookeeper** — zookeeper lifecycle: reached end-of-life (3.7, 3.6, 3.5, 3.4)
  Scope: 3.7, 3.6, 3.5, 3.4 · Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

## Upcoming Changes

No upcoming changes with trustworthy dates this month.

## Category Overview

| Category | Changes | Requiring attention |
|---|---|---|
| Distribution | 0 | 0 |
| Security | 102 | 0 |
| License | 0 | 0 |
| Lifecycle | 93 | 57 |
| Support | 0 | 0 |
| Ownership | 0 | 0 |
| Repository | 0 | 0 |
| Other | 0 | 0 |

## Evidence Quality

- CONFIRMED (0): official announcement from the source itself.
- CORROBORATED (0): confirmed by 2+ independent source families.
- EMERGING (195): single credible source.
- UNVERIFIED (0): weak or unconfirmed signal — never action-framed.

## What OpenPulse Added This Month

OpenPulse is designed to answer a question traditional dependency monitoring often does not answer: Something changed upstream. Does it affect what we depend on?

This month the report answers it with the findings below — detected upstream changes, explained in context, correlated across sources, attributed to dependency identity, with warning where dates allow. OpenPulse does not replace SCA, SBOM, vulnerability, or lifecycle databases — it is an intelligence layer across them.

### Upstream Change Detection

- Security (102): e.g. **bitnami** — CVE-2025-22248 [AFFECTS_PACKAGE] tracked by nvd
- Lifecycle (93): e.g. **airflow** — apache-airflow lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2, 1.10, 1.9, 1.8, 1.7)

### Dependency Attribution

- Affected version: `3.2` — apache-airflow lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2, 1.10, 1.9, 1.8, 1.7)

### Evidence-backed Intelligence

- Confirmation level: strongest finding this month is EMERGING; full breakdown in Evidence Quality. No opaque risk scores.
- 2 independent source families across 800 supporting references.
- Scope established for 93/195 findings.
- Effective date known for 93/195 findings.

### Early Warning

- No upcoming changes with trustworthy dates this month — nothing to warn about yet.

### From Public Intelligence to Early Warning

- Public intelligence: “What is changing in OSS?” — this report.
- Dependency intelligence: “What is changing in the OSS projects I use?” — `openpulse check --watchlist <file>`.
- Customer impact: “Does this affect my software?” — matched dependencies only.
- Early warning: “How much warning do I have?” — warning windows above.

## For Your Environment

This report describes open-source ecosystem intelligence. It does not establish that a specific customer environment is affected.

Dependency-aware impact requires a customer watchlist, inventory, or equivalent dependency context: public intelligence → dependency context (`openpulse check --watchlist <file>`) → affected dependency → actionable warning. Only that last step can speak about your environment.

## Appendix

### A. All project findings

#### bitnami

### **bitnami** — CVE-2025-22248 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/bitnami/charts/security/advisories/GHSA-mx38-x658-5fwj

#### gradle

### **gradle** — gradle lifecycle: ended active support (9, 8)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `9`, `8`

Timing: Effective 2025-07-31 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/gradle

### **gradle** — gradle lifecycle: reached end-of-life (7, 6, 5, 4, 3, 2, 1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `7`, `6`, `5`, `4`, `3`, `2`, `1`

Timing: Effective 2014-07-01 (already effective)

Why it matters: EOL effective for scoped versions `7`, `6`, `5`, `4`, `3`, `2`, `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/gradle

### **gradle** — CVE-2016-6199 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://discuss.gradle.org/t/a-security-issue-about-gradle-rce/17726
- https://philwantsfish.github.io/security/java-deserialization-github

### **gradle** — CVE-2019-11065 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/gradle/gradle/pull/8927
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/WVXOXNLAYRGPKAZV63PYNV3HF27JW2MW/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/Y43P7SVDJOG6OUDVFR4ZIDITZLNHPGTO/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/YQ5CGOV5QVQCSPGE3WRZDKUGIXLHSZDR/

### **gradle** — CVE-2019-15052 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/gradle/gradle/issues/10278
- https://github.com/gradle/gradle/pull/10176
- https://github.com/gradle/gradle/security/advisories/GHSA-4cwg-f7qc-6r95

### **gradle** — CVE-2019-16370 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/gradle/gradle/commit/425b2b7a50cd84106a77cdf1ab665c89c6b14d2f
- https://github.com/gradle/gradle/pull/10543

#### grafana

### **grafana** — grafana lifecycle: ended active support (13.2, 13.1, 13.0, 12.4)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `13.2`, `13.1`, `13.0`, `12.4`

Timing: Effective 2026-04-17 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/grafana

### **grafana** — grafana lifecycle: approaching end-of-life (13.1, 13.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `13.1`, `13.0`

Timing: Effective 2027-01-09 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/grafana

### **grafana** — grafana lifecycle: reached end-of-life (12.3, 12.2, 12.1, 12.0, 11.6, 11.5, 11.4, 11.3, 11.2, 11.1, 11.0, 10.4, 10.3, 10.2, 10.1, 10.0, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8, 7, 6)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `12.3`, `12.2`, `12.1`, `12.0`, `11.6`, `11.5`, `11.4`, `11.3`, `11.2`, `11.1`, `11.0`, `10.4`, `10.3`, `10.2`, `10.1`, `10.0`, `9.5`, `9.4`, `9.3`, `9.2`, `9.1`, `9.0`, `8`, `7`, `6`

Timing: Effective 2021-06-08 (already effective)

Why it matters: EOL effective for scoped versions `12.3`, `12.2`, `12.1`, `12.0`, `11.6`, `11.5`, `11.4`, `11.3`, `11.2`, `11.1`, `11.0`, `10.4`, `10.3`, `10.2`, `10.1`, `10.0`, `9.5`, `9.4`, `9.3`, `9.2`, `9.1`, `9.0`, `8`, `7`, `6`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/grafana

### **grafana** — CVE-2018-1000816 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/grafana/grafana/issues/13667

### **grafana** — CVE-2018-12099 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/grafana/grafana/pull/11813
- https://github.com/grafana/grafana/releases/tag/v5.2.0-beta1
- https://security.netapp.com/advisory/ntap-20190416-0004/

### **grafana** — CVE-2018-15727 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/105184
- https://access.redhat.com/errata/RHSA-2018:3829
- https://access.redhat.com/errata/RHSA-2019:0019
- https://grafana.com/blog/2018/08/29/grafana-5.2.3-and-4.6.4-released-with-important-security-fix/

### **grafana** — CVE-2018-18623 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/grafana/grafana/issues/15293
- https://github.com/grafana/grafana/pull/11813
- https://github.com/grafana/grafana/releases/tag/v6.0.0
- https://security.netapp.com/advisory/ntap-20200608-0008/

### **grafana** — CVE-2018-18624 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/grafana/grafana/pull/11813
- https://security.netapp.com/advisory/ntap-20200608-0008/

### **grafana** — CVE-2018-19039 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://lists.opensuse.org/opensuse-security-announce/2020-10/msg00009.html
- http://www.securityfocus.com/bid/105994
- https://access.redhat.com/errata/RHSA-2019:0747
- https://access.redhat.com/errata/RHSA-2019:0911
- https://community.grafana.com/t/grafana-5-3-3-and-4-6-5-security-update/11961
- https://security.netapp.com/advisory/ntap-20190416-0004/
- https://www.percona.com/blog/2018/11/20/how-cve-2018-19039-affects-percona-monitoring-and-management/

### **grafana** — CVE-2019-13068 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://packetstormsecurity.com/files/171500/Grafana-6.2.4-HTML-Injection.html
- https://github.com/grafana/grafana/issues/17718
- https://github.com/grafana/grafana/releases/tag/v6.2.5
- https://security.netapp.com/advisory/ntap-20190710-0001/

### **grafana** — CVE-2019-15043 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://lists.opensuse.org/opensuse-security-announce/2020-06/msg00060.html
- http://lists.opensuse.org/opensuse-security-announce/2020-07/msg00083.html
- http://lists.opensuse.org/opensuse-security-announce/2020-10/msg00009.html
- https://community.grafana.com/t/grafana-5-4-5-and-6-3-4-security-update/20569
- https://community.grafana.com/t/release-notes-v6-3-x/19202
- https://github.com/grafana/grafana/releases
- https://grafana.com/blog/2019/08/29/grafana-5.4.5-and-6.3.4-released-with-important-security-fix/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/RF5ARGYX3WYB7H2FDR7VAWTEQ27UX3FU/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/UO4NBL7PKW4OSFRVZENGC42EWEJV2YAH/
- https://security.netapp.com/advisory/ntap-20191004-0004/

### **grafana** — CVE-2019-15635 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://exchange.xforce.ibmcloud.com/vulnerabilities/167244
- https://security.netapp.com/advisory/ntap-20191009-0002/

### **grafana** — CVE-2020-12052 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://community.grafana.com/t/release-notes-v6-7-x/27119
- https://security.netapp.com/advisory/ntap-20200511-0001/

### **grafana** — CVE-2020-12245 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://lists.opensuse.org/opensuse-security-announce/2020-06/msg00060.html
- http://lists.opensuse.org/opensuse-security-announce/2020-07/msg00083.html
- http://lists.opensuse.org/opensuse-security-announce/2020-10/msg00009.html
- http://lists.opensuse.org/opensuse-security-announce/2020-10/msg00017.html
- https://community.grafana.com/t/release-notes-v6-7-x/27119
- https://github.com/grafana/grafana/blob/master/CHANGELOG.md#673-2020-04-23
- https://github.com/grafana/grafana/pull/23816
- https://security.netapp.com/advisory/ntap-20200511-0001/

### **grafana** — CVE-2020-12458 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/security/cve/CVE-2020-12458
- https://bugzilla.redhat.com/show_bug.cgi?id=1827765
- https://github.com/grafana/grafana/issues/8283
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/CTQCKJZZYXMCSHJFZZ3YXEO5NUBANGZS/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/WEBCIEVSYIDDCA7FTRS2IFUOYLIQU34A/
- https://security.netapp.com/advisory/ntap-20200518-0001/

### **grafana** — CVE-2020-12459 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/security/cve/CVE-2020-12459
- https://bugzilla.redhat.com/show_bug.cgi?id=1829724
- https://github.com/grafana/grafana/issues/8283
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/CTQCKJZZYXMCSHJFZZ3YXEO5NUBANGZS/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/WEBCIEVSYIDDCA7FTRS2IFUOYLIQU34A/
- https://security.netapp.com/advisory/ntap-20200518-0004/
- https://src.fedoraproject.org/rpms/grafana/c/fab93d67363eb0a9678d9faf160cc88237f26277

### **grafana** — CVE-2020-13430 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/grafana/grafana/pull/24539
- https://github.com/grafana/grafana/releases/tag/v7.0.0
- https://security.netapp.com/advisory/ntap-20200528-0003/

#### influxdb

### **influxdb** — influxdb lifecycle: reached end-of-life (3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`

Timing: Effective 2025-06-25 (already effective)

Why it matters: EOL effective for scoped versions `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/influxdb

### **influxdb** — CVE-2018-17572 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://gist.github.com/Raghavrao29/1cb84f1f2d8ce993fd7b2d1366d35f48
- https://github.com/influxdata/influxdb/releases/tag/v0.9.6

### **influxdb** — CVE-2019-10329 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.openwall.com/lists/oss-security/2019/05/31/2
- http://www.securityfocus.com/bid/108540
- https://jenkins.io/security/advisory/2019-05-31/#SECURITY-1403

### **influxdb** — CVE-2019-20933 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/influxdata/influxdb/commit/761b557315ff9c1642cf3b0e5797cd3d983a24c0
- https://github.com/influxdata/influxdb/compare/v1.7.5...v1.7.6
- https://github.com/influxdata/influxdb/issues/12927
- https://lists.debian.org/debian-lts-announce/2020/12/msg00030.html
- https://www.debian.org/security/2021/dsa-4823

### **influxdb** — CVE-2022-36640 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.krsecu.com/CVE/409b5310045bd6b9a984a5fb63bd8786d5c5681a8ad5b1c815c84b2b90002ad7.docx
- https://dl.influxdata.com/influxdb/releases/influxdb_1.8.10_amd64.deb
- https://portal.influxdata.com/downloads/
- https://www.influxdata.com/

#### kafka

### **kafka** — apache-kafka lifecycle: reached end-of-life (3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.1, 1.0, 0.11, 0.10, 0.9, 0.8, 0.7)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.8`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.1`, `1.0`, `0.11`, `0.10`, `0.9`, `0.8`, `0.7`

Timing: Effective 2013-12-03 (already effective)

Why it matters: EOL effective for scoped versions `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.8`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.1`, `1.0`, `0.11`, `0.10`, `0.9`, `0.8`, `0.7`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-kafka

### **kafka** — CVE-2017-12610 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://www.securityfocus.com/bid/104899
- https://lists.apache.org/thread.html/519eb0fd45642dcecd9ff74cb3e71c20a4753f7d82e2f07864b5108f%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/b0656d359c7d40ec9f39c8cc61bca66802ef9a2a12ee199f5b0c1442%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/b6157be1a09df332294213bd21e90dcf9fe4c1810193be54620e4210%40%3Cusers.kafka.apache.org%3E
- https://lists.apache.org/thread.html/f9bc3e55f4e28d1dcd1a69aae6d53e609a758e34d2869b4d798e13cc%40%3Cissues.drill.apache.org%3E
- https://www.oracle.com/security-alerts/cpujul2020.html

### **kafka** — CVE-2018-1288 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://www.securityfocus.com/bid/104900
- https://access.redhat.com/errata/RHSA-2018:3768
- https://lists.apache.org/thread.html/29f61337323f48c47d4b41d74b9e452bd60e65d0e5103af9a6bb2fef%40%3Cusers.kafka.apache.org%3E
- https://lists.apache.org/thread.html/519eb0fd45642dcecd9ff74cb3e71c20a4753f7d82e2f07864b5108f%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/b0656d359c7d40ec9f39c8cc61bca66802ef9a2a12ee199f5b0c1442%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/d1581fb6464c9bec8a72575c01f5097d68e2fbb230aff24622622a58%40%3Ccommits.kafka.apache.org%3E
- https://lists.apache.org/thread.html/f9bc3e55f4e28d1dcd1a69aae6d53e609a758e34d2869b4d798e13cc%40%3Cissues.drill.apache.org%3E
- https://lists.apache.org/thread.html/r07e1bbd1643847d599feb34c707906a4fdcc81e3a6ab01a10c451d40%40%3Cissues.flink.apache.org%3E
- https://lists.apache.org/thread.html/r35322aec467ddae34002690edaa4d9f16e7df9b5bf7164869b75b62c%40%3Cdev.kafka.apache.org%3E
- https://www.oracle.com/security-alerts/cpujul2020.html

### **kafka** — CVE-2018-17196 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/109139
- https://lists.apache.org/thread.html/519eb0fd45642dcecd9ff74cb3e71c20a4753f7d82e2f07864b5108f%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/b0656d359c7d40ec9f39c8cc61bca66802ef9a2a12ee199f5b0c1442%40%3Cdev.drill.apache.org%3E
- https://lists.apache.org/thread.html/d1581fb6464c9bec8a72575c01f5097d68e2fbb230aff24622622a58%40%3Ccommits.kafka.apache.org%3E
- https://lists.apache.org/thread.html/f9bc3e55f4e28d1dcd1a69aae6d53e609a758e34d2869b4d798e13cc%40%3Cissues.drill.apache.org%3E
- https://lists.apache.org/thread.html/r66de86b9a608c1da70b2d27d765c11ec88edf6e5dd6f379ab33e072a%40%3Cuser.flink.apache.org%3E
- https://lists.apache.org/thread.html/r8890b8f18f1de821595792b58b968a89692a255bc20d86d395270740%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/rc27d424d0bdeaf31081c3e246db3c66e882243ae3f342dfa845e0261%40%3Ccommits.kafka.apache.org%3E
- https://www.mail-archive.com/dev%40kafka.apache.org/msg99277.html
- https://www.oracle.com/security-alerts/cpujul2020.html
- https://www.oracle.com/security-alerts/cpuoct2020.html

### **kafka** — CVE-2019-12399 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.openwall.com/lists/oss-security/2020/01/14/1
- https://lists.apache.org/thread.html/r0e3a613705d70950aca2bfe9a6265c87503921852d9a3dbce512ca9f%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r2d390dec5f360ec8aa294bef18e1a4385e2a3698d747209216f5a48b%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r3154f5adbc905f1f9012a92240c8e00a96628470cc819453b9606d0e%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r3203d7f25a6ca56ff3e48c43a6aa7cb60b8e5d57d0eed9f76dc2b7a8%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r47c225db363d1ee2c18c4b3b2f51b63a9789f78c7fa602e5976ecd05%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r4b20b40c40d4a4c641e2ef4228098a57935e5782bfdfdf3650e48265%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r4d9e87cdae99e98d7b244cfa53d9d2532d368d3a187fbc87c493dcbe%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r56eb055b544931451283fee51f7e1f5b8ebd3085fed7d77aaba504c9%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r6af5ed95726874e9add022955be83c192428c248d1c9a1914aff89d9%40%3Cannounce.apache.org%3E
- https://lists.apache.org/thread.html/r6af5ed95726874e9add022955be83c192428c248d1c9a1914aff89d9%40%3Cdev.kafka.apache.org%3E
- https://lists.apache.org/thread.html/r6af5ed95726874e9add022955be83c192428c248d1c9a1914aff89d9%40%3Cusers.kafka.apache.org%3E
- https://lists.apache.org/thread.html/r6fa1cff4786dcef2ddd1d717836ef123c878e8321c24855bad24ae0f%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r801c68bf987931f35d2e24ecc99f3aa2850fdd8f5ef15fe6c60fecf3%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r8890b8f18f1de821595792b58b968a89692a255bc20d86d395270740%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/r9871a4215b621c1d09deee5eba97f0f44fde01b4363deb1bed0dd160%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/rc27d424d0bdeaf31081c3e246db3c66e882243ae3f342dfa845e0261%40%3Ccommits.kafka.apache.org%3E
- https://lists.apache.org/thread.html/rda253155601968331b5cf0da4f273813bbd91843c2568a8495d1c662%40%3Ccommits.kafka.apache.org%3E
- https://lists.apache.org/thread.html/rde947ee866de6687bc51cdc8dfa6d7e6b3ad4ce8c708c344f773e6dc%40%3Ccommits.druid.apache.org%3E
- https://lists.apache.org/thread.html/rfe90ca0463c199b99c2921410639aed53a172ea8b733eab0dc776262%40%3Ccommits.druid.apache.org%3E
- https://www.oracle.com//security-alerts/cpujul2021.html
- https://www.oracle.com/security-alerts/cpuApr2021.html
- https://www.oracle.com/security-alerts/cpuapr2022.html
- https://www.oracle.com/security-alerts/cpujan2021.html

### **kafka** — CVE-2021-38153 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://kafka.apache.org/cve-list
- https://lists.apache.org/thread.html/r26390c8b09ecfa356582d665b0c01f4cdcf16ac047c85f9f9f06a88c%40%3Cdev.kafka.apache.org%3E
- https://lists.apache.org/thread.html/r26390c8b09ecfa356582d665b0c01f4cdcf16ac047c85f9f9f06a88c%40%3Cusers.kafka.apache.org%3E
- https://lists.apache.org/thread.html/r35322aec467ddae34002690edaa4d9f16e7df9b5bf7164869b75b62c%40%3Cdev.kafka.apache.org%3E
- https://lists.apache.org/thread.html/r45cc0602d5f2cbb72e48896dfadf5e5b87ed85630449598b40e8f0be%40%3Cdev.kafka.apache.org%3E
- https://lists.apache.org/thread.html/r45cc0602d5f2cbb72e48896dfadf5e5b87ed85630449598b40e8f0be%40%3Cusers.kafka.apache.org%3E
- https://lists.apache.org/thread.html/rd9ef217b09fdefaf32a4e1835b59b96629542db57e1f63edb8b006e6%40%3Cdev.kafka.apache.org%3E
- https://lists.apache.org/thread.html/rd9ef217b09fdefaf32a4e1835b59b96629542db57e1f63edb8b006e6%40%3Cusers.kafka.apache.org%3E
- https://www.oracle.com/security-alerts/cpuapr2022.html
- https://www.oracle.com/security-alerts/cpujan2022.html
- https://www.oracle.com/security-alerts/cpujul2022.html

### **kafka** — CVE-2022-34917 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://kafka.apache.org/cve-list

#### keycloak

### **keycloak** — keycloak lifecycle: reached end-of-life (26.6, 26.5, 26.4, 26.3, 26.2, 26.1, 26.0, 25.0, 24.0, 23.0, 22.0, 21.1, 21.0, 20.0, 19.0, 18.0, 17.0, 16.1, 16.0, 15.1, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `26.6`, `26.5`, `26.4`, `26.3`, `26.2`, `26.1`, `26.0`, `25.0`, `24.0`, `23.0`, `22.0`, `21.1`, `21.0`, `20.0`, `19.0`, `18.0`, `17.0`, `16.1`, `16.0`, `15.1`, `15.0`, `14.0`, `13.0`, `12.0`, `11.0`, `10.0`

Timing: Effective 2020-07-22 (already effective)

Why it matters: EOL effective for scoped versions `26.6`, `26.5`, `26.4`, `26.3`, `26.2`, `26.1`, `26.0`, `25.0`, `24.0`, `23.0`, `22.0`, `21.1`, `21.0`, `20.0`, `19.0`, `18.0`, `17.0`, `16.1`, `16.0`, `15.1`, `15.0`, `14.0`, `13.0`, `12.0`, `11.0`, `10.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/keycloak

### **keycloak** — CVE-2014-3651 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://bugzilla.redhat.com/show_bug.cgi?id=1144278
- https://issues.jboss.org/browse/KEYCLOAK-699

### **keycloak** — CVE-2014-3709 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/101508
- https://bugzilla.redhat.com/show_bug.cgi?id=1154971
- https://issues.jboss.org/browse/KEYCLOAK-765

### **keycloak** — CVE-2016-8609 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://rhn.redhat.com/errata/RHSA-2016-2945.html
- http://www.securityfocus.com/bid/95070
- http://www.securitytracker.com/id/1037460
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2016-8609

### **keycloak** — CVE-2016-8629 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://rhn.redhat.com/errata/RHSA-2017-0876.html
- http://www.securityfocus.com/bid/97392
- http://www.securitytracker.com/id/1038180
- https://access.redhat.com/errata/RHSA-2017:0872
- https://access.redhat.com/errata/RHSA-2017:0873
- https://bugzilla.redhat.com/show_bug.cgi?id=1388988

### **keycloak** — CVE-2017-12158 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://www.securityfocus.com/bid/101618
- https://access.redhat.com/errata/RHSA-2017:2904
- https://access.redhat.com/errata/RHSA-2017:2905
- https://access.redhat.com/errata/RHSA-2017:2906
- https://bugzilla.redhat.com/show_bug.cgi?id=1489161

### **keycloak** — CVE-2017-12159 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/101601
- https://access.redhat.com/errata/RHSA-2017:2904
- https://access.redhat.com/errata/RHSA-2017:2905
- https://access.redhat.com/errata/RHSA-2017:2906
- https://bugzilla.redhat.com/show_bug.cgi?id=1484111

### **keycloak** — CVE-2017-12160 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://access.redhat.com/errata/RHSA-2017:2904
- https://access.redhat.com/errata/RHSA-2017:2905
- https://access.redhat.com/errata/RHSA-2017:2906
- https://bugzilla.redhat.com/show_bug.cgi?id=1484154

### **keycloak** — CVE-2017-12161 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://bugzilla.redhat.com/show_bug.cgi?id=1484564
- https://github.com/keycloak/keycloak-documentation/pull/268/commits/a2b58aadee42af2c375b72e86dffc2cf23cc3770

### **keycloak** — CVE-2017-2582 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://www.securityfocus.com/bid/101046
- http://www.securitytracker.com/id/1041707
- https://access.redhat.com/errata/RHSA-2017:2808
- https://access.redhat.com/errata/RHSA-2017:2809
- https://access.redhat.com/errata/RHSA-2017:2810
- https://access.redhat.com/errata/RHSA-2017:2811
- https://access.redhat.com/errata/RHSA-2017:3216
- https://access.redhat.com/errata/RHSA-2017:3217
- https://access.redhat.com/errata/RHSA-2017:3218
- https://access.redhat.com/errata/RHSA-2017:3219
- https://access.redhat.com/errata/RHSA-2017:3220
- https://access.redhat.com/errata/RHSA-2018:2740
- https://access.redhat.com/errata/RHSA-2018:2741
- https://access.redhat.com/errata/RHSA-2018:2742
- https://access.redhat.com/errata/RHSA-2018:2743
- https://access.redhat.com/errata/RHSA-2019:0136
- https://access.redhat.com/errata/RHSA-2019:0137
- https://access.redhat.com/errata/RHSA-2019:0139
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2017-2582
- https://github.com/keycloak/keycloak/pull/3715/commits/0cb5ba0f6e83162d221681f47b470c3042eef237

### **keycloak** — CVE-2017-2585 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://rhn.redhat.com/errata/RHSA-2017-0876.html
- http://www.securityfocus.com/bid/97393
- http://www.securitytracker.com/id/1038180
- https://access.redhat.com/errata/RHSA-2017:0872
- https://access.redhat.com/errata/RHSA-2017:0873
- https://bugzilla.redhat.com/show_bug.cgi?id=1412376

### **keycloak** — CVE-2017-2646 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/96882
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2017-2646

### **keycloak** — CVE-2018-10894 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/errata/RHSA-2018:3592
- https://access.redhat.com/errata/RHSA-2018:3593
- https://access.redhat.com/errata/RHSA-2018:3595
- https://access.redhat.com/errata/RHSA-2019:0877
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-10894

### **keycloak** — CVE-2018-10912 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/errata/RHSA-2018:2428
- https://access.redhat.com/errata/RHSA-2019:0877
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-10912

### **keycloak** — CVE-2018-14637 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-14637

### **keycloak** — CVE-2018-14655 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/errata/RHSA-2018:3592
- https://access.redhat.com/errata/RHSA-2018:3593
- https://access.redhat.com/errata/RHSA-2018:3595
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-14655

### **keycloak** — CVE-2018-14657 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://access.redhat.com/errata/RHSA-2018:3592
- https://access.redhat.com/errata/RHSA-2018:3593
- https://access.redhat.com/errata/RHSA-2018:3595
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-14657

### **keycloak** — CVE-2018-14658 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/errata/RHSA-2018:3592
- https://access.redhat.com/errata/RHSA-2018:3593
- https://access.redhat.com/errata/RHSA-2018:3595
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-14658

#### loki

### **loki** — CVE-2021-36156 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/grafana/loki/pull/4020#issue-694377133
- https://github.com/grafana/loki/releases/tag/v2.3.0

#### nodejs

### **nodejs** — nodejs lifecycle: reached end-of-life (25, 23, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `25`, `23`, `21`, `20`, `19`, `18`, `17`, `16`, `15`, `14`, `13`, `12`, `11`, `10`, `9`, `8`, `7`, `6`, `5`, `4`, `3`, `2`, `1`

Timing: Effective 2016-06-30 (already effective)

Why it matters: EOL effective for scoped versions `25`, `23`, `21`, `20`, `19`, `18`, `17`, `16`, `15`, `14`, `13`, `12`, `11`, `10`, `9`, `8`, `7`, `6`, `5`, `4`, `3`, `2`, `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/nodejs

### **nodejs** — nodejs 22 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `22`

Timing: Effective 2025-10-21 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/nodejs

### **nodejs** — CVE-2019-15606 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://lists.opensuse.org/opensuse-security-announce/2020-03/msg00008.html
- https://access.redhat.com/errata/RHSA-2020:0573
- https://access.redhat.com/errata/RHSA-2020:0579
- https://access.redhat.com/errata/RHSA-2020:0597
- https://access.redhat.com/errata/RHSA-2020:0598
- https://access.redhat.com/errata/RHSA-2020:0602
- https://hackerone.com/reports/730779
- https://nodejs.org/en/blog/release/v10.19.0/
- https://nodejs.org/en/blog/release/v12.15.0/
- https://nodejs.org/en/blog/release/v13.8.0/
- https://nodejs.org/en/blog/vulnerability/february-2020-security-releases/
- https://security.gentoo.org/glsa/202003-48
- https://security.netapp.com/advisory/ntap-20200221-0004/
- https://www.debian.org/security/2020/dsa-4669
- https://www.oracle.com//security-alerts/cpujul2021.html
- https://www.oracle.com/security-alerts/cpuapr2020.html

#### openssl

### **openssl** — openssl lifecycle: approaching end-of-life (3.6, 3.4)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.6`, `3.4`

Timing: Effective 2026-10-22 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/openssl

### **openssl** — openssl lifecycle: reached end-of-life (3.3, 3.2, 3.1, 3.0, 1.1.1, 1.1.0, 1.0.2, 1.0.1, 1.0.0, 0.9.8)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.3`, `3.2`, `3.1`, `3.0`, `1.1.1`, `1.1.0`, `1.0.2`, `1.0.1`, `1.0.0`, `0.9.8`

Timing: Effective 2015-12-31 (already effective)

Why it matters: EOL effective for scoped versions `3.3`, `3.2`, `3.1`, `3.0`, `1.1.1`, `1.1.0`, `1.0.2`, `1.0.1`, `1.0.0`, `0.9.8`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/openssl

### **openssl** — CVE-1999-0428 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.osvdb.org/3936

### **openssl** — CVE-2000-0535 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://archives.neohapsis.com/archives/freebsd/2000-06/0083.html
- http://www.securityfocus.com/bid/1340

### **openssl** — CVE-2001-1141 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.netbsd.org/pub/NetBSD/security/advisories/NetBSD-SA2001-013.txt.asc
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000418
- http://www.linux-mandrake.com/en/security/2001/MDKSA-2001-065.php3?dis=8.0
- http://www.linuxsecurity.com/advisories/other_advisory-1483.html
- http://www.osvdb.org/853
- http://www.redhat.com/support/errata/RHSA-2001-051.html
- http://www.securityfocus.com/advisories/3475
- http://www.securityfocus.com/archive/1/195829
- http://www.securityfocus.com/bid/3004
- https://exchange.xforce.ibmcloud.com/vulnerabilities/6823

### **openssl** — CVE-2002-0655 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.0.txt
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.1.txt
- ftp://ftp.freebsd.org/pub/FreeBSD/CERT/advisories/FreeBSD-SA-02:33.openssl.asc
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000513
- http://www.cert.org/advisories/CA-2002-23.html
- http://www.kb.cert.org/vuls/id/308891
- http://www.linux-mandrake.com/en/security/2002/MDKSA-2002-046.php
- http://www.securityfocus.com/bid/5364

### **openssl** — CVE-2002-0656 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.0.txt
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.1.txt
- ftp://ftp.freebsd.org/pub/FreeBSD/CERT/advisories/FreeBSD-SA-02:33.openssl.asc
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000513
- http://www.cert.org/advisories/CA-2002-23.html
- http://www.iss.net/security_center/static/9714.php
- http://www.iss.net/security_center/static/9716.php
- http://www.kb.cert.org/vuls/id/102795
- http://www.kb.cert.org/vuls/id/258555
- http://www.linux-mandrake.com/en/security/2002/MDKSA-2002-046.php
- http://www.securityfocus.com/bid/5362
- http://www.securityfocus.com/bid/5363

### **openssl** — CVE-2002-0657 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.0.txt
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.1.txt
- ftp://ftp.freebsd.org/pub/FreeBSD/CERT/advisories/FreeBSD-SA-02:33.openssl.asc
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000513
- http://www.cert.org/advisories/CA-2002-23.html
- http://www.iss.net/security_center/static/9715.php
- http://www.kb.cert.org/vuls/id/561275
- http://www.linux-mandrake.com/en/security/2002/MDKSA-2002-046.php
- http://www.securityfocus.com/bid/5361

### **openssl** — CVE-2002-0659 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.0.txt
- ftp://ftp.caldera.com/pub/security/OpenLinux/CSSA-2002-033.1.txt
- ftp://ftp.freebsd.org/pub/FreeBSD/CERT/advisories/FreeBSD-SA-02:33.openssl.asc
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000516
- http://rhn.redhat.com/errata/RHSA-2002-160.html
- http://rhn.redhat.com/errata/RHSA-2002-161.html
- http://rhn.redhat.com/errata/RHSA-2002-164.html
- http://www.cert.org/advisories/CA-2002-23.html
- http://www.iss.net/security_center/static/9718.php
- http://www.kb.cert.org/vuls/id/748355
- http://www.securityfocus.com/bid/5366

### **openssl** — CVE-2002-1568 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://cvs.openssl.org/chngview?cn=7659
- http://marc.info/?l=bugtraq&m=106511018214983
- http://www.ebitech.sk/patrik/SA/SA-20031002.txt

### **openssl** — CVE-2003-0078 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.netbsd.org/pub/NetBSD/security/advisories/NetBSD-SA2003-001.txt.asc
- ftp://patches.sgi.com/support/free/security/advisories/20030501-01-I
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000570
- http://marc.info/?l=bugtraq&m=104567627211904&w=2
- http://marc.info/?l=bugtraq&m=104568426824439&w=2
- http://marc.info/?l=bugtraq&m=104577183206905&w=2
- http://www.ciac.org/ciac/bulletins/n-051.shtml
- http://www.debian.org/security/2003/dsa-253
- http://www.iss.net/security_center/static/11369.php
- http://www.linuxsecurity.com/advisories/engarde_advisory-2874.html
- http://www.mandrakesoft.com/security/advisories?name=MDKSA-2003:020
- http://www.openssl.org/news/secadv_20030219.txt
- http://www.osvdb.org/3945
- http://www.redhat.com/support/errata/RHSA-2003-062.html
- http://www.redhat.com/support/errata/RHSA-2003-063.html
- http://www.redhat.com/support/errata/RHSA-2003-082.html
- http://www.redhat.com/support/errata/RHSA-2003-104.html
- http://www.redhat.com/support/errata/RHSA-2003-205.html
- http://www.securityfocus.com/bid/6884
- http://www.trustix.org/errata/2003/0005

### **openssl** — CVE-2003-0131 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- ftp://ftp.netbsd.org/pub/NetBSD/security/advisories/NetBSD-SA2003-007.txt.asc
- ftp://ftp.sco.com/pub/security/OpenLinux/CSSA-2003-014.0.txt
- ftp://patches.sgi.com/support/free/security/advisories/20030501-01-I
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000625
- http://eprint.iacr.org/2003/052/
- http://lists.apple.com/mhonarc/security-announce/msg00028.html
- http://marc.info/?l=bugtraq&m=104811162730834&w=2
- http://marc.info/?l=bugtraq&m=104852637112330&w=2
- http://marc.info/?l=bugtraq&m=104878215721135&w=2
- http://www.debian.org/security/2003/dsa-288
- http://www.gentoo.org/security/en/glsa/glsa-200303-20.xml
- http://www.kb.cert.org/vuls/id/888801
- http://www.linuxsecurity.com/advisories/immunix_advisory-3066.html
- http://www.mandriva.com/security/advisories?name=MDKSA-2003:035
- http://www.openpkg.org/security/OpenPKG-SA-2003.026-openssl.html
- http://www.openssl.org/news/secadv_20030319.txt
- http://www.redhat.com/support/errata/RHSA-2003-101.html
- http://www.redhat.com/support/errata/RHSA-2003-102.html
- http://www.securityfocus.com/archive/1/316577/30/25310/threaded
- http://www.securityfocus.com/bid/7148
- https://exchange.xforce.ibmcloud.com/vulnerabilities/11586
- https://lists.opensuse.org/opensuse-security-announce/2003-04/msg00005.html
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A461

### **openssl** — CVE-2003-0147 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.sco.com/pub/security/OpenLinux/CSSA-2003-014.0.txt
- ftp://patches.sgi.com/support/free/security/advisories/20030501-01-I
- http://archives.neohapsis.com/archives/vulnwatch/2003-q1/0130.html
- http://crypto.stanford.edu/~dabo/papers/ssl-timing.pdf
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000625
- http://marc.info/?l=bugtraq&m=104766550528628&w=2
- http://marc.info/?l=bugtraq&m=104792570615648&w=2
- http://marc.info/?l=bugtraq&m=104819602408063&w=2
- http://marc.info/?l=bugtraq&m=104829040921835&w=2
- http://marc.info/?l=bugtraq&m=104861762028637&w=2
- http://www.debian.org/security/2003/dsa-288
- http://www.gentoo.org/security/en/glsa/glsa-200303-23.xml
- http://www.kb.cert.org/vuls/id/997481
- http://www.mandrakesecure.net/en/advisories/advisory.php?name=MDKSA-2003:035
- http://www.openpkg.com/security/advisories/OpenPKG-SA-2003.019.html
- http://www.openssl.org/news/secadv_20030317.txt
- http://www.redhat.com/support/errata/RHSA-2003-101.html
- http://www.redhat.com/support/errata/RHSA-2003-102.html
- http://www.securityfocus.com/archive/1/316165/30/25370/threaded
- http://www.securityfocus.com/archive/1/316577/30/25310/threaded
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A466

### **openssl** — CVE-2003-0543 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://bugzilla.redhat.com/bugzilla/show_bug.cgi?id=104893
- http://secunia.com/advisories/22249
- http://sunsolve.sun.com/search/document.do?assetkey=1-66-201029-1
- http://www-1.ibm.com/support/docview.wss?uid=swg21247112
- http://www.cert.org/advisories/CA-2003-26.html
- http://www.debian.org/security/2003/dsa-393
- http://www.debian.org/security/2003/dsa-394
- http://www.kb.cert.org/vuls/id/255484
- http://www.linuxsecurity.com/advisories/engarde_advisory-3693.html
- http://www.redhat.com/support/errata/RHSA-2003-291.html
- http://www.redhat.com/support/errata/RHSA-2003-292.html
- http://www.securityfocus.com/bid/8732
- http://www.uniras.gov.uk/vuls/2003/006489/openssl.htm
- http://www.vupen.com/english/advisories/2006/3900
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A4254
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A5292

### **openssl** — CVE-2003-0544 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://bugzilla.redhat.com/bugzilla/show_bug.cgi?id=104893
- http://secunia.com/advisories/22249
- http://sunsolve.sun.com/search/document.do?assetkey=1-66-201029-1
- http://www-1.ibm.com/support/docview.wss?uid=swg21247112
- http://www.cert.org/advisories/CA-2003-26.html
- http://www.debian.org/security/2003/dsa-393
- http://www.debian.org/security/2003/dsa-394
- http://www.kb.cert.org/vuls/id/380864
- http://www.linuxsecurity.com/advisories/engarde_advisory-3693.html
- http://www.redhat.com/support/errata/RHSA-2003-291.html
- http://www.redhat.com/support/errata/RHSA-2003-292.html
- http://www.securityfocus.com/bid/8732
- http://www.uniras.gov.uk/vuls/2003/006489/openssl.htm
- http://www.vupen.com/english/advisories/2006/3900
- https://exchange.xforce.ibmcloud.com/vulnerabilities/43041
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A4574

### **openssl** — CVE-2003-0545 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://secunia.com/advisories/22249
- http://www-1.ibm.com/support/docview.wss?uid=swg21247112
- http://www.cert.org/advisories/CA-2003-26.html
- http://www.debian.org/security/2003/dsa-394
- http://www.kb.cert.org/vuls/id/935264
- http://www.redhat.com/support/errata/RHSA-2003-292.html
- http://www.securityfocus.com/bid/8732
- http://www.uniras.gov.uk/vuls/2003/006489/openssl.htm
- http://www.vupen.com/english/advisories/2006/3900
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A2590

### **openssl** — CVE-2003-0851 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.netbsd.org/pub/NetBSD/security/advisories/NetBSD-SA2004-003.txt.asc
- ftp://patches.sgi.com/support/free/security/advisories/20040304-01-U.asc
- http://marc.info/?l=bugtraq&m=106796246511667&w=2
- http://marc.info/?l=bugtraq&m=108403850228012&w=2
- http://rhn.redhat.com/errata/RHSA-2004-119.html
- http://secunia.com/advisories/17381
- http://www.cisco.com/warp/public/707/cisco-sa-20030930-ssl.shtml
- http://www.kb.cert.org/vuls/id/412478
- http://www.openssl.org/news/secadv_20031104.txt
- http://www.redhat.com/archives/fedora-announce-list/2005-October/msg00087.html
- http://www.securityfocus.com/bid/8970
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A5528

### **openssl** — CVE-2004-0079 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- ftp://ftp.freebsd.org/pub/FreeBSD/CERT/advisories/FreeBSD-SA-04:05.openssl.asc
- ftp://ftp.netbsd.org/pub/NetBSD/security/advisories/NetBSD-SA2004-005.txt.asc
- ftp://ftp.sco.com/pub/updates/OpenServer/SCOSA-2004.10/SCOSA-2004.10.txt
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000834
- http://docs.info.apple.com/article.html?artnum=61798
- http://fedoranews.org/updates/FEDORA-2004-095.shtml
- http://lists.apple.com/archives/security-announce/2005//Aug/msg00001.html
- http://lists.apple.com/archives/security-announce/2005/Aug/msg00000.html
- http://lists.apple.com/mhonarc/security-announce/msg00045.html
- http://marc.info/?l=bugtraq&m=107953412903636&w=2
- http://marc.info/?l=bugtraq&m=108403806509920&w=2
- http://secunia.com/advisories/11139
- http://secunia.com/advisories/17381
- http://secunia.com/advisories/17398
- http://secunia.com/advisories/17401
- http://secunia.com/advisories/18247
- http://security.gentoo.org/glsa/glsa-200403-03.xml
- http://sunsolve.sun.com/pub-cgi/retrieve.pl?doc=fsalert/57524
- http://support.avaya.com/elmodocs2/security/ASA-2005-239.htm
- http://support.lexmark.com/index?page=content&id=TE88&locale=EN&userlocale=EN_US
- http://www.ciac.org/ciac/bulletins/o-101.shtml
- http://www.cisco.com/warp/public/707/cisco-sa-20040317-openssl.shtml
- http://www.debian.org/security/2004/dsa-465
- http://www.kb.cert.org/vuls/id/288574
- http://www.linuxsecurity.com/advisories/engarde_advisory-4135.html
- http://www.mandriva.com/security/advisories?name=MDKSA-2004:023
- http://www.novell.com/linux/security/advisories/2004_07_openssl.html
- http://www.openssl.org/news/secadv_20040317.txt
- http://www.redhat.com/archives/fedora-announce-list/2005-October/msg00087.html
- http://www.redhat.com/support/errata/RHSA-2004-120.html
- http://www.redhat.com/support/errata/RHSA-2004-121.html
- http://www.redhat.com/support/errata/RHSA-2004-139.html
- http://www.redhat.com/support/errata/RHSA-2005-829.html
- http://www.redhat.com/support/errata/RHSA-2005-830.html
- http://www.securityfocus.com/bid/9899
- http://www.slackware.org/security/viewer.php?l=slackware-security&y=2004&m=slackware-security.455961
- http://www.trustix.org/errata/2004/0012
- http://www.uniras.gov.uk/vuls/2004/224012/index.htm
- http://www.us-cert.gov/cas/techalerts/TA04-078A.html
- https://exchange.xforce.ibmcloud.com/vulnerabilities/15505
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A2621
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A5770
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A870
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A975
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A9779

### **openssl** — CVE-2004-0081 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.sco.com/pub/updates/OpenServer/SCOSA-2004.10/SCOSA-2004.10.txt
- ftp://patches.sgi.com/support/free/security/advisories/20040304-01-U.asc
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000834
- http://fedoranews.org/updates/FEDORA-2004-095.shtml
- http://marc.info/?l=bugtraq&m=107955049331965&w=2
- http://marc.info/?l=bugtraq&m=108403850228012&w=2
- http://rhn.redhat.com/errata/RHSA-2004-119.html
- http://secunia.com/advisories/11139
- http://security.gentoo.org/glsa/glsa-200403-03.xml
- http://sunsolve.sun.com/pub-cgi/retrieve.pl?doc=fsalert/57524
- http://www.cisco.com/warp/public/707/cisco-sa-20040317-openssl.shtml
- http://www.debian.org/security/2004/dsa-465
- http://www.kb.cert.org/vuls/id/465542
- http://www.linuxsecurity.com/advisories/engarde_advisory-4135.html
- http://www.redhat.com/support/errata/RHSA-2004-120.html
- http://www.redhat.com/support/errata/RHSA-2004-121.html
- http://www.redhat.com/support/errata/RHSA-2004-139.html
- http://www.securityfocus.com/bid/9899
- http://www.trustix.org/errata/2004/0012
- http://www.uniras.gov.uk/vuls/2004/224012/index.htm
- http://www.us-cert.gov/cas/techalerts/TA04-078A.html
- https://exchange.xforce.ibmcloud.com/vulnerabilities/15509
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A11755
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A871
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A902

### **openssl** — CVE-2004-0112 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- ftp://ftp.netbsd.org/pub/NetBSD/security/advisories/NetBSD-SA2004-005.txt.asc
- ftp://ftp.sco.com/pub/updates/OpenServer/SCOSA-2004.10/SCOSA-2004.10.txt
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000834
- http://docs.info.apple.com/article.html?artnum=61798
- http://lists.apple.com/archives/security-announce/2005//Aug/msg00001.html
- http://lists.apple.com/archives/security-announce/2005/Aug/msg00000.html
- http://lists.apple.com/mhonarc/security-announce/msg00045.html
- http://marc.info/?l=bugtraq&m=107953412903636&w=2
- http://marc.info/?l=bugtraq&m=108403806509920&w=2
- http://secunia.com/advisories/11139
- http://security.gentoo.org/glsa/glsa-200403-03.xml
- http://sunsolve.sun.com/pub-cgi/retrieve.pl?doc=fsalert/57524
- http://www.ciac.org/ciac/bulletins/o-101.shtml
- http://www.cisco.com/warp/public/707/cisco-sa-20040317-openssl.shtml
- http://www.kb.cert.org/vuls/id/484726
- http://www.mandriva.com/security/advisories?name=MDKSA-2004:023
- http://www.novell.com/linux/security/advisories/2004_07_openssl.html
- http://www.openssl.org/news/secadv_20040317.txt
- http://www.redhat.com/support/errata/RHSA-2004-120.html
- http://www.redhat.com/support/errata/RHSA-2004-121.html
- http://www.securityfocus.com/bid/9899
- http://www.slackware.org/security/viewer.php?l=slackware-security&y=2004&m=slackware-security.455961
- http://www.trustix.org/errata/2004/0012
- http://www.uniras.gov.uk/vuls/2004/224012/index.htm
- http://www.us-cert.gov/cas/techalerts/TA04-078A.html
- https://exchange.xforce.ibmcloud.com/vulnerabilities/15508
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A1049
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A928
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A9580

#### pandas

### **pandas** — CVE-2020-13091 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/0FuzzingQ/vuln/blob/master/pandas%20unserialize.md
- https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_pickle.html

#### postgresql

### **postgresql** — postgresql 14 EOL approaching (2026-11-12)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `14`

Timing: Effective 2026-11-12 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/postgresql

### **postgresql** — postgresql lifecycle: reached end-of-life (13, 12, 11, 10, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.4, 8.3, 8.2, 8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 6.5, 6.4, 6.3)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `13`, `12`, `11`, `10`, `9.6`, `9.5`, `9.4`, `9.3`, `9.2`, `9.1`, `9.0`, `8.4`, `8.3`, `8.2`, `8.1`, `8.0`, `7.4`, `7.3`, `7.2`, `7.1`, `7.0`, `6.5`, `6.4`, `6.3`

Timing: Effective 2003-03-01 (already effective)

Why it matters: EOL effective for scoped versions `13`, `12`, `11`, `10`, `9.6`, `9.5`, `9.4`, `9.3`, `9.2`, `9.1`, `9.0`, `8.4`, `8.3`, `8.2`, `8.1`, `8.0`, `7.4`, `7.3`, `7.2`, `7.1`, `7.0`, `6.5`, `6.4`, `6.3`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/postgresql

### **postgresql** — CVE-1999-0862 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://exchange.xforce.ibmcloud.com/vulnerabilities/CVE-1999-0862

### **postgresql** — CVE-2000-1199 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://marc.info/?l=bugtraq&m=95659987018649&w=2
- http://www.securityfocus.com/bid/1139
- https://exchange.xforce.ibmcloud.com/vulnerabilities/4364

### **postgresql** — CVE-2002-0802 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://marc.info/?l=postgresql-general&m=102032794322362
- http://www.iss.net/security_center/static/10328.php
- http://www.redhat.com/support/errata/RHSA-2002-149.html

### **postgresql** — CVE-2002-0972 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://marc.info/?l=bugtraq&m=102987608300785&w=2
- http://secunia.com/advisories/8034
- http://www.redhat.com/support/errata/RHSA-2003-001.html

### **postgresql** — CVE-2002-1397 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://developer.postgresql.org/cvsweb.cgi/pgsql-server/src/backend/utils/adt/cash.c.diff?r1=1.51&r2=1.52
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000524
- http://marc.info/?l=bugtraq&m=102977465204357&w=2
- http://secunia.com/advisories/8034
- http://www.redhat.com/support/errata/RHSA-2003-001.html
- http://www.securityfocus.com/bid/5497
- https://exchange.xforce.ibmcloud.com/vulnerabilities/9891

### **postgresql** — CVE-2002-1398 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://archives.postgresql.org/pgsql-announce/2002-08/msg00004.php
- http://marc.info/?l=bugtraq&m=102978152712430&w=2
- http://marc.info/?l=bugtraq&m=102996089613404&w=2
- http://marc.info/?l=bugtraq&m=103021186622725&w=2
- http://marc.info/?l=bugtraq&m=103036987114437&w=2
- http://marc.info/?l=postgresql-announce&m=103062536330644
- http://secunia.com/advisories/8034
- http://www.debian.org/security/2002/dsa-165
- http://www.novell.com/linux/security/advisories/2002_038_postgresql.html
- http://www.redhat.com/support/errata/RHSA-2003-001.html

### **postgresql** — CVE-2002-1399 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://archives.postgresql.org/pgsql-hackers/2002-08/msg00708.php
- http://archives.postgresql.org/pgsql-hackers/2002-08/msg00713.php
- http://marc.info/?l=bugtraq&m=102978152712430&w=2

### **postgresql** — CVE-2002-1400 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://archives.postgresql.org/pgsql-announce/2002-08/msg00004.php
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000524
- http://marc.info/?l=bugtraq&m=102987306029821&w=2
- http://marc.info/?l=bugtraq&m=103021186622725&w=2
- http://marc.info/?l=bugtraq&m=103036987114437&w=2
- http://marc.info/?l=postgresql-announce&m=103062536330644
- http://secunia.com/advisories/8034
- http://www.mandriva.com/security/advisories?name=MDKSA-2002:062
- http://www.novell.com/linux/security/advisories/2002_038_postgresql.html
- http://www.redhat.com/support/errata/RHSA-2003-001.html

### **postgresql** — CVE-2002-1401 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://archives.postgresql.org/pgsql-hackers/2002-08/msg02047.php
- http://archives.postgresql.org/pgsql-hackers/2002-08/msg02081.php
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000524
- http://secunia.com/advisories/8034
- http://www.debian.org/security/2002/dsa-165
- http://www.redhat.com/support/errata/RHSA-2003-001.html

### **postgresql** — CVE-2002-1402 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://archives.postgresql.org/pgsql-announce/2002-08/msg00004.php
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000524
- http://marc.info/?l=bugtraq&m=103021186622725&w=2
- http://marc.info/?l=bugtraq&m=103036987114437&w=2
- http://secunia.com/advisories/8034
- http://www.debian.org/security/2002/dsa-165
- http://www.mandriva.com/security/advisories?name=MDKSA-2002:062
- http://www.redhat.com/support/errata/RHSA-2003-001.html

### **postgresql** — CVE-2002-1642 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://archives.postgresql.org/pgsql-announce/2002-10/msg00000.php
- http://www.kb.cert.org/vuls/id/891177
- http://www.redhat.com/support/errata/RHSA-2003-001.html
- http://www.securityfocus.com/bid/7657
- https://exchange.xforce.ibmcloud.com/vulnerabilities/11102

### **postgresql** — CVE-2002-1657 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://archives.postgresql.org/pgsql-admin/2002-08/msg00253.php
- http://marc.info/?l=bugtraq&m=111402558115859&w=2
- http://marc.info/?l=bugtraq&m=111403050902165&w=2
- https://exchange.xforce.ibmcloud.com/vulnerabilities/20215

### **postgresql** — CVE-2003-0901 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://developer.postgresql.org/cvsweb.cgi/pgsql-server/src/backend/utils/adt/ascii.c
- http://distro.conectiva.com.br/atualizacoes/?id=a&anuncio=000784
- http://distro.conectiva.com.br/atualizacoes/index.php?id=a&anuncio=000772
- http://www.debian.org/security/2003/dsa-397
- http://www.redhat.com/support/errata/RHSA-2003-313.html
- http://www.redhat.com/support/errata/RHSA-2003-314.html
- http://www.securityfocus.com/bid/8741

### **postgresql** — CVE-2004-0547 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://www.debian.org/security/2004/dsa-516
- http://www.mandrakesecure.net/en/advisories/advisory.php?name=MDKSA-2004:072
- https://exchange.xforce.ibmcloud.com/vulnerabilities/16329

### **postgresql** — CVE-2005-0245 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://archives.postgresql.org/pgsql-committers/2005-01/msg00298.php
- http://archives.postgresql.org/pgsql-committers/2005-02/msg00049.php
- http://archives.postgresql.org/pgsql-patches/2005-01/msg00216.php
- http://marc.info/?l=bugtraq&m=110806034116082&w=2
- http://secunia.com/advisories/12948
- http://www.debian.org/security/2005/dsa-683
- http://www.mandriva.com/security/advisories?name=MDKSA-2005:040
- http://www.novell.com/linux/security/advisories/2005_36_sudo.html
- http://www.redhat.com/support/errata/RHSA-2005-138.html
- http://www.redhat.com/support/errata/RHSA-2005-150.html
- http://www.securityfocus.com/bid/12417
- https://exchange.xforce.ibmcloud.com/vulnerabilities/19188
- https://oval.cisecurity.org/repository/search/definition/oval%3Aorg.mitre.oval%3Adef%3A10175

#### prometheus

### **prometheus** — prometheus 3.15 EOL approaching (2026-11-06)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.15`

Timing: Effective 2026-11-06 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/prometheus

### **prometheus** — prometheus lifecycle: reached end-of-life (3.14, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.55, 2.54, 2.53, 2.52, 2.51, 2.50, 2.49, 2.48, 2.47, 2.46, 2.45, 2.44, 2.43, 2.42, 2.41, 2.40, 2.39, 2.38, 2.37, 2.36)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.14`, `3.12`, `3.11`, `3.10`, `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.55`, `2.54`, `2.53`, `2.52`, `2.51`, `2.50`, `2.49`, `2.48`, `2.47`, `2.46`, `2.45`, `2.44`, `2.43`, `2.42`, `2.41`, `2.40`, `2.39`, `2.38`, `2.37`, `2.36`

Timing: Effective 2022-07-11 (already effective)

Why it matters: EOL effective for scoped versions `3.14`, `3.12`, `3.11`, `3.10`, `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.55`, `2.54`, `2.53`, `2.52`, `2.51`, `2.50`, `2.49`, `2.48`, `2.47`, `2.46`, `2.45`, `2.44`, `2.43`, `2.42`, `2.41`, `2.40`, `2.39`, `2.38`, `2.37`, `2.36`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/prometheus

### **prometheus** — CVE-2002-1211 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://archives.neohapsis.com/archives/vulnwatch/2002-q4/0050.html
- http://marc.info/?l=bugtraq&m=103616306403031&w=2
- http://www.idefense.com/advisory/10.31.02b.txt
- http://www.iss.net/security_center/static/10515.php
- http://www.securityfocus.com/bid/6087

### **prometheus** — CVE-2019-3826 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://access.redhat.com/errata/RHBA-2019:0327
- https://advisory.checkmarx.net/advisory/CX-2019-4297
- https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2019-3826
- https://github.com/prometheus/prometheus/commit/62e591f9
- https://github.com/prometheus/prometheus/pull/5163
- https://lists.apache.org/thread.html/r48d5019bd42e0770f7e5351e420a63a41ff1f16924942442c6aff6a8%40%3Ccommits.zookeeper.apache.org%3E
- https://lists.apache.org/thread.html/r8e3f7da12bf5750b0a02e69a78a61073a2ac950eed7451ce70a65177%40%3Ccommits.zookeeper.apache.org%3E
- https://lists.apache.org/thread.html/rdf2a0d94c3b5b523aeff7741ae71347415276062811b687f30ea6573%40%3Ccommits.zookeeper.apache.org%3E

### **prometheus** — CVE-2021-29622 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/prometheus/prometheus/releases/tag/v2.26.1
- https://github.com/prometheus/prometheus/releases/tag/v2.27.1
- https://github.com/prometheus/prometheus/security/advisories/GHSA-vx57-7f4q-fpc7

#### redis

### **redis** — redis lifecycle: ended active support (8.10, 8.8, 8.6, 8.4, 8.2, 8.0, 7.4, 7.2, 6.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `8.10`, `8.8`, `8.6`, `8.4`, `8.2`, `8.0`, `7.4`, `7.2`, `6.2`

Timing: Effective 2022-04-27 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/redis

### **redis** — redis 8.0 EOL approaching (2026-12-01)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `8.0`

Timing: Effective 2026-12-01 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/redis

### **redis** — redis lifecycle: reached end-of-life (7.0, 6.0, 5.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `7.0`, `6.0`, `5.0`

Timing: Effective 2022-04-27 (already effective)

Why it matters: EOL effective for scoped versions `7.0`, `6.0`, `5.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/redis

### **redis** — CVE-2013-7458 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- http://lists.opensuse.org/opensuse-updates/2016-08/msg00029.html
- http://lists.opensuse.org/opensuse-updates/2016-08/msg00030.html
- http://www.debian.org/security/2016/dsa-3634
- https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=832460
- https://github.com/antirez/linenoise/issues/121
- https://github.com/antirez/linenoise/pull/122
- https://github.com/antirez/redis/blob/3.2/00-RELEASENOTES
- https://github.com/antirez/redis/issues/3284
- https://github.com/antirez/redis/pull/1418
- https://github.com/antirez/redis/pull/3322

### **redis** — CVE-2015-4335 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://benmmurphy.github.io/blog/2015/06/04/redis-eval-lua-sandbox-escape/
- http://lists.fedoraproject.org/pipermail/package-announce/2015-July/162094.html
- http://lists.fedoraproject.org/pipermail/package-announce/2015-July/162146.html
- http://lists.opensuse.org/opensuse-updates/2015-10/msg00014.html
- http://rhn.redhat.com/errata/RHSA-2015-1676.html
- http://www.debian.org/security/2015/dsa-3279
- http://www.openwall.com/lists/oss-security/2015/06/04/12
- http://www.openwall.com/lists/oss-security/2015/06/04/8
- http://www.openwall.com/lists/oss-security/2015/06/05/3
- http://www.securityfocus.com/bid/75034
- https://github.com/antirez/redis/commit/fdf9d455098f54f7666c702ae464e6ea21e25411
- https://groups.google.com/forum/#%21msg/redis-db/4Y6OqK8gEyk/Dg-5cejl-eUJ
- https://security.gentoo.org/glsa/201702-16

### **redis** — CVE-2015-8080 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://lists.opensuse.org/opensuse-updates/2016-05/msg00126.html
- http://rhn.redhat.com/errata/RHSA-2016-0095.html
- http://rhn.redhat.com/errata/RHSA-2016-0096.html
- http://rhn.redhat.com/errata/RHSA-2016-0097.html
- http://www.debian.org/security/2015/dsa-3412
- http://www.openwall.com/lists/oss-security/2015/11/06/2
- http://www.openwall.com/lists/oss-security/2015/11/06/4
- http://www.securityfocus.com/bid/77507
- https://github.com/antirez/redis/issues/2855
- https://raw.githubusercontent.com/antirez/redis/2.8/00-RELEASENOTES
- https://raw.githubusercontent.com/antirez/redis/3.0/00-RELEASENOTES
- https://security.gentoo.org/glsa/201702-16

### **redis** — CVE-2016-10517 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/101572
- https://github.com/antirez/redis/commit/874804da0c014a7d704b3d285aa500098a931f50
- https://raw.githubusercontent.com/antirez/redis/3.2/00-RELEASENOTES
- https://www.reddit.com/r/redis/comments/5r8wxn/redis_327_is_out_important_security_fixes_inside/

### **redis** — CVE-2016-8339 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- http://www.securityfocus.com/bid/93283
- http://www.talosintelligence.com/reports/TALOS-2016-0206/
- https://github.com/antirez/redis/commit/6d9f8e2462fc2c426d48c941edeb78e5df7d2977
- https://security.gentoo.org/glsa/201702-16

### **redis** — CVE-2017-15047 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/antirez/redis/issues/4278
- https://security.gentoo.org/glsa/202008-17

### **redis** — CVE-2018-12453 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://gist.github.com/fakhrizulkifli/34a56d575030682f6c564553c53b82b5
- https://github.com/antirez/redis/commit/c04082cf138f1f51cedf05ee9ad36fb6763cafc6
- https://www.exploit-db.com/exploits/44908/

#### timescaledb

### **timescaledb** — CVE-2022-24128 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://docs.timescale.com/timescaledb/latest/overview/release-notes/
- https://github.com/timescale/timescaledb/commit/6275c2985927cfd4900b85cac5120227c8cb1f0c
- https://github.com/timescale/timescaledb/commit/c8b8516e466c2bb7d2ae6a4b0b2e8e60b24b24a2
- https://github.com/timescale/timescaledb/security/advisories/GHSA-fh8v-663w-79w9

### **timescaledb** — CVE-2023-25149 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/timescale/timescaledb/pull/5259
- https://github.com/timescale/timescaledb/releases/tag/2.9.3
- https://github.com/timescale/timescaledb/security/advisories/GHSA-44jh-j22r-33wq

### **timescaledb** — CVE-2026-29089 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/timescale/timescaledb/commit/9a8f7f8bdeb99e6abae0786ffe526791a8628ce3
- https://github.com/timescale/timescaledb/pull/9331
- https://github.com/timescale/timescaledb/releases/tag/2.25.2
- https://github.com/timescale/timescaledb/security/advisories/GHSA-vgp2-jj5c-828m

### **timescaledb** — CVE-2026-70633 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-dos-via-gorilla-compression-reverse-iterator

### **timescaledb** — CVE-2026-70634 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-information-disclosure-via-dictionary-compression-reverse-iterator

### **timescaledb** — CVE-2026-70635 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/timescale/timescaledb/commit/517c13e7cc6afadb4a7deaa7a5a5a29065e5b5a3
- https://github.com/timescale/timescaledb/pull/10360
- https://www.vulncheck.com/advisories/timescaledb-out-of-bounds-read-dos-via-bulk-dictionary-decompression-negative-index

#### webpack

### **webpack** — CVE-2023-28154 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Assess whether the affected package and version are in your inventory.

Evidence:
- https://github.com/webpack/webpack/compare/v5.75.0...v5.76.0
- https://github.com/webpack/webpack/pull/16500
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/AU7BOXTBK3KDYSWH67ASZ22TUIOZ3X5G/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/PPSAXUTXBCCTAHTCX5BUR4YVP25XALQ3/
- https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/U2AFCM6FFE3LRYI6KNEQWKMXMQOBZQ2D/

### **webpack** — CVE-2024-43788 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/webpack/webpack/commit/955e057abc6cc83cbc3fa1e1ef67a49758bf5a61
- https://github.com/webpack/webpack/issues/18718#issuecomment-2326296270
- https://github.com/webpack/webpack/security/advisories/GHSA-4vvj-4cpr-p986
- https://research.securitum.com/xss-in-amp4email-dom-clobbering
- https://scnps.co/papers/sp23_domclob.pdf

### **webpack** — CVE-2025-68157 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/webpack/webpack/security/advisories/GHSA-38r7-794h-5758

### **webpack** — CVE-2025-68458 [AFFECTS_PACKAGE] tracked by nvd

Category: Security · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: project

Sources: nvd

Timing: Effective date unknown

Why it matters: AFFECTS_PACKAGE from security correlation; placement follows analyst impact

Investigate: Track the advisory; confirm exposure if a version match emerges.

Evidence:
- https://github.com/webpack/webpack/security/advisories/GHSA-8fgc-7cc6-rx7x

#### airflow

### **airflow** — apache-airflow 3.3 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.3`

Timing: Effective date unknown

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/apache-airflow

### **airflow** — apache-airflow lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2, 1.10, 1.9, 1.8, 1.7)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.2`, `3.1`, `3.0`, `2`, `1.10`, `1.9`, `1.8`, `1.7`

Timing: Effective 2017-03-19 (already effective)

Why it matters: EOL effective for scoped versions `3.2`, `3.1`, `3.0`, `2`, `1.10`, `1.9`, `1.8`, `1.7`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-airflow

#### angular

### **angular** — angular lifecycle: ended active support (21, 20)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `21`, `20`

Timing: Effective 2025-11-19 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/angular

### **angular** — angular 20 EOL approaching (2026-11-28)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `20`

Timing: Effective 2026-11-28 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/angular

### **angular** — angular lifecycle: reached end-of-life (19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `19`, `18`, `17`, `16`, `15`, `14`, `13`, `12`, `11`, `10`, `9`

Timing: Effective 2021-08-06 (already effective)

Why it matters: EOL effective for scoped versions `19`, `18`, `17`, `16`, `15`, `14`, `13`, `12`, `11`, `10`, `9`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/angular

#### ansible

### **ansible** — ansible lifecycle: reached end-of-life (13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2.10, 2.9)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `13`, `12`, `11`, `10`, `9`, `8`, `7`, `6`, `5`, `4`, `3`, `2.10`, `2.9`

Timing: Effective 2021-02-09 (already effective)

Why it matters: EOL effective for scoped versions `13`, `12`, `11`, `10`, `9`, `8`, `7`, `6`, `5`, `4`, `3`, `2.10`, `2.9`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/ansible

#### argocd

### **argocd** — argo-cd lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.14, 2.13, 2.12, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.2`, `3.1`, `3.0`, `2.14`, `2.13`, `2.12`, `2.11`, `2.10`, `2.9`, `2.8`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2019-11-13 (already effective)

Why it matters: EOL effective for scoped versions `3.2`, `3.1`, `3.0`, `2.14`, `2.13`, `2.12`, `2.11`, `2.10`, `2.9`, `2.8`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/argo-cd

#### calico

### **calico** — calico lifecycle: reached end-of-life (3.30, 3.29, 3.28, 3.27, 3.26, 3.25)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.30`, `3.29`, `3.28`, `3.27`, `3.26`, `3.25`

Timing: Effective 2023-12-15 (already effective)

Why it matters: EOL effective for scoped versions `3.30`, `3.29`, `3.28`, `3.27`, `3.26`, `3.25`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/calico

#### cassandra

### **cassandra** — apache-cassandra lifecycle: reached end-of-life (3.11, 3.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.11`, `3.0`

Timing: Effective 2024-09-05 (already effective)

Why it matters: EOL effective for scoped versions `3.11`, `3.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-cassandra

#### cert-manager

### **cert-manager** — cert-manager lifecycle: reached end-of-life (1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`

Timing: Effective 2023-05-19 (already effective)

Why it matters: EOL effective for scoped versions `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/cert-manager

#### cilium

### **cilium** — cilium lifecycle: reached end-of-life (1.17, 1.16, 1.15, 1.14, 1.13)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.17`, `1.16`, `1.15`, `1.14`, `1.13`

Timing: Effective 2024-07-24 (already effective)

Why it matters: EOL effective for scoped versions `1.17`, `1.16`, `1.15`, `1.14`, `1.13`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/cilium

#### clickhouse

### **clickhouse** — clickhouse lifecycle: reached end-of-life (26.6, 26.5, 26.4, 26.2, 26.1, 25.12, 25.11, 25.10, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `26.6`, `26.5`, `26.4`, `26.2`, `26.1`, `25.12`, `25.11`, `25.10`, `25.9`, `25.8`, `25.7`, `25.6`, `25.5`, `25.4`, `25.3`, `25.2`, `25.1`

Timing: Effective 2025-04-22 (already effective)

Why it matters: EOL effective for scoped versions `26.6`, `26.5`, `26.4`, `26.2`, `26.1`, `25.12`, `25.11`, `25.10`, `25.9`, `25.8`, `25.7`, `25.6`, `25.5`, `25.4`, `25.3`, `25.2`, `25.1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/clickhouse

### **clickhouse** — clickhouse 26.3 EOL approaching (2027-03-26)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `26.3`

Timing: Effective 2027-03-26 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/clickhouse

#### consul

### **consul** — consul 1.22 EOL approaching (2026-10-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.22`

Timing: Effective 2026-10-31 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/consul

### **consul** — consul lifecycle: reached end-of-life (1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`

Timing: Effective 2020-11-24 (already effective)

Why it matters: EOL effective for scoped versions `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/consul

#### containerd

### **containerd** — containerd lifecycle: approaching end-of-life (2.2, 2.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `2.2`, `2.0`

Timing: Effective 2026-11-06 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/containerd

### **containerd** — containerd lifecycle: reached end-of-life (2.1, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `2.1`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2018-12-05 (already effective)

Why it matters: EOL effective for scoped versions `2.1`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/containerd

### **containerd** — containerd 2.0 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `2.0`

Timing: Effective 2025-11-07 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/containerd

#### couchdb

### **couchdb** — apache-couchdb lifecycle: reached end-of-life (3.3, 3.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.3`, `3.2`

Timing: Effective 2024-09-20 (already effective)

Why it matters: EOL effective for scoped versions `3.3`, `3.2`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-couchdb

#### cpython

### **cpython** — python lifecycle: ended active support (3.13, 3.12, 3.11, 3.10)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.13`, `3.12`, `3.11`, `3.10`

Timing: Effective 2023-04-05 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/python

### **cpython** — python 3.10 EOL approaching (2026-10-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.10`

Timing: Effective 2026-10-31 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/python

### **cpython** — python lifecycle: reached end-of-life (3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 2.7, 3.1, 3.0, 2.6)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `2.7`, `3.1`, `3.0`, `2.6`

Timing: Effective 2009-06-27 (already effective)

Why it matters: EOL effective for scoped versions `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `2.7`, `3.1`, `3.0`, `2.6`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/python

#### django

### **django** — django lifecycle: ended active support (6.0, 5.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `6.0`, `5.2`

Timing: Effective 2025-12-03 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/django

### **django** — django lifecycle: reached end-of-life (5.1, 5.0, 4.2, 4.1, 4.0, 3.2, 3.1, 3.0, 2.2, 2.1, 2.0, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `5.1`, `5.0`, `4.2`, `4.1`, `4.0`, `3.2`, `3.1`, `3.0`, `2.2`, `2.1`, `2.0`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`

Timing: Effective 2013-02-26 (already effective)

Why it matters: EOL effective for scoped versions `5.1`, `5.0`, `4.2`, `4.1`, `4.0`, `3.2`, `3.1`, `3.0`, `2.2`, `2.1`, `2.0`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/django

#### elasticsearch

### **elasticsearch** — elasticsearch lifecycle: reached end-of-life (9.3, 9.2, 9.1, 8.18, 9.0, 8.17, 8.16, 7, 6)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `9.3`, `9.2`, `9.1`, `8.18`, `9.0`, `8.17`, `8.16`, `7`, `6`

Timing: Effective 2022-02-10 (already effective)

Why it matters: EOL effective for scoped versions `9.3`, `9.2`, `9.1`, `8.18`, `9.0`, `8.17`, `8.16`, `7`, `6`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/elasticsearch

#### envoy

### **envoy** — envoy lifecycle: approaching end-of-life (1.37, 1.36)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.37`, `1.36`

Timing: Effective 2026-10-14 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/envoy

### **envoy** — envoy lifecycle: reached end-of-life (1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.35`, `1.34`, `1.33`, `1.32`, `1.31`, `1.30`, `1.29`, `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2016-11-30 (already effective)

Why it matters: EOL effective for scoped versions `1.35`, `1.34`, `1.33`, `1.32`, `1.31`, `1.30`, `1.29`, `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/envoy

#### etcd

### **etcd** — etcd lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.4`, `3.3`, `3.2`, `3.1`, `3.0`

Timing: Effective 2017-01-20 (already effective)

Why it matters: EOL effective for scoped versions `3.4`, `3.3`, `3.2`, `3.1`, `3.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/etcd

#### express

### **express** — express lifecycle: reached end-of-life (3, 2, 1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3`, `2`, `1`

Timing: Effective 2011-03-01 (already effective)

Why it matters: EOL effective for scoped versions `3`, `2`, `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/express

#### flux

### **flux** — flux lifecycle: reached end-of-life (2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.25)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.25`

Timing: Effective 2022-11-02 (already effective)

Why it matters: EOL effective for scoped versions `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.25`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/flux

#### go

### **go** — go lifecycle: reached end-of-life (1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`

Timing: Effective 2019-02-25 (already effective)

Why it matters: EOL effective for scoped versions `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/go

#### haproxy

### **haproxy** — haproxy 3.3 EOL approaching (2027-01-01)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `3.3`

Timing: Effective 2027-01-01 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/haproxy

### **haproxy** — haproxy lifecycle: reached end-of-life (3.1, 2.9, 2.7, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.1`, `2.9`, `2.7`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2001-12-30 (already effective)

Why it matters: EOL effective for scoped versions `3.1`, `2.9`, `2.7`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/haproxy

#### istio

### **istio** — istio lifecycle: approaching end-of-life (1.31, 1.30, 1.29)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.31`, `1.30`, `1.29`

Timing: Effective 2026-10-31 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/istio

### **istio** — istio lifecycle: reached end-of-life (1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`

Timing: Effective 2021-02-25 (already effective)

Why it matters: EOL effective for scoped versions `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/istio

#### jaeger

### **jaeger** — jaeger 1 is end-of-life

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1`

Timing: Effective 2025-12-31 (already effective)

Why it matters: EOL effective for scoped versions `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/jaeger

#### jenkins

### **jenkins** — jenkins lifecycle: reached end-of-life (2.555, 2.541, 2.528, 2.516, 2.504, 2.492, 2.479, 2.462, 2.452, 2.440, 2.426, 2.414, 2.401, 2.387, 2.375, 2.361, 2.346)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `2.555`, `2.541`, `2.528`, `2.516`, `2.504`, `2.492`, `2.479`, `2.462`, `2.452`, `2.440`, `2.426`, `2.414`, `2.401`, `2.387`, `2.375`, `2.361`, `2.346`

Timing: Effective 2022-09-07 (already effective)

Why it matters: EOL effective for scoped versions `2.555`, `2.541`, `2.528`, `2.516`, `2.504`, `2.492`, `2.479`, `2.462`, `2.452`, `2.440`, `2.426`, `2.414`, `2.401`, `2.387`, `2.375`, `2.361`, `2.346`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/jenkins

#### kubernetes

### **kubernetes** — kubernetes lifecycle: approaching end-of-life (1.35, 1.34)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `1.35`, `1.34`

Timing: Effective 2026-10-27 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/kubernetes

### **kubernetes** — kubernetes 1.34 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `1.34`

Timing: Effective 2026-08-27 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/kubernetes

### **kubernetes** — kubernetes lifecycle: reached end-of-life (1.33, 1.32, 1.31, 1.30, 1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.33`, `1.32`, `1.31`, `1.30`, `1.29`, `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`

Timing: Effective 2020-08-04 (already effective)

Why it matters: EOL effective for scoped versions `1.33`, `1.32`, `1.31`, `1.30`, `1.29`, `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/kubernetes

#### kyverno

### **kyverno** — kyverno lifecycle: reached end-of-life (1.16, 1.15, 1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`

Timing: Effective 2023-11-10 (already effective)

Why it matters: EOL effective for scoped versions `1.16`, `1.15`, `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/kyverno

#### mariadb

### **mariadb** — mariadb 13.0 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `13.0`

Timing: Effective 2026-12-31 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/mariadb

### **mariadb** — mariadb lifecycle: reached end-of-life (12.2, 12.1, 12.0, 11.7, 11.6, 11.5, 11.3, 11.2, 11.1, 11.0, 10.10, 10.9, 10.8, 10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 5.5, 5.3, 5.2, 5.1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `12.2`, `12.1`, `12.0`, `11.7`, `11.6`, `11.5`, `11.3`, `11.2`, `11.1`, `11.0`, `10.10`, `10.9`, `10.8`, `10.7`, `10.6`, `10.5`, `10.4`, `10.3`, `10.2`, `10.1`, `10.0`, `5.5`, `5.3`, `5.2`, `5.1`

Timing: Effective 2015-02-01 (already effective)

Why it matters: EOL effective for scoped versions `12.2`, `12.1`, `12.0`, `11.7`, `11.6`, `11.5`, `11.3`, `11.2`, `11.1`, `11.0`, `10.10`, `10.9`, `10.8`, `10.7`, `10.6`, `10.5`, `10.4`, `10.3`, `10.2`, `10.1`, `10.0`, `5.5`, `5.3`, `5.2`, `5.1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/mariadb

#### maven

### **maven** — apache-maven lifecycle: reached end-of-life (3.8, 3.6, 3.5, 3.3, 3.2, 3.1, 3.0, 2, 1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.8`, `3.6`, `3.5`, `3.3`, `3.2`, `3.1`, `3.0`, `2`, `1`

Timing: Effective 2013-06-28 (already effective)

Why it matters: EOL effective for scoped versions `3.8`, `3.6`, `3.5`, `3.3`, `3.2`, `3.1`, `3.0`, `2`, `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-maven

#### memcached

### **memcached** — memcached lifecycle: reached end-of-life (1.5, 1.4)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.5`, `1.4`

Timing: Effective 2017-07-21 (already effective)

Why it matters: EOL effective for scoped versions `1.5`, `1.4`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/memcached

#### mongodb

### **mongodb** — mongodb lifecycle: reached end-of-life (8.2, 8.1, 7.3, 7.2, 7.1, 6.3, 6.2, 6.1, 6.0, 5.3, 5.2, 5.1, 5.0, 4.4, 4.2, 4.0, 3.6, 3.4, 3.2, 3.0, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `8.2`, `8.1`, `7.3`, `7.2`, `7.1`, `6.3`, `6.2`, `6.1`, `6.0`, `5.3`, `5.2`, `5.1`, `5.0`, `4.4`, `4.2`, `4.0`, `3.6`, `3.4`, `3.2`, `3.0`, `2.6`, `2.4`, `2.2`, `2.0`, `1.8`, `1.6`, `1.4`, `1.2`, `1.0`

Timing: Effective 2010-08-31 (already effective)

Why it matters: EOL effective for scoped versions `8.2`, `8.1`, `7.3`, `7.2`, `7.1`, `6.3`, `6.2`, `6.1`, `6.0`, `5.3`, `5.2`, `5.1`, `5.0`, `4.4`, `4.2`, `4.0`, `3.6`, `3.4`, `3.2`, `3.0`, `2.6`, `2.4`, `2.2`, `2.0`, `1.8`, `1.6`, `1.4`, `1.2`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/mongodb

#### mysql

### **mysql** — mysql lifecycle: reached end-of-life (9.6, 9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.3, 8.2, 8.1, 8.0, 5.7, 5.6, 5.5)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `9.6`, `9.5`, `9.4`, `9.3`, `9.2`, `9.1`, `9.0`, `8.3`, `8.2`, `8.1`, `8.0`, `5.7`, `5.6`, `5.5`

Timing: Effective 2018-12-31 (already effective)

Why it matters: EOL effective for scoped versions `9.6`, `9.5`, `9.4`, `9.3`, `9.2`, `9.1`, `9.0`, `8.3`, `8.2`, `8.1`, `8.0`, `5.7`, `5.6`, `5.5`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/mysql

#### neo4j

### **neo4j** — neo4j lifecycle: reached end-of-life (2026.08, 2026.07, 2026.06, 2026.05, 2026.04, 2026.03, 2026.02, 2026.01, 2025.12, 2025.11, 2025.10, 2025.09, 2025.08, 2025.07, 2025.06, 2025.05, 2025.04, 2025.03, 2025.02, 2025.01, 5.25, 5.24, 5.23, 5.22, 5.21, 5.20, 5.19, 5.18, 5.17, 5.16, 5.15, 5.14, 5.13, 5.12, 5.11, 5.10, 5.9, 5.8, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.4, 4.3, 4.2, 4.1, 4.0, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `2026.08`, `2026.07`, `2026.06`, `2026.05`, `2026.04`, `2026.03`, `2026.02`, `2026.01`, `2025.12`, `2025.11`, `2025.10`, `2025.09`, `2025.08`, `2025.07`, `2025.06`, `2025.05`, `2025.04`, `2025.03`, `2025.02`, `2025.01`, `5.25`, `5.24`, `5.23`, `5.22`, `5.21`, `5.20`, `5.19`, `5.18`, `5.17`, `5.16`, `5.15`, `5.14`, `5.13`, `5.12`, `5.11`, `5.10`, `5.9`, `5.8`, `5.7`, `5.6`, `5.5`, `5.4`, `5.3`, `5.2`, `5.1`, `4.4`, `4.3`, `4.2`, `4.1`, `4.0`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.3`, `2.2`, `2.1`, `2.0`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2011-08-23 (already effective)

Why it matters: EOL effective for scoped versions `2026.08`, `2026.07`, `2026.06`, `2026.05`, `2026.04`, `2026.03`, `2026.02`, `2026.01`, `2025.12`, `2025.11`, `2025.10`, `2025.09`, `2025.08`, `2025.07`, `2025.06`, `2025.05`, `2025.04`, `2025.03`, `2025.02`, `2025.01`, `5.25`, `5.24`, `5.23`, `5.22`, `5.21`, `5.20`, `5.19`, `5.18`, `5.17`, `5.16`, `5.15`, `5.14`, `5.13`, `5.12`, `5.11`, `5.10`, `5.9`, `5.8`, `5.7`, `5.6`, `5.5`, `5.4`, `5.3`, `5.2`, `5.1`, `4.4`, `4.3`, `4.2`, `4.1`, `4.0`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.3`, `2.2`, `2.1`, `2.0`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/neo4j

#### nginx

### **nginx** — nginx lifecycle: reached end-of-life (1.29, 1.28, 1.27, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.16, 1.14, 1.12, 1.10, 1.8, 1.6, 1.4, 1.2, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.29`, `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.16`, `1.14`, `1.12`, `1.10`, `1.8`, `1.6`, `1.4`, `1.2`, `1.0`

Timing: Effective 2012-04-23 (already effective)

Why it matters: EOL effective for scoped versions `1.29`, `1.28`, `1.27`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.16`, `1.14`, `1.12`, `1.10`, `1.8`, `1.6`, `1.4`, `1.2`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/nginx

#### numpy

### **numpy** — numpy 2.2 EOL approaching (2026-12-09)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `2.2`

Timing: Effective 2026-12-09 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/numpy

### **numpy** — numpy lifecycle: reached end-of-life (2.1, 2.0, 1.26, 1.25, 1.24, 1.23, 1.22, 1.21, 1.20, 1.19, 1.18, 1.17, 1.16, 1.15, 1.14)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `2.1`, `2.0`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`

Timing: Effective 2020-01-07 (already effective)

Why it matters: EOL effective for scoped versions `2.1`, `2.0`, `1.26`, `1.25`, `1.24`, `1.23`, `1.22`, `1.21`, `1.20`, `1.19`, `1.18`, `1.17`, `1.16`, `1.15`, `1.14`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/numpy

#### php

### **php** — php lifecycle: ended active support (8.3, 8.2)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `8.3`, `8.2`

Timing: Effective 2024-12-31 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/php

### **php** — php 8.2 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `8.2`

Timing: Effective 2026-12-31 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/php

### **php** — php lifecycle: reached end-of-life (8.1, 8.0, 7.4, 7.3, 7.2, 7.1, 7.0, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 5.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `8.1`, `8.0`, `7.4`, `7.3`, `7.2`, `7.1`, `7.0`, `5.6`, `5.5`, `5.4`, `5.3`, `5.2`, `5.1`, `5.0`

Timing: Effective 2005-09-05 (already effective)

Why it matters: EOL effective for scoped versions `8.1`, `8.0`, `7.4`, `7.3`, `7.2`, `7.1`, `7.0`, `5.6`, `5.5`, `5.4`, `5.3`, `5.2`, `5.1`, `5.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/php

#### pulsar

### **pulsar** — apache-pulsar lifecycle: reached end-of-life (4.2, 4.1, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `4.2`, `4.1`, `3.3`, `3.2`, `3.1`, `3.0`, `2.11`, `2.10`, `2.9`, `2.8`, `2.7`, `2.6`, `2.5`

Timing: Effective 2021-01-15 (already effective)

Why it matters: EOL effective for scoped versions `4.2`, `4.1`, `3.3`, `3.2`, `3.1`, `3.0`, `2.11`, `2.10`, `2.9`, `2.8`, `2.7`, `2.6`, `2.5`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-pulsar

### **pulsar** — apache-pulsar 4.0 EOL approaching (2026-10-21)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.0`

Timing: Effective 2026-10-21 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/apache-pulsar

#### rabbitmq

### **rabbitmq** — rabbitmq lifecycle: reached end-of-life (4.2, 4.1, 4.0, 3.13, 3.12, 3.11, 3.10, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `4.2`, `4.1`, `4.0`, `3.13`, `3.12`, `3.11`, `3.10`, `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`

Timing: Effective 2013-11-30 (already effective)

Why it matters: EOL effective for scoped versions `4.2`, `4.1`, `4.0`, `3.13`, `3.12`, `3.11`, `3.10`, `3.9`, `3.8`, `3.7`, `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/rabbitmq

#### react

### **react** — react lifecycle: ended active support (19, 18, 17, 16, 15)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `19`, `18`, `17`, `16`, `15`

Timing: Effective 2020-10-14 (already effective)

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/react

#### ruby

### **ruby** — ruby lifecycle: reached end-of-life (3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0.0, 1.9.3)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.2`, `3.1`, `3.0`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0.0`, `1.9.3`

Timing: Effective 2015-02-23 (already effective)

Why it matters: EOL effective for scoped versions `3.2`, `3.1`, `3.0`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0.0`, `1.9.3`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/ruby

#### rust

### **rust** — rust lifecycle: reached end-of-life (1.97, 1.96, 1.95, 1.94, 1.93, 1.92, 1.91, 1.90, 1.89, 1.88, 1.87, 1.86, 1.85, 1.84, 1.83, 1.82, 1.81, 1.80, 1.79, 1.78, 1.77, 1.76, 1.75, 1.74, 1.73, 1.72, 1.71, 1.70, 1.69, 1.68, 1.67, 1.66, 1.65, 1.64, 1.63, 1.62, 1.61, 1.60, 1.59, 1.58, 1.57, 1.56, 1.55, 1.54, 1.53, 1.52, 1.51, 1.50, 1.49, 1.48, 1.47, 1.46, 1.45, 1.44, 1.43, 1.42, 1.41, 1.40, 1.39, 1.38, 1.37, 1.36, 1.35, 1.34, 1.33, 1.32, 1.31, 1.30, 1.29)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.97`, `1.96`, `1.95`, `1.94`, `1.93`, `1.92`, `1.91`, `1.90`, `1.89`, `1.88`, `1.87`, `1.86`, `1.85`, `1.84`, `1.83`, `1.82`, `1.81`, `1.80`, `1.79`, `1.78`, `1.77`, `1.76`, `1.75`, `1.74`, `1.73`, `1.72`, `1.71`, `1.70`, `1.69`, `1.68`, `1.67`, `1.66`, `1.65`, `1.64`, `1.63`, `1.62`, `1.61`, `1.60`, `1.59`, `1.58`, `1.57`, `1.56`, `1.55`, `1.54`, `1.53`, `1.52`, `1.51`, `1.50`, `1.49`, `1.48`, `1.47`, `1.46`, `1.45`, `1.44`, `1.43`, `1.42`, `1.41`, `1.40`, `1.39`, `1.38`, `1.37`, `1.36`, `1.35`, `1.34`, `1.33`, `1.32`, `1.31`, `1.30`, `1.29`

Timing: Effective 2018-10-26 (already effective)

Why it matters: EOL effective for scoped versions `1.97`, `1.96`, `1.95`, `1.94`, `1.93`, `1.92`, `1.91`, `1.90`, `1.89`, `1.88`, `1.87`, `1.86`, `1.85`, `1.84`, `1.83`, `1.82`, `1.81`, `1.80`, `1.79`, `1.78`, `1.77`, `1.76`, `1.75`, `1.74`, `1.73`, `1.72`, `1.71`, `1.70`, `1.69`, `1.68`, `1.67`, `1.66`, `1.65`, `1.64`, `1.63`, `1.62`, `1.61`, `1.60`, `1.59`, `1.58`, `1.57`, `1.56`, `1.55`, `1.54`, `1.53`, `1.52`, `1.51`, `1.50`, `1.49`, `1.48`, `1.47`, `1.46`, `1.45`, `1.44`, `1.43`, `1.42`, `1.41`, `1.40`, `1.39`, `1.38`, `1.37`, `1.36`, `1.35`, `1.34`, `1.33`, `1.32`, `1.31`, `1.30`, `1.29`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/rust

#### solr

### **solr** — solr lifecycle: reached end-of-life (8, 7, 6, 5, 4, 3, 1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `8`, `7`, `6`, `5`, `4`, `3`, `1`

Timing: Effective 2017-10-24 (already effective)

Why it matters: EOL effective for scoped versions `8`, `7`, `6`, `5`, `4`, `3`, `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/solr

#### spark

### **spark** — apache-spark 4.0 EOL approaching (2026-11-23)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.0`

Timing: Effective 2026-11-23 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/apache-spark

### **spark** — apache-spark lifecycle: reached end-of-life (3.4, 3.3, 3.2, 3.1, 3.0, 2.4, 2.3, 2.2, 2.1, 2.0, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2014-09-03 (already effective)

Why it matters: EOL effective for scoped versions `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/apache-spark

#### spring-boot

### **spring-boot** — spring-boot 4.0 EOL approaching (2026-12-31)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `4.0`

Timing: Effective 2026-12-31 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/spring-boot

### **spring-boot** — spring-boot lifecycle: reached end-of-life (3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.5)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.5`

Timing: Effective 2019-03-01 (already effective)

Why it matters: EOL effective for scoped versions `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.5`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/spring-boot

#### terraform

### **terraform** — terraform lifecycle: reached end-of-life (1.14, 1.13, 1.12, 1.11, 1.10, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`

Timing: Effective 2022-05-18 (already effective)

Why it matters: EOL effective for scoped versions `1.14`, `1.13`, `1.12`, `1.11`, `1.10`, `1.9`, `1.8`, `1.7`, `1.6`, `1.5`, `1.4`, `1.3`, `1.2`, `1.1`, `1.0`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/terraform

#### traefik

### **traefik** — traefik 3.7 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.7`

Timing: Effective date unknown

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/traefik

### **traefik** — traefik lifecycle: reached end-of-life (3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.11, 2.10, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.7)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.11`, `2.10`, `2.9`, `2.8`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.7`

Timing: Effective 2019-12-11 (already effective)

Why it matters: EOL effective for scoped versions `3.6`, `3.5`, `3.4`, `3.3`, `3.2`, `3.1`, `3.0`, `2.11`, `2.10`, `2.9`, `2.8`, `2.7`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1.7`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/traefik

#### vitess

### **vitess** — vitess 23 EOL approaching (2026-11-04)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (WATCH)

Scope: `23`

Timing: Effective 2026-11-04 (upcoming; first detection unrecorded)

Why it matters: EOL announced but not yet effective: watch

Investigate: Note the upcoming date; confirm you have migration runway.

Evidence:
- https://endoflife.date/vitess

### **vitess** — vitess lifecycle: reached end-of-life (22, 21, 20, 19, 18, 17, 16, 15, 14, 13)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `22`, `21`, `20`, `19`, `18`, `17`, `16`, `15`, `14`, `13`

Timing: Effective 2023-02-22 (already effective)

Why it matters: EOL effective for scoped versions `22`, `21`, `20`, `19`, `18`, `17`, `16`, `15`, `14`, `13`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/vitess

#### vue

### **vue** — vue 3.5 ended active support

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.5`

Timing: Effective date unknown

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/vue

### **vue** — vue lifecycle: reached end-of-life (3.4, 3.3, 2.7, 3.2, 3.1, 3.0, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.4`, `3.3`, `2.7`, `3.2`, `3.1`, `3.0`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1`

Timing: Effective 2016-11-22 (already effective)

Why it matters: EOL effective for scoped versions `3.4`, `3.3`, `2.7`, `3.2`, `3.1`, `3.0`, `2.6`, `2.5`, `2.4`, `2.3`, `2.2`, `2.1`, `2.0`, `1`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/vue

#### zookeeper

### **zookeeper** — zookeeper lifecycle: ended active support (3.9, 3.8)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (REVIEW)

Scope: `3.9`, `3.8`

Timing: Effective date unknown

Why it matters: active support ended: review support posture

Investigate: Track the affected versions in your inventory; schedule migration planning.

Evidence:
- https://endoflife.date/zookeeper

### **zookeeper** — zookeeper lifecycle: reached end-of-life (3.7, 3.6, 3.5, 3.4)

Category: Lifecycle · Evidence confidence: EMERGING · Assessment: PROJECT_CHANGE (ACTION)

Scope: `3.7`, `3.6`, `3.5`, `3.4`

Timing: Effective 2020-06-01 (already effective)

Why it matters: EOL effective for scoped versions `3.7`, `3.6`, `3.5`, `3.4`: evidence and scope justify action-oriented framing (applies only if you run these versions)

Investigate: Check whether you run the affected versions (`openpulse check --watchlist <file>`); plan upgrade or extended support.

Evidence:
- https://endoflife.date/zookeeper

### B. Source references

Finding source distribution: NVD 52.3%, endoflife.date 47.7%
Independent source families observed: 2 (across 2 recorded source labels).

### C. Data gaps and limitations

No signals observed for: bitnami-redis-stack, buildkit, celery, cockroach, coredns, cosign, crio, crossplane, falco, fastapi, flask, helm, itext, junit, k9s, kustomize, langchain, linkerd, minio, nats, nest, ollama, opa, opentelemetry, pytest, pytorch, qdrant, redpanda, requests, tensorflow, tidb, transformers, trivy, typescript, valkey, vault, vite.

317 related-but-unconfirmed or below-bar records held back (see `openpulse analyze` for the full stream).

### D. Notes

- Collectors: endoflife.date, GitHub releases + repo metadata, NVD, CISA KEV, Docker Hub.
- GitHub calls unauthenticated (60 req/hr budget); some repos may show gaps.
- NVD queried without API key (5 req/30s); misses degrade to gaps, not findings.
- Keyword-associated CVE records without identity evidence are held back, not narrated.
- Public intelligence describes project-level change; whether it affects YOUR dependencies needs a watchlist (`openpulse check`).
