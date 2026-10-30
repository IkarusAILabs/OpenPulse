# AI-assisted labelling pilot (not independent labels)

The study planned an outside human labeller (L2) on a 25% sample (DESIGN §6). Both rounds of returned labels came from an AI-assisted process, so **neither counts as independent labelling**. Per the owner's decision (DESIGN §11), they are reported only as a consistency check on L1's labels, and no label in the analysis was changed because of them.

| Round | Files | Provenance | Pairs | Agreement with L1 | κ |
|---|---|---|---|---|---|
| 1 | `round-1/` | Undocumented. Cites sources outside the packet, and every pair is logged at 3 minutes. | 42 | 36 | 0.722 |
| 2 | `round-2/` | `L2-method.md`: "ChatGPT was used to prepare the labels and rationales". Packet sources only, no web search. | 42 | 38 | 0.825 |

Both κ figures measure agreement between L1 and an AI-assisted labeller. They are **not inter-rater reliability**.

## Round-2 disagreements, and L1's review against the sources

| Pair | L1 | Pilot | L1's review | Analysis label |
|---|---|---|---|---|
| LIC-4-s2, `mongo:4.0.4` | in scope | undeterminable | The packet gave the 2018-10-16 cutoff but no release dates. The dates are now archived in `evidence/mongodb-release-tags.txt`: 4.0.4 was tagged on 2018-11-06. | in scope (kept; basis now archived) |
| LIC-4-n2, `mongo:4.0.2` | out of scope | undeterminable | Same gap. 4.0.2 was tagged on 2018-08-27. | out of scope (kept; basis now archived) |
| DEP-5-n2, `go.yaml.in/yaml/v3` | out of scope | undeterminable | The sources declare go-yaml/yaml unmaintained. `go.yaml.in/yaml/v3` is another module path, published by another project. | out of scope (kept) |
| EOL-1-n1, `circleci/python:2.7` | undeterminable | in scope | A downstream image's support is the distributor's to state (TR-2026-01 §5.1). The same rule decides EOL-3-n3. | undeterminable (kept) |

Round 1's six disagreements are in `round-1/AGREEMENT.md`. Five of them judged a different event, and round 2 agreed with L1 on all five.
