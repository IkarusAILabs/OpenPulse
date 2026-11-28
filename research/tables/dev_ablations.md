**Ablations on openpulse-dev-2026-10: change in pair counts relative to C**

| configuration (vs C) | false clears | false positives | silent misses | unresolved | correct affected | correct unaffected | new failure modes |
|---|---|---|---|---|---|---|---|
| C, completeness assumed | 0 | 0 | 0 | 0 | 0 | 0 | none |
| C, no freshness bound | 0 | 0 | 0 | 0 | 0 | 0 | none |
| C, both assumed | +1 | 0 | 0 | -2 | 0 | +1 | false clear |
| C, unresolved identity = unrelated | 0 | 0 | 0 | -12 | 0 | 0 | none |
| C read as binary (post hoc) | +2 | 0 | 0 | -17 | 0 | +16 | false clear |
| C without curated identity (post hoc) | 0 | 0 | 0 | +17 | -11 | -5 | none |
| C with name identity only (post hoc) | +1 | 0 | +12 | -17 | -11 | -4 | false clear, silent miss |
