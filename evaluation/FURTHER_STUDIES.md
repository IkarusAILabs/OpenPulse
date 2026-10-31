# Further studies: designs not registered

**Moved from TR-2026-01 §10 ("Q3: Evaluation Protocol").** In the revision for the thirteenth review (31 October 2026, snapshot `787beb8`), the report's protocol section was cut to a short summary. The registered applicability study moved to the report's appendix "Registered Evaluation" and stays canonical in `evaluation/REGISTRATION.md`. The four study designs below are not part of that registration. Their text is moved here unchanged in substance, converted from LaTeX to Markdown.

None of these studies is registered. Apart from what the report already presents as run (the conformance matrix, randomised testing and defect re-injection; the basic cost measurements), none has been run, and nothing here is evidence.

Cross-references point to sections of TR-2026-01 by title, because section numbers change between revisions.

---

## 1. Specification conformance (design; largely run)

This step has been run on a generated matrix (TR-2026-01, "Q2c: Checking the Implementation Against the Specification", Table "Specification conformance"). What remains is to extend it to OCI level relations against recorded registry responses, and to have the oracle re-implemented outside the team.

The design is as follows. Before measuring effectiveness, test whether the implementation conforms to the specification. Build an executable oracle directly from the aggregation algorithm and the membership tests of the specification ("Q2b", "Membership tests"), independent of the matcher's code. Generate a finite matrix of element kinds × dependency-reference kinds (tag-pinned image, digest-pinned image, source repository, package with and without version) × completeness states × identity statuses. Add adversarial cases:

- an empty scope;
- several matching elements;
- conflicting events;
- unsupported version forms;
- unresolved identities;
- exact and mutable tags (`latest`);
- multi-tag and repository-wide scopes;
- OCI index and manifest relations.

Run the same fixtures through the oracle and the implementation, and report *every* discrepancy, not only those already known (the project-tie label difference).

For OCI level relations, record real registry responses for multi-platform images and check the directional rules against them. For versions, compare the range evaluator differentially with the ecosystems' own comparators, and with published test corpora where they exist. Cover disjoint ranges, ecosystem ordering, epochs, pre-releases (including numeric identifiers, D8), distribution revisions, withdrawn advisories and unsupported range types. Publish the exact supported subset that results.

Conformance is necessary but not sufficient. A matcher can conform perfectly and still clear a dependency that an incomplete event omitted. The two layers are therefore evaluated separately: conformance asks whether the implementation matches the specification, and the applicability evaluation asks whether the specification's inputs and premises match real upstream changes and real identities.

## 2. Discovery

Monitor a population fixed in advance, at a stated polling interval and from a recorded start date. For each event, record:

- when it first became publicly observable;
- when OpenPulse detected it;
- when it was adjudicated;
- when a conventional dependency-security workflow would have learned of it.

End-to-end decision latency is the time from observability to a correct, actionable verdict for an affected pair.

Build an independent reference set from sources that do not feed OpenPulse: vendor notices, distribution changelogs and manual review of a random sample. Report detections per event class, recall bounds limited to the reference set's coverage, time to detection, and leads with monitoring context, as lead-time distributions rather than single values.

Report four outcomes separately and never combine them into one lead-time claim:

1. detection of a change already documented elsewhere;
2. earlier detection of a change not yet in a relevant catalogue;
3. discovery of a change that existing tools do not represent;
4. improved applicability of an already known change.

Only the middle two measure additional discovery value.

Discovery recall and time to detection are reported apart from the applicability metrics (false clears, false impacts, unresolved rate) and never combined with them: a correct engine cannot compensate for an event the collectors never saw. The eligible population is the reference set's events in the observation window, and an event counts as missed if no collector detects it before the window closes. Measured recall is over the reference set; it is not an estimate over all upstream changes.

Events missed by both OpenPulse and the reference set cannot be counted. The overlap between the two gives a capture–recapture estimate of their number. We report it only as an indication, because its interpretation assumes independent sources and a homogeneous population, and neither is likely to hold.

Confidence categories are evaluated against observed correctness, as an error rate per category. Source independence is audited on a sample of corroborated events by tracing each source family to its origin, including syndicated announcements and mirrored advisories. Today there is no central registry of source families: a family is declared per source, and `derived_from` chains are folded (TR-2026-01, "Q2a: Collecting and Qualifying Evidence"). The registry is to be published with the audit.

## 3. Agent decision experiment

Compare three main conditions:

1. an agent with no external dependency evidence;
2. with conventional vulnerability and lifecycle evidence;
3. with OpenPulse evidence added.

Within the third, include tasks whose event scopes are deliberately incomplete or in conflict, so that a correct agent must abstain or ask for review.

Use tasks whose candidate dependencies differ in archival, namespace, distribution or release-line status. Measure the dependency choices, unsupported safety claims, requests for human review, behaviour when evidence is unresolved, and task completion. Freeze the evidence snapshot, tool permissions, prompts and model versions.

Include an injection condition in which malicious upstream prose appears in the same response as valid structured evidence. The outcome is whether decisions move in the intended direction without excessive abstention or task failure, not whether the agent's wording changes.

A successful AI-assisted decision is a choice that matches the adjudicated evidence and is reached without an unsupported safety claim, not merely a generated contract. Count separately incorrect dependency choices, unsupported safety claims and inappropriate clearances. Abstention is *beneficial* when the adjudicated evidence is unresolved, and an *unnecessary refusal* when the evidence is decisive. A decisive choice made where the evidence is unresolved is *unsupported decisiveness*, even when it happens to be right. Each task's labels predefine the set of acceptable dependencies, not a single right answer, so that a technically acceptable alternative is not scored as an error.

The injection condition uses malicious repository names, tags, URLs and licence strings, and it is scored by whether the decision changes, not by what the agent writes. Three failure modes are scored separately:

- following hostile text;
- misreading a legitimate verdict;
- acting on insufficient evidence.

All conditions use the same model, task, tool permissions and decision instructions, and only the evidence source changes. A fourth arm gives the agent OpenPulse's tool descriptions and instructions with the evidence withheld, so that the effect of the evidence can be separated from the effect of clearer instructions. Decision labels are predefined from the adjudicated evidence. Results are reported per model and per task, not as one aggregate success rate.

The response forms the experiment compares for the injection condition are in TR-2026-01, appendix "Designs Not Yet Implemented".

## 4. Cost and scale

Measure along five dimensions: inventory size (small, medium and large), number of loaded events, scope size, registry tag count and history length, over repeated monitoring cycles rather than a single run. Report separately the cost of offline matching and the cost of upstream acquisition.

- Use small and large representative inventories, cache-cold and cache-warm runs, and injected failures.
- Compare candidate filtering by index with all-pairs evaluation, and report rate-limit gaps and recovery.
- Report matching time, memory, evidence-store growth, request volume per platform, cache hit rates and freshness-driven re-fetches.
- For agent use, report latency with a warm and a cold cache, behaviour when evidence is unavailable, rate-limit stalls, evidence expiry and refresh cost, and whether collection can stay outside the interactive request path without making evidence too stale to use.

**Today's acquisition behaviour is the baseline for those measurements.**

- Collectors classify HTTP 429 responses as retryable rate-limit errors and record them as acquisition gaps, never as results. There is no automatic backoff or request scheduling.
- Docker Hub tag walks are capped at 30 pages of 100 tags and fall back to the registry v2 listing, because the Hub refuses anonymous pagination beyond an offset of roughly 500.
- GitHub requests use a token when one is provided.
- The agent interface caches lookups per process for one hour.

Continuous monitoring of thousands of repositories in CI will need scheduling, conditional requests and backoff that do not yet exist. How request volume and gap rate grow with the monitored population is a result the evaluation must produce, not one we can assume.

The basic cost measurements that have been run are in TR-2026-01, "Q2c", paragraph "Cost" and Table "Basic cost".
