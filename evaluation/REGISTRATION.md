# Registration: completeness-aware applicability decisions (TR-2026-01 evaluation)

**Status: drafted 2026-10-30, not yet archived.** This document becomes the registered protocol when the author archives it, with its fields completed, on OSF Registries or Zenodo (DOI) **before any held-out label exists**. Until then it is a draft and may change. After archiving, any change is an amendment (§11).

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

## 2. Policies compared

All policies receive the same replayed events and the same dependency, and none receives the label. Their definitions are in `evaluation/PROTOCOL.md` §2 and the code is in `evaluation/policies.py` and `evaluation/strong_baseline.py`.

| Code | Policy | Role |
|---|---|---|
| **C** | OpenPulse (`check_dependency`), freshness bound set | the tested system |
| **B** | conservative: affected if listed, otherwise abstain | primary comparator |
| **A** | naive: affected if listed, otherwise not affected | safety comparator |
| **V** | strong conservative baseline: C's model (typed scopes, completeness basis, curated identity) with ecosystem comparators and no engine-specific matching | equivalence comparator |

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

**Reported but never tested:**
- A's false-clear events and their bound;
- C minus A in resolution rate. A answers everything, so this can favour A even while A falsely clears;
- every metric of `evaluation/PROTOCOL.md` §4: pair-level FCR_affected and FCR_clear, false impact, decisive coverage, unsupported decisiveness, evidence completeness;
- the ablations (completeness, freshness, both, identity);
- every result stratified by event class, identity status, completeness basis and label independence.

## 5. Guardrails

These are conditions on how usable C is, reported next to the verdict.

| Guardrail | Rule |
|---|---|
| **G1:** silent misses | C's no-association rate on in-scope pairs **≤ 0.02**, with every such case analysed. A consumer may read "no association" as "proceed". |
| **G2:** abstention | C's unresolved rate on decidable pairs **≤ B's + 0.05**. A completeness-aware policy that abstains more than "abstain on everything unlisted" offers nothing. |
| **G3:** per-class abstention | Reported for every event class, with any class **> 0.60** flagged. It shows where curation is the bottleneck. It is not a test. |

A failed G1 or G2 is reported as a limitation of the result. It changes neither the primary verdict nor its wording, which states the guardrail outcome next to it.

## 6. Sample size

**Events.** The target is **60–80 independent events at risk**.
- At 60 events with zero false-clear events, the exact bound is 0.049, which meets δ.
- **A single false-clear event fails H1 at 60 events** (bound 0.0766). Tolerating one needs at least 93 events. That strictness is intended, and the author may choose to sample more events.
- Collection stops at a pre-set number of events, fixed at archiving (**to fill**: 60, 80 or more). It never stops at a result.

**Pairs.** 6–10 pairs per event, about 500 pairs in all.

**Power for H2** (rough, stated so it can be checked):
- **Assumptions:** a design effect of 2–3 for clustering, giving about 200 effective pairs, and C and B disagreeing on 20–30% of pairs.
- **Result:** the standard error of the paired difference is about 0.035, so a true gain of 0.10 gives roughly 80% one-sided power.
- **Caveat:** the design effect is the weakest assumption. The development set (13 event sets) gave a C-minus-B difference of 0.196, 95% interval 0.02–0.34. That is far too few events to estimate the design effect.

**Labelling budget.** About 500 pairs × 2 annotators at 3–5 minutes per pair, so 25–40 hours per annotator, plus adjudication.

## 7. Population and sampling

**Events.**
- **Sources:** events are sampled from sources that do not feed OpenPulse: vendor and project announcements, distribution changelogs, and platform transfer and archival records.
- **Window:** a **prospective** observation window that starts after the implementation freeze (§1 table). OpenPulse cannot replay registry state it never recorded, and reconstructing past state from today's invites hindsight bias. A retrospective event is admitted only with archived contemporaneous evidence, and is reported separately.
- **Classes:** repository relocation, repository archival, distribution change (images or tags withdrawn or moved), lifecycle end (EOL/EOS), licence change, and breaking release.
- **Inclusion criteria per class** (**to complete at archiving**): what counts as one event, which source dates it, and the minimum evidence needed to include it. They are fixed before sampling.

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
python evaluation/run.py --require-comparators --cases <frozen held-out set>
```

at the freeze commit, with every pinned comparator installed. `--require-comparators` refuses to run otherwise, and a result whose `registration.registered.valid` is false is not the registered result. The registered result is `registration.registered` in the results file, computed on independently labelled pairs only. Nothing else in that file is the registered result.

Specifically:
- **Unit:** the dependency-event pair.
- **Clusters:** a case's event set.
- **Bootstrap:** seed and resample count are fixed in `registration.py`.
- **Undeterminable pairs:** they never count as false clears or false impacts. They are reported as unsupported decisiveness.

## 10. Freeze and leakage control

- **Implementation:** the tested OpenPulse is frozen at a tag before labelling. A defect fixed after the freeze is reported as a separate, labelled run, and never replaces the registered one.
- **Policies:** the definitions in `evaluation/policies.py` and `evaluation/strong_baseline.py`, and the event-replay code, are frozen with the implementation.
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
- **+0.10:** a practitioner-meaningful gain, well below the development set's 0.196, so it was not set to match it.
- **±0.05, 0.02, +0.05 and 0.60:** judgement, stated here so that readers can weigh them.

Development-set results are illustrative, never evidence. They are in `evaluation/PROTOCOL.md` §7.

## 13. Known limitations of the design

- The policies are compared given the same events. Discovery (whether events are found at all) is measured separately, so a missed event is not a false clear here.
- Identity mappings come from OpenPulse's curated catalog for both C and V. The comparison with V therefore cannot detect a curation error that both share. The independent oracle kit (`conformance/independent/`) and the annotators' labels are the checks on curation.
- The labelling budget, not the statistics, limits the number of events. A null result at 60 events is weak evidence of absence.
- **Comparator choices.**
  - V counts a pre-release in its own core's line (the specification's rule). npm's `satisfies` would exclude it.
  - Maven versions are decidable only when their canonical form starts with a number, because ComparableVersion itself never rejects a string.
  - Debian packages are out of scope: OpenPulse ingests no `pkg:deb` dependencies, so no dpkg comparator is pinned.
  - Container image tags follow no ecosystem; V decides them by plain dotted numbers only.
