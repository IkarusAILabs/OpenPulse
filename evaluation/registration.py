"""The registered analysis (REGISTRATION.md): frozen thresholds and tests.

Every number a result is judged against lives here, as a constant, so the
archived registration and the code that applies it cannot drift apart.
Changing a constant after held-out labelling starts is a protocol
amendment (REGISTRATION.md section 9) and is reported as one.

Pure Python, no new dependencies: an exact one-sided Clopper-Pearson
bound, a seeded event-clustered paired bootstrap, two one-sided tests
for equivalence, and Holm's step-down correction.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any

from metrics import IN, OUT, UNDET
from policies import AFFECTED, CLEARED, NONE, UNRESOLVED

# --- frozen thresholds (REGISTRATION.md sections 3-5) -------------------------

#: The tested system and its comparators.
SYSTEM, PRIMARY_BASELINE, NAIVE, STRONG = (
    "C-openpulse",
    "B-conservative",
    "A-naive",
    ("V-strong-conservative"),
)
#: H1 (safety, non-inferiority): margin on the event-level false-clear share.
DELTA_SAFETY = 0.05
#: Independent events needed for H1 to be decidable (3 / 60 = 0.05).
MIN_EVENTS = 60
#: H2 (usefulness, superiority): minimum gain in resolution rate over B.
MIN_GAIN = 0.10
#: S1 (C vs V equivalence): margin on the resolution-rate difference.
EQUIVALENCE_MARGIN = 0.05
#: G1: maximum silent-miss rate (no association on an in-scope pair).
MAX_SILENT_MISS = 0.02
#: G2: C's unresolved rate on decidable pairs may exceed B's by at most this.
UNRESOLVED_SLACK = 0.05
#: G3: per-class unresolved rate above which a class is flagged (not a test).
CLASS_FLAG = 0.60
#: Confidence level and resampling.
ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 4000
BOOTSTRAP_SEED = 20261030


# --- statistics ---------------------------------------------------------------


def _binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson_upper(k: int, n: int, alpha: float = ALPHA) -> float | None:
    """Exact one-sided (1 - alpha) upper bound on a proportion; None if n == 0.

    For k == 0 it is 1 - alpha ** (1 / n), about 3 / n at alpha 0.05.
    """
    if n == 0:
        return None
    if k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _binom_cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return round(hi, 4)


def holm(pvalues: dict[str, float | None], alpha: float = ALPHA) -> dict[str, dict[str, Any]]:
    """Holm's step-down adjustment. None p-values are carried, never tested."""
    tested = sorted((p, name) for name, p in pvalues.items() if p is not None)
    out: dict[str, dict[str, Any]] = {
        name: {"p": None, "p_holm": None, "reject": None}
        for name, p in pvalues.items()
        if p is None
    }
    running, m = 0.0, len(tested)
    for rank, (p, name) in enumerate(tested):
        running = max(running, min(1.0, (m - rank) * p))
        out[name] = {"p": round(p, 4), "p_holm": round(running, 4), "reject": running <= alpha}
    return out


# --- pairing and clustering ----------------------------------------------------------


def _correct(row: dict[str, Any]) -> int:
    return int((row["label"], row["outcome"]) in ((IN, AFFECTED), (OUT, CLEARED)))


def _paired(rows: dict[str, list[dict[str, Any]]], x: str, y: str) -> dict[str, list[tuple]]:
    """Decidable pairs of policies x and y, aligned by case, grouped by event set."""
    by_case = {r["case"]: r for r in rows[y]}
    clusters: dict[str, list[tuple]] = defaultdict(list)
    for r in rows[x]:
        if r["label"] == UNDET:
            continue
        s = by_case[r["case"]]
        clusters[r["event"]].append((_correct(r), _correct(s)))
    return dict(clusters)


def paired_difference(
    rows: dict[str, list[dict[str, Any]]],
    x: str,
    y: str,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Resolution-rate difference x - y on decidable pairs, event-clustered.

    Clusters are a case's event set; the bootstrap resamples clusters with
    replacement, so correlated pairs of one event move together.
    """
    clusters = _paired(rows, x, y)
    keys = sorted(clusters)

    def diff(sample: list[str]) -> float | None:
        pairs = [p for k in sample for p in clusters[k]]
        if not pairs:
            return None
        return sum(a - b for a, b in pairs) / len(pairs)

    point = diff(keys)
    if point is None:
        return {"x": x, "y": y, "difference": None, "clusters": 0, "pairs": 0}
    rng = random.Random(seed)
    draws = sorted(
        d
        for d in (diff([rng.choice(keys) for _ in keys]) for _ in range(resamples))
        if d is not None
    )

    def quantile(q: float) -> float:
        return draws[min(len(draws) - 1, max(0, int(q * len(draws))))]

    def tail(pred) -> float:
        return (1 + sum(1 for d in draws if pred(d))) / (1 + len(draws))

    return {
        "x": x,
        "y": y,
        "clusters": len(keys),
        "pairs": sum(len(v) for v in clusters.values()),
        "difference": round(point, 4),
        "ci95": [round(quantile(0.025), 4), round(quantile(0.975), 4)],
        "ci90": [round(quantile(0.05), 4), round(quantile(0.95), 4)],
        "lower_one_sided_95": round(quantile(0.05), 4),
        "p_greater_than_zero": round(tail(lambda d: d <= 0), 4),
        "draws": draws,
    }


def paired_event_false_clears(
    rows: dict[str, list[dict[str, Any]]],
    worse: str,
    better: str,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Event-level false-clear share, ``worse`` minus ``better``, over the same
    events at risk; one-sided p-value for "worse has more false-clear events"."""

    def failed(policy: str) -> set[str]:
        return {r["event"] for r in rows[policy] if (r["label"], r["outcome"]) == (IN, CLEARED)}

    at_risk = sorted({r["event"] for r in rows[better] if r["label"] == IN})
    if not at_risk:
        return {"worse": worse, "better": better, "events_at_risk": 0, "difference": None}
    fw, fb = failed(worse), failed(better)
    d = {e: int(e in fw) - int(e in fb) for e in at_risk}
    point = sum(d.values()) / len(at_risk)
    rng = random.Random(seed)
    draws = [sum(d[rng.choice(at_risk)] for _ in at_risk) / len(at_risk) for _ in range(resamples)]
    return {
        "worse": worse,
        "better": better,
        "events_at_risk": len(at_risk),
        "difference": round(point, 4),
        "p_greater_than_zero": round((1 + sum(1 for x in draws if x <= 0)) / (1 + resamples), 4),
    }


def event_false_clears(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Events with at least one in-scope pair, and those with a false clear."""
    at_risk = {r["event"] for r in rows if r["label"] == IN}
    failed = {r["event"] for r in rows if (r["label"], r["outcome"]) == (IN, CLEARED)}
    n, k = len(at_risk), len(failed)
    return {
        "events_at_risk": n,
        "events_with_false_clear": k,
        "share": round(k / n, 4) if n else None,
        "upper_one_sided_95": clopper_pearson_upper(k, n),
        "failed_events": sorted(failed),
    }


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def unresolved_on_decidable(rows: list[dict[str, Any]]) -> float | None:
    decidable = [r for r in rows if r["label"] != UNDET]
    return _rate(sum(1 for r in decidable if r["outcome"] == UNRESOLVED), len(decidable))


# --- the registered analysis ------------------------------------------------------------


def analyse(rows: dict[str, list[dict[str, Any]]], independent_only: bool) -> dict[str, Any]:
    """H1, H2, secondary tests (Holm-corrected) and guardrails.

    ``independent_only`` restricts every row to independently labelled
    pairs, the registered evaluation population; the development set has
    none, so its registered result is "not decidable" by design.
    """
    if independent_only:
        rows = {k: [r for r in v if r["independent"]] for k, v in rows.items()}
    c, b = rows[SYSTEM], rows[PRIMARY_BASELINE]
    safety_c, safety_b = event_false_clears(c), event_false_clears(b)
    decidable_h1 = safety_c["events_at_risk"] >= MIN_EVENTS
    bound = safety_c["upper_one_sided_95"]
    h1_pass = (
        decidable_h1 and bound is not None and bound - (safety_b["share"] or 0.0) <= DELTA_SAFETY
    )
    gain = paired_difference(rows, SYSTEM, PRIMARY_BASELINE)
    h2_pass = (
        gain["difference"] is not None
        and gain["difference"] >= MIN_GAIN
        and gain["lower_one_sided_95"] > 0
    )
    primary = {
        "H1_safety_noninferiority": {
            "rule": f"upper_95(event false-clear share of C) - share(B) <= {DELTA_SAFETY}, "
            f"with >= {MIN_EVENTS} events at risk",
            "C": safety_c,
            "B": safety_b,
            "decidable": decidable_h1,
            "pass": h1_pass if decidable_h1 else None,
        },
        "H2_resolution_superiority": {
            "rule": f"difference(C - B) >= {MIN_GAIN} and its one-sided 95% lower bound > 0",
            **{k: v for k, v in gain.items() if k != "draws"},
            "pass": h2_pass if gain["difference"] is not None else None,
        },
    }
    # Primary success needs both; a failed safety test is a failure whatever H2 says.
    if h1_pass is True and decidable_h1:
        primary["verdict"] = "success" if h2_pass else "failure: no usefulness gain"
    elif not decidable_h1:
        primary["verdict"] = (
            f"not decidable: {safety_c['events_at_risk']} events at risk, need {MIN_EVENTS}"
        )
    else:
        primary["verdict"] = "failure: safety margin not met"

    # Secondary tests, Holm-corrected together.
    equivalence = paired_difference(rows, SYSTEM, STRONG)
    tost_p = None
    if equivalence["difference"] is not None:
        draws, m = equivalence["draws"], EQUIVALENCE_MARGIN
        p_low = (1 + sum(1 for d in draws if d <= -m)) / (1 + len(draws))
        p_high = (1 + sum(1 for d in draws if d >= m)) / (1 + len(draws))
        tost_p = max(p_low, p_high)
    naive = paired_event_false_clears(rows, NAIVE, SYSTEM)
    secondary_p = {
        "S1_C_vs_V_equivalence": tost_p,
        "S2_A_vs_C_false_clears": naive["p_greater_than_zero"]
        if naive["difference"] is not None
        else None,
    }
    adjusted = holm(secondary_p)
    secondary = {
        "S1_C_vs_V_equivalence": {
            "rule": f"90% CI of difference(C - V) within +/-{EQUIVALENCE_MARGIN} (TOST)",
            **{k: v for k, v in equivalence.items() if k != "draws"},
            **adjusted["S1_C_vs_V_equivalence"],
        },
        "S2_A_vs_C_false_clears": {
            "rule": "event-level false-clear share of A minus C > 0, one-sided (safety)",
            **naive,
            **adjusted["S2_A_vs_C_false_clears"],
        },
        # Descriptive only, never tested: A answers everything, so its
        # resolution rate can exceed C's while it clears in-scope pairs.
        "D1_A_false_clears": event_false_clears(rows[NAIVE]),
        "D2_C_vs_A_resolution": {
            k: v for k, v in paired_difference(rows, SYSTEM, NAIVE).items() if k != "draws"
        },
    }

    # Guardrails.
    in_scope = [r for r in c if r["label"] == IN]
    silent = [r["case"] for r in in_scope if r["outcome"] == NONE]
    unresolved_c, unresolved_b = unresolved_on_decidable(c), unresolved_on_decidable(b)
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in c:
        by_class[str(r["class"])].append(r)
    class_rates = {k: unresolved_on_decidable(v) for k, v in sorted(by_class.items())}
    silent_rate = _rate(len(silent), len(in_scope))
    guardrails = {
        "G1_silent_miss": {
            "rule": f"no-association rate on in-scope pairs <= {MAX_SILENT_MISS}; all analysed",
            "rate": silent_rate,
            "cases": silent,
            "pass": None if silent_rate is None else silent_rate <= MAX_SILENT_MISS,
        },
        "G2_unresolved_vs_B": {
            "rule": f"unresolved rate on decidable pairs <= B's + {UNRESOLVED_SLACK}",
            "C": unresolved_c,
            "B": unresolved_b,
            "pass": None
            if unresolved_c is None or unresolved_b is None
            else unresolved_c <= unresolved_b + UNRESOLVED_SLACK,
        },
        "G3_class_flags": {
            "rule": f"report every class; flag unresolved rate > {CLASS_FLAG} (not a test)",
            "rates": class_rates,
            "flagged": [k for k, v in class_rates.items() if v is not None and v > CLASS_FLAG],
        },
    }
    return {
        "population": "independent labels only" if independent_only else "all labels",
        "pairs": len(c),
        "primary": primary,
        "secondary": secondary,
        "guardrails": guardrails,
    }


def thresholds() -> dict[str, Any]:
    """The frozen constants, for the results file and the registration."""
    return {
        "system": SYSTEM,
        "primary_baseline": PRIMARY_BASELINE,
        "delta_safety": DELTA_SAFETY,
        "min_events": MIN_EVENTS,
        "min_gain": MIN_GAIN,
        "equivalence_margin": EQUIVALENCE_MARGIN,
        "max_silent_miss": MAX_SILENT_MISS,
        "unresolved_slack": UNRESOLVED_SLACK,
        "class_flag": CLASS_FLAG,
        "alpha": ALPHA,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }
