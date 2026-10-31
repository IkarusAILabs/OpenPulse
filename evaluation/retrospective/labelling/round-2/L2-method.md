# L2 Method Note — Round 2 (AI-assisted draft)

## Important validity note
This is an AI-assisted draft, not a compliant independent-human Round 2 labelling run. The supplied `L2-INSTRUCTIONS.md` explicitly prohibits AI tools and automated lookups. ChatGPT was used to prepare the labels and rationales at the user's request; therefore these outputs must not be represented as having followed that prohibition or as a valid independent L2 annotation.

## Materials used
- `L2-INSTRUCTIONS.md`
- `L2-packet.jsonl` (42 pair records, including each event title, dependency declaration, and quoted sources)
- `L2-sample.json` was not used to make label decisions.
- `openjdk-2025-deleted-tags.txt` for the DIS-3 pair.

## Method
For each pair, I compared the dependency as written with the event title and only the source names and quotations included in that pair's packet entry. I did not conduct web searches or consult current documentation. For DIS-3, I checked whether the exact declared image tag appeared in the supplied deleted-tag list. Where the packet quotation did not settle a key version/date or package-identity question, I used `undeterminable` or stated the limitation in the rationale.

## Tools used
- ChatGPT (AI-assisted interpretation and drafting)
- Python for reading the supplied JSONL packet and deleted-tag list, and writing the output files
- No web search or external source lookup

## Timing
The instructions request actual per-pair minutes. No human per-pair stopwatch or time log was available, and I cannot reliably report actual minutes spent per item. Accordingly, `minutes` is `null` in the JSONL rather than an invented duration. A human rerun should replace these nulls with recorded minutes.

## Limitations
These labels are a source-constrained AI-assisted interpretation, not an independent human annotation. They should be treated as a pilot/draft for discussion only, excluded from the formal inter-rater agreement calculation unless the study protocol explicitly permits AI-assisted labels.
