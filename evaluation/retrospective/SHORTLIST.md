# Retrospective study: candidate events and their screening

**Status: for approval, with DESIGN.md.** Each candidate below was researched on 2026-10-30 against primary sources and archived snapshots. Its sources are listed, and DESIGN.md §3's criteria are applied to it. **No OpenPulse code has been run on any candidate (X3).** Every source in this file was fetched; a fact that could not be confirmed is marked as such, never filled from memory. I independently re-checked a sample of the research against the live sources: 22 claims across all three event families, and all 22 held. The re-checks are marked ✔ in the notes.

**Legend.** ✓ meets the criterion. ✗ fails it. ◐ provisional: E5 needs 3 real pre-event dependents, and fewer are verified so far. ◐ events are completed or dropped under DESIGN §9 when dependents are sampled, before any run.

## Summary

| Class | Researched | Included or provisional | Rejected | Target |
|---|---|---|---|---|
| Relocation | 6 | **3** | 3 | 4–6 |
| Archival or deprecation | 6 | **6** | 0 | 4–6 |
| Distribution change | 8 | **6** | 2 | 4–6 |
| Licence change | 5 | **4** | 1 | 4–6 |
| End of life | 3 | **3** | 0 | 4–6 |
| Compromised versions | 5 | **5** | 0 | 4–6 |
| **Total** | **33** | **27** | **6** | **30** |

**Gaps to close before data collection:** relocation and end of life are each one event short of the minimum of 4, and the total is 3 short of 30. See "Decisions" at the end.

## Relocation

| ID | Change | Sources (primary; archived) | E1–E6 | Notes |
|---|---|---|---|---|
| **REL-1** | `docker/docker` → `moby/moby`, 2017-04 | moby/moby#32691 (2017-04-18); snapshot 20170420213705 | ✓✓✓✓◐✓ | The redirect affects URLs; the Go import path `github.com/docker/docker` kept working. Dependents: kubernetes (Godeps, 2017-03-28) and nomad (vendor.json, 2017-04-01): 2 of 3. The transfer falls between Wayback 200 (2017-03-31) and 301 (2017-04-22). |
| **REL-3** | `docker/distribution` → `distribution/distribution`, 2021-01 | Docker blog, 2021-02-04; snapshot 20210205005303 | ✓✓✓✓◐✓ | The v2 import path is unchanged; `/v3` is a separate module change. Dependents: kubernetes `go.mod` (v1.20.0, 2020-12-04) and moby `vendor.conf` (2020-12-07): 2 of 3. ✔ GitHub now resolves the old path to `distribution/distribution`. |
| **REL-4** | `coreos/prometheus-operator` → `prometheus-operator/prometheus-operator`, 2020-08-05 | prometheus-operator#3384 (merged 2020-08-05); repository snapshot 20200615012237 | ✓✓✓✓◐✓ | The module path changed with release 0.42.0, and images were pushed to both Quay organisations. Dependents: openshift cluster-monitoring-operator `go.mod` (2020-07-31) and kube-prometheus (2020-04-01): 2 of 3. ✔ The snapshot exists. |
| REL-2 | `kubernetes/helm` → `helm/helm`, 2018 | kubernetes/community#2288 | ✓✓✓✓**✗**✓ | **Rejected, E5.** The only pre-event references found are documentation links, not dependency manifests. Go consumers used the vanity path `k8s.io/helm`, which the transfer did not change. |
| REL-5 | `coreos/flannel` → `flannel-io/flannel`, 2021 | flannel-io#1422 (module move only) | **✗**✓✓✓◐✓ | **Rejected, E1.** No announcement of the transfer was found. |
| (uber/jaeger) | | | | **Rejected:** no redirect exists, so it is not a relocation. |

## Archival or deprecation

| ID | Change | Sources | E1–E6 | Notes |
|---|---|---|---|---|
| **DEP-1** | npm `request` fully deprecated, 2020-02-11 | README commit aded7e4f8e (2020-02-11); npm deprecation on every version; snapshot 20200211201636 | ✓✓✓✓◐✓ | **The repository is not archived**, contrary to the brief. ✔ `archived=false`. Dependents: npm/cli and node-gyp `package.json` (2020-01): 2 of 3. |
| **DEP-2** | `golang/dep` deprecated (2020-03-30) and archived (2020-09-08) | golang/go#38158; snapshot 20200917033647 | ✓✓✓✓◐✓ | "Affected" means projects that use the tool (Gopkg files or the install script), not ones that import its path. Dependents: istio and heptio/ark: 2 of 3. ✔ `archived=true`. |
| **DEP-3** | `tslint` deprecated in favour of ESLint (announced 2019-02-19; PRs stop 2020-12-01; archived 2021-03/04) | Medium post and roadmap issue #4534; snapshot 20190219201734 | ✓✓✓✓◐✓ | **The registry flags only versions 6.0.0–6.1.3; 5.x is unflagged.** ✔ Re-checked. This makes it a version-scoped case. Dependents: angular and vscode (5.x, 2019-02-19): 2 of 3. |
| **DEP-4** | `node-sass` end of life: npm deprecated, repository archived, 2024-07-24 | sass-lang.com blog; snapshot 20240812011239 | ✓✓✓✓◐✓ | ✔ All 148 versions are deprecated, and the snapshot exists. Dependents: bootstrap (2019): 1 of 3. A commit nearer 2024 is needed. |
| **DEP-5** | `go-yaml/yaml` (`gopkg.in/yaml.v2` and `v3`) unmaintained (2025-04-01), then archived | README commit 944c86a; snapshot 20250401151649 | ✓✓✓✓◐✓ | Archived, but the module metadata has no `Deprecated:` comment. Dependents: kubernetes and helm `go.mod` (2025-03-14): 2 of 3. |
| **DEP-6** | `golang.org/x/lint` frozen and deprecated (accepted 2020-06-03; archived 2021-05-08) | golang/go#38968; snapshot 20210511082834 | ✓✓✓✓◐✓ | The GitHub mirror is archived, but the canonical source on googlesource got a commit in 2024. Dependents: kubernetes `go.mod` (2021-03-31): 1 of 3. |

## Distribution change (registries and images)

| ID | Change | Sources | E1–E6 | Notes |
|---|---|---|---|---|
| **DIS-1** | `k8s.gcr.io` → `registry.k8s.io`: redirect 2023-03-20, freeze 2023-04-03 | kubernetes.io posts of 2022-11-28, 2023-02-06 and 2023-03-10; snapshots 20221129154618, 20230213025122 and 20230315231813 | ✓✓✓✓✓✓ | A registry-level scope. Existing references keep resolving through the redirect. What breaks is new tags pulled from the old host, allow-listed networks, and clients that don't follow redirects. The GA post's scope text was **corrected after publication** (1.25 → 1.27), and the snapshot shows the original. ✔ `k8s.gcr.io` returns 302 to `registry.k8s.io` today. Dependents: ingress-nginx, metrics-server and ingress-gce (2022–23): 3 of 3. |
| **DIS-2** | Official `openjdk` image deprecated, 2022-06 (no non-EA updates after July 2022) | docker-library/docs commit 326814f, openjdk#505; snapshot 20220718201219 | ✓✓✓✓◐✓ | "Stops receiving updates", not removal. EA tags are excluded. Dependents: Graylog (pre-event confirmed), plus 2 more whose dates are unchecked. |
| **DIS-3** | 1,051 floating `openjdk` tags **deleted** from Docker Hub, 2025-11-03 | official-images#20210 (merged 2025-11-03T23:06:16Z ✔); the exact tag list is saved as `evidence/openjdk-2025-deleted-tags.txt` (1,051 tags ✔); snapshot 20251105030321 | ✓✓✓✓✓✓ | **The strongest breaking case.** The scope is an exact tag list. ✔ `openjdk:17` and `:latest` return 404, while `11.0.16-jdk` and `8u342-jre` return 200. `openjdk:21-slim` is in the list ✔. Dependents: fabric8io, navikt and pterodactyl (2025-11): 3 of 3. |
| **DIS-4** | Official `centos` image deprecated (2022-09-22), then all tags removed from the library manifest (2024-07-02) | docs#2205, official-images#17094; snapshot 20221014104857 | ✓✓✓✓◐✓ | "Removed from the manifest" ≠ deleted from Hub: `centos:7` and `:8` still pull. `centos:latest` returns 404, cause and date unknown. Dependents: 2 of 3. |
| **DIS-5** | Official `adoptopenjdk` image deprecated in favour of `eclipse-temurin`, 2021-08 | docs commit 4baab4b; snapshot 20210825110321 | ✓✓✓✓◐✓ | The effective date (2021-08-01) **precedes** the announcement (2021-08-13). Tags still pull. Dependents: 1, not confirmed pre-event. |
| **DIS-6** | Official `java` image deprecated in favour of `openjdk`, 2016-08-11 (no updates after 2016-12-31) | docs commit a3439b6; snapshot 20161027201850 | ✓✓✓✓◐✓ | Floating tags are now 404, but when they were deleted is unknown, so the scope is deprecation, not removal. Dependents: 2, not confirmed pre-event. |
| DIS-x | Google Container Registry deprecation and shutdown, 2023–2025 | cloud.google.com deprecation page | ✓✓**✗**✓**✗**✓ | **Rejected, E3 and E5.** The affected identifiers are private, per-project registries, and no public pre-event dependents are identifiable. |
| DIS-y | `microsoft/mssql-server-linux` disabled on Docker Hub (by 2021-05-31) → MCR | Microsoft blog, 2021-05-20 | ✓**✗**✓✓◐✓ | **Rejected, E2.** The earliest Wayback capture is from 2024-06-16 ✔ (CDX), outside the contemporaneous window. |

## Licence change with a version boundary

| ID | Change | Sources | E1–E6 | Notes |
|---|---|---|---|---|
| **LIC-1** | Elasticsearch and Kibana Apache-2.0 → SSPL / Elastic License 2.0, from 7.11.0 | elastic.co blog (2021-01-14); snapshot 20210115230839; LICENSE files at the v7.10.2 and v7.11.0 tags | ✓✓✓✓◐✓ | The 6.8.x patch line kept the Apache default, so the boundary is "7.x ≥ 7.11.0", not a date. The clients, Beats and Logstash are excluded. The found dependents are current-HEAD pins; pre-event commits still need finding. |
| **LIC-2** | Terraform MPL-2.0 → BSL 1.1, from 1.6.0 (first tag 1.6.0-alpha20230816) | HashiCorp blog (2023-08-10); snapshot 20230811223350 | ✓✓✓✓◐✓ | ✔ LICENSE is MPL 2.0 at v1.5.7 and BSL at v1.6.0. APIs and SDKs are excluded. The blog names no version, so the boundary comes from the tag LICENSE files (a permanent record, E2). The dependents found pin 1.5.7; pre-event dates are unchecked. |
| **LIC-3** | Grafana Apache-2.0 → AGPLv3, from 8.0.0 | grafana.com blog (2021-04-20); snapshot 20210421230514 | ✓✓✓✓◐✓ | ✔ Apache at v7.5.7, AGPL at v8.0.0. The version boundary is derived from tag LICENSE files, not stated in the blog. Plugins and some libraries are excluded. |
| **LIC-4** | MongoDB Community Server AGPL → SSPL for releases **dated** on or after 2018-10-16, on every branch | MongoDB SSPL FAQ; snapshot 20181023161242 | ✓✓✓✓◐✓ | **The boundary is a date across branches** (r4.0.4 and r3.6.8 are SSPL, r4.0.3 is AGPL), so per-version sets come from tag LICENSE files. A floating `mongo:4.0` is honestly undeterminable. This is a representation test for RQ-R2. |
| LIC-x | Redis BSD → RSALv2 / SSPLv1, from 7.4 | redis.io blog (2024-03-20) | ✓✓✓✓◐✓ **X1** | **Rejected, X1.** Redis is a development-set project (Redis 6.2 end of life). The event is otherwise strong, and it can be offered to the prospective study instead. |

## End of life (vendor-announced)

| ID | Change | Sources | E1–E6 | Notes |
|---|---|---|---|---|
| **EOL-1** | Python 2.7, 2020-01-01 (final release 2.7.18, 2020-04-20) | python.org "Sunset Python 2"; snapshot 20200102202103; PEP 373 | ✓✓✓✓◐✓ | `major.minor == 2.7`. No PEP snapshot exists near 2020; the sunset page carries E2. |
| **EOL-2** | CentOS Linux 8, 2021-12-31 (announced 2020-12-08) | blog.centos.org; snapshot 20201211014354 | ✓✓✓✓◐✓ | CentOS 7 and Stream 8 are excluded. It overlaps DIS-4's project but is a different event. |
| **EOL-3** | Node.js 12, 2022-04-30 | nodejs/Release schedule; snapshot 20220430045420 | ✓✓✓✓◐✓ | A schedule entry with no dated announcement post. The schedule itself is the vendor's record. |

## Compromised or sabotaged versions

| ID | Change | Sources | E1–E6 | Notes |
|---|---|---|---|---|
| **CMP-1** | `colors` 1.4.1, 1.4.2 and 1.4.44-liberty-2 (2022-01-08/09) | GHSA-5rqg (enumerated) and GHSA-gh88 (≥ 1.4.1); registry timestamps; snapshot 20220115123912 | ✓✓✓✓✓✓ | **The two advisories disagree on extent**, so by DESIGN §6 precedence the versions in the disputed region are `undeterminable`. ✔ Only 1.4.0 remains in the registry, and the timestamps are as reported. Dependents: karrot, aws-cdk and winston (dated fix commits): 3 of 3. |
| **CMP-2** | `faker` 6.6.6 (2022-01-05) | GHSA-5w9c (2022-03-22); registry timestamp; repository snapshot 20220106193513 | ✓✓✓✓◐✓ | 6.6.6 is still in the registry. Dependents: Dependabot bumps into 6.6.6 (pulumi/actions, rubyforgood/casa): 2 of 3. |
| **CMP-3** | `node-ipc` [10.1.1, 10.1.3), {9.2.2} and [11.0.0, 12.0.0), with three different severities (2022-03) | Three GHSAs (2022-03-16); registry timestamps; snapshot 20220321003825 | ✓✓✓✓◐✓ | The project issue is now 404, so the GHSAs plus the registry are the record (E4 is met through the registry). A caret range `^9.1.1` resolves into 9.2.2: vue-cli. Dependents: 2 of 3. |
| **CMP-4** | `ua-parser-js` 0.7.29, 0.8.0 and 1.0.0 (account hijack, 2021-10-22) | Maintainer issue #536; GHSA-pjwm; snapshot 20211023193659 ✔ | ✓✓✓✓◐✓ | One bad version per release line, so it tests line semantics. Dependents: 2 of 3 (lockfiles that resolved 0.7.29). |
| **CMP-5** | `event-stream` 3.3.6, through `flatmap-stream` 0.1.1 (published 2018-09-09; disclosed 2018-11-26) | npm blog (2018-11-27); GHSA-mh6f; snapshot 20181129013028 | ✓✓✓✓✓✓ | ✔ 3.3.6 is absent from the registry, with the time as reported. The extent of `flatmap-stream` is disputed (npm says 0.1.1, the GHSA says ≥ 0), so those pairs are `undeterminable`. A transitive dependency case. Dependents: 3 of 3. |

## Decisions needed before data collection

1. **Fill the gaps (recommended):** research 1–2 more relocations and 1–2 more vendor end-of-life events, under the same criteria. Candidates to check are a Go module relocation with a dated announcement, and the end of life of CentOS 7, Debian 10 or Ubuntu 18.04. That brings the total to 30.
   - Alternative: accept **27 events** and report the shortfall.
2. **E5 provisional events:** 23 of the 27 have fewer than 3 verified pre-event dependents (all but DIS-1, DIS-3, CMP-1 and CMP-5). Per DESIGN §9, each is completed during dependent sampling or dropped if fewer than 2 are found. All drops are listed, and none is made after a policy runs.
3. **X1 for Redis:** excluded as written. Terraform and Grafana appear in the golden tests as *end-of-life* scenarios, not licence events. X1's list names neither, so their licence events stay included. I flag this so you can tighten X1 if you prefer.

## Freeze

The implementation is frozen at tag `retro-freeze-2026-10-30` (`3639a0f`, the merge of #180). The CI cross-check of OpenPulse's version comparator against the pinned ecosystem tools, at that commit, reported **0 disagreements**. OpenPulse abstains on pre-release line membership: 108 of 324 npm cases and 72 of 264 Go cases. It also abstains on 2,422 of 2,652 Maven orderings. That is a coverage cost to report in RQ-R1.
