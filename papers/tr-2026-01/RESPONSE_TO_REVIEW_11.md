# Response to the eleventh review — TR-2026-01

We checked every point against the current draft (audit snapshot `8a9c3a8`, current snapshot `a1ecc58`) and, where the point concerns behaviour, against the code. Recommendation: **Reject** for IEEE S&P, CCS, USENIX Security or NDSS; valuable as a technical report.

## Overall

We accept the recommendation. The review's central distinction is right, and the draft did not make it sharply enough: oracle agreement shows that the implementation follows its decision policy, not that the policy's inputs justify real negatives. Of the review's six "decisive gaps", the first three and the fifth need independent annotators, a monitored population or an agent experiment, and are not closed here. The fourth (assurance missing from the contract and the live interface) is now stated precisely. The sixth (internal inconsistencies) is fixed.

One note on provenance: several of the minor comments (4.1 in full) describe a build earlier than commit `e6e5ddf`, which had already fixed them. We list those as already resolved.

## Revisions in this draft

| Point | Valid? | Change |
|---|---|---|
| 3.1 / Q1: what differs from baseline (v) once inputs are shared | **Yes.** §10 said that (v) "isolates what OpenPulse's richer identity and evidence machinery adds", and then gave (v) that machinery. | §10 now states that completeness, identity and admission are *shared*, so (v) cannot measure their value. It names the two mechanisms that differ, before any evaluation: Go module ↔ source repository (D-R1), and release read from variant image tags (`node:12-alpine`). New §11 paragraph "Where C and V differ": 23 of 167 pairs after the fixes (22 at the freeze), all through those two mechanisms: 18 Go-module pairs and 5 image-tag pairs. None involves completeness, identity or admission. |
| 3.2: the lemma moves the hard questions into its premises | **Yes**, as a matter of emphasis. | §6 now says plainly that agreement shows only that the implementation follows the policy. It lists the five input questions the review names as Lemma 1's unmeasured premises. |
| 3.3 / Q3: default admission vs full N1–N5 vs fit at consumption | **Yes**, confirmed in code. `core/agent_tools.py` calls `check_dependency` with no freshness bound, and the agent response carries no completeness basis. | New Table "Assurance of a negative" (the field-level table of 4.6). The agent-interface paragraph now answers Q3: yes, the live interface can issue NotAffected on evidence of any age, and it does not say so. Replay mode and current-assessment mode are distinguished, and the mode split is stated as not implemented. |
| 3.4 / Q7: loaded-set summary vs global clearance | **Yes.** | New paragraph after the cross-event aggregation: "cleared" means "excluded by the events we have". Nothing records the loaded set's coverage, and a failed acquisition does not withdraw a negative. The lemma's assurance is about the former only. |
| 3.6: mutants vs defects | **Yes.** | "22 historical-defect and rule-disabling mutants" in the abstract, the novelty table (§2.1), §6 and the conclusion. §6 adds that catching them shows sensitivity to chosen perturbations, not broad fault coverage. |
| 3.7 / Q4: workload of the unresolved-identity policy | **Partly.** The retrospective study measures it per pair: 44 of C's 82 non-correct decisions come from uncatalogued packages. | §12 now gives that per-pair figure and says the per-inventory and per-cycle cost is unmeasured. It states the always-abstain point. §10 says the cost should be reported per inventory and per monitoring cycle. |
| 4.2: defect breakdown | **Yes.** | The abstract, contributions, conclusion and §12 now say fifteen defects: twelve false-clear or clearance-shown, plus D7 (false impact) and D14, D15 (under-positive). |
| 4.3 / Q5: 3,995 vs 4,335 | **Yes.** Verified in `conformance/matrix.py`. | §6 now says that the two project-wide scopes run only as partial, giving (15·3+2)·5·17 = 3,995. The current matrix is (19·3+2)·5·21 = 6,195. |
| 4.4 / Q6: Appendix A etcd discrepancy | **Yes, Appendix A was stale.** We ran the oracle on the case. With the repository encoded as a named example, which is how `affected_artifacts` is encoded and what correction S4 fixed, the oracle gives AffectsProject. That matches the implementation. | Appendix A was rewritten: the repository is a named example, and all three verdicts agree. The old reading is explained, and the only remaining discrepancy is the project-tie label. §10's "(the etcd package verdict)" was corrected. |
| 4.5 / Q6: D8 reproduction | **Yes.** Run at each commit: `False` at `f0c3b48`, `None` at `9d53ce2`, and `True` from `dabafef` (D11) on, including `8a9c3a8` and `a1ecc58`. | Appendix C now gives all three results. Appendix B says the D8 repair was intermediate for SEMVER ranges. |
| 4.6: field-level contract table | **Yes.** | New Table "Assurance of a negative" (see 3.3). Its "at consumption" column is empty, which is the honest answer. |
| 4.7: `OWNERSHIP_CHANGE` for a relocation | **Yes.** | Appendix A now says the name is a legacy schema label and the event asserts only a path change, not a change of principals. **We did not rename the type**, because that is a schema change. |

## Not changed, and why

| Point | Reason |
|---|---|
| 4.1: stale "not yet available" and "not differentially tested" | Already fixed in `e6e5ddf`, before this review's build. §6, Table 9 and §12 now agree on what was tested: PEP 440, npm, Go and Maven differentially; SemVer by vectors at `8a9c3a8` and by node-semver at `a1ecc58`. |
| 3.5: no independent effectiveness evaluation | Correct, and already stated. It needs annotators who did not build the detector. The retrospective study's outside labels turned out to be AI-assisted and are reported only as a consistency check. |
| 3.5 / Q8: agent benefit | Correct. The interface is described as an unvalidated integration boundary. No agent experiment has been run. |
| 3.8: scalability | Already stated accurately: the five-dimension protocol in §10, and the limitations in §12 (no index, full snapshots, no backoff, one machine). |
| 4.8: move the protocol to an appendix | Agreed for a venue submission. Not done for the technical report, where the protocol is the registration's reference text. We will restructure when results exist to fill the space. |
| Q2: how often are declarations and mappings wrong? | Unknown. Measuring it needs independently sampled events with adjudicated scopes. That is the declaration-reliability measurement the review asks for, and it is not in the current protocol as a separate endpoint. **We consider adding it the most useful protocol change this review suggests.** |

## Follow-up worth doing in code

The review's design suggestion for 3.3 is cheap and would turn a documented gap into enforced behaviour:
- give the agent tools an explicit current-assessment mode that requires a freshness bound and reports a missing one;
- add `scope.completeness` and the `evaluation_context` to the agent response.

That is an implementation change. It would move the snapshot the paper pins, so it was not made in this revision.

## Build

`main.tex` was checked statically: braces and environments balance, every `\ref` resolves, and the new table's rows are well-formed. No TeX installation is available locally, so the PDF has not been rebuilt here. The CI `latexmk` job builds it.
