# Comparative decision-policy evaluation — protocol

Status: **harness implemented, development set run; registration drafted ([`REGISTRATION.md`](REGISTRATION.md), not yet archived); held-out evaluation not started.** The registration is the authority for the primary and secondary hypotheses, thresholds and stopping rule. This document defines the policies, labels and metrics it uses. This protocol implements the core of TR-2026-01 §10 (Applicability) and the comparative experiment recommended in the external review of 2026-10-30 (Priority 1). It is fixed here before any held-out case is labelled. A change to sections 2–4 after held-out labelling starts is a protocol amendment and is reported as one.

Run it:

```bash
python evaluation/run.py
```

Results go to `evaluation/results/<dataset>.json`, which records the dataset's SHA-256, the commit, the freshness bound, every policy's metrics and every pair's outcome. Tests: `tests/test_evaluation.py`.

## 1. Question

Does requiring a complete scope, established identity and current evidence before a negative (OpenPulse's admission conditions N1–N5) produce better dependency decisions than simpler policies? "Better" means both of these, read together:

- **safer:** fewer false clears (an in-scope dependency reported as not affected);
- **still useful:** a decisive, correct answer often enough to be worth having.

A policy that abstains on everything is perfectly safe and useless. A policy that never abstains is decisive and unsafe. The result is a trade-off, reported per policy.

## 2. Policies (registered before any case is run)

Every policy receives the same replayed events and the same dependency. None receives the label.

| Policy | Decision rule | What it tests |
|---|---|---|
| **A-naive** | Affected if the dependency is *listed* by any current event, otherwise **NotAffected**. | The risk of reading absence from a list as absence of impact. |
| **B-conservative** | Affected if listed, otherwise **unresolved** (an abstention). | The cost of never clearing anything. |
| **V-strong-conservative** | TR-2026-01 §10 baseline (v), in `strong_baseline.py`. It uses the same typed scopes, admissibility and curated identity mappings as C, with exact (curated, VERIFIED) identity only, the ecosystems' own pinned comparators (PyPI: `packaging`; npm: node-semver; Go: x/mod/semver; Maven: ComparableVersion; see `comparators/README.md`; plain dotted numbers only for image tags, or when a bridge is not installed in a development run), and every undecidable relation undetermined. | The equivalence comparison (REGISTRATION S1): what C's engine adds beyond a careful conservative consumer of the same model. It was primary in the TR draft. The registration makes B primary, because V shares the model under test. |
| **R-existing-representation** *(amended 2026-10-30)* | Each event is re-encoded from its primary sources as OSV or OpenVEX, under written rules ([`representations/ENCODING.md`](representations/ENCODING.md)), and frozen with its SHA-256 in the case set. A conservative consumer (`existing_representation.py`) reads it: exact purl identity, the pinned ecosystem comparators (the same as V's), and *not affected* only from an excluding OSV range or an explicit `not_affected` statement. Everything else, including an event with no encoding, is unresolved. See REGISTRATION §2. | REGISTRATION S3: what the model adds over existing formats read with care. |
| **C-openpulse** | The production engine (`check_dependency`), freshness bound set. Events only, with no advisory data, so the advisory path is out of scope. | Whether structured scope, completeness, identity and freshness conditions buy decisiveness without false clears. |
| C-ablate-completeness | C on inputs where every populated scope is declared complete (basis `announced`). | Premise N3. |
| C-ablate-freshness | C with no freshness bound. | Premise N4 (freshness). |
| C-ablate-both | Both of the above. | Whether either premise masks the other. |
| C-ablate-identity | C with `check_dependency(unresolved_identity="unrelated")`: a self-resolved reference counts as another project. | Premise N2 and the D10/D13 rule. |

**Listed** (A and B share it, `policies.listed`): the dependency matches the union of the event's scope values and its named affected artefacts, read literally:

- container references are compared after the specification's canonicalisation, using the oracle's parser (`conformance/oracle.py`, independent of the engine): Docker Hub host aliases fold to `docker.io`, and single names get `library`;
- namespace elements (`ns/*`) and the tag predicates `<version>` and `*` are honoured, and digests compare by equality;
- identity is **by name**: an image's repository name, or a package's name, equal to the event's project slug or to a listed package. That is how an affected-product list is commonly read, and it is the identity information a list-reading consumer actually has;
- versions compare by numeric release-line prefix (`6.2` covers `6.2.14`).

The completeness and freshness ablations change the *input events*, never the code, so each is reproducible from its transform alone (`policies._assume_complete`). The identity ablation cannot be an input transform, because identity is resolved inside the engine. It is an explicit, call-scoped engine parameter (`unresolved_identity`), unsound by design and never a production setting.

V shares C's model: the typed scope, completeness with a basis, and curated identities. So a C-over-V result measures the *engine* (matching semantics, version grammar), not the *model*. The model's value shows in the comparison of V and C with R, the careful consumer of existing formats, and with A and B.

V's comparators are pinned: node-semver 7.8.5, x/mod v0.42.0 and maven-artifact 3.9.16, through bridges (`comparators/README.md`). The registered run requires all of them. Debian is out of scope, since OpenPulse ingests no OS packages. The development-set figures in §7 were computed without the bridges installed; npm, Go and Maven pairs there used plain dotted numbers.

## 3. Labels

Each case is one (dependency, event set) pair with one label, written from the events' cited sources and the recorded registry or repository state at the replay date:

- `in_scope`: the dependency is in the change's scope;
- `out_of_scope`: it is not;
- `undeterminable`: the sources do not settle it, or they conflict.

Every label needs a `rationale` and a `label_source`, and `run.validate` refuses a case without them. Undeterminable pairs are never counted as false clears or false impacts. They feed *unsupported decisiveness* instead: abstaining on them is correct.

Each case records whether its label is independent (`independent_label`). Results are stratified by it, and only independent labels count as evaluation evidence.

## 4. Metrics (`metrics.summarise`)

| Metric | Definition |
|---|---|
| False clears | NotAffected on an in-scope pair. |
| FCR_affected | False clears / in-scope pairs. This one is comparable across policies. |
| FCR_clear | False clears / all NotAffected outcomes. It is policy-conditioned, and **undefined** (not zero) when a policy never clears. |
| Silent-miss rate | `no_association` on an in-scope pair / in-scope pairs. This is OpenPulse's Unknown, which a consumer may read as "proceed", so it is reported next to false clears. |
| False-impact rate | Affected on out-of-scope pairs / out-of-scope pairs. |
| Resolution rate | Correct decisive outcomes (affected on in-scope, cleared on out-of-scope) / determinable pairs. |
| Decisive coverage | (affected + cleared) / all pairs. It measures how often a policy answers, not whether the answer is right. |
| Abstention rate | Unresolved / all pairs. |
| Unsupported decisiveness | Decisive outcomes on undeterminable pairs / undeterminable pairs. |
| Evidence completeness | For decisive outcomes, read from the evidence contracts (v1.2) a consumer would receive, one per cited event: the share that name sources, give every source an acquisition time, state the verdict's meaning, cite a completeness basis that admits the negative (negatives only), and validate against the schema. Baselines and the identity ablation emit no contracts, so for them it is `None`. |
| Per-event false-clear bound | When no false clear is observed: a one-sided 95% upper bound of 3 / n_events (the rule of three) over independent events, never over correlated pairs. |

Rates with a zero denominator are `None`. Results are stratified by event class and by label independence.

## 5. Replay ("what was known, and when")

Each event names a fixture and a replay date `as_of` (`replay.py`):

- raw bundles are re-analysed by the production analysts with `today = as_of`;
- curated events are loaded as recorded;
- evidence fetched after `as_of` is dropped, and an event left with no evidence was not known then and is not loaded.

The replay uses the current code, and the results name the commit. This is the simplest mechanism that supports historical replay. It reconstructs the inputs, not the code that ran at the time.

## 6. Data sets

| Set | Status | Use |
|---|---|---|
| `cases/dev-2026-10.json` | **Development.** 60 pairs over 13 events from the development ledger, labelled by the developer before running. | Exercises the harness and surfaces defects. **Not evaluation evidence.** |
| Held-out set | Not started. | Events sampled from sources that do not feed OpenPulse, from an observation window after the implementation freeze. Every label comes from two annotators independent of the detector, with a third to adjudicate. Agreement is reported as Cohen's κ. Inclusion criteria are fixed per event class before sampling. |

The held-out set is frozen, and its SHA-256 recorded, before any policy runs on it. Fixes made after the freeze are reported as a separate run.

## 7. Development-set results (2026.10.30-2, illustrative only)

60 pairs over 13 events. The labeller is not independent.

The R row is from revision 3 (2026.10.30-3), which changes no case or label. The other rows are as recorded for revision 2. Later engine changes have since moved them: the current code gives V 0.627, C 0.647 resolved and 0.417 abstention, and an H2 gain of 0.216 (95% interval 0.07–0.34). Refreshing those rows is a separate change.

| Policy | False clears | FCR_aff | False impact | Resolved | Abstain | Unsupported decisive |
|---|---|---|---|---|---|---|
| A-naive | 5 | 0.185 | 0.25 | 0.784 | 0.0 | 1.0 |
| B-conservative | 0 | 0.0 | 0.25 | 0.431 | 0.433 | 0.667 |
| V-strong-conservative | 0 | 0.0 | 0.0 | 0.608 | 0.45 | 0.0 |
| C-openpulse | 0 | 0.0 | 0.0 (was 0.042 before F1) | 0.627 (0.588 before package curation) | 0.433 | 0.0 |
| C-ablate-both | 1 | 0.037 | 0.0 | 0.647 | 0.4 | 0.0 |
| C-ablate-identity | 0 (silent misses 0.037) | 0.0 | 0.0 | 0.627 | 0.2 (0.183 before F4 curation) | 0.0 |
| R-existing-representation (revision 3; 6 of 13 events encoded) | 0 | 0.0 | 0.0 | 0.098 | 0.917 | 0.0 |

What this set shows, and what it does not:

- **C vs V (REGISTRATION S1; primary in the TR draft).** They differ on one pair of 60.
  - On `postgres:13.16-alpine` (pg-02), V has no comparator for a tag with a variant suffix and abstains, while C's version grammar decides it correctly.
  - Before F2 was specified, C and V also differed on two iText modules (it-02 and it-03). C was affected through a then-unspecified rule: a package is a member when the scope lists its project. The rule is now specified (SPEC §4.4, project package element), and V applies it too.
 On this set, nearly all of C's advantage over A and B comes from the model, which V shares, and very little from the engine. If the held-out set confirms this, the paper should claim the representation (typed scope, completeness with a basis, curated identity) and its admission rule as the contribution, and treat the engine as one implementation of it.
- **C vs B.** Both issue no false clears. C resolves more pairs correctly (0.59 vs 0.43), has a lower false-impact rate, and makes no decisive call on undeterminable pairs. Its abstention rate, however, is *higher* than B's. Most of the abstentions are relocation and identity cases, where B's name-based listing guesses and C does not.
- **Ablations.** Neither single ablation changes any outcome. Only removing both clears React 18.3.1 (rx-02) against a partial, stale scope. On this set the two premises are redundant protections. Separating them needs held-out events with complete-but-stale and partial-but-fresh scopes.
- **F1: a defect the evaluation found, now fixed.** C marked the PyPI package `redis` 6.2.0 (redis-py, the client) AFFECTS_VERSION under Redis 6.2 end of life (re-06). The cause was that package identity resolved by name across ecosystems. It was a false impact, not a false clear. Package identity is now per ecosystem, redis-py is curated as its own project, and re-06 has no association (CHANGELOG, `tests/test_evaluation.py`).
- **Identity: the D10 trade-off, measured.** Reading unresolved identity as "another project" cuts abstention from 0.47 to 0.18, but in-scope pairs then silently get no association. Before package curation there were 3 of 27: the archived fbsdk repository (fa-01) and two unlisted iText modules (it-02, it-03). After curation, only fa-01 remains, because the iText modules are curated and resolve. With D10, C reports the uncurated ones as unresolved. The other 14 pairs the ablation changes are out-of-scope or undeterminable. That is the coverage cost TR-2026-01 §11 listed as unmeasured: on this set, 17 of 60 pairs, or 28%, are held unresolved by D10 alone, and 3 of those 17 are truly in scope. Curation is what wins those clearances back, and package curation already turned two of the three into correct positives.
- **R (REGISTRATION S3): illustrative only, and weaker than that.** Dataset revision 3 adds OSV/OpenVEX encodings for six events (`representations/dev-2026-10/`). The developer wrote them, after the labels and after every other policy's results were seen, so they are neither blind nor independent. The other seven events have no encoding, and R leaves their pairs unresolved. The run had no npm, Go or Maven bridge installed.
  - **Overall:** no false clear and no false impact, but R resolves only 5 of 51 decidable pairs (0.098) and abstains on 55 of 60.
  - **Encoded events only (40 pairs, 7 event sets):** R resolves 0.15, B 0.45, C 0.70.
  - **Encoding loss:** Bitnami (namespace, tag class, closed list: L1–L3), Redis 6.2 end of life (a server line with no package or named image: L6) and the iText licence change (a product name without coordinates: L4) lose what decides their pairs. R is unresolved on all of them.
  - **Lossless events (Django, etcd, React; 14 pairs):** R and C both resolve 5 of 11 decidable pairs. R clears the relocation's destination (et-02) from an explicit `not_affected` statement, where C abstains. C decides react 18.2.0 (rx-01), which R cannot without the npm bridge: its range boundaries (`18.0.0-0`, `19.0.0-0`) are not plain numbers. With the bridge (CI's `comparators` job), R would also decide rx-01 to rx-03. That run is not reported here.
  - **Reading:** on this set, C's advantage over R comes from events whose scope the formats cannot express, not from events they can. Whether that holds on independent encodings is what S3, and R's results on lossless events, will show.
- **Sample size.** With 13 events, the rule-of-three bound on per-event false clears is about 0.23. The set cannot support any claim about rates.

## 8. Registered analysis

[`REGISTRATION.md`](REGISTRATION.md) fixes the hypotheses. `evaluation/registration.py` holds every threshold as a constant and applies them. `run.py` writes the result to `registration.registered` (independently labelled pairs only), and to `registration.all_labels_illustrative`, which is never evidence.

| | Rule |
|---|---|
| **H1:** safety | C's event-level false-clear share: exact one-sided 95% upper bound − B's share ≤ 0.05, with ≥ 60 events at risk. One false-clear event fails it at 60 events (bound 0.0766). |
| **H2:** usefulness | resolution rate C − B ≥ 0.10, with an event-clustered one-sided 95% lower bound > 0 |
| **S1** | C vs V equivalence within ±0.05 (TOST); Holm-corrected with S2 |
| **S2** | A − C event-level false-clear share > 0 |
| **S3** | resolution rate C − R > 0, event-clustered one-sided 95% lower bound; Holm-corrected with S1 and S2 |
| **G1–G3** | silent misses ≤ 0.02 of in-scope pairs; unresolved rate ≤ B's + 0.05; per-class flag above 0.60 |
| **G4** | median W1 (unresolved references per inventory and weekly cycle) of C ≤ B's; needs `--inventories` |
| Reported | attribution B→R→V→C; R's false clears and its results on lossless events; encoding loss per event and class; W1–W3 (`--inventories`, `--annotations`); D1–D2 (`--annotations`) |

On the development set the registered result is **not decidable**. It has no independent labels, and only 13 event sets where 60 are needed. The all-labels illustration:
- **H1:** C has no false-clear event (bound 0.206).
- **H2:** gain 0.196, 95% interval 0.02–0.34.
- **S1:** not established (C − V = 0.02, Holm p 0.08).
- **S2:** A has false-clear events in 3 of 13 event sets (Holm p 0.06).
- **S3:** C − R = 0.55, 95% interval 0.32–0.74 (Holm p < 0.001). This reflects the seven unencoded events and the lossy encodings above, not a measured advantage of the model.
- **Attribution:** B→R −0.33, R→V +0.53, V→C +0.02.
- **G4, W1–W3, D1–D2:** not computed. The development set has no participating inventories and no annotators' records.
- **G1 and G2:** pass.
- **G3:** flags archival, breaking-change and relocation.

