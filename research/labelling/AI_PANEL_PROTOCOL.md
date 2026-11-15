# AI-panel labelling and adjudication protocol (round AP-1)

**Status:** fixed before any labeller ran. The SHA-256 of this file, the packets and the prompts is recorded in `ai-panel-2026-11/LOCK.json` *before* the first label is produced, and the labels' hashes are added *before* any comparison with the developer's labels (L1).

**What this is not.** It is not independent human annotation, and its labels are never marked `independent_label: true`. `LABELING_GUIDE.md` §5 (two human annotators who did not build OpenPulse, and a human adjudicator) remains the standard. This protocol exists because no such annotators are available. It gives a *structured, blinded second and third reading* of every pair, and a measure of how much the study's results depend on who, or what, labelled them.

## 1. Question

Do the retrospective study's results (false clears, unresolved outcomes, resolution, per policy) change when the developer's labels are replaced by labels produced under a protocol that keeps the labeller blind to the developer's labels, to every policy's output, and to each other?

## 2. Roles

| Role | Who | Sees | Does not see |
|---|---|---|---|
| Packet builder | `research/scripts/label_packets.py`, deterministic | the case file | — (mechanical; no judgement) |
| Labeller A | Claude Opus 5.5 (`claude-opus-5-5`), fresh context | its packet | L1 labels or rationales, case ids, any policy output, labeller B |
| Labeller B | Claude Sonnet 5.5 (`claude-sonnet-5-5`), fresh context | its packet (different order) | the same, and labeller A |
| Adjudicator | Claude Fable 5.1 (`claude-fable-5-1`), fresh context | the disagreed pairs, both labels and rationales as "Reader 1" and "Reader 2" in random order | which model gave which label, L1, any policy output |
| Analyst | `research/scripts/label_sensitivity.py`, deterministic | all label sets and the recorded policy outcomes | — |
| Orchestrator | the AI coding assistant that wrote this protocol, under the developer's direction | everything | — |

Each labeller and the adjudicator start in a new context with no access to the conversation that designed the study. Three different models are used so that one model's systematic reading does not decide every label.

## 3. Materials (the packet)

Built by `label_packets.py` from the frozen case file, one packet per labeller.

**Per event:**
- the event id;
- its title;
- the knowledge date (`as_of`);
- each primary source's name, URL, archive record and the archived quotation;
- for LIC-4 and DIS-3, the archived evidence file the developer's labels also relied on (`evaluation/retrospective/evidence/`).

**Per reference:**
- a neutral id;
- the dependency exactly as declared;
- where it was found (repository, commit, file, date).

**Withheld:**
- the label and its rationale;
- the case id, whose suffix encodes the label;
- the case's role and template;
- the event's curated scope encoding, which OpenPulse itself reads;
- the event's summary and the developer's representation notes in `SOURCES.md`;
- every result file.

The builder fails if a withheld value appears in the data part of a packet.

**Order.** Events and references are shuffled independently for each labeller, with seeds 101 (A) and 202 (B). Neutral ids are the first 8 hex digits of SHA-256 over `"AP-1:" + case id`; the key from neutral id to case id is written to `key.json` and is not given to any labeller.

## 4. Codebook

The codebook is `LABELING_GUIDE.md` §1–3, included verbatim in the prompt, plus these rules:
- **The packet is the only source.** No web access and no outside knowledge of the event. If a decision needs anything outside the packet, the answer is `undeterminable`.
- **Only this event.** A reference that some other event affects is `out_of_scope` for this one unless this event's sources cover it.

Output, one JSON object per reference:

```json
{"id": "<neutral id>", "label": "in_scope|out_of_scope|undeterminable", "rationale": "<one or two sentences naming the rule and the source passage>", "sources_used": ["<source name>"]}
```

## 5. Procedure

1. Build the packets and prompts. Record their hashes, and this file's, in `LOCK.json`.
2. Run labeller A and labeller B, each once, on all pairs. Each saves its own answers with a single file write to `raw/labeller-<X>.jsonl`; that is the only tool use permitted. The orchestrator does not edit raw files.
3. **Validate.** Every neutral id must be answered exactly once with a valid label. If any is missing or invalid, the labeller is asked once, in a new context, for the missing ids only; the request and its answer are kept in `raw/`. Record the label files' hashes in `LOCK.json`.
4. **Adjudicate.** Pairs on which A and B agree take that label. Pairs on which they disagree go to the adjudicator, with both labels and rationales anonymised and in random order (seed 303). The adjudicator chooses one of the three labels from the sources; it may choose a label neither reader gave. Record the hash in `LOCK.json`.
5. **Unblind.** Only after step 4 is locked are the labels compared with L1 and with policy outputs (`label_sensitivity.py`).
6. **No label is changed after unblinding.** The developer may review disagreements with L1 against the sources and record a view (as `PILOT.md` did), but the AI-panel label sets stay as produced. Any review is reported beside them, never merged into them.

## 6. Pre-specified analysis

Run by `label_sensitivity.py`:

1. **Agreement.**
   - Between A and B before adjudication: raw agreement, Cohen's κ with an event-clustered bootstrap 95% interval (10,000 resamples, seed 20261101), and the confusion matrix.
   - Between each AI label set and L1: the same statistics.
   - κ between two models measures their consistency, not the labels' validity.
2. **Disagreement types.** Count in↔out, in↔undeterminable and out↔undeterminable, by event class.
3. **Sensitivity.** Recompute every policy's error categories under each label set: L1, A, B, the adjudicated set (AP), and the two bounding sets below. Policy outcomes do not depend on labels, so the recorded outcomes are reused. Report false clears (pairs and events), unresolved outcomes, resolution and false positives.
4. **Bounds.**
   - *Against C:* a pair is in scope if any of L1, A or B says so (the most false clears C could have under any of these readings).
   - *Against A (naive):* a pair is in scope only if all three say so.
5. **Pre-specified reading.**
   - OpenPulse's zero false clears is *robust to the labelling method* if C has no false clear under L1, A, B and AP.
   - Otherwise every changed pair is reported with each labeller's rationale.
   - The comparison with naive reading A is *robust* if A's false-clear count exceeds C's under every set.

## 7. Limitations, to be disclosed wherever these labels are used

1. **Not independent humans.** All three readers are language models from one vendor and may share systematic errors, training data and blind spots. Model diversity reduces, but does not remove, correlated error.
2. **Same vendor as the tooling.** The orchestrator is a model from the same family as the labellers. It has seen L1 and every result. It cannot influence the packets, which are built mechanically, but it wrote the prompts.
3. **Evidence is what the developer archived.** Packets contain the quotations and evidence files the developer selected. A reader cannot find what the developer left out. This shared-evidence dependence is the main remaining correlation with L1.
4. **No web access.** Readers cannot open the archived pages, so "undeterminable" may reflect a thin quotation rather than a real ambiguity.
5. **One run, no temperature control.** Model output is not deterministic. A re-run may give different labels. The raw outputs are kept; reproducibility of the analysis starts from them, not from the models.
6. **Compliance cannot be enforced technically.** Labellers are instructed to use no tool except one file write and to read nothing else. The session transcripts are the record of whether they did.
7. **Prompt sensitivity.** The codebook's wording, written for humans, may be read differently by models. No prompt variation was tested.
8. **Registration.** The registered analysis (`evaluation/REGISTRATION.md`) requires independent human labels. These labels do not satisfy it, and the registered population stays empty.
9. **Disclosure.** Any manuscript using these labels must say they are AI-generated, and must name the models and this protocol. It must follow the target venue's policy on AI use.
