**Ablations on openpulse-retro-2026-11: change in pair counts relative to C**

| configuration (vs C) | false clears | false positives | silent misses | unresolved | correct affected | correct unaffected | new failure modes |
|---|---|---|---|---|---|---|---|
| C, completeness assumed | 0 | 0 | 0 | -7 | 0 | +7 | none |
| C, no freshness bound | 0 | 0 | 0 | 0 | 0 | 0 | none |
| C, both assumed | 0 | 0 | 0 | -7 | 0 | +7 | none |
| C, unresolved identity = unrelated | 0 | 0 | +17 | -43 | 0 | 0 | silent miss |
| C read as binary (post hoc) | +26 | 0 | 0 | -62 | 0 | +42 | false clear |
| C without curated identity (post hoc) | 0 | 0 | 0 | +20 | -16 | -3 | none |
| C with name identity only (post hoc) | 0 | 0 | +35 | -52 | -16 | -3 | silent miss |
