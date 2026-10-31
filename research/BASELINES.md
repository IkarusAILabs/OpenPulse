# Baselines and ablations

Every policy receives the same replayed events (each as known at its knowledge cut) and the same dependency reference. Every policy returns one outcome per pair: `affected`, `cleared`, `unresolved` or `no_association`.

The registered policies were fixed in `evaluation/PROTOCOL.md` and `evaluation/REGISTRATION.md` before the retrospective set was run. The post-hoc ablations (§4) were not.

## 1. Baseline A: naive matching (`policies.naive`)

**Rule.** If the event's affected set *lists* the dependency, the outcome is affected. Otherwise it is **cleared**.

**"Listed" is read literally, but not weakly** (`policies.listed`):
- **Images** compare after the reference parser's canonicalisation: Docker Hub host aliases fold to `docker.io`, and single names fall under `library`.
- **Identity** is by bare name: a repository or package name equal to the event's project slug or to a listed package.
- **Versions** compare by numeric release-line prefix.
- **Missing evidence:** an event with no listing clears everything.
- **Scope completeness** is not consulted; every list is read as complete.

**Why this is fair.** This is how an affected-products list is commonly consumed. A uses the oracle's own reference parser, so it is not weakened by a poor parser. It shares no matching code with OpenPulse.

## 2. Baseline B: conservative matching (`policies.conservative`)

**Rule.** Same listing as A, but an unlisted dependency is **unresolved**, never cleared.

B never clears, so its false-clear rate is 0 by construction. It is the registered comparator for usefulness (H2), not for safety.

## 3. Baseline V (strong conservative) and baseline R (existing representation)

**V** (`evaluation/strong_baseline.py`):
- C's model (typed scope, completeness basis, curated identity), read with each ecosystem's own version comparator: `packaging` (PyPI), node-semver 7.8.5, Go x/mod v0.42.0, Maven ComparableVersion 3.9.16.
- It isolates OpenPulse's own version and tag handling.
- In the research pipeline V runs without the npm/Go/Maven bridges, for determinism (`REPRODUCIBILITY.md` §4).
- On both case sets this changes no pair: the freeze-tag results, made with the bridges, match pair for pair (`research/tables/*_versions.md`).

**R** (`evaluation/existing_representation.py`):
- A careful consumer of OSV and OpenVEX re-encodings of each event, written under `evaluation/representations/ENCODING.md`.
- Exact purl identity. Each encoding is frozen with its SHA-256.

**Where R can be evaluated.**

| Set | Events encoded | How R is reported |
|---|---|---|
| Development | 6 of 12, written by the developer after seeing results | Over encoded pairs only (40 of 60). The 20 others are `not_encoded`. |
| Retrospective | 0 of 27 | **Not evaluable.** No number is reported. |

Unencoded pairs are a separate category, `not_encoded`. It is distinct from:
- an *unsupported event type*: what OSV/OpenVEX cannot express, documented per event in `SOURCES.md` under "Representation";
- *missing source evidence*: an event not known at replay. No such case occurs in either set (`events_not_known_at_replay` is empty);
- an *incorrect decision*: a false clear or false positive;
- an *unresolved decision*.

None of these is counted as another.

**Not implemented.** The registered existing-format comparator X_K, and the factorial cells L₀, L_K and T₀ (REGISTRATION.md §2). The comparison with existing formats (S3) therefore cannot be run as registered (audit F-10).

**Other candidates considered.**
- **OSV and OpenVEX** are represented by R. They are formats, not decision procedures, so R fixes a careful reading.
- **CycloneDX/SPDX VEX profiles and CSAF** were not encoded. Doing so needs a blind encoder (RESEARCH_PLAN R5).
- **SCA tools** answer a different question: vulnerability presence by version, not applicability of non-vulnerability upstream changes. Running one would produce numbers without a valid interpretation for most event classes, so none is reported.
- **Lifecycle catalogues** (endoflife.date) are an evidence source OpenPulse consumes, not a competing decision procedure.

## 4. Proposed method C and its ablations

**C** (`policies.openpulse`) is the production `check_dependency`, with a 90-day freshness bound. It also records the justification read from the v1.2 evidence contracts a consumer would receive.

**Registered ablations.** Each changes the *input*, or one engine switch, never the code.

| Configuration | What is removed | Interpretation |
|---|---|---|
| C-ablate-completeness | Every populated scope declared complete (N3 off) | Do completeness-aware negatives matter? |
| C-ablate-freshness | No freshness bound | Do stale negatives matter? |
| C-ablate-both | Both | Either alone can mask the other |
| C-ablate-identity | An unresolved identity is read as unrelated (D10/D13 off) | Does identity conservatism matter? |

**Post-hoc ablations** (`research/scripts/evaluate.py`; defined after the registered results were known, so exploratory).

| Configuration | What is removed | Interpretation | When inappropriate |
|---|---|---|---|
| C-posthoc-binary | The unresolved outcome. The same engine verdict, read by a binary consumer: anything not affected is cleared. | Model without explicit unresolved outcomes (brief §11.3). Separates matching quality from abstention. | Never as a deployable configuration. It exists to measure what the third outcome buys. |
| C-posthoc-no-curated-identity | Curated identity: no explicit aliases, no catalogue mappings. Every reference resolves to itself or by heuristic. | Model without canonical identity or alias handling (§11.4). Measures the value of curation. | Interpretable only with identity conservatism on, otherwise it would be unsafe by design. The next row is that combination. |
| C-posthoc-name-identity | Curated identity, *and* an unresolved identity read as unrelated | C's scope and completeness rules over name-based identity, the nearest analogue of naive name-based matching (§11.5) inside C | — |

**Equivalent evidence.** Every policy reads the same event records. C additionally reads the completeness basis and the evidence timestamps from those same records. A and B ignore them by definition. No policy uses evidence another cannot see.

## 5. Results

See `research/tables/retro_outcomes.md`, `retro_ablations.md` and `retro_by_class.md`, and the dev equivalents. They are generated; do not copy numbers by hand.
