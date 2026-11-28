# OpenPulse research package

This directory holds everything needed to evaluate OpenPulse's applicability model as a research contribution, and to reproduce every reported number from the code and the frozen data.

It builds on the evaluation harness in `evaluation/` and the conformance tooling in `conformance/`. It does not duplicate either.

**Start here:** run `python research/scripts/reproduce.py --check`. It regenerates every result, table and figure offline and verifies them against the committed files (`REPRODUCIBILITY.md`).

| Document | What it answers |
|---|---|
| [RESEARCH_READINESS_AUDIT.md](RESEARCH_READINESS_AUDIT.md) | What exists, what was wrong (P0–P3), what was fixed, and what the evidence does and does not support |
| [RESEARCH_PLAN.md](RESEARCH_PLAN.md) | Hypotheses, steps with acceptance criteria, their state, and decisions left to the authors |
| [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) | The model mapped to code, the eight decision invariants, what is verified and what is assumed, and the evaluation design |
| [DATASET_CARD.md](DATASET_CARD.md) | The case sets: composition, provenance, labels, limitations, redistribution |
| [LABELING_GUIDE.md](LABELING_GUIDE.md) | Labels and decision rules for independent annotators; agreement and adjudication |
| [BASELINES.md](BASELINES.md) | Every baseline and ablation, what it models, and where it cannot be evaluated |
| [METRICS.md](METRICS.md) | Error categories, every denominator, intervals and clustering, and what the numbers may be used for |
| [THREATS_TO_VALIDITY.md](THREATS_TO_VALIDITY.md) | Construct, internal, external, conclusion and research-integrity threats |
| [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Environment, exact commands, expected outputs, failure conditions |
| [paper/](paper/) | Draft manuscript (LaTeX), bibliography, literature protocol |
| [FINAL_REPORT.md](FINAL_REPORT.md) | What was inspected, changed and tested in this round, and what remains |

| Directory | Contents | Produced by |
|---|---|---|
| `scripts/` | `validate_dataset`, `evaluate`, `inference`, `compare`, `tables`, `reproduce` | — |
| `dataset/` | `schema.json` for case sets | — |
| `results/` | Per case set: `evaluation.json` (every pair, every policy), `inference.json`, `versions.json`; plus `conformance.json` and `MANIFEST.json` | `reproduce.py` |
| `tables/` | Markdown and LaTeX tables, plus `numbers.tex` (every number the manuscript's prose cites) | `tables.py` |
| `figures/` | SVG and TikZ outcome figures | `tables.py` |

Do not edit anything under `results/`, `tables/` or `figures/` by hand. CI regenerates them and fails on any difference.
