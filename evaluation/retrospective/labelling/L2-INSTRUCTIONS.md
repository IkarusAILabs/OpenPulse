# Instructions for the second labeller (L2)

Thank you for labelling. You are labeller L2 in DESIGN.md §6. Your labels
measure how far the developer's labels (L1) can be trusted, so please work
**without** looking at L1's labels, the case draft
(`cases/retro-2026-11.draft.json`), `build_cases.py`, or any OpenPulse output.

## What you receive

- `L2-packet.jsonl`: 42 pairs, one per line. Each pair is one historical
  event and one dependency that a real repository declared at a stated
  commit.
- For each event, `events/<ID>/SOURCES.md`: the archived primary sources
  (announcements, advisories, registry records, licence files), with their
  Wayback snapshot links.

## The question for each pair

> Using only the event's primary sources, as they read at the time, does
> the event apply to this dependency?

Answer with exactly one of:

| Label | When |
|---|---|
| `in_scope` | The sources show the event applies to this dependency (its name, and its version or tag where the event limits them). |
| `out_of_scope` | The sources show the event does not apply: a different package or image, or a version or tag the event excludes. |
| `undeterminable` | The sources do not settle it, for example a downstream image that repackages the affected software. |

Rules:

1. Judge by the announcing source. Where a registry flag and an
   announcement disagree, the announcement defines the scope.
2. Judge the dependency as written at that commit. Do not look up whether
   the repository later changed it.
3. Do not guess. If you would need information the sources do not give,
   answer `undeterminable` and say what is missing.

## What to return

A file `L2-labels.jsonl`, one line per pair:

```json
{"id": "DIS-3-s2", "label": "in_scope", "rationale": "tag 8-jdk is in the deleted-tag list", "minutes": 3}
```

`rationale` is one sentence naming the source line you relied on. `minutes`
is optional.

## Afterwards

Agreement is reported as Cohen's κ over the 42 pairs (DESIGN §6).
Disagreements are adjudicated against the sources by both labellers and
recorded with their resolution; the adjudicated label is the one the study
uses, and pairs you labelled become the study's independent labels.
