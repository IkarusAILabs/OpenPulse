# Threats to validity

The threats are organised by the usual four kinds. Each entry says what is done about it here, or that nothing is.

## Construct validity: do the measures measure the claims?

- **"False clear" depends on the label.** A false clear is disagreement with the developer's label (L1), not with an independent reading. *Not mitigated.* Independent labels are blocked on people (LABELING_GUIDE.md, RESEARCH_PLAN R4).
- **The cleared/unresolved distinction is the model's own.** A policy that never clears, B, has a false-clear rate of 0 by construction. False clears alone therefore cannot rank policies. *Mitigated:* every result is reported together with resolution, unresolved and silent-miss rates.
- **"No association" is not a clearance in OpenPulse**, but a naive consumer may read it as one. *Mitigated:*
  - silent misses (in scope, no association) are a separate error category;
  - the post-hoc binary ablation measures what happens when every non-affected outcome is read as cleared.
- **Scope membership is not harm.** An "affected" verdict means the reference is in the event's directly named scope. It does not mean the dependency is broken, unsafe or unmaintained (`core/verdict_meaning.py`). The paper must not equate the two.
- **Operational cost.** Review burden is not measured. H3's "additional review effort" is unsupported either way.

## Internal validity: do the results follow from the method?

- **Same team for engine, oracle, generator, labels and invariants.** A shared misunderstanding passes every check.
  - *Partly mitigated:* the oracle imports nothing from `core`; labels were fixed by written rules before any policy ran; an independent-oracle kit exists (`conformance/independent/`).
  - Nobody outside the team has used the kit.
- **Fixes after the retrospective run.**
  - The engine was changed after the frozen run (`results/after-fixes/`). Results on the same set after fixes are optimistic. They are reported as "after fixes", with every changed pair listed (`research/tables/retro_versions.md`).
  - D16 and F-17, fixed during this audit, change no pair of either set.
- **Post-hoc ablations** were defined after the results were known. They are exploratory and must not be presented as tests.
- **Comparators.** The research pipeline runs baseline V without its pinned npm/Go/Maven comparators. All three versions agree pair for pair, so this changes nothing on these sets, but it could on others.
- **Generated-case coverage.** The invariants are checked on cases from a finite vocabulary (two curated projects, a few repositories and tags; `conformance/randomized.py`). Properties that hold there can fail on references the generator never produces. Holding on 12,000 cases is evidence, not proof.

## External validity: does it generalise?

- **Purposive sample** of 27 well-documented, famous events, chosen under class quotas. No estimate of incidence, of performance on a random dependency, or of a production false-clear rate may be drawn.
- **Ecosystems and kinds.** npm, Go and container images only on the evidence set. PyPI, Maven, crates.io and OS packages are untested there.
- **Identity mix.**
  - 138 of 167 pairs resolve only to themselves (unresolved identity);
  - 29 through curated mappings;
  - 0 by heuristic.
  - Results on a curated-heavy inventory could differ.
- **Event discovery is assumed.** All results take the events as given. Discovery recall, measured once, was low (0/15 as shipped, 8/15 after fixes). A tool that never sees an event cannot apply it.
- **AI coding agents.** No agent was run. Nothing here shows that OpenPulse changes an agent's dependency decisions, prevents malicious package selection, or resists prompt injection through tool outputs.

## Conclusion validity: are the statistics right?

- **Clustering.** Pairs share events. *Mitigated:* event-clustered bootstrap, event-level false-clear counts, and the event as the unit of every registered test.
- **Small samples.**
  - 27 events. The registered H1 needs at least 60 events at risk and is "not decidable" here.
  - With 0 observed false clears, the event-level 95% upper bound is about 0.105, above the registered 0.05 margin.
- **Multiple comparisons.** The registered secondary tests are Holm-corrected. The research tables report many rates without correction. They are descriptive.
- **Significance.** The sign test and bootstrap p-values describe this sample only (METRICS.md §5).

## Research-integrity threats

- **Review provenance.**
  - The "external reviews" of the technical report appear to have been produced with an AI tool (`review12/REVIEW.txt` carries tool citation artefacts).
  - The L2 round-2 labels were prepared with ChatGPT.
  - Both must be disclosed in the manuscript and the cover letter, and the venue's AI policy must be checked before submission (audit F-03).
- **Unverified references.** 15 references entered from memory are flagged in `paper/LITERATURE_PROTOCOL.md`. No citation in the draft manuscript is presented as verified unless it is in the verified set.
