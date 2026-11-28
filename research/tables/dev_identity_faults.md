**C-openpulse with a wrong curated identity mapping injected (openpulse-dev-2026-10)**

| fault (one wrong curated alias per reference) | references | outcome changed | outcomes with the fault |
|---|---|---|---|
| misattributed: a curated reference aliased to an unrelated project | 18 | 9 | abstained (undeterminable): 3; correct affected: 3; correct unaffected: 3; false clear: 1; no association: 4; silent miss: 4 |
| collided: an out-of-scope image reference aliased to the event's project | 6 | 0 | correct unaffected: 1; unresolved: 5 |

Each reference is run once with one explicit alias added; the engine is unchanged. Not injected: image reference with no applicable fault: 15; package reference (catalogue package map, not injected): 21.
