"""Counts, rates and intervals for every policy (METRICS.md §§2-4).

    python research/scripts/inference.py [retro|dev]

Reads research/results/<dataset>/evaluation.json and writes
inference.json next to it. Every rate is reported as k / n with its
denominator named, an exact Clopper-Pearson interval that treats pairs
as independent, and a percentile interval from an event-clustered
bootstrap that does not: pairs of one event share its evidence, so they
are resampled together. Comparisons with C are paired (the same
resampled events for both policies). Nothing here is a significance
claim about dependency incidents in general: the events are a
purposive sample (THREATS_TO_VALIDITY.md).
"""

from __future__ import annotations

import argparse
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import _common  # noqa: F401  (first: puts evaluation/ on sys.path)
from _common import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, DATASETS, RESULTS, load_json, write_json
from registration import clopper_pearson_interval

SYSTEM = "C-openpulse"

#: name -> (numerator categories, denominator: label set or "all"), METRICS.md §2.
RATES = {
    "false_clear_rate": ({"false_clear"}, {"in_scope"}),
    "silent_miss_rate": ({"silent_miss"}, {"in_scope"}),
    "correct_affected_rate": ({"correct_affected"}, {"in_scope"}),
    "false_positive_rate": ({"false_positive"}, {"out_of_scope"}),
    "correct_unaffected_rate": ({"correct_unaffected"}, {"out_of_scope"}),
    "resolution_rate": ({"correct_affected", "correct_unaffected"}, {"in_scope", "out_of_scope"}),
    "unresolved_rate": ({"unresolved", "abstained_undeterminable"}, "all"),
    "decisive_rate": (
        {
            "correct_affected",
            "correct_unaffected",
            "false_clear",
            "false_positive",
            "unsupported_decision",
        },
        "all",
    ),
}
DENOMINATORS = {
    "false_clear_rate": "in-scope pairs",
    "silent_miss_rate": "in-scope pairs",
    "correct_affected_rate": "in-scope pairs",
    "false_positive_rate": "out-of-scope pairs",
    "correct_unaffected_rate": "out-of-scope pairs",
    "resolution_rate": "determinable pairs (in- or out-of-scope)",
    "unresolved_rate": "all evaluated pairs",
    "decisive_rate": "all evaluated pairs",
}


def _counts(rows: list[dict[str, Any]], name: str) -> tuple[int, int]:
    num, den = RATES[name]
    pool = rows if den == "all" else [r for r in rows if r["label"] in den]
    return sum(1 for r in pool if r["category"] in num), len(pool)


def _by_event(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[r["event"]].append(r)
    return groups


class ClusterBootstrap:
    """One set of resampled events, shared by every policy and metric."""

    def __init__(self, events: list[str], resamples: int, seed: int):
        rng = random.Random(seed)
        self.events = events
        self.weights = []
        for _ in range(resamples):
            w = defaultdict(int)
            for _ in events:
                w[rng.randrange(len(events))] += 1
            self.weights.append(dict(w))

    def draws(self, per_event: list[tuple[float, float]]) -> list[float]:
        """Ratio estimates sum(num)/sum(den) over each resample (den > 0 only)."""
        out = []
        for w in self.weights:
            num = sum(per_event[i][0] * k for i, k in w.items())
            den = sum(per_event[i][1] * k for i, k in w.items())
            if den:
                out.append(num / den)
        return out


def _percentile(draws: list[float], lo: float = 0.025, hi: float = 0.975) -> list[float] | None:
    if not draws:
        return None
    s = sorted(draws)
    pick = lambda q: s[min(len(s) - 1, max(0, int(q * len(s))))]  # noqa: E731
    return [round(pick(lo), 4), round(pick(hi), 4)]


def _per_event(rows_by_event, events, name) -> list[tuple[float, float]]:
    return [_counts(rows_by_event.get(e, []), name) for e in events]


def sign_test(b: int, c: int) -> float | None:
    """Exact one-sided binomial sign test: P(X >= b | n = b + c, p = 1/2)."""
    n = b + c
    if n == 0:
        return None
    return round(sum(math.comb(n, i) for i in range(b, n + 1)) / 2**n, 6)


def policy_rows(evaluation: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in evaluation["pairs"]:
        rows[pair["policy"]].append(pair)
    return rows


def infer(evaluation: dict[str, Any], resamples: int = BOOTSTRAP_RESAMPLES) -> dict[str, Any]:
    rows = policy_rows(evaluation)
    events = sorted({r["event"] for r in rows[SYSTEM]})
    boot = ClusterBootstrap(events, resamples, BOOTSTRAP_SEED)
    sizes = [len(v) for v in _by_event(rows[SYSTEM]).values()]
    out: dict[str, Any] = {
        "dataset": evaluation["dataset"],
        "dataset_sha256": evaluation["dataset_sha256"],
        "clusters": {
            "unit": "event (a case's event set)",
            "events": len(events),
            "pairs": sum(sizes),
            "mean_pairs_per_event": round(sum(sizes) / len(sizes), 2),
            "max_pairs_per_event": max(sizes),
        },
        "bootstrap": {"resamples": resamples, "seed": BOOTSTRAP_SEED, "interval": "percentile 95%"},
        "denominators": DENOMINATORS,
        "policies": {},
        "paired_with_C": {},
    }
    c_by_event = _by_event(rows[SYSTEM])
    for policy, prows in rows.items():
        evaluable = [r for r in prows if r["category"] != "not_encoded"]
        block: dict[str, Any] = {
            "pairs": len(prows),
            "not_encoded": len(prows) - len(evaluable),
        }
        if not evaluable:
            block["status"] = "not evaluable: the representation encodes no event of this set"
            out["policies"][policy] = block
            continue
        by_event = _by_event(evaluable)
        for name in RATES:
            k, n = _counts(evaluable, name)
            draws = boot.draws(_per_event(by_event, events, name))
            block[name] = {
                "k": k,
                "n": n,
                "rate": round(k / n, 4) if n else None,
                "clopper_pearson_95": clopper_pearson_interval(k, n),
                "event_bootstrap_95": _percentile(draws) if n else None,
            }
        at_risk = sorted({r["event"] for r in evaluable if r["label"] == "in_scope"})
        failed = sorted({r["event"] for r in evaluable if r["category"] == "false_clear"})
        block["events_with_false_clear"] = {
            "k": len(failed),
            "n": len(at_risk),
            "clopper_pearson_95": clopper_pearson_interval(len(failed), len(at_risk)),
            "events": failed,
        }
        out["policies"][policy] = block
        if policy == SYSTEM or block["not_encoded"]:
            continue
        # Paired with C over the same events (R is skipped: it covers a subset).
        x_fail = set(failed)
        c_fail = {r["event"] for r in rows[SYSTEM] if r["category"] == "false_clear"}
        b, c = len(x_fail - c_fail), len(c_fail - x_fail)
        diffs = {}
        for name in ("false_clear_rate", "resolution_rate", "unresolved_rate"):
            xs = _per_event(by_event, events, name)
            cs = _per_event(c_by_event, events, name)
            point_x, point_c = (
                sum(v[0] for v in s) / max(1, sum(v[1] for v in s)) for s in (xs, cs)
            )
            draws = []
            for w in boot.weights:
                nx = sum(xs[i][0] * k for i, k in w.items())
                dx = sum(xs[i][1] * k for i, k in w.items())
                nc = sum(cs[i][0] * k for i, k in w.items())
                dc = sum(cs[i][1] * k for i, k in w.items())
                if dx and dc:
                    draws.append(nx / dx - nc / dc)
            diffs[name] = {
                "difference_x_minus_C": round(point_x - point_c, 4),
                "event_bootstrap_95": _percentile(draws),
            }
        out["paired_with_C"][policy] = {
            "events_false_clear_only_here": b,
            "events_false_clear_only_C": c,
            "sign_test_one_sided_p": sign_test(b, c),
            "sign_test_note": "within this purposive sample only; not a population inference",
            **diffs,
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", nargs="?", default="retro", choices=sorted(DATASETS))
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    folder = args.results / args.dataset
    result = infer(load_json(folder / "evaluation.json"))
    write_json(folder / "inference.json", result)
    for policy, block in result["policies"].items():
        if "status" in block:
            print(f"{policy:30} {block['status']}")
            continue
        fc, res = block["false_clear_rate"], block["resolution_rate"]
        print(
            f"{policy:30} FC {fc['k']}/{fc['n']} CP{fc['clopper_pearson_95']} "
            f"boot{fc['event_bootstrap_95']}  resolved {res['k']}/{res['n']} "
            f"boot{res['event_bootstrap_95']}"
        )


if __name__ == "__main__":
    main()
