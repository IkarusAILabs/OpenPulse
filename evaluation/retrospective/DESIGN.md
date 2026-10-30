# Retrospective study on real historical changes (ROADMAP R-C0): design

**Status: design for approval. No event fixture, case, label or OpenPulse run on a candidate exists yet.** Every rule below is fixed before data collection. Any change after approval is recorded in §11 with its date and reason.

## 1. What this study is, and is not

The study evaluates OpenPulse on **real upstream changes of the past**, judged on what was knowable at the time. It answers the external recommendation's Priority 2.

- **Exploratory, not confirmatory.** The registered evaluation (`evaluation/REGISTRATION.md`) takes its primary evidence from a *prospective* window, with independent annotators. This study is retrospective and mostly developer-labelled, so it is reported as exploratory, in its own section, and is never pooled with the registered result.
- **It cannot show advance warning.** These events are past, so any detection today is late by construction. Lead time is not measured.
- **It is disjoint from both other data sets.** Its events are excluded from the development set and the case ledger (§3, X1), and, being historical, from the registered prospective window.

## 2. Questions

- **RQ-R1, decisions.** On real events and contemporaneous dependency references, how do A (naive), B (conservative), V (strong conservative, pinned comparators) and C (OpenPulse) compare on false clears, false impact, resolution, abstention and unsupported decisiveness, per event class?
- **RQ-R2, representation.** Can OpenPulse's typed scope express each event's announced scope exactly (exact elements, envelopes, version boundaries, completeness with a basis)? Where can it not?
- **RQ-R3, discovery.** For event classes OpenPulse's own analysts detect (relocation, archival, distribution), do today's collectors detect the end state? Does the scope they construct match the announced one, and how is identity resolved?

## 3. Event selection

**Classes, with a target of 30 events (at least 4 and at most 6 per class):** relocation, archival or deprecation, registry or image distribution change, licence change with a version boundary, end of life (vendor-announced), and compromised or sabotaged versions.

**Inclusion: an event is included only if all of these hold.**

| | Criterion |
|---|---|
| E1 | A **primary source** states the change and its scope: the vendor, the maintainer, or the registry's own statement. A news article or a third-party database alone is not enough. |
| E2 | The primary source is **archived contemporaneously**: a Wayback Machine snapshot dated between 30 days before the announcement and 180 days after the effective date, or a permanent record whose own history shows the text at the time (a git commit, a release tag, a registry record with timestamps). |
| E3 | The affected identifiers are machine-identifiable: a repository path, a package with its ecosystem, an image reference or registry, and a version boundary where the scope is versioned. |
| E4 | The ground truth does not rest **only** on a feed that OpenPulse itself consumes. Lifecycle events need the vendor's notice, not just endoflife.date. Compromised versions need the maintainer's or registry's statement, not just an OSV record. Such feeds may still be cited as corroboration. |
| E5 | At least **3 real public dependents** can be found that referenced the affected identifier before the effective date: a manifest, lockfile, Dockerfile, Kubernetes manifest or `go.mod` at a commit dated before it. |
| E6 | The effective date is between 2016-01-01 and 2026-06-30. Archives before 2016 are thin, and the end date leaves a margin before the freeze. |

**Exclusion.**

| | Criterion |
|---|---|
| X1 | The event, or its project, is already in the development set or the case ledger: Bitnami (including Spark), etcd, capa, traefik, react-native-fbsdk, Redis 6.2, PostgreSQL 13, Django 4.2, iText, and React 18. Development data never becomes test data. |
| X2 | The primary source leaves the event's extent undefined, so no scope can be written down. *Within* an included event, a single dependency whose membership the source does not settle is kept and labelled `undeterminable` (§6). It is not excluded. |
| X3 | The event was chosen *because* of how OpenPulse handles it. To rule this out, **OpenPulse is not run on any candidate before the case file is frozen** (§7). |

**Choosing among qualifying events.** Candidates come from documented research. Every candidate is listed in `SHORTLIST.md`, with its sources and, if rejected, the criterion it failed. If more events qualify in a class than its quota of 6, the events used are chosen by a seeded shuffle (seed `20261031`, recorded), not by judgement.

## 4. Event fixtures (the input every policy receives)

Each included event becomes `events/<id>/event.json`, an OSSEvent, plus `events/<id>/SOURCES.md` with every URL and its archived snapshot. It is written **as a producer could have written it at the time, from the primary source alone, before any dependency is looked at.**

- **Evidence.** Each entry carries the source URL, the archived snapshot URL, the announcement and effective dates as stated, and `fetched_at` set to the snapshot's timestamp. Replay then sees exactly what was archived.
- **Scope.**
  - Typed elements: repository, namespace (with a tag predicate where the source distinguishes tags), registry, release line or package version list, or ecosystem-qualified package (`pkg:` purl).
  - `exhaustive: true` with basis `announced` **only** where the source states the complete extent. Otherwise the scope is partial.
  - Named example artefacts appear only as `affected_artifacts`, never as scope.
- **Representation gaps (RQ-R2).** Where the scope language cannot state the announced extent exactly, the fixture states the closest *safe* over-approximation: an envelope, or a partial scope. The gap is recorded in `SOURCES.md` under "representation", and the study reports it.

## 5. Dependency references (pairs)

For each event, **up to 8 pairs**:

- **In-scope candidates (up to 4).** References from real public dependents at a commit dated **before** the effective date. Record the repository, commit SHA, file and the reference as written. They are found by GitHub code search, by dependents listings, or by an ecosystem's reverse-dependency data. Git history provides the contemporaneous inventory.
- **Neighbours (at least 3).** References to the same name somewhere the event does not apply, built from fixed templates:

  | | Template |
  |---|---|
  | n1 | The same repository or image name in another namespace or registry. |
  | n2 | A same-named package of another project: a client library, fork or successor, curated in the catalog as another project. |
  | n3 | For versioned events, a version just outside the boundary, on each side where both exist. |
  | n4 | For relocations and registry moves, the new canonical location. |

  Each neighbour is a real reference where one is found, and otherwise a constructed one, marked `synthetic: true`. Results are reported both with and without synthetic pairs.

Sampling is per event, by these rules, and **before any policy is run**. A pair is never chosen or dropped by looking at an outcome.

## 6. Labels

- **Labels and their basis.** Each pair is `in_scope`, `out_of_scope` or `undeterminable`. The label is decided from the primary source's text and the dependent's state at its commit. It comes with a rationale and the archived source. When sources conflict, the precedence of REGISTRATION §8 applies: the announcing source defines the intended scope, and an unresolved conflict is `undeterminable`.
- **Labeller L1** is the OpenPulse developer, who labels every pair.
- **Labeller L2** is one person outside the detector's development. L2 independently labels a seeded random **25% sample** of pairs (seed `20261101`, at least one pair per event). L2 is blind to L1's labels and to every policy's output, and declares their independence.
- **Agreement.** Cohen's κ between L1 and L2 on the sample, before adjudication. Each disagreement is adjudicated by discussion, with the reasoning recorded.
- **Analysis labels.** The primary analysis uses the adjudicated labels: L1's labels corrected wherever adjudication changed a sampled pair. Results on the L2-labelled sample alone are reported too, marked `independent_label: true`.

## 7. Freeze and run

1. **Implementation.** It is frozen at tag **`retro-freeze-2026-10-30`** (`3639a0f`). Any defect the study exposes is fixed in its own PR. The study reports the run **at the freeze tag** as its result, and any post-fix run separately, as "after fixes".
2. **Case file.** `cases/retro-2026-11.json` is frozen, with its SHA-256 recorded, **after** labelling and adjudication and **before** any policy runs on it.
3. **Run.** The command is:

   ```bash
   python evaluation/run.py --require-comparators --cases evaluation/retrospective/cases/retro-2026-11.json
   ```

   It runs at the freeze tag, in CI's `comparators` environment, with a 90-day freshness bound measured from each event's replay date. Replay dates are the event's archived snapshot dates (§4), so each event is evaluated as it was knowable then.
4. **Outputs.**
   - All metrics of PROTOCOL §4, and the registered analysis, clearly marked "exploratory, retrospective, not registered".
   - Per-class tables.
   - An error analysis of **every** wrong or unresolved decision on a determinable pair, and of every decisive outcome on an `undeterminable` pair.

## 8. Discovery (RQ-R3)

For every included event of the relocation, archival and distribution classes:
- run OpenPulse's live collectors and analysts on the affected project, on one recorded date, with a read-only `GITHUB_TOKEN`;
- record whether the change was detected, which scope was constructed, how it compares with the fixture's scope (`match`, `narrower`, `broader`, `missing`), and the identity-resolution outcome.

Licence, end-of-life and compromise events reach OpenPulse through curated events or feeds, not its own discovery, so RQ-R3 does not apply to them. Recall is reported **only over this event set**, never as population recall.

## 9. Dropping an event

An included event is dropped only for one of these reasons, before any policy runs:
- its archived evidence turns out to be inaccessible when the fixture is built;
- fewer than 2 real in-scope dependents can be found, although E5 promised 3.

Every drop is listed with its reason. **Nothing is dropped after a policy has run.**

## 10. Reporting

`evaluation/retrospective/REPORT.md` is written for the paper and covers:
- the method (this document, as executed);
- the event table with sources;
- RQ-R1 tables per policy and class, with event counts beside pair counts;
- RQ-R2 representation gaps;
- RQ-R3 discovery;
- κ;
- the error analysis;
- defects found and their fixes;
- limitations.

The reproducibility package is:
- the event fixtures with their archived URLs;
- the case file with its SHA-256;
- the results JSON;
- the freeze tag.

## 11. Changes to this design

- **2026-10-30, owner decision, before any data collection:**
  - The study runs on the **27 events** that passed screening (`SHORTLIST.md`), not the target of 30.
  - Relocation and end of life keep **3 events each**, below §3's minimum of 4. No further events are researched.
  - The report states the shortfall and its effect: per-class results for those two classes rest on 3 events and are descriptive only.
  - X1 is unchanged. The Terraform and Grafana licence events stay included.

## 12. Known limitations

- **Labels are mostly the developer's.** Only the 25% sample is independent.
- **Representativeness.** Events were researched rather than sampled from a defined population, so this is not a representative sample of upstream changes. The class quotas and §3's rules limit selection effects, but do not remove them.
- **Fixture authorship.** The author of the event fixtures knows OpenPulse's scope language. That can make representation look easier than it is for a real producer, which is why RQ-R2 records every gap.
- **Hindsight in dependent selection.** It is limited, not removed. Dependents are found today, among repositories that still exist, although their references are read at pre-event commits.
