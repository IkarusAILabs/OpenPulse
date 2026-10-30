# Retrospective study R-C0: results

**Exploratory, retrospective, not registered.** This study evaluates OpenPulse at the freeze tag on 27 real upstream changes (2016–2025) and 167 real dependency references. It is reported apart from the registered prospective evaluation (`evaluation/REGISTRATION.md`) and is never pooled with it. The design is `DESIGN.md`. Every departure from it is in DESIGN §11 and summarised in §1 below.

## 0. Findings in brief

1. **No false clears by OpenPulse (C).** It cleared no in-scope dependency on any of the 27 events. The naive baseline (A) falsely cleared 35 pairs in 10 of the 27 events. The difference is significant at the event level (S2: A − C = 0.370, Holm p = 0.0004). With 27 events, the one-sided 95% upper bound on C's per-event false-clear share is 0.105. That is above the registered 0.05 margin, and 27 is below the 60 events H1 needs, so **H1 is not decidable** here.
2. **A defect caused silent misses (guardrail G1 fails).** 12 of 103 in-scope pairs (11.7%) got **no association at all**:
   - 11 relocation pairs: every Go module reference to a relocated repository;
   - 1 deprecation pair: a Go module reference to golang/dep.

   OpenPulse never compares a Go module dependency with an event's source-repository artifact, although a Go module path *is* a repository path. Baseline V associated all 12. This is defect **D-R1** (§6).
3. **Little difference from baseline V overall.** C resolves 50.3% of determinable pairs and V 47.3% (difference 0.030, 90% CI [0.000, 0.075]). Equivalence at ±0.05 is not shown (S1: p = 0.197). C's gain over the conservative baseline B, 0.091 (95% CI [−0.054, 0.245]), misses the registered 0.10 with a lower bound below zero (H2 not met). The gain is concentrated in end of life, where C resolves 88.2% and V 58.8%.
4. **Most non-decisions come from identity, not scope.** All 31 compromised-package pairs and most deprecation neighbours are unresolved, because the packages (colors, faker, node-ipc, ua-parser-js, event-stream, sass and others) are not in OpenPulse's catalog. A package with no recorded identity is left unresolved by design (F4). Unsupported decisiveness is 0% for C: it decided neither undeterminable pair.
5. **Discovery was weak at the freeze tag** (§5): 0 of 15 events detected as shipped, and 5 of 15 when each repository or image was supplied directly. All 5 are archivals, each with a project-wide scope broader than the fixture's. The GitHub collector does not follow GitHub's 301 redirect for transferred repositories. So the relocation analyst never observes the ownership change it exists to detect (defect **D-R2**), and only 1 of the 15 discovery-class projects is in the catalog.

## 1. Method as executed

- **Events**: 27 events in 6 classes, from SHORTLIST.md (DESIGN §3, owner decision §11). The fixtures are built from archived primary sources (`events/<ID>/event.json` and `SOURCES.md`). No event was dropped (§9).
- **Dependents**: 102 in-scope references and 65 neighbours. Each is a real repository file at a stated commit inside the event's window (`dependents/*.json`). There are no synthetic pairs.
- **Labels**: 167 pairs, all labelled by L1, the developer: 103 in scope, 62 out of scope and 2 undeterminable. Each label follows one written rule per event (`build_cases.py`).
  - **No independent human labels were obtained.** Two rounds of outside labelling turned out to be AI-assisted (`labelling/PILOT.md`). They are reported only as a consistency check: L1 against the pilot, κ = 0.722 in round 1 and κ = 0.825 in round 2. These figures are not inter-rater reliability.
  - Every pair has `independent_label: false`, so the registered population is empty and the registered verdict is "not decidable" by construction.
- **Freeze**:
  - The implementation is frozen at tag `retro-freeze-2026-10-30` (3639a0f).
  - The case file `cases/retro-2026-11.json` is frozen before any policy run, with SHA-256 `70832760…a1bf83`. CI checks this hash before running.
- **Run**:
  - It ran in CI (`.github/workflows/retrospective.yml`) on the freeze-tag checkout, with `--require-comparators`. The pinned comparators were node-semver 7.8.5, golang.org/x/mod v0.42.0 and maven-artifact 3.9.16, and all three were available.
  - Freshness was bounded at 90 days. Each event was replayed at its archived snapshot date, and no event was unknown at replay time.
  - The results are in `results/openpulse-retro-2026-11.json` (SHA-256 `2bce9237…ed1376`). A second CI run produced a byte-identical results file, and a local re-run reproduced all 167 of C's decisions.

## 2. Events

| Event | Class | Title | Sources | Replay date | Pairs |
|---|---|---|---|---|---|
| REL-1 | relocation | docker/docker repository relocated to moby/moby | 1 | 2017-04-20 | 6 |
| REL-3 | relocation | docker/distribution relocated to distribution/distribution | 2 | 2021-02-05 | 6 |
| REL-4 | relocation | coreos/prometheus-operator relocated to prometheus-operator/prometheus-operator | 2 | 2020-08-05 | 6 |
| DEP-1 | deprecation | npm package request fully deprecated | 2 | 2020-02-11 | 6 |
| DEP-2 | deprecation | golang/dep deprecated and archived | 2 | 2020-09-17 | 5 |
| DEP-3 | deprecation | TSLint deprecated in favour of ESLint | 2 | 2019-05-08 | 6 |
| DEP-4 | deprecation | Node Sass end of life | 1 | 2024-08-12 | 6 |
| DEP-5 | deprecation | go-yaml/yaml unmaintained and archived | 2 | 2025-04-01 | 7 |
| DEP-6 | deprecation | golint frozen and deprecated | 1 | 2021-05-11 | 7 |
| DIS-1 | distribution | k8s.gcr.io redirected to registry.k8s.io and frozen | 3 | 2023-03-15 | 7 |
| DIS-2 | distribution | Official openjdk image deprecated (no non-EA updates after July 2022) | 2 | 2022-07-18 | 7 |
| DIS-3 | distribution | 1,051 floating openjdk tags deleted from Docker Hub | 1 | 2025-11-05 | 7 |
| DIS-4 | distribution | Official centos image deprecated and removed from the library | 2 | 2024-12-12 | 7 |
| DIS-5 | distribution | Official adoptopenjdk image deprecated in favour of eclipse-temurin | 1 | 2021-08-25 | 6 |
| DIS-6 | distribution | Official java image deprecated in favour of openjdk | 1 | 2016-10-27 | 5 |
| LIC-1 | licence | Elasticsearch and Kibana relicensed from Apache-2.0 from 7.11 | 1 | 2021-01-15 | 5 |
| LIC-2 | licence | Terraform relicensed from MPL-2.0 to BSL 1.1 from 1.6 | 2 | 2023-10-04 | 7 |
| LIC-3 | licence | Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0 | 1 | 2021-04-21 | 7 |
| LIC-4 | licence | MongoDB relicensed to SSPL for releases on or after 2018-10-16 | 1 | 2018-10-23 | 4 |
| EOL-1 | eol | Python 2.7 end of life | 1 | 2020-01-02 | 6 |
| EOL-2 | eol | CentOS Linux 8 end of life | 1 | 2020-12-11 | 6 |
| EOL-3 | eol | Node.js 12 end of life | 1 | 2022-04-30 | 7 |
| CMP-1 | compromised | Sabotaged colors versions | 2 | 2022-01-21 | 7 |
| CMP-2 | compromised | Sabotaged faker 6.6.6 | 2 | 2022-03-22 | 6 |
| CMP-3 | compromised | Protestware in node-ipc | 2 | 2022-03-21 | 7 |
| CMP-4 | compromised | Hijacked ua-parser-js versions | 1 | 2021-10-23 | 5 |
| CMP-5 | compromised | Malicious flatmap-stream dependency in event-stream 3.3.6 | 1 | 2018-11-29 | 6 |

## 3. RQ-R1: decisions

How to read the table:
- **False clears**: in-scope pairs decided not affected, with the number of events that have one.
- **Silent miss**: in-scope pairs with no association, as a share of in-scope pairs.
- **False impact**: out-of-scope pairs decided affected, as a share of out-of-scope pairs.
- **Resolved**: correct decisive decisions, as a share of determinable pairs.
- **Abstained**: unresolved pairs, as a share of all pairs.
- **Unsupported decisive**: decisive outcomes on undeterminable pairs, as a share of those pairs.

The registered tests and guardrails, computed on all labels and therefore illustrative only:

| Test | Result |
|---|---|
| H1 (safety non-inferiority vs B) | Not decidable: 27 events at risk, 60 needed. C and B both have 0 false-clear events, with an upper bound of 0.105. |
| H2 (resolution gain C − B ≥ 0.10) | 0.091, 95% CI [−0.054, 0.245], one-sided 95% lower bound −0.036: **not met** |
| S1 (C ≡ V within ±0.05) | 0.030, 90% CI [0.000, 0.075]: equivalence **not shown** (p = 0.197) |
| S2 (A − C event false clears > 0) | 0.370: **rejected null** (Holm p = 0.0004) |
| G1 (silent miss ≤ 0.02) | 0.117: **fails** (§6, D-R1) |
| G2 (C unresolved ≤ B + 0.05) | 0.382 vs 0.576: passes |
| G3 (class flag at unresolved > 0.60) | Flagged: compromised (1.00) and licence (0.61) |

#### All events

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 27 | 167 | 35 (10 ev.) | 0.0% | 3.2% | 77.6% | 0.0% | 100.0% |
| B-conservative | 27 | 167 | 0 (0 ev.) | 0.0% | 3.2% | 41.2% | 58.1% | 0.0% |
| V-strong-conservative | 27 | 167 | 0 (0 ev.) | 0.0% | 1.6% | 47.3% | 52.1% | 0.0% |
| C-openpulse | 27 | 167 | 0 (0 ev.) | 11.7% | 1.6% | 50.3% | 38.9% | 0.0% |
| C-ablate-completeness | 27 | 167 | 0 (0 ev.) | 11.7% | 1.6% | 54.5% | 34.7% | 0.0% |
| C-ablate-freshness | 27 | 167 | 0 (0 ev.) | 11.7% | 1.6% | 50.3% | 38.9% | 0.0% |
| C-ablate-both | 27 | 167 | 0 (0 ev.) | 11.7% | 1.6% | 54.5% | 34.7% | 0.0% |
| C-ablate-identity | 27 | 167 | 0 (0 ev.) | 29.1% | 1.6% | 50.3% | 11.4% | 0.0% |

#### relocation

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 3 | 18 | 11 (3 ev.) | 0.0% | 0.0% | 38.9% | 0.0% | – |
| B-conservative | 3 | 18 | 0 (0 ev.) | 0.0% | 0.0% | 5.6% | 94.4% | – |
| V-strong-conservative | 3 | 18 | 0 (0 ev.) | 0.0% | 0.0% | 11.1% | 88.9% | – |
| C-openpulse | 3 | 18 | 0 (0 ev.) | 91.7% | 0.0% | 11.1% | 0.0% | – |

#### deprecation

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 6 | 37 | 10 (3 ev.) | 0.0% | 8.3% | 70.3% | 0.0% | – |
| B-conservative | 6 | 37 | 0 (0 ev.) | 0.0% | 8.3% | 40.5% | 56.8% | – |
| V-strong-conservative | 6 | 37 | 0 (0 ev.) | 0.0% | 0.0% | 64.9% | 35.1% | – |
| C-openpulse | 6 | 37 | 0 (0 ev.) | 4.0% | 0.0% | 64.9% | 32.4% | – |

#### distribution

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 6 | 39 | 0 (0 ev.) | 0.0% | 6.7% | 97.4% | 0.0% | – |
| B-conservative | 6 | 39 | 0 (0 ev.) | 0.0% | 6.7% | 61.5% | 35.9% | – |
| V-strong-conservative | 6 | 39 | 0 (0 ev.) | 0.0% | 6.7% | 87.2% | 10.3% | – |
| C-openpulse | 6 | 39 | 0 (0 ev.) | 0.0% | 6.7% | 87.2% | 10.3% | – |

#### licence

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 4 | 23 | 6 (2 ev.) | 0.0% | 0.0% | 73.9% | 0.0% | – |
| B-conservative | 4 | 23 | 0 (0 ev.) | 0.0% | 0.0% | 34.8% | 65.2% | – |
| V-strong-conservative | 4 | 23 | 0 (0 ev.) | 0.0% | 0.0% | 34.8% | 60.9% | – |
| C-openpulse | 4 | 23 | 0 (0 ev.) | 0.0% | 0.0% | 34.8% | 60.9% | – |

#### eol

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 3 | 19 | 8 (2 ev.) | 0.0% | 0.0% | 52.9% | 0.0% | 100.0% |
| B-conservative | 3 | 19 | 0 (0 ev.) | 0.0% | 0.0% | 23.5% | 79.0% | 0.0% |
| V-strong-conservative | 3 | 19 | 0 (0 ev.) | 0.0% | 0.0% | 58.8% | 47.4% | 0.0% |
| C-openpulse | 3 | 19 | 0 (0 ev.) | 0.0% | 0.0% | 88.2% | 21.1% | 0.0% |

#### compromised

| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |
|---|---|---|---|---|---|---|---|---|
| A-naive | 5 | 31 | 0 (0 ev.) | 0.0% | 0.0% | 100.0% | 0.0% | – |
| B-conservative | 5 | 31 | 0 (0 ev.) | 0.0% | 0.0% | 51.6% | 48.4% | – |
| V-strong-conservative | 5 | 31 | 0 (0 ev.) | 0.0% | 0.0% | 0.0% | 100.0% | – |
| C-openpulse | 5 | 31 | 0 (0 ev.) | 0.0% | 0.0% | 0.0% | 100.0% | – |

## 4. RQ-R2: representation

Where the scope language could not state an event's announced extent exactly, the fixture states a safe over-approximation (DESIGN §4). Every such gap was recorded before the run, in each event's `SOURCES.md`, and this is how each one showed up in C's decisions:

| Gap | Events | Effect at the freeze tag |
|---|---|---|
| A registry-wide scope ("every image on k8s.gcr.io") exists only as an envelope | DIS-1 | 4 in-scope pairs unresolved ("shares event registry scope but no artifact was established") |
| An open-ended version boundary ("from 1.6 on") cannot be stated, so the scope lists versions and is not exhaustive | LIC-2, LIC-3 | 5 out-of-scope pairs unresolved rather than cleared |
| A date-based boundary across branches | LIC-4 | All 4 pairs unresolved ("impact not established") |
| An exclusion for Early Access tags | DIS-2 | **1 false impact**: `openjdk:19-ea-16-slim` decided affected |
| A per-tag scope over an enumerated set | LIC-1 | 4 pairs unresolved ("the named tag does not establish the others") |
| CentOS Linux 8 tags enumerated in a partial scope | EOL-2 | 2 out-of-scope pairs unresolved |
| Packages with no catalogued identity | CMP-1…5, DEP neighbours, LIC-1-s2 | 44 pairs unresolved (§6) |

## 5. RQ-R3: discovery

Discovery covered the 15 events of the relocation, archival and distribution classes, all run on one recorded date. The recorded run is CI run 41098862646, started 2026-10-30T17:27:21Z at the freeze tag, with the job's read-only `GITHUB_TOKEN`. Its outputs are `results/discovery.json` and `discovery.log`.

Each event was run two ways:
- **As shipped**: OpenPulse's own catalog lookup.
- **Supplied**: the affected repository or Docker Hub image handed straight to the same collectors and change analyst.

How to read the Scope column, which compares the constructed scope with the fixture's:
- `match`: the same scope;
- `narrower`: a smaller scope than the fixture's;
- `broader`: a larger scope than the fixture's;
- `missing`: nothing was detected.

| Event | In catalog | As shipped | Supplied input | Detected | Scope vs fixture | Identity | Why |
|---|---|---|---|---|---|---|---|
| REL-1 | no | – | docker/docker | no | missing | – | **D-R2**: the API's 301 for the transferred repository is recorded as an error, so `full_name` is never read |
| REL-3 | no | – | docker/distribution | no | missing | – | D-R2 |
| REL-4 | no | – | coreos/prometheus-operator | no | missing | – | D-R2 |
| DEP-1 | no | – | request/request | no | missing | – | The repository is not archived. The deprecation lives in the npm registry and the README, and no collector reads npm deprecations |
| DEP-2 | no | – | golang/dep | PROJECT_ARCHIVED | broader | unresolved | The scope is the whole project with no artifact. The fixture names the repository exactly |
| DEP-3 | no | – | palantir/tslint | PROJECT_ARCHIVED | broader | unresolved | The scope is the whole project. The fixture names `pkg:npm/tslint`. The slug is not catalogued, so no package is tied to the finding |
| DEP-4 | no | – | sass/node-sass | PROJECT_ARCHIVED | broader | unresolved | As DEP-3, for `pkg:npm/node-sass` |
| DEP-5 | no | – | go-yaml/yaml | PROJECT_ARCHIVED | broader | unresolved | As DEP-3, for `gopkg.in/yaml.v2` and `yaml.v3` |
| DEP-6 | no | – | golang/lint | PROJECT_ARCHIVED | broader | unresolved | As DEP-3, for `golang.org/x/lint` |
| DIS-1 | yes (kubernetes) | 20 EOL findings, all for Kubernetes releases | – | no | missing | – | No collector probes registries other than Docker Hub, so k8s.gcr.io is not observed |
| DIS-2 | no | – | library/openjdk | no | missing | – | The probe succeeds, but the deprecation is stated in the image's docs, not in its tag structure. The generic rule needs a latest-only or legacy-namespace pair |
| DIS-3 | no | – | library/openjdk | no | missing | – | A tag deletion shows only as a difference between two observations (`observe`/`sweep`), which a one-date probe cannot see |
| DIS-4 | no | – | library/centos | no | missing | – | As DIS-2 |
| DIS-5 | no | – | library/adoptopenjdk | no | missing | – | As DIS-2 |
| DIS-6 | no | – | library/java | no | missing | – | As DIS-2 |

**Recall over this event set** (never population recall):
- **As shipped:** 0 of 15 events detected. Only DIS-1's project is catalogued, and nothing about the registry change was found.
- **Supplied:** 5 of 15 detected, all archivals and all `broader`, with identity unresolved.
- **Relocations:** detected by neither route (D-R2).
- **Distribution changes:** detected by neither route. The analysts see tag structure, not deprecation notices.

## 6. Error analysis

This section covers every wrong or unresolved decision by C on a determinable pair (82 of 165), and every decisive outcome on an undeterminable pair (none).

| Cause | Pairs | Outcome | Category |
|---|---|---|---|
| **D-R1**: a Go module dependency is never compared with a source-repository artifact | 12 in scope (REL-1 ×4, REL-3 ×4, REL-4 ×3, DEP-2-s1); 5 neighbours (REL-1-n1/n2, REL-3-n1/n2, REL-4-n2) | No association (silent miss for the 12) | **Defect** |
| No catalogued identity for the dependency's package (F4) | 44: all 31 compromised pairs, 12 deprecation pairs (including DEP-6-n1) and LIC-1-s2 | Unresolved | Coverage: by design, not a defect |
| Representation gaps (§4) | 19 unresolved; 1 false impact (DIS-2-n3) | Unresolved / false impact | Scope language |
| A different project, correctly not associated | LIC-2-n3 (OpenTofu) | No association | Correct non-decision |

**Notes on D-R1:**
- Go's go.mod reader emits `{"kind": "package", "ecosystem": "Go", "package": "github.com/docker/docker"}`. The relocation analyst names `github.com/docker/docker` as a `source-repository` artifact, and its own comment says go.mod requires are what this artifact should reach.
- The only relocation pair C decided (REL-4-s2) was written as a repository reference, not a Go module.
- Silent misses are worse than abstention, because nothing reaches the user. That is why G1 exists, and why this is reported as the study's main defect.

## 7. Defects found and fixes

The run above is the result **at the freeze tag**. Under DESIGN §7, fixes land in their own PRs, and a post-fix run is reported separately as "after fixes".

| Id | Defect | Exposed by | Status |
|---|---|---|---|
| D-R1 | `check_dependency` does not compare a Go module package with a source-repository artifact naming the same path | 12 silent misses (RQ-R1) | Open: fix PR to follow |
| D-R2 | The GitHub collector treats the API's 301 for a transferred repository as an error, so ownership drift is never observed | Discovery of REL-1, REL-3 and REL-4 (RQ-R3) | Open: fix PR to follow |

## 8. Limitations

- **The labels are the developer's.** There are no independent human labels. The AI-assisted pilot agrees with L1 (κ = 0.825), but it is not a second human judgement. Any error in L1's rules propagates into every metric.
- **Small sample.** 27 events cannot decide H1, which needs 60. The confidence intervals are wide, and the pairs within an event are correlated, so the tests are clustered by event.
- **The events are not a population sample.** They were researched under class quotas (DESIGN §3), so recall and rates describe this set only.
- **Hindsight in dependent selection.** Dependents were found today among repositories that still exist, although their references are read at pre-event commits.
- **Fixture authorship.** The person who wrote the fixtures knows OpenPulse's scope language, which can make representation look easier than it is for a real producer.
- **Inventory reader coverage.** 9 Go references come from Godeps or vendor files, for which OpenPulse has no reader. They are represented by their module root, as a go.mod would name them.

## 9. Reproducibility

The package consists of:
- the event fixtures (`events/`) with their archived URLs;
- the frozen case file and its SHA-256;
- `results/openpulse-retro-2026-11.json`;
- the freeze tag `retro-freeze-2026-10-30`;
- the CI workflow `.github/workflows/retrospective.yml`.

To re-run it, use the same workflow, or the command in DESIGN §7 on a checkout of the tag with the study data copied in.
