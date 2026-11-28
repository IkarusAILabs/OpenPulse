**C-openpulse with a wrong curated identity mapping injected (openpulse-retro-2026-11)**

| fault (one wrong curated alias per reference) | references | outcome changed | outcomes with the fault |
|---|---|---|---|
| misattributed: a curated reference aliased to an unrelated project | 29 | 28 | no association: 11; silent miss: 18 |
| collided: an out-of-scope image reference aliased to the event's project | 16 | 0 | correct unaffected: 14; unresolved: 2 |

Each reference is run once with one explicit alias added; the engine is unchanged. Not injected: image reference with no applicable fault: 42; package reference (catalogue package map, not injected): 80.
