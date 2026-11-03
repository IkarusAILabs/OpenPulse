"""The track T study, Part A: star-history indicators (protocol item TR4 onward).

Run from the repository root, offline:

    python benchmarks/track_t_study.py calibrate

``docs/research/TRACK_T_STUDY_PROTOCOL.md`` defines the indicators (§3), the
split and the calibration (§5). This script implements them:

- **SH1** peak week share, **SH2** four-week concentration and **SH3** daily
  spike, computed from a recorded weekly star history
  (``record_star_history.py``); each needs at least ``MIN_STARS`` stars and a
  complete history (status 200), else the repository is not eligible.
- **Split.** Each organic set is split 50/50 by name with the protocol seed,
  before any value is computed; the split depends on names only.
- **Calibration.** On the calibration half only, each threshold is the
  (k+1)-th largest eligible value, k = floor(1% of eligible), and an
  indicator fires when a value is strictly above it, so at most 1% of the
  calibration half fires.

``calibrate`` never computes a value for a held-out repository or a positive;
it writes the split (names only) and the thresholds to
``benchmarks/fixtures/reputation/star-calibration-<date>.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "benchmarks" / "fixtures" / "reputation"
SETS = {"organic": "stars-organic-2026-11-03.json", "young": "stars-young-2026-11-03.json"}
SEED = 20261103
MIN_STARS = 50
FALSE_POSITIVE_CAP = 0.01
WEEK = 7 * 86400
DAY = 86400
PRIOR_DAYS = 56  # the 8 weeks before the busiest day
INDICATORS = ("SH1", "SH2", "SH3")


# ---------------------------------------------------------------------------
# Indicators (protocol §3)
# ---------------------------------------------------------------------------


def daily(weeks: list[list[int]]) -> dict[int, int]:
    """{day (epoch seconds): stars} for the days with stars."""
    out: dict[int, int] = {}
    for week, *days in weeks:
        for offset, count in enumerate(days):
            if count:
                out[week + offset * DAY] = out.get(week + offset * DAY, 0) + count
    return out


def indicators(history: dict[str, Any]) -> dict[str, float] | None:
    """SH1-SH3 for an eligible history, else None."""
    if history.get("status") != 200:
        return None
    weeks = sorted(history.get("weeks") or [])
    totals = {w[0]: sum(w[1:]) for w in weeks}
    stars = sum(totals.values())
    if stars < MIN_STARS:
        return None
    sh1 = max(totals.values()) / stars
    sh2 = max(sum(totals.get(start + i * WEEK, 0) for i in range(4)) for start in totals) / stars
    days = daily(weeks)
    busiest = min(days, key=lambda d: (-days[d], d))  # ties: the earliest day
    prior = [days.get(busiest - i * DAY, 0) for i in range(1, PRIOR_DAYS + 1)]
    sh3 = days[busiest] / max(statistics.median(prior), 1)
    return {"SH1": sh1, "SH2": sh2, "SH3": sh3}


# ---------------------------------------------------------------------------
# Split and calibration (protocol §5)
# ---------------------------------------------------------------------------


def split(names: list[str], seed: int = SEED) -> tuple[list[str], list[str]]:
    """(calibration, held-out): half of the names (rounded down) by the seed."""
    ordered = sorted(names, key=str.lower)
    chosen = set(random.Random(seed).sample(ordered, len(ordered) // 2))
    return [n for n in ordered if n in chosen], [n for n in ordered if n not in chosen]


def threshold(values: list[float], cap: float = FALSE_POSITIVE_CAP) -> dict[str, Any]:
    """The smallest observed value that at most ``cap`` of ``values`` exceed."""
    ordered = sorted(values, reverse=True)
    allowed = math.floor(cap * len(ordered))
    value = ordered[allowed]
    return {
        "threshold": value,
        "eligible": len(ordered),
        "allowed_to_fire": allowed,
        "fire": sum(1 for v in ordered if v > value),
    }


def load(filename: str) -> tuple[dict[str, Any], str]:
    path = FIXTURES / filename
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def calibrate(sets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Split every set, then compute thresholds on the pooled calibration halves."""
    halves: dict[str, dict[str, list[str]]] = {}
    pooled: dict[str, list[float]] = {name: [] for name in INDICATORS}
    ineligible: dict[str, int] = {}
    for label, doc in sets.items():
        calibration, held_out = split(list(doc["repositories"]))
        halves[label] = {"calibration": calibration, "held_out": held_out}
        ineligible[label] = 0
        for repo in calibration:  # never a held-out repository
            values = indicators(doc["repositories"][repo])
            if values is None:
                ineligible[label] += 1
                continue
            for name in INDICATORS:
                pooled[name].append(values[name])
    return {
        "split": halves,
        "calibration_ineligible": ineligible,
        "thresholds": {name: threshold(pooled[name]) for name in INDICATORS},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["calibrate"])
    parser.parse_args(argv)
    sets, sources = {}, {}
    for label, filename in SETS.items():
        sets[label], digest = load(filename)
        sources[label] = {"file": filename, "sha256": digest}
    result = calibrate(sets)
    doc = {
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "benchmarks/track_t_study.py",
        "protocol": "docs/research/TRACK_T_STUDY_PROTOCOL.md §5",
        "seed": SEED,
        "min_stars": MIN_STARS,
        "false_positive_cap": FALSE_POSITIVE_CAP,
        "rule": "fires when the value is strictly above the threshold",
        "sources": sources,
        **result,
    }
    out = FIXTURES / f"star-calibration-{doc['computed_at'][:10]}.json"
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    for name, t in doc["thresholds"].items():
        print(name, json.dumps(t))
    print("calibration ineligible", json.dumps(result["calibration_ineligible"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
