# L1–L2 agreement and adjudication (DESIGN §6)

Round 1. L2's labels arrived as `L2-labels.jsonl` on 2026-10-30. They cover 42 pairs, the same ids as `L2-sample.json`, with no duplicates and valid labels throughout.

## Agreement before adjudication

| | |
|---|---|
| Pairs | 42 |
| Agreements | 36 (85.7%) |
| Chance agreement p_e | 0.485 |
| **Cohen's κ** | **0.722** |
| L1 labels | 20 in scope, 21 out of scope, 1 undeterminable |
| L2 labels | 26 in scope, 16 out of scope, 0 undeterminable |

All six disagreements are cases where L1 said out of scope or undeterminable and L2 said in scope.

## Disagreements

| Pair | Dependency | L1 | L2 | Checked against the archived sources | L1's position |
|---|---|---|---|---|---|
| DEP-2-n1 | `github.com/tools/godep` | out | in | L2 cites godep's own archival, a different event. DEP-2 is the deprecation of golang/dep, and its SOURCES.md does not mention godep. | out |
| DEP-3-n1 | `tslint-config-prettier` 1.18.0 | out | in | L2 cites that package's own archive notice, a different event. DEP-3's sources deprecate tslint. | out |
| DEP-6-n3 | `honnef.co/go/tools` | out | in | L2's rationale is about API stability in Staticcheck's docs, not a deprecation. DEP-6's sources deprecate golint. | out |
| DIS-3-n2 | `openjdk:11.0.16-jdk-slim` | out | in | L2 applies the DIS-2 deprecation notice. DIS-3 is the 2025 tag deletion, and no `openjdk:11.0.16*` tag is in the 1,051-tag list (`evidence/openjdk-2025-deleted-tags.txt`). | out |
| CMP-2-n1 | `faker` 5.5.3 | out | in | The advisory in CMP-2's sources (GHSA-5w9c-rv96-fr7g) affects `faker = 6.6.6` only, and 5.5.3 was the last regular release. | out |
| EOL-1-n1 | `circleci/python:2.7` | undeterminable | in | Python 2.7 did reach end of life. Whether a downstream image that repackages it is in scope is the question that TR-2026-01 §5.1 leaves to the distributor. | **open: a real methodological disagreement** |

## Notes on the returned labels

- **Sources outside the packet.** Several rationales cite sources that are not in the events' SOURCES.md: current Moby migration guidance, Staticcheck documentation, the OpenTofu manifesto, the godep and tslint-config-prettier READMEs, and a "Faker incident announcement". Instructions rule 1 limits labelling to the event's own primary sources.
- **Wrong event.** Five of the six disagreements come from judging whether *some* event affects the dependency, rather than *this* event.
- **Time per pair.** `minutes` is 3 for all 42 pairs.

## Adjudication

Superseded: the owner chose to re-label (DESIGN §11, second labelling round). No round-1 label is adjudicated or used.
