# Cost measurements — TR-2026-01

Implementation: `main` at `5e369ae`. Machine: Windows 11, Intel 64-bit (12 logical CPUs), Python 3.14.6. Measured 2026-10-29. Single machine, single session: absolute numbers depend on hardware; the shapes are the result.

```bash
python benchmarks/cost.py          # offline: matching and history growth
python benchmarks/cost.py --live   # also live acquisition through the agent interface
```

Raw results are in `benchmarks/results/cost.json`. Since 2026-10-30 that file holds a run with the catalogue-map cache (`0174a26`, below); the tables in the rest of this report are the original 2026-10-29 run.

## Re-measurement at `a1ecc58`, and with the cache (2026-10-30)

On the same machine, three runs at `a1ecc58` were interleaved with two fresh runs of the audit snapshot `8a9c3a8`. The fresh `8a9c3a8` runs reproduced the tables below within about 15%. The "with cache" column is `a1ecc58` plus the catalogue-map cache (`0174a26`), measured in three further runs. Medians:

| Setting | `8a9c3a8` | `a1ecc58` | with cache |
|---|---:|---:|---:|
| µs per pair (inventory sizes 100–5,000, 10 events) | 42 | 75 | 25 |
| 5,000 dependencies × 10 events | 2.1–2.6 s | 3.7–3.9 s | 1.9 s |
| 1,000 dependencies × 100 events | 3.98 s | 6.85 s | 2.66 s |
| Per scope element per pair | 2.6–2.8 µs | 2.9–3.4 µs | 3.0–3.2 µs |
| Peak memory, 5,000 × 10 | 24.6 MiB | 24.6 MiB | 24.6 MiB |
| Sweep per repository / store growth per run | 34 ms / 6.1–7.1 KB | 34 ms / 6.1–7.1 KB | 35–45 ms / 6.1–7.1 KB |

**Matching was about 1.8× slower** at `a1ecc58`. The cause was a fixed cost per package dependency, not per scope element. Since F1, `package_trust` rebuilt the catalogue's package map (`package_map`) on every call, and `resolution_trust` rebuilt the alias map (`catalog_alias_map`). In a profile of 1,000 dependencies × 10 events, these took about 2.6 s of 3.5 s.

**The cache** (`0174a26`) memoises those maps per catalogue object. It brings matching to about 25 µs per pair, below the audit snapshot. Decisions are unchanged:
- the conformance matrix;
- 100,000 random cases;
- 22 re-injected mutants;
- the dev and retrospective case files.

Per-element scope cost is the same. The sweep code is unchanged, so its spread across columns is run-to-run variation.

## Matching (offline, `check_watchlist`)

Synthetic inventories are half container images and half packages. Synthetic events are artifact-scoped and declared complete. Timings are the median of 3 runs.

| Varying | Setting | Pairs | Time | µs per pair |
|---|---|---:|---:|---:|
| Inventory size (10 events, 5-element scopes) | 10 | 100 | 0.005 s | 48 |
| | 100 | 1,000 | 0.040 s | 40 |
| | 1,000 | 10,000 | 0.41 s | 41 |
| | 5,000 | 50,000 | 2.06 s | 41 |
| Event count (1,000 dependencies) | 1 | 1,000 | 0.066 s | 66 |
| | 10 | 10,000 | 0.41 s | 41 |
| | 100 | 100,000 | 3.87 s | 39 |
| Scope size (1,000 dependencies, 1 event) | 1 element | 1,000 | 0.053 s | 53 |
| | 10 | 1,000 | 0.078 s | 78 |
| | 100 | 1,000 | 0.32 s | 315 |
| | 1,000 | 1,000 | 2.61 s | 2,607 |

- **Cost is linear in pairs,** at about 40 µs per dependency–event pair.
- **Peak memory** for 5,000 dependencies × 10 events is 24.6 MiB.
- **Scope size is the expensive dimension.** Every element is evaluated for every dependency, with no index, which costs about 2.6 µs per element per pair. An index from repository to elements would make large catalogue-wide scopes cheap, but there is none yet. In practice, namespace elements keep scopes small: the Bitnami event has 4.

## History growth (offline, `sweep_catalog` with the production observation store)

50 repositories with 51 tags each, swept 20 times on consecutive days. In one mode nothing changes; in the other, every repository gains one tag per run.

| Mode | Run 1 (baseline) | Runs 2–20, median per sweep | Range | Per repository | Store growth |
|---|---:|---:|---:|---:|---:|
| Steady | 0.11 s | 1.73 s | 1.59–1.91 s | 35 ms | 6.1 KB per repository per run |
| One new tag per run | 0.11 s | 1.77 s | 0.64–1.98 s | 35 ms | 7.1 KB per repository per run |

- **The store keeps a full snapshot per run,** so it grows linearly even when nothing changes. At daily sweeps that is about 2.2 MB per repository per year at this tag count.
- **Each sweep reads the repository's whole history** (`load_all`), so sweep time also grows slowly with history length. A 60-run series of 20 repositories went from 0.71 s at run 11 to 0.84 s at run 60.
- **Run 1 is cheap** because it only records a baseline.
- **Timings vary between runs on this machine,** probably from file-system scanning. Medians are reported.

## Live acquisition (agent interface, `--live`)

`dependency_status` for five PyPI packages, each looked up cold and then warm, with every HTTP request counted.

| Package | Cold | Requests | Warm | Requests |
|---|---:|---:|---:|---:|
| django | 2.45 s | 3 | 0.005 s | 0 |
| redis | 0.79 s | 3 | 0.002 s | 0 |
| flask | 0.48 s | 2 | 0.003 s | 0 |
| celery | 0.50 s | 2 | 0.003 s | 0 |
| requests | 0.53 s | 2 | 0.003 s | 0 |

- **HTTP statuses:** 9 × 200 and 3 × 404, the 404s being sources that do not track a package. There were no errors and no rate limiting.
- The first cold lookup includes connection setup.
- Warm lookups are served from the one-hour per-process cache and make no requests.
- An unauthenticated GitHub client allows 60 requests per hour, which at 1–3 requests per package is 20–60 cold lookups per hour without a token.

## What is not measured

- Registry tag walks for large repositories, and acquisition under rate limiting: none occurred.
- Scheduled monitoring of a large population.
- Dependency on network conditions: the live numbers are one session from one location.
- Indexed matching, which does not exist yet.
