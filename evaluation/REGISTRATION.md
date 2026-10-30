# Registration: completeness-aware applicability decisions (TR-2026-01 evaluation)

**Status: drafted 2026-10-30, amended 2026-10-30 (§12), not yet archived.** This document becomes the registered protocol when the author archives it, with its fields completed, on OSF Registries or Zenodo (DOI) **before any held-out label exists**. Until then it is a draft and may change. After archiving, any change is an amendment (§11).

**Not archivable yet: only the archiving fields remain.** The 2026-10-30 amendments are implemented, with their constants in `registration.py` (§9):
- policy R: its encoding rules (`evaluation/representations/ENCODING.md`) and its consumer (`evaluation/existing_representation.py`), with each event's encoding frozen by SHA-256 in the case set;
- S3, G4 and the attribution steps B→R→V→C;
- the review-burden measures W1–W3: the inventory run per weekly cycle, and W3's seeded sample and summary;
- the reliability measures D1–D2, tabulated from the annotators' records.

The stopping rule (§6) and the inclusion criteria per event class (§7) are drafted (2026-10-30) for the author to confirm or change before archiving. What remains is the registry fields of the table below: registry and identifier, archive date, implementation freeze, event-window start, and annotators.

| Field | Value |
|---|---|
| Title | Do completeness-aware applicability rules make better dependency decisions than simpler policies? |
| Author | Mehmet KI, Ikarus AI Labs |
| Registry and identifier | **to fill at archiving** (OSF Registries or Zenodo DOI) |
| Archive date | **to fill at archiving** |
| Implementation freeze | **to fill at archiving**: tag and full commit of the tested OpenPulse |
| Analysis code | `evaluation/registration.py` and `evaluation/run.py` at the freeze commit; thresholds as constants (`registration.thresholds()`) |
| Baseline V comparators | npm: node-semver `semver` 7.8.5, Node 24.22.0. Go: `golang.org/x/mod` v0.42.0, Go 1.26 (go1.26.10). Maven: `org.apache.maven:maven-artifact` 3.9.16 (jar SHA-256 `54cc1c1e…3ad3e8`), Temurin 25. PyPI: `packaging` as hash-locked. Each bridge reports its library version and must match (`evaluation/ecosystem_versions.PINS`); `evaluation/comparators/README.md` |
| Event-window start | **to fill at archiving**: the first day of the observation window (§7) |
| Annotators | **to fill at archiving**: identities or pseudonymous IDs, and their declared independence (§8) |

## 1. Background and question

TR-2026-01 specifies when a dependency may be reported as **not affected** by an upstream change. All of the following must hold:
- the event's scope is declared complete with a recorded basis;
- every scope element decisively excludes the dependency;
- exclusion by identity rests on a curated mapping;
- the evidence is current and uncontested.

Its evidence so far is conformance: the implementation follows the specification. That doesn't show that the specification produces better decisions. This study asks:

> Compared with simpler policies given the same evidence, does OpenPulse avoid false clears while deciding correctly more often?

**Scope of the claim: event-scope decisions only.** C runs `check_dependency` with events and no advisory data. OpenPulse's second decision path never runs in this study: it correlates OSV and NVD advisories by package and version. The retrospective study found a false clear in that path (TR-2026-01 §11), so no result here extends to it.

Evaluating the advisory path needs its own registration. It would also need advisories as they stood on each event's date, which OpenPulse has not recorded.

The study also does not evaluate discovery (§13) or the agent interface.

## 2. Policies compared

All policies receive the same replayed events and the same dependency, and none receives the label. Their definitions are in `evaluation/PROTOCOL.md` §2 and the code is in `evaluation/policies.py` and `evaluation/strong_baseline.py`.

| Code | Policy | Role |
|---|---|---|
| **C** | OpenPulse (`check_dependency`), freshness bound set | the tested system |
| **B** | conservative: affected if listed, otherwise abstain | primary comparator |
| **A** | naive: affected if listed, otherwise not affected | safety comparator |
| **V** | strong conservative baseline: C's model (typed scopes, completeness basis, curated identity) with ecosystem comparators and no engine-specific matching | equivalence comparator |
| **R** | existing-representation baseline: each event re-encoded in OSV or OpenVEX and read by a careful conservative consumer, without C's model (below) | model comparator |

**Policy R.** R asks what the model adds over formats that already exist, read with care.

- **Encoding.** Each held-out event is re-encoded from its primary sources alone, following written rules (`evaluation/representations/ENCODING.md`, frozen at archiving). Version and package changes become an OSV record. Changes to images, repositories and distributions become OpenVEX statements, with products as purls and status `affected`, `not_affected` or `under_investigation`.
- **The encoder.** The encoder is not an annotator, sees no labels and no policy output, and finishes before any policy runs. For each event, the encoder records what the format could not express (the *encoding loss*). An example is "every image under this namespace".
- **The consumer.** It reports *affected* when an OSV range for the dependency's package includes its version under the pinned ecosystem comparator (the same pins as V), or when a statement with status `affected` names its exact purl. It reports *not affected* only in two cases:
  - an OSV range for the same package excludes the version;
  - a `not_affected` statement names the exact purl.

  Everything else is unresolved.
- **What R lacks.** Identity is exact purl equality. R has no curated catalogue, no typed namespace elements and no completeness declaration.

R's code is `evaluation/existing_representation.py`, frozen with the other policies (§10).

**Attribution.** The four comparators separate the following contributions (reported in §4, never tested together):
- B to R: what existing formats and a careful consumer add;
- R to V: what the typed model adds (typed elements, completeness with a basis, curated identity);
- V to C: what the engine adds.

Each step is reported with its resolution gain and its review cost (W1–W3, §5).

**Why B, not V, is primary.** This is a change from the draft in TR-2026-01 §10, and it is disclosed in §12. V shares C's model, so C against V measures only the engine. The claim under test is about the model, so the primary comparison sets OpenPulse against a policy without the model. C against V is kept as a secondary equivalence test.

## 3. Primary hypotheses

Both must hold for the primary result to be a success.

**H1, safety (non-inferiority).**
- **Measure:** the event-level false-clear share. A false-clear event is an event with at least one in-scope pair that C reports as NOT_AFFECTED. The share is false-clear events divided by events with at least one in-scope pair ("events at risk").
- **Decision rule:** the exact one-sided 95% upper bound (Clopper–Pearson) of C's share, minus B's observed share, must be **≤ δ = 0.05**. B never clears, so its share is 0 by construction.
- **Decidability:** H1 is decidable only with **at least 60 events at risk**. With fewer, the result is "not decidable", never a pass.
- **Why events, not pairs:** pairs that share an event are correlated, and with zero false clears a clustered interval has zero width, which is uninformative. The rule of three over independent events is the honest instrument.

**H2, usefulness (superiority).**
- **Measure:** resolution rate, meaning correct decisive outcomes (AFFECTS on an in-scope pair, NOT_AFFECTED on an out-of-scope pair) over decidable pairs. Undeterminable pairs are excluded from the denominator.
- **Decision rule:** the paired difference, C minus B, must be **≥ 0.10**, *and* its one-sided 95% lower bound must be **above 0**.
- **Interval:** an event-clustered paired bootstrap, resampling a case's event set with replacement. 4,000 resamples, seed 20261030.

**Verdict.**
- **success:** H1 passes and H2 passes;
- **failure: no usefulness gain:** H1 passes and H2 fails;
- **failure: safety margin not met:** H1 fails, whatever H2 shows. A result that gains usefulness by breaking the safety margin is a failure, not a trade-off;
- **not decidable:** fewer than 60 events at risk.

**Any** observed false-clear event is analysed in full and reported, whatever the bound.

## 4. Secondary tests

Holm-corrected together at α = 0.05, and never used to rescue a failed primary result.

| Test | Rule | What it shows |
|---|---|---|
| **S1:** C vs V equivalence | Two one-sided tests: the 90% bootstrap interval of the resolution difference, C minus V, lies within **±0.05** | whether the engine adds anything beyond a careful implementation of the same model |
| **S2:** A vs C safety | The event-level false-clear share of A minus C is above 0, one-sided, by paired event bootstrap | whether reading absence as exclusion causes false clears that the model avoids |
| **S3:** C vs R usefulness | The resolution difference, C minus R, is above 0: one-sided 95% lower bound of the event-clustered paired bootstrap | whether the model decides correctly more often than a careful consumer of existing formats |

R's false-clear events and their exact bound are reported next to S3. A gain over R that comes with more false-clear events than R is reported as a trade-off, not as an improvement.

**Reported but never tested:**
- A's false-clear events and their bound;
- C minus A in resolution rate. A answers everything, so this can favour A even while A falsely clears;
- every metric of `evaluation/PROTOCOL.md` §4: pair-level FCR_affected and FCR_clear, false impact, decisive coverage, unsupported decisiveness, evidence completeness;
- the ablations (completeness, freshness, both, identity);
- the attribution steps B→R→V→C (§2), each with its resolution difference and interval and its review-burden difference (W1);
- the encoding loss per event and event class (§2), and R's results restricted to events with no encoding loss;
- the review-burden measures W1–W3 (§5) and the reliability measures D1–D2 (§5a);
- every result stratified by event class, identity status, completeness basis and label independence.

## 5. Guardrails

These are conditions on how usable C is, reported next to the verdict.

| Guardrail | Rule |
|---|---|
| **G1:** silent misses | C's no-association rate on in-scope pairs **≤ 0.02**, with every such case analysed. A consumer may read "no association" as "proceed". |
| **G2:** abstention | C's unresolved rate on decidable pairs **≤ B's + 0.05**. A completeness-aware policy that abstains more than "abstain on everything unlisted" offers nothing. |
| **G3:** per-class abstention | Reported for every event class, with any class **> 0.60** flagged. It shows where curation is the bottleneck. It is not a test. |
| **G4:** review burden | C's median W1 across inventories **≤ B's median W1**. A policy that leaves more references for a person to review than "abstain on everything unlisted" has not reduced the work. |

A failed G1, G2 or G4 is reported as a limitation of the result. It changes neither the primary verdict nor its wording, which states the guardrail outcome next to it.

**Review burden.** Per-pair rates hide workload: many defensible but uninformative associations can be burdensome even when each verdict is correct. These are reported for C, V, R and B:

- **W1, unresolved per inventory and cycle.** Run every reference of each participating inventory (not only the sampled pairs) against every held-out event current in each weekly cycle of the window. Count the references whose cross-event summary is unresolved. Report:
  - the count and its share of the inventory, as a median, interquartile range and maximum across inventories and cycles;
  - the count of *new* unresolved references per cycle.

  W1 needs no labels.
- **W2, unresolved per event at risk.** The number of references an event leaves unresolved across all participating inventories.
- **W3, minutes per review.** One annotator resolves a random sample of 50 of C's unresolved summaries and 50 of B's from primary sources, timing each. Report the mean minutes per item, with a bootstrap 95% interval, and the implied reviewer hours per inventory and cycle (W1 × W3).

## 5a. Reliability of admitted inputs

The soundness lemma makes a negative sound only if its inputs are true of the real change. Oracle agreement does not test that. These two measures do, on the held-out events. Both are reported with exact 95% intervals and counts; neither is a test.

- **D1, completeness declarations.** Take every held-out event whose scope C admits for a negative (declared complete with a basis). Two annotators compare the declared scope with the affected set its primary sources establish, and judge it:
  - **correct**;
  - **under-inclusive:** it omits an affected artefact. That is a false-clear risk whether or not a sampled pair hit it;
  - **over-inclusive.**

  Report the under-inclusive rate per basis (definitional, announced, corroborated). If fewer than 10 events have an admitted declaration, say so. Do not pool across bases to inflate the count.
- **D2, identity mappings.** Take every curated identity mapping (catalogue entry or package mapping) that a decisive verdict of C or V on a held-out pair relies on. Check it against the project's own sources and judge it **correct**, **wrong** or **stale** (correct once, not at the event date). Report the error rate, and list every wrong or stale mapping with the verdicts that relied on it.

## 6. Sample size

**Events.** The target is **60–80 independent events at risk**.
- At 60 events with zero false-clear events, the exact bound is 0.049, which meets δ.
- **A single false-clear event fails H1 at 60 events** (bound 0.0766). Tolerating one needs at least 93 events. That strictness is intended, and the author may choose to sample more events.
- **Stopping rule** (drafted 2026-10-30; the author confirms or changes it at archiving):
  - Collection stops when **80 events** meet the inclusion criteria (§7), counted in order of first observation.
  - If fewer than 60 of those 80 are at risk (at least one in-scope pair), sampling continues in the same order until 60 are at risk, or until the window closes. Whether an event is at risk is read from its adjudicated labels alone, and no policy runs before collection stops. So the rule depends on labels, never on a result.
  - If the window closes with fewer than 60 events at risk, the result is "not decidable" (§3).
- **Why 80:** some included events will have no in-scope pair among their drawn pairs, so stopping at 60 events would risk a "not decidable" result. 80 leaves about a quarter for that. One false-clear event still fails H1 at 80 (bound 0.058); tolerating one needs at least 93 events, at about 1.5 times the labelling and encoding budget of 60.

**Pairs.** 6–10 pairs per event, about 500 pairs in all.

**Power for H2** (rough, stated so it can be checked):
- **Assumptions:** a design effect of 2–3 for clustering, giving about 200 effective pairs, and C and B disagreeing on 20–30% of pairs.
- **Result:** the standard error of the paired difference is about 0.035, so a true gain of 0.10 gives roughly 80% one-sided power.
- **Caveat:** the design effect is the weakest assumption. The development set (13 event sets) gave a C-minus-B difference of 0.196, 95% interval 0.02–0.34, in the run that informed this draft (revision 2, 2026-10-30). The current code gives 0.216, 0.07–0.34, because one pair (fa-01) is now resolved (PROTOCOL §7). Either way, that is far too few events to estimate the design effect.

**Labelling budget.** About 500 pairs × 2 annotators at 3–5 minutes per pair, so 25–40 hours per annotator, plus adjudication. The amendments add, roughly:
- **R encoding:** 15–25 minutes per event, about 20 hours for one encoder at 60 events;
- **D1:** 10 minutes per admitted declaration per annotator;
- **D2:** 2–5 minutes per mapping;
- **W3:** 100 timed reviews, about 8 hours.

At the drafted 80 events and 8 pairs per event: about 640 pairs, so 32–53 hours per annotator, and 20–33 hours of R encoding.

## 7. Population and sampling

**Events.**
- **Sources:** events are sampled from sources that do not feed OpenPulse: vendor and project announcements, distribution changelogs, and platform transfer and archival records.
- **Window:** a **prospective** observation window that starts after the implementation freeze (§1 table). OpenPulse cannot replay registry state it never recorded, and reconstructing past state from today's invites hindsight bias. A retrospective event is admitted only with archived contemporaneous evidence, and is reported separately.
- **Classes:** repository relocation, repository archival, distribution change (images or tags withdrawn or moved), lifecycle end (EOL/EOS), licence change, and breaking release.
- **Inclusion criteria** (drafted 2026-10-30; the author confirms or changes them at archiving). They are fixed before sampling, and adapted from the retrospective study's (`evaluation/retrospective/DESIGN.md` §3) to a prospective window.

  **Every event must meet all of these:**

  | | Criterion |
  |---|---|
  | I1 | A **primary source** states the change and its scope: the vendor, the maintainer, or the registry's or platform's own record. A news article or a third-party database alone is not enough. |
  | I2 | The event is **first observed within the window**, and announced or effective no more than 30 days before it is first observed. |
  | I3 | Its primary sources are **archived when first observed**: a snapshot (Wayback Machine, or a copy stored with the fixture) taken within 7 days, or a permanent record whose own history shows the text then (a commit, a release tag, a registry record with timestamps). |
  | I4 | The affected identifiers are **machine-identifiable**: a repository path, a package with its ecosystem, an image reference, namespace or registry, and a version boundary where the scope is versioned. |
  | I5 | It was found in a source that does **not feed OpenPulse**. Feeds OpenPulse consumes (endoflife.date, OSV, NVD, GitHub repository metadata as collected) may corroborate it, never establish it. |
  | I6 | At least one participating inventory has a reference whose repository, package or image name matches a project or artefact the source names. This is a name search done before labelling, never a policy run. |

  **Exclusions:**

  | | Exclusion |
  |---|---|
  | X1 | The same change of the same project is in the development set, the case ledger or the retrospective study. |
  | X2 | The primary source leaves the event's extent undefined, so no scope can be written down. *Within* an included event, a dependency whose membership the source does not settle is kept and labelled `undeterminable`. |
  | X3 | OpenPulse, or any policy, was run on the candidate before its case file was frozen. Selection must not see how a policy handles an event. |

  **Per class: what counts as one event, what dates it, and the minimum evidence:**

  | Class | One event | Dated by | Minimum evidence |
  |---|---|---|---|
  | Repository relocation | One announcement or platform record moving one or more repositories to a new owner or path. Repositories moved together are one event, with each repository a scope element. | The platform's transfer or redirect record, or the maintainer's announcement, whichever is earlier | The old and new paths, from the platform's record (redirect or repository metadata) or the maintainer's statement |
  | Repository archival | One repository marked archived or read-only, or declared unmaintained by its maintainers | The platform's archive timestamp, or the statement's date | The platform's archived flag as observed, or the maintainers' statement |
  | Distribution change | One publisher's announcement that images, tags, charts or packages are withdrawn, moved, or no longer published in a registry or namespace | The announcement, or the first observed registry change if there is none | The publisher's statement naming the registry, namespace or artefacts, and the registry listing when first observed |
  | Lifecycle end | One release line reaching end of life or end of support on the vendor's own schedule | The end date the vendor states | The vendor's lifecycle page or announcement naming the line and the date |
  | Licence change | One change of licence terms for a project's releases from a stated version or date | The release or announcement that introduces it | The project's licence text at the boundary, and the maintainers' statement of the boundary |
  | Breaking release | One major release that its maintainers declare breaking | The release tag's date | Release notes or a migration guide naming the breaking changes and the release line |

  **Balance across classes:** no class contributes more than 20 of the 80 events. A class with fewer than 8 included events by the end of the window is reported as such. It is never filled by relaxing a criterion.

**Dependencies.**
- **Inventories:** from collaborators and public projects that contain container images, distributions and embedded components.
- **Pairs:** drawn by stratified random sampling over event class and reference kind, so the sample is not limited to cases the detector handles easily.
- **Labelling:** every drawn pair is labelled, including pairs OpenPulse never associates with the event.

**Replay.** Each event is recorded as a fixture with its evidence and replayed as known on its first-observation date (`evaluation/replay.py`), with a freshness bound of 90 days.

## 8. Labelling

**Annotators.**
- Two annotators label each pair, blind to every policy's output. A third adjudicates disagreements.
- None of the three developed the detector. Each states their independence in the archived record.
- Agreement is reported as Cohen's κ, before adjudication.

**Labels.** `in_scope`, `out_of_scope` or `undeterminable`, each with a rationale and a source (`run.validate` enforces this). When sources conflict:
- the announcing source defines the intended scope;
- registry and repository observations establish the current state;
- an unresolved conflict is `undeterminable`, never forced into a binary label.

**Freeze.** The labelled set is frozen and its SHA-256 recorded **before** any policy runs on it. Every results file records the dataset hash.

## 9. Analysis

The analysis is:

```bash
python evaluation/run.py --require-comparators --require-encodings \
    --cases <frozen held-out set> --inventories <inventories> --annotations <annotators' records>
```

at the freeze commit, with every pinned comparator installed and every held-out event's R encoding frozen. `--require-comparators` and `--require-encodings` refuse to run otherwise, and a result whose `registration.registered.valid` is false is not the registered result. The registered result is `registration.registered` in the results file, computed on independently labelled pairs only. Nothing else in that file is the registered result.

Specifically:
- **Unit:** the dependency-event pair.
- **Clusters:** a case's event set.
- **Bootstrap:** seed and resample count are fixed in `registration.py`.
- **Undeterminable pairs:** they never count as false clears or false impacts. They are reported as unsupported decisiveness.
- **Inputs beyond the pairs:** `--inventories` gives the participating inventories and the window, for W1, W2 and G4. `--annotations` gives the timed reviews (W3) and the D1 and D2 judgements. W3's items are drawn by `registration.review_sample` with the bootstrap seed. A missing input leaves its table empty and is listed under `missing_inputs`; it never changes the verdict.

## 10. Freeze and leakage control

- **Implementation:** the tested OpenPulse is frozen at a tag before labelling. A defect fixed after the freeze is reported as a separate, labelled run, and never replaces the registered one.
- **Policies:** the definitions in `evaluation/policies.py`, `evaluation/strong_baseline.py` and `evaluation/existing_representation.py`, and the event-replay code, are frozen with the implementation.
- **R encodings:** `ENCODING.md` is frozen at archiving. The per-event OSV and OpenVEX encodings are frozen, with their SHA-256 recorded, before any policy runs. They are never revised after a result is seen.
- **Labels:** frozen independently, before any policy runs on the held-out pairs.
- **Separation from the development set:** held-out events come from a later window, and from projects outside the development set.

## 11. Deviations and amendments

Any change after archiving is filed as a dated amendment in the same registry, with its reason. This covers:
- a threshold;
- a policy definition;
- the population;
- the stopping rule;
- the analysis code.

Results are reported under the registered protocol. If an amendment changes a result, both results are reported.

## 12. Disclosure: what informed this registration

A developer-labelled development set (`evaluation/cases/dev-2026-10.json`, 60 pairs over 13 events from the case ledger) was run before this registration. It informed four choices:
- making B, not V, the primary comparator, because C and V differed on 1 of 60 pairs;
- measuring safety per event;
- using resolution rate rather than decisive coverage;
- setting G2 relative to B rather than as an absolute ceiling.

The thresholds were set after those results were seen:
- **0.05 and 60 events:** what a realistic labelling budget can demonstrate.
- **+0.10:** a practitioner-meaningful gain, well below the development set's 0.196 (0.216 with the current code), so it was not set to match it.
- **±0.05, 0.02, +0.05 and 0.60:** judgement, stated here so that readers can weigh them.

Development-set results are illustrative, never evidence. They are in `evaluation/PROTOCOL.md` §7.

**Amendments of 2026-10-30, before archiving.** These were made after an external review of TR-2026-01 and a follow-up recommendation. Both were read after the retrospective study (TR-2026-01 §11) had been run, so they are disclosed as informed by it. Four changes:

1. **Scope narrowed to event-scope decisions** (§1). The advisory path is excluded, because the retrospective study found a false clear in it.
2. **Policy R, test S3 and the attribution steps added** (§2, §4). In the retrospective study, C and V differed on only 23 of 167 pairs, all through two matching mechanisms (Go module to repository, and variant image tags). So V cannot show what the model adds, and R can.
3. **Review burden W1–W3 and guardrail G4 added** (§5). Per-pair abstention (G2) does not measure workload per inventory. G4's threshold, "no worse than B", is judgement, set relative to B for the same reason as G2.
4. **Reliability measures D1–D2 added** (§5a). The soundness lemma's premises were unmeasured.

None of the primary hypotheses, margins, sample-size rules or thresholds of §3 changed.

**Drafted 2026-10-30, before archiving: the stopping rule (§6) and the inclusion criteria (§7).** They fill fields the draft left to archiving, and use no held-out data. The criteria adapt the retrospective study's (`evaluation/retrospective/DESIGN.md` §3), written before that study ran. The number 80 was chosen for decidability (some events have no in-scope pair) and budget, not from any result.

## 13. Known limitations of the design

- The policies are compared given the same events. Discovery (whether events are found at all) is measured separately, so a missed event is not a false clear here.
- Identity mappings come from OpenPulse's curated catalog for both C and V. The comparison with V therefore cannot detect a curation error that both share. D2 measures those errors directly. R does not use the catalogue, and the annotators' labels are a further check.
- R is only as good as its encoder and its encoding rules. A poor encoding would flatter C. That is why the encoding loss is reported per event, and R's results are reported on events with no loss.
- D1 and D2 measure inputs on the held-out events only. They are not estimates for curated data in general.
- The agent interface's freshness modes (TR-2026-01 §7) are not evaluated. C here is the engine with the freshness bound set, which corresponds to the interface's current mode.
- The labelling budget, not the statistics, limits the number of events. A null result at 60 events is weak evidence of absence.
- **Comparator choices.**
  - V counts a pre-release in its own core's line (the specification's rule). npm's `satisfies` would exclude it.
  - Maven versions are decidable only when their canonical form starts with a number, because ComparableVersion itself never rejects a string.
  - Debian packages are out of scope: OpenPulse ingests no `pkg:deb` dependencies, so no dpkg comparator is pinned.
  - Container image tags follow no ecosystem; V decides them by plain dotted numbers only.
