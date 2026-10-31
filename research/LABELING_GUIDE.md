# Labelling guide

This guide is for annotators who did **not** build OpenPulse. It defines the labels and decision rules **before** any annotator sees a policy's output.

It consolidates and supersedes nothing. The rules come from:
- the retrospective design (`evaluation/retrospective/DESIGN.md` §6);
- the L2 instructions (`labelling/round-2/L2-INSTRUCTIONS.md`);
- the registered protocol (`evaluation/REGISTRATION.md` §6).

Where those disagree, REGISTRATION.md governs.

## 1. What you are deciding

For each pair (reference, event), decide whether the reference, **as written**, denotes an object inside the set of objects the event changed. Use only the event's primary sources and the reference itself.

- You are **not** deciding whether the dependency is safe, maintained or vulnerable.
- You are **not** deciding whether OpenPulse would know.

## 2. Labels

| Label | Use when |
|---|---|
| `in_scope` | The sources establish that the referenced object is among the objects the event changed. |
| `out_of_scope` | The sources establish that it is **not**: a different project, a version outside a stated boundary, a namespace the change did not touch. |
| `undeterminable` | The sources and the reference together do not settle membership. Examples: no version in the reference against a version-bounded event; a digest whose tag is unknown; a boundary the sources do not state. |

## 3. Decision rules

1. **Names are not identity.** Two references with the same name in different registries, namespaces or ecosystems are different objects unless a primary source says otherwise. `docker.io/library/redis` is not `docker.io/bitnami/redis`. PyPI `redis` is not npm `redis`.
2. **A redirect is not equivalence.** A repository that redirects after a move is the moved object only for that move's own event. For other events, decide identity from the sources.
3. **Examples are not bounds.** A source that names some affected images or versions "for example" does not exclude the others. Label `undeterminable` unless the sources state the full set.
4. **Absence is not exclusion.** If the sources list affected objects and the reference is not listed, it is `out_of_scope` only if the sources say the list is complete. Otherwise it is `undeterminable`.
5. **Version boundaries.** Use the boundary the sources state. If you derived it yourself (from tags, licence files or changelogs), write that in the rationale.
6. **Moving tags.** A tag (`:latest`, `:7`) names whatever it pointed to at the reference's commit date, if you can establish that. Otherwise label `undeterminable`.
7. **Time.** Judge with what was published by the event's `as_of` date, which is given in the packet.
8. **Conflicting sources.** The announcing source defines the intended scope. A conflict it does not resolve makes the pair `undeterminable` (REGISTRATION.md §8; `DESIGN.md` §6).

## 4. What to record per pair

- `label`.
- `rationale`: one or two sentences naming the rule and the source passage.
- `sources_used`: URLs. Use only the packet's sources, unless you mark an outside source as such.
- `minutes`: time spent. This measures review burden (W3).

Do not discuss pairs with the other annotator before both have submitted.

## 5. Agreement and adjudication

- **Annotators.** Two independent annotators label every pair. A third person adjudicates disagreements. The authors of OpenPulse may not be annotators or the adjudicator.
- **Statistic.** Cohen's κ on the three labels, before adjudication, with its 95% interval.
- **Assumptions of κ.** Two fixed raters, the same items, and nominal categories.
- **Limits of κ.**
  - It depends on prevalence. The set is about 62% in scope, so report raw agreement and per-label agreement alongside κ.
  - It treats in/out confusions and in/undeterminable confusions alike. Report the confusion matrix.
- **Disagreements.**
  - Record every disagreement with both rationales and the adjudicated label.
  - Keep the pre-adjudication labels in the dataset version: they are data.
  - A disagreement about *which event* a pair concerns, as five of six in round 1 were, is a packet defect. Fix the packet and relabel that pair.
- **Dataset.** Adjudicated labels form a new dataset version with `labelled_by: L2/L3` and `independent_label: true`. Only then does `evaluate.py` report a non-empty registered population.

## 6. If independent annotators cannot be found

Then the paper must:
- describe the labels as the developer's, assigned by written rules before any policy ran;
- report the AI-assisted pilot only as a pilot;
- never call either "ground truth" or "independently labelled";
- list this in Threats to Validity.

The draft manuscript in `paper/` does this.
