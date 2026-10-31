# Prevalence study: upstream source changes among widely used packages

A pre-specified, cross-sectional measurement of how often the most
depended-upon packages of npm, PyPI and Go have an archived, relocated or
unreachable source repository, how exposed their dependents are, and
whether a dependency tool could see it in registry, advisory or lifecycle
data. It answers TR-2026-01's Q1 with data, and uses no OpenPulse code or
data, so it is not an evaluation of OpenPulse.

Target venue: *Empirical Software Engineering* (research article).

## Files

| File | Role |
|---|---|
| `PROTOCOL.md` | Research questions, sample, measures, validation and analysis, written before collection; amendments are logged at its end |
| `RATING_GUIDE.md` | The human rating tasks of the validation (§6), written before any rating |
| `collect.py` | Collector: frame, sample and measures. Standard library only |
| `analysis.py` | The pre-specified analysis; writes `RESULTS.md` for a run |
| `test_collect.py` | Tests for the repository-URL rule. Outside the repository's `tests/`, so CI doesn't run them: `python -m pytest papers/prevalence/test_collect.py` |
| `paper/main.tex` | Manuscript draft. Every result is a red `[RESULT: …]` placeholder until the frozen run exists |
| `data/pilot-v1/`, `data/pilot-v2/` | Instrument pilots (top 100 per ecosystem). **Not results**: they were used only to fix the measures (see below) |

## Status

| Step | State |
|---|---|
| Protocol drafted | done |
| Instrument pilot | done: v1 found two gaps in the repository-URL rule (PyPI keys, Go vanity paths); v2 confirmed the fix |
| Protocol frozen | done: `data/FREEZE.md` (tag `prevalence-freeze-2026-10-31`) |
| Main collection | done 2026-10-31: `data/main/` (6,000 packages, `RESULTS.md`); `raw.jsonl.gz` (615 MB) goes to Zenodo |
| Ratings (§6) | not started; needs at least one rater who is not the author |
| Paper results | not started |

## Running

Python 3.11+, no dependencies. GitHub requests use `GITHUB_TOKEN`, or
`gh auth token` when it is unset. The full run takes about 90 minutes at
the documented rate limits.

```bash
python collect.py frame   --out data/main --max-rank 20000
python collect.py sample  --out data/main --top 1000 --tail 1000 --seed <seed from FREEZE.md>
python collect.py measure --out data/main
python analysis.py data/main/measures.jsonl > data/main/RESULTS.md
```

`measure` resumes where it stopped: it skips packages already in
`measures.jsonl`.

## Data

`frame-*.jsonl`, `sample.jsonl` and `measures.jsonl` are kept in git.
`raw.jsonl.gz`, every HTTP response with its URL, status and time, runs to
hundreds of megabytes at full scale. It is archived on Zenodo with the
frozen run instead (see `papers/ZENODO.md`).
