# Response to the twelfth review: TR-2026-01

The review was received as "Review 2" on 2026-10-31. We checked every point against the draft (current snapshot `a1ecc58`, evaluation code `56b88e5`) and, where the point concerns behaviour, against the code. The review recommends **Reject** for IEEE S&P, CCS, USENIX Security or NDSS, with encouragement to resubmit after a substantial empirical revision.

## Overall

We accept the recommendation and its reason: the decision rule is coherent and testable, but the evidence does not yet show that it delivers practical assurance. The three decisive issues (§5.2) are:
1. the soundness premises are not independently established;
2. the empirical evidence is neither independent nor sufficiently powered;
3. the advisory path, discovery, agent integration and operational cost are unevaluated.

None can be closed by revising text. Each needs independent annotators, a frozen held-out window, a second benchmark, or an agent experiment.

What this revision does instead:
- it makes every claim match the evidence, and adopts the review's recommended thesis (§5.4);
- it implements the points that are engineering rather than data: freshness as a default admission condition in every interface, executable adversarial-input tests, and the reporting changes in §3.3.2 and §3.4.2;
- it writes down the designs for the rest.

Code and text changes are in commit `787beb8` and the paper revision that follows it.

## Revisions in this draft

| Point | Valid? | Change |
|---|---|---|
| 3.1.1 The security boundary is narrower than the motivating narrative; seven attacker capabilities need explicit treatment | **Yes.** The threat table organised threats by property, not by what an attacker can do to a negative. | New Table "Attacker capabilities against a negative verdict" (§8), with each capability's effect, mechanism and status. Each is pinned by an executable test in `tests/test_adversarial_inputs.py`, which runs on every change. The table and the text say these are regression tests on constructed inputs, not a representative adversarial evaluation. |
| 3.1.2 Completeness is the central trust assumption and is unverified | **Yes.** Of the review's two options, we take the second: we sharply delimit the claim to a trusted-declaration model. | The abstract, introduction, §8, Limitations and Conclusion now state that the assurance holds under trusted completeness declarations and curated identity mappings. A test *pins* the boundary: a declaration that omits an artefact yields a false clear. The premises table gains a column, "checked or trusted", per premise. Per-basis results were already pre-specified (REGISTRATION §4 and D1), and are now implemented in `run.py` and `registration.py`. Verifying declarations is not attempted. D1 measures, per basis, how often they are wrong on held-out events. |
| 3.1.3 Freshness and cross-event consistency must be admission conditions in all interfaces, and tested | **Partly addressed.** Freshness was opt-in on the command line, which was a real gap. | The CLI's `check`, `attest`, `digest` and `warnings` now default to the agent tools' current mode: a 90-day bound as of the start of today. `--replay` drops the bound and says so, and contracts record the frame (CHANGELOG, Upgrade notes). Contradictions within an event already blocked negatives in every interface. Across events, the summary rule already withholds a negative whenever any loaded event associates the dependency, and a test now pins it. Tests cover stale observations, retracted and superseded events, and contradictory event pairs. **Not addressed:** a failed acquisition still does not withdraw a negative. A superseding record whose scope is wrongly narrower is still trusted. Both are stated in §5 and in Limitations. |
| 3.1.4 / 3.5.2 The AI-agent threat model is not validated, and the motivation is broader than the contribution | **Yes.** | The introduction now says that OpenPulse is an evidence and applicability layer that could support agent decisions. It is not a validated defence against malicious packages, prompt injection or unsafe agent actions, and no agent experiment has been run. The abstract and conclusion restrict the security claim to event-scope applicability. The agent experiment stays separate. The roadmap's new track T (PR #211) plans it as its own study, outside this registration. |
| 3.3.1 The retrospective study is exploratory | **Yes**, and the paper already says so. | No change of claim. The sampling frame the review asks for is now fixed for the held-out study: inclusion criteria I1–I6, exclusions X1–X3, per-class definitions, a class cap and a labels-only stopping rule (REGISTRATION §6–§7, summarised in §10). |
| 3.3.2 Limited power; the unit of analysis; intervals at both levels; zero observed is not a low rate | **Yes.** | §11 now gives both levels: C cleared 0 of 103 in-scope pairs. The independent-pairs bound (0.029) is labelled optimistic, and the event-level bound (0.105) as the honest one. A's 35 of 103 pairs has an event-clustered bound of 0.486, and its 10 of 27 events a bound of 0.547. Zero observed is stated as an observation about these events. The registered analysis now reports the pair-level share with both bounds next to H1, and withholds the clustered bound when it would have zero width (REGISTRATION §3). |
| 3.3.3 Baselines answer different questions; make the strong and existing-representation comparisons central | **Yes.** | New paragraph in §10, "What each comparison can show". Beating (iv) establishes safety and minimum usefulness, not superiority. The practical conclusion rests on S3 against (vi) and S1 against (v). (vi) is reported overall and on lossless events, and its encoding rules are published (`evaluation/representations/ENCODING.md`). **Decided by the author:** S3 remains a Holm-corrected secondary test, not a primary hypothesis (see below). |
| 3.3.4 Post-hoc fixes are not unbiased evidence | **Yes**, and the draft already said so in §11. | Now repeated in the abstract ("the improved figures are diagnostic") and the conclusion. §11 adds that post-hoc results are never pooled with a confirmatory result. |
| 3.3.5 The advisory path is a major gap | **Yes.** | The claim is restricted to the event-scope path in the abstract, introduction and conclusion. New paragraph in §10, "Two evaluation domains". New design `evaluation/advisory/DESIGN.md`: advisory state reconstructed from history-bearing databases, strata for CVE-less, multi-package, version-only, withdrawn and later-corrected advisories, and correlation errors kept apart from data errors. It needs its own registration, which is not drafted. |
| 3.3.6 A recognised, reproducible benchmark strategy across two domains | **Yes.** | The same §10 paragraph separates the two domains. The event-scope study's frozen fixtures, encodings and labels and the advisory design's frozen snapshots together form that corpus. Neither is built yet. |
| 3.3.7 Discovery and applicability must be measured separately | **Yes.** The protocol already reported discovery outcomes separately, but did not define the population. | §10 Discovery now reports recall and time to detection apart from the applicability metrics. It defines the eligible population (the reference set's events in the window) and when an event counts as missed. |
| 3.4.1 Scalability evidence is insufficient | **Yes.** | The §10 cost plan now names small, medium and large inventories and repeated monitoring cycles. No new measurement was made, and Limitations already said costs were measured on one machine. |
| 3.4.2 Review burden should be a primary utility outcome; deduplication, actionable share | **Partly addressed.** | W1 now also reports the actionable share and the unique review items after deduplication across inventories and cycles (`registration.py`; REGISTRATION §5). G4 already makes C's median W1 no worse than B's a guardrail. **Decided by the author:** burden stays a guardrail and a reported measure, not a primary outcome (see below). |
| 3.5.1 Novelty over a carefully engineered existing-format consumer | **Yes.** It is exactly what baseline (vi) and S3 test. | No new claim. §10 points to the encoding-loss codes and the lossless-event results as the evidence of which classes the typed model handles and existing formats do not. The development-set illustration, where that advantage came only from inexpressible scopes, is labelled as not evidence. |
| Priority 2: map every premise to a mechanism or a trust assumption | **Yes.** | The premises table now marks each premise as checked (code, oracle or differential), trusted (with the held-out measure that estimates it) or outside OpenPulse. The N-contract paragraph states the current enforcement of N4 and N5 per interface. |

## A finding from the new tests

Writing the adversarial tests showed that the F1 summary in the paper was too strong. A package dependency with **no** stated ecosystem still resolves through the catalogue's curated bare-name alias, as SPEC §4.4 allows ("a stated ecosystem of `generic` counts as not stated"). So `django` with no ecosystem is the Django project, and can be cleared. With an ecosystem stated, only a curated (ecosystem, name) pair establishes identity.

This is the package–source ambiguity of §3.1.1, and it is now a pinned, documented trusted input; the paper's F1 row has been corrected. The behaviour is unchanged, by the author's decision (below).

## Not addressed, and why

| Point | Why not here |
|---|---|
| Priority 1: independent held-out evaluation | It needs the registration archived, a frozen implementation, independent annotators and a prospective window. The protocol, analysis code, stopping rule and inclusion criteria are ready. What remains is the registry record (REGISTRATION, "Not archivable yet"). |
| Priority 2: independently validating completeness declarations | We delimit the claim instead (3.1.2), and D1 estimates the error rate per basis. |
| Priority 2: an independently implemented oracle | It needs an engineer outside the team. The independent kit (`conformance/independent/`) is ready for one. |
| Priority 3: running the advisory benchmark | The design is written. Building it needs snapshots, cases and its own registration. |
| Priority 4: discovery, scale and agent measurements | They need monitored populations and an agent experiment, which are planned. |

## Decisions for the author

1. **S3 stays secondary (decided 2026-10-31).** The review asks for the strong comparisons to be "central to the paper's conclusions". This revision makes them central in the interpretation (§10, "What each comparison can show"). They are not added as primary hypotheses. H1 and H2 remain the only primary tests, so the success criterion and the power argument are unchanged.
2. **Review burden stays a guardrail (decided 2026-10-31).** It is reported (W1–W3, with the actionable share and unique review items) and guarded by G4 (C's median W1 no worse than B's). It is not a primary outcome. A primary burden outcome would need a threshold for "acceptable" burden that no data yet support.
3. **Bare-name identity stays as specified (decided 2026-10-31).** A package with no stated ecosystem keeps resolving through the catalogue's curated bare-name alias (SPEC §4.4), and can be cleared. The alias is a trusted input like any curated mapping. `tests/test_adversarial_inputs.py` pins the behaviour, the paper states it (F1 row, Table "Attacker capabilities"), and D2 checks such mappings on held-out pairs.
