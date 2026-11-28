# Metrics

All metrics are computed by script from the labelled pairs. No reported rate is typed by hand.

The registered metric code is `evaluation/metrics.py` and `evaluation/registration.py`. The research pipeline adds `research/scripts/inference.py`.

## 1. Unit and labels

- The **pair** (reference, event) is the unit of decision.
- Labels:
  - `in_scope`: the reference is affected by the event;
  - `out_of_scope`;
  - `undeterminable`.
- A pair is **determinable** if its label is one of the first two.

## 2. Error categories

Each pair receives exactly one category (`research/scripts/evaluate.py:CATEGORY`; tested in `tests/test_research_pipeline.py`).

| Label \ outcome | affected | cleared | unresolved | no association |
|---|---|---|---|---|
| in scope | correct affected | **false clear** | unresolved | **silent miss** |
| out of scope | **false positive** | correct unaffected | unresolved | no association |
| undeterminable | unsupported decision | unsupported decision | abstained | abstained |

Baseline R's pairs whose event has no encoding are `not_encoded`, whatever their outcome (BASELINES.md §3).

## 3. Rates and their denominators

Every rate is reported as **k / n**, with n named. A zero denominator gives "undefined" (`None`), never 0.

| Metric | Numerator | Denominator |
|---|---|---|
| **False-clear rate** | false clears | **in-scope pairs** |
| False clears, event level | events with ≥ 1 false clear | events with ≥ 1 in-scope pair (events at risk) |
| FCR among clears (registered `fcr_clear`) | false clears | cleared outcomes |
| Silent-miss rate | silent misses | in-scope pairs |
| Correctly identified affected | correct affected | in-scope pairs |
| **False-positive rate** | false positives | **out-of-scope pairs** |
| Correctly identified unaffected | correct unaffected | out-of-scope pairs |
| Resolution rate | correct affected + correct unaffected | determinable pairs |
| Unresolved rate | unresolved + abstained | all evaluated pairs |
| Decisive rate | affected + cleared outcomes | all evaluated pairs |
| Identity-resolution coverage | pairs by identity status (curated, self, heuristic) | all pairs (`by_identity_status`) |
| Evidence-completeness coverage | pairs by the basis of admitted completeness | all pairs (`by_completeness_basis`) |
| Justification completeness (C only) | decisive verdicts whose contracts name sources, acquisition times and meaning, and, for a negative, a basis | decisive verdicts (`evidence_completeness` in `metrics.summarise`) |

Every metric is also reported by event class (`by_class`).

## 4. Intervals and clustering

Pairs of one event share its evidence, so they are not independent. Pairs per event: mean 6.2, maximum 7, on the retrospective set. Two intervals are therefore reported side by side.

- **Exact Clopper–Pearson 95%** (`registration.clopper_pearson_interval`). It treats pairs as independent, so it is too narrow under clustering.
- **Event-clustered percentile bootstrap 95%.** Events are resampled with replacement and their pairs move together. 10,000 resamples, seed 20261031. The same resampled events are used for every policy, so differences with C are paired.

**When nothing is observed** (0 false clears), the bootstrap interval collapses to [0, 0]. It carries no information. Report the exact upper bound, together with the event-level bound:
- the registered `upper_one_sided_95`;
- with 27 events at risk, 1 − 0.05^(1/27) ≈ 0.105.

**Paired comparisons with C:**
- events where only the other policy false-clears, and events where only C does;
- an exact one-sided sign test on those discordant events;
- bootstrap intervals of the difference in false-clear, resolution and unresolved rates.

The registered tests (H1, H2, S1–S3, Holm-corrected) are in `registration.py` and are reported in `evaluation.json → registered_analysis`. After the fix in audit F-04, the Holm adjustment uses unrounded p-values.

## 5. What these numbers may and may not be used for

- They describe agreement with the **developer's labels** on a **purposive** sample of famous events.
- They are **not** estimates of a production false-clear rate, of how common such events are, or of performance on unseen events or ecosystems.
- The sign test and the bootstrap describe variability *within this sample of events*. With non-random selection they do not support a population inference. No result here is described as statistically significant in general.
- **Operational measures.**
  - Processing time: a single-machine microbenchmark exists (`benchmarks/REPORT.md`, about 25 µs per pair). It is reported only as that.
  - Review burden and time to investigate unresolved cases (W1–W3): **not measured**, because they need annotators (REGISTRATION.md). No value is reported.
