# Freeze record

The protocol, the rating guide, the collector and the analysis were
frozen at the commit below, approved by the author, **before** the main
run's sampling frame was fetched. The main run (`data/main/`) uses
exactly these files.

| | |
|---|---|
| Frozen at | 2026-10-31T18:13:34Z |
| Commit | `db81ca30c48a6644ef55974311d53b2fbe66b6a1` |
| Tag | `prevalence-freeze-2026-10-31` |
| Random seed (Tail stratum) | `20261031` |
| Python | 3.14.6 |

**Seed.** `20261031` is the freeze date, fixed here before any frame data
for the main run existed, and never varied.

**Hashes.** SHA-256 of each file as committed (LF line endings), and its
git blob ID. Check them with
`git show <commit>:papers/prevalence/<file> | sha256sum`.

| File | SHA-256 | Git blob |
|---|---|---|
| `PROTOCOL.md` | `694d72f9307f27f5b176d874c48190ce43c0b99a0286010485eb8d04e266ba59` | `131cb4cb1a5e8c4a3fd00b52e30618ca308b8f6e` |
| `RATING_GUIDE.md` | `b54b1bf4d40400c23563466ff8edbef963a651a1fc3d98e4eb9dd4e1f8e7613a` | `e9e70cdcbe764f740f7467433f4ce7a914d65202` |
| `collect.py` | `b00a6d7aca242f28b2e302842ee062bb6d08dd153ec72b4f8a196387dec07d13` | `f8da527c679694a2d7cbd98ece64b844a7117b7d` |
| `analysis.py` | `baf7b3e3b231035d24d75d57d83a28f397664a0a8b1d4775f4de8084e55b49e3` | `15d0950d050ce2aaed2efed37b83249d7df4d6f0` |

**Commands** (run from `papers/prevalence/`):

```bash
python collect.py frame   --out data/main --max-rank 20000
python collect.py sample  --out data/main --top 1000 --tail 1000 --seed 20261031
python collect.py measure --out data/main
python analysis.py data/main/measures.jsonl > data/main/RESULTS.md
```

**The frame.** ecosyste.ms ranks change daily, and packages tied on
`dependent_repos_count` have no stable order. The frame files of the main
run (`frame-*.jsonl`) are therefore the frozen sampling frame; rerunning
`frame` later gives a different one. `sample` is reproducible from them.

## Main run

Collected 2026-10-31, 18:14–19:46 UTC, with the frozen `collect.py` and
`analysis.py` (git blobs checked against the table above before the
analysis ran). 6,000 packages measured, none in state *error*.
`raw.jsonl.gz` (615 MB, SHA-256 below) is not in git; it is archived on
Zenodo with the run.

**Note for the paper.** The frame-against-source check in `RESULTS.md`
covers every package where both values exist (5,531), not the random 10%
named in PROTOCOL.md §6. The full set contains any 10% sample, so this
adds rather than changes information; the paper reports it as such.
- `*raw.jsonl.gz`: `5417362034b810781427bb8b1cb437f9bb0f1a047c2128d067e49fe46038f923`
- `*measures.jsonl`: `1fb61b86443ae248d4e28f0354d65b1fc645047893fa4918e4b813e59cae454f`
