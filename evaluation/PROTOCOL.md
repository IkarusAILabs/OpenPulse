# Comparative decision-policy evaluation — protocol

Status: **harness implemented, development set run; held-out evaluation not started.** This protocol implements the core of TR-2026-01 §10 (Applicability) and the comparative experiment recommended in the external review of 2026-10-30 (Priority 1). It is fixed here before any held-out case is labelled. A change to sections 2–4 after held-out labelling starts is a protocol amendment and is reported as one.

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
| **V-strong-conservative** | TR-2026-01 §10 baseline (v), in `strong_baseline.py`. It uses the same typed scopes, admissibility and curated identity mappings as C, with exact (curated, VERIFIED) identity only, ecosystem comparators (PyPI: `packaging`; elsewhere plain dotted numbers only), and every undecidable relation undetermined. | **The primary comparison:** what C's engine adds beyond a careful conservative consumer of the same model. |
| **C-openpulse** | The production engine (`check_dependency`), freshness bound set. | Whether structured scope, completeness, identity and freshness conditions buy decisiveness without false clears. |
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

V shares C's model: the typed scope, completeness with a basis, and curated identities. So a C-over-V result measures the *engine* (matching semantics, version grammar), not the *model*. The model's value shows in the comparison of V and C with A and B.

Not yet pinned for V: comparators for npm (node-semver), Go (`x/mod/semver`), Maven (`ComparableVersion`) and Debian (`dpkg --compare-versions`). Until they are pinned, V abstains on those ecosystems' non-numeric versions.

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
| Evidence completeness | For decisive outcomes: the share that name sources, carry an acquisition time, and cite a recorded completeness basis. Baselines emit no justification, so for them it is `None`. |
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

| Policy | False clears | FCR_aff | False impact | Resolved | Abstain | Unsupported decisive |
|---|---|---|---|---|---|---|
| A-naive | 5 | 0.185 | 0.25 | 0.784 | 0.0 | 1.0 |
| B-conservative | 0 | 0.0 | 0.25 | 0.431 | 0.433 | 0.667 |
| V-strong-conservative | 0 | 0.0 | 0.0 | 0.569 | 0.483 | 0.0 |
| C-openpulse | 0 | 0.0 | 0.0 (was 0.042 before F1) | 0.588 | 0.467 | 0.0 |
| C-ablate-both | 1 | 0.037 | 0.0 | 0.608 | 0.433 | 0.0 |
| C-ablate-identity | 0 (silent misses 0.111) | 0.0 | 0.0 | 0.588 | 0.183 | 0.0 |

What this set shows, and what it does not:

- **C vs V (the primary comparison).** They differ on one pair of 60. On `postgres:13.16-alpine` (pg-02), V has no comparator for a tag with a variant suffix and abstains, while C's version grammar decides it correctly. On this set, nearly all of C's advantage over A and B comes from the model, which V shares, and very little from the engine. If the held-out set confirms this, the paper should claim the representation (typed scope, completeness with a basis, curated identity) and its admission rule as the contribution, and treat the engine as one implementation of it.
- **C vs B.** Both issue no false clears. C resolves more pairs correctly (0.59 vs 0.43), has a lower false-impact rate, and makes no decisive call on undeterminable pairs. Its abstention rate, however, is *higher* than B's. Most of the abstentions are relocation and identity cases, where B's name-based listing guesses and C does not.
- **Ablations.** Neither single ablation changes any outcome. Only removing both clears React 18.3.1 (rx-02) against a partial, stale scope. On this set the two premises are redundant protections. Separating them needs held-out events with complete-but-stale and partial-but-fresh scopes.
- **F1: a defect the evaluation found, now fixed.** C marked the PyPI package `redis` 6.2.0 (redis-py, the client) AFFECTS_VERSION under Redis 6.2 end of life (re-06). The cause was that package identity resolved by name across ecosystems. It was a false impact, not a false clear. Package identity is now per ecosystem, redis-py is curated as its own project, and re-06 has no association (CHANGELOG, `tests/test_evaluation.py`).
- **Identity: the D10 trade-off, measured.** Reading unresolved identity as "another project" cuts abstention from 0.47 to 0.18, but 3 of 27 in-scope pairs then silently get no association: the archived fbsdk repository (fa-01) and two unlisted iText modules (it-02, it-03). With D10, C reports them as unresolved. The other 14 pairs the ablation changes are out-of-scope or undeterminable. That is the coverage cost TR-2026-01 §11 listed as unmeasured: on this set, 17 of 60 pairs, or 28%, are held unresolved by D10 alone, and 3 of those 17 are truly in scope. Curation is what wins those clearances back.
- **Sample size.** With 13 events, the rule-of-three bound on per-event false clears is about 0.23. The set cannot support any claim about rates.
