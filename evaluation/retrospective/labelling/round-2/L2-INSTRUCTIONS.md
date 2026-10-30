# Instructions for the second labeller (L2), round 2

Thank you for labelling again. These are the same 42 pairs as round 1, with
stricter rules. Round 1 is kept in `round-1/` for the record. Please do not
look at it, or at your earlier answers, while you label.

Please also do not look at the developer's labels (L1), the case draft in
`cases/`, `build_cases.py`, `dependents/`, or any OpenPulse output.

## What you receive

- `L2-packet.jsonl`: 42 pairs, one per line. Each line gives:
  - `event` and `event_title`: the one event you are judging;
  - `sources`: that event's archived primary sources, each with a quotation;
  - `dependency`: the dependency a real repository declared at a stated commit;
  - `label_source`: where that reference comes from.
- `events/<ID>/SOURCES.md`, with the Wayback snapshot of each source.
- For DIS-3 only: `evidence/openjdk-2025-deleted-tags.txt`, the published list of deleted tags.

## The question for each pair

> Using only **this event's** sources listed in the packet, as archived, does **this event** apply to this dependency?

| Label | When |
|---|---|
| `in_scope` | The sources show this event applies to this dependency (its name, and its version or tag where the event limits them). |
| `out_of_scope` | The sources show this event does not apply: a different package or image, or a version or tag the event excludes. |
| `undeterminable` | The sources do not settle it. |

## Rules

1. **Only the listed sources.** Use the event's sources in the packet and their archived snapshots, nothing else: no web search, no current documentation, and no other project's notices. If you could only decide by using something else, answer `undeterminable`.
2. **Only this event.** A dependency that some *other* event affects (its own deprecation, a different advisory, or a different notice about the same image) is `out_of_scope` for this event.
3. **No assistants.** Do not use AI tools or automated lookups to produce labels or rationales.
4. Where a registry flag and the announcement disagree, the announcement defines the scope.
5. Judge the dependency as written at that commit.

## What to return

Return a file `L2-labels.jsonl`, with one line per pair:

```json
{"id": "<pair id>", "label": "out_of_scope", "rationale": "...", "sources_used": ["<source name from the packet>"], "minutes": 4}
```

- `rationale` is one sentence that quotes or points to the line you relied on.
- `sources_used` names the packet sources you read for this pair. Use `"evidence/openjdk-2025-deleted-tags.txt"` where it applies.
- `minutes` is your actual time per pair. Please record it as you go.

Then add a short note, `L2-method.md`, on how you worked: what you read, any tools you used, and when.

## Afterwards

Agreement is reported as Cohen's κ for round 2, with round 1's κ (0.722) reported alongside it. Disagreements are then resolved by discussion against the sources, as before.
