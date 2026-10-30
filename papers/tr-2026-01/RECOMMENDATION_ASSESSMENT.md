# Assessment of the external recommendation on TR-2026-01 (2026-10-30)

The recommendation ("revise the paper and strengthen OpenPulse before submitting") was checked against the report at snapshot `8a9c3a8` and against the repository. Its conclusions are below, each with our position and what we have done.

## Overall verdict

**We accept the recommendation's main conclusion.** The report is a specification and implementation audit, and it says so itself (Abstract; §1 Status; §11 "Evidence of value"). A competitive software-engineering or security journal will ask whether completeness-aware decisions are *better*, and the report cannot yet answer that. §10 is a draft protocol that has not been run.

Two qualifications:

1. **Much of what it asks for is already planned in the report**, and in some places the report's plan is stricter than the recommendation's:
   - §10 already specifies five baselines, including a *strong conservative* baseline (v) that the recommendation's baseline B does not match;
   - it already specifies event-clustered intervals and the two false-clear rates;
   - it already specifies independent annotation, ablations and a leakage-controlled freeze.

   What is missing is execution, not design.
2. **Publishing the report now as a technical report is consistent with the recommendation.** Its own Level 1 row says so. The journal version waits for Level 2.

## Point by point

| Recommendation | Assessment | Action taken or planned |
|---|---|---|
| **P1: comparative experiment, A naive / B conservative / C OpenPulse** | Agree, and it is the most valuable step. **Caveat:** B as defined ("unlisted → unknown") is a weak baseline. Beating it on decisiveness is easy, because B has no identity or version semantics. The fair primary comparison is the report's baseline (v): the same scope language and admissibility, curated identities, and the ecosystems' own comparators. | **Done:** the A/B/C harness, ablations, metrics and replay (`evaluation/`). **Next:** baseline v (ROADMAP R-B4), which becomes the primary comparison. |
| P1 metrics: false clear, false impact, resolution, abstention, evidence completeness | Agree. We added two. *Silent miss* (Unknown on an in-scope pair) is a consumer-visible "proceed" that FCR alone hides. *Unsupported decisiveness* covers decisive calls on undeterminable pairs, so that a policy cannot gain by guessing. "Evidence completeness" needed an operational definition. We use the share of decisive verdicts that name sources, carry an acquisition time and cite a completeness basis. | Implemented in `evaluation/metrics.py`. Definitions are in `evaluation/PROTOCOL.md` §4. |
| P1: a system that abstains on everything is useless | Agree, and the development set already shows the tension. C's abstention rate (0.47) is *higher* than B's (0.43), while its resolution rate is higher too (0.59 vs 0.43). The paper must report the trade-off, not a single number. | Reported per policy. Pre-commitment in ROADMAP R-C. |
| **P2: real historical changes, with no hindsight bias** | Agree. **Practical constraint the recommendation understates:** OpenPulse can replay only evidence it recorded. Its recorded history starts in October 2026. Reconstructing earlier registry state from today's state is exactly the hindsight bias the recommendation warns about. | Replay of recorded evidence "as known at" a date is implemented (`evaluation/replay.py`). We recommend a **prospective window after the freeze** as the main held-out source. Retrospective events count only with archived contemporaneous evidence (R-C1). |
| P2: discovery precision and recall where ground truth exists | Agree. Recall needs a reference set independent of OpenPulse's sources. The development ledger has no denominator, and §11 says so. | R-C4. |
| **P3: novelty, without claiming completeness reasoning or three-valued logic as new** | Already largely done. §2 ("Completeness reasoning") cites the closed-world assumption, Motro, Imieliński–Lipski and Etzioni et al., and states "We claim no new logical principle". The contribution is framed as a typed local completeness assertion applied to an upstream change's affected set. **Still weak:** related work on VEX/CSAF consumption, SBOM accuracy, package identity (purl) and AI package recommendation. | R-A1 (contribution as a testable model), R-A3 (related work). |
| **P4: independent validation; the oracle and implementation may share assumptions** | Agree. This is the report's own concession (§6: "its oracle was written by the same team"). The development set is a first labelled set with rationale, but it is *not* independent: the labeller is the developer. | R-B7: an oracle and edge cases written from the specification text alone by a second engineer. R-C2: independent annotators. |
| **P5: reproducibility** | Mostly in place: pinned commit, offline replay, the conformance results, the aggregation check and the audit transplant script. Missing are a versioned dataset, metric scripts for the comparison, and an archived release with a DOI. | Dataset SHA-256 and commit are recorded per run. R-D2 covers the archived release. |
| OpenPulse development priorities (the "Essential / Selective / Low / Defer" table) | Agree with every disposition: essential items for evaluation, selective ecosystem expansion, low priority for dashboards and SaaS, and SafeAI integration deferred. This conflicts with the current roadmap, which had M6 SaaS ACTIVE and v0.8.0 next. | ROADMAP re-baselined: track R first, M6 PAUSED, M9 deferred out of this paper, v0.8.0 after R-C. |
| Replayable historical evidence, kept simple | Agree. We did not build event sourcing. Replay is recorded inputs plus a date, run through current code, with the commit recorded. | `evaluation/replay.py`. |
| Level 2 target; 8–16 weeks | Agree with Level 2. 8–16 weeks is plausible only if **outside annotators** are recruited early. Independence is the critical path, not code. | ROADMAP "Next 8–16 weeks". |
| If the results are unfavourable | Agree, and we pre-commit. "Fewer false clears at the price of more abstention" and "no better than baseline v" are both reportable outcomes. | ROADMAP R-C. |

## What the first harness run already found

The development set has 60 pairs over 13 events. Its labels were written by the developer before running, so it is not evaluation evidence.

- **E1, a false impact in OpenPulse.** The PyPI package `redis` 6.2.0 is redis-py, the Python client. Under the Redis 6.2 end-of-life event it is AFFECTS_VERSION. The cause has two parts:
  - package identity resolves by name across ecosystems;
  - the catalog's `redis` entry names PyPI `redis` as its OSV package.

  None of the conformance machinery could find this, because the oracle takes identity as ground truth. That is the recommendation's circularity point, made concrete. The fix touches the trust core and gets its own PR (R-B3).
- **The admission premises are redundant on this set.** Removing completeness alone, or freshness alone, changes nothing. Removing both clears React 18.3.1 against a partial, stale scope. Separating the two premises needs held-out events that exercise each one.
- **The coverage cost of the D10 rule is visible.** A reference to the archived fbsdk repository stays unresolved because it resolves only to itself.

## If the report is published now as a technical report

Statements that are now out of date or worth adjusting:

- §10 says nothing in it "has been run" apart from conformance and cost. A sentence could add that a comparison harness and a developer-labelled development set exist, and that their results are not evidence of effectiveness.
- E1 is a new false-impact defect. If the report is published before E1 is fixed, §6 or §11 should name it as found after the snapshot. It is not a false clear, so the twelve-defect false-clear count is unchanged.

Both are optional for a technical report. Neither is optional for the journal version.
