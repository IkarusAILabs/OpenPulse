"""The registered analysis (REGISTRATION.md): frozen thresholds and tests.

Every number a result is judged against lives here, as a constant, so the
archived registration and the code that applies it cannot drift apart.
Changing a constant after held-out labelling starts is a protocol
amendment (REGISTRATION.md section 9) and is reported as one.

Pure Python, no new dependencies: exact Clopper-Pearson bounds, a seeded
event-clustered paired bootstrap, two one-sided tests for equivalence,
and Holm's step-down correction.

Beside the tests it builds the amended draft's reported measures (section
12, 2026-10-30): the attribution chain B -> R -> V -> C, the review
burden W1-W3 and guardrail G4 (section 5), and the reliability of
admitted inputs D1-D2 (section 5a). W1 and W2 run whole inventories and
need no labels; W3, D1 and D2 tabulate annotators' records.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any

from metrics import IN, OUT, UNDET
from policies import AFFECTED, CLEARED, NONE, UNRESOLVED

from core.entities.identity import package_trust, resolution_trust

# --- frozen thresholds (REGISTRATION.md sections 3-5) -------------------------

#: The tested system and its comparators.
SYSTEM, PRIMARY_BASELINE, NAIVE, STRONG = (
    "C-openpulse",
    "B-conservative",
    "A-naive",
    ("V-strong-conservative"),
)
#: S3's comparator: OSV/OpenVEX encodings read by a careful consumer.
EXISTING = "R-existing-representation"
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
#: G4 and W1-W3 (section 5): the policies whose review burden is reported,
#: and the two whose unresolved summaries are timed (W3), 50 items each.
BURDEN_POLICIES = (SYSTEM, STRONG, EXISTING, PRIMARY_BASELINE)
REVIEW_POLICIES = (SYSTEM, PRIMARY_BASELINE)
REVIEW_SAMPLE = 50
#: The attribution steps, (later, earlier) in the chain B -> R -> V -> C.
ATTRIBUTION = ((EXISTING, PRIMARY_BASELINE), (STRONG, EXISTING), (SYSTEM, STRONG))
#: D1 (section 5a): bases reported apart, and the fewest declarations per
#: basis whose rate is reported without a warning; never pooled.
DECLARATION_BASES = ("definitional", "announced", "corroborated")
DECLARATION_JUDGEMENTS = ("correct", "under-inclusive", "over-inclusive")
MIN_DECLARATIONS = 10
#: D2 (section 5a): judgements of a curated identity mapping.
MAPPING_JUDGEMENTS = ("correct", "wrong", "stale")
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


def clopper_pearson_interval(k: int, n: int, alpha: float = ALPHA) -> list[float] | None:
    """Exact two-sided (1 - alpha) interval on a proportion; None if n == 0."""
    if n == 0:
        return None
    upper = 1.0 if k >= n else clopper_pearson_upper(k, n, alpha / 2)
    if k == 0:
        return [0.0, upper]
    lo, hi = 0.0, k / n
    for _ in range(80):
        mid = (lo + hi) / 2
        if 1 - _binom_cdf(k - 1, n, mid) < alpha / 2:
            lo = mid
        else:
            hi = mid
    return [round(lo, 4), upper]


def _proportion(k: int, n: int) -> dict[str, Any]:
    return {"count": k, "of": n, "rate": _rate(k, n), "ci95_exact": clopper_pearson_interval(k, n)}


def _spread(values: list[float]) -> dict[str, Any] | None:
    """Median, interquartile range and maximum; None for no values."""
    if not values:
        return None
    q = statistics.quantiles(values, n=4, method="inclusive") if len(values) > 1 else values * 3
    return {
        "n": len(values),
        "median": round(statistics.median(values), 4),
        "iqr": [round(q[0], 4), round(q[2], 4)],
        "max": round(max(values), 4),
    }


def _bootstrap_mean(values: list[float], resamples: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    draws = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(resamples))
    return [round(draws[int(0.025 * resamples)], 4), round(draws[int(0.975 * resamples) - 1], 4)]


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


def pair_false_clears(
    rows: list[dict[str, Any]],
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Pair-level false-clear share (FCR_affected) with two upper bounds.

    The exact bound treats in-scope pairs as independent, which they are
    not, so it is optimistic. The event-clustered bootstrap bound resamples
    events; with no false clear observed it has zero width and is not
    reported. Neither turns zero observed errors into a low rate: the
    event-level exact bound governs H1.
    """
    in_scope = [r for r in rows if r["label"] == IN]
    k = sum(1 for r in in_scope if r["outcome"] == CLEARED)
    n = len(in_scope)
    out: dict[str, Any] = {
        "false_clears": k,
        "in_scope_pairs": n,
        "share": _rate(k, n),
        "upper_one_sided_95_if_pairs_independent": clopper_pearson_upper(k, n),
        "upper_one_sided_95_event_clustered": None,
    }
    if k:
        clusters: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in in_scope:
            clusters[r["event"]][0] += r["outcome"] == CLEARED
            clusters[r["event"]][1] += 1
        keys = sorted(clusters)
        rng = random.Random(seed)
        draws = []
        for _ in range(resamples):
            sample = [clusters[rng.choice(keys)] for _ in keys]
            draws.append(sum(a for a, _ in sample) / sum(b for _, b in sample))
        draws.sort()
        out["upper_one_sided_95_event_clustered"] = round(draws[int(0.95 * resamples) - 1], 4)
    return out


def strata(rows: dict[str, list[dict[str, Any]]], key: str) -> dict[str, dict[str, Any]]:
    """C's and B's safety and resolution within each stratum of ``key``."""
    out = {}
    values = sorted({str(r.get(key)) for r in rows[SYSTEM]})
    for value in values:
        cell = {}
        for name in (SYSTEM, PRIMARY_BASELINE):
            subset = [r for r in rows[name] if str(r.get(key)) == value]
            decidable = [r for r in subset if r["label"] != UNDET]
            cell[name] = {
                "pairs": len(subset),
                "event_false_clears": event_false_clears(subset),
                "resolution_rate": _rate(sum(_correct(r) for r in decidable), len(decidable)),
            }
        out[value] = cell
    return out


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def unresolved_on_decidable(rows: list[dict[str, Any]]) -> float | None:
    decidable = [r for r in rows if r["label"] != UNDET]
    return _rate(sum(1 for r in decidable if r["outcome"] == UNRESOLVED), len(decidable))


# --- review burden W1-W3 and guardrail G4 (section 5) ---------------------------------


def weekly_cycles(start: date, end: date) -> list[datetime]:
    """The end of each weekly cycle of the window, the last ending on or after ``end``."""
    day, cycles = start + timedelta(days=6), []
    while True:
        cycles.append(datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc))
        if day >= end:
            return cycles
        day += timedelta(days=7)


def inventory_burden(
    policies: dict[str, Callable[..., dict[str, Any]]],
    inventories: dict[str, list[dict[str, Any]]],
    cycles: list[tuple[datetime, dict[str, Any]]],
    max_evidence_age: timedelta | None = None,
) -> dict[str, Any]:
    """W1 and W2 for each policy over whole inventories; no labels.

    ``cycles`` holds, per weekly cycle, its end time and the held-out
    events current then, by name, as known at that time. W1 counts each
    inventory's references whose summary over those events is unresolved,
    and those newly unresolved since the previous cycle. Each cell also
    counts the decisive (actionable) summaries. Across the window, the
    unique review items are the distinct references left unresolved in
    any inventory and cycle, so a reference shared by inventories, or
    unresolved for several cycles, is reviewed once. W2 counts, per
    event, the references of every inventory that the event alone leaves
    unresolved, in the first cycle it is current.
    """
    first: dict[str, tuple[datetime, Any]] = {}
    for at, events in cycles:
        for name, event in events.items():
            first.setdefault(name, (at, event))
    w1: dict[str, list[dict[str, Any]]] = {}
    w2: dict[str, dict[str, int]] = {}
    unique: dict[str, int] = {}
    for name, policy in policies.items():

        def outcome(dep: dict[str, Any], events: list[Any], at: datetime) -> str:
            decision = policy(dep, events, as_of=at, max_evidence_age=max_evidence_age)
            return decision["outcome"]

        def unresolved(dep: dict[str, Any], events: list[Any], at: datetime) -> bool:
            return outcome(dep, events, at) == UNRESOLVED

        cells, review_items = [], set()
        for inventory, refs in sorted(inventories.items()):
            before: set[int] = set()
            for at, events in cycles:
                current = list(events.values())
                outcomes = [outcome(dep, current, at) if current else NONE for dep in refs]
                held = {i for i, o in enumerate(outcomes) if o == UNRESOLVED}
                decisive = sum(1 for o in outcomes if o in (AFFECTED, CLEARED))
                review_items.update(json.dumps(refs[i], sort_keys=True) for i in held)
                cells.append(
                    {
                        "inventory": inventory,
                        "cycle": at.date().isoformat(),
                        "count": len(held),
                        "share": _rate(len(held), len(refs)),
                        "new": len(held - before),
                        "decisive": decisive,
                        "actionable_share": _rate(decisive, len(refs)),
                        "unresolved": sorted(held),
                    }
                )
                before = held
        w1[name] = cells
        unique[name] = len(review_items)
        w2[name] = {
            event_name: sum(
                1 for refs in inventories.values() for dep in refs if unresolved(dep, [event], at)
            )
            for event_name, (at, event) in sorted(first.items())
        }
    return {
        "inventories": {k: len(v) for k, v in sorted(inventories.items())},
        "cycles": [at.date().isoformat() for at, _ in cycles],
        "W1_cells": w1,
        "W2_per_event": w2,
        "unique_review_items": unique,
    }


def burden_summary(burden: dict[str, Any], at_risk: set[str] | None = None) -> dict[str, Any]:
    """W1 across inventories and cycles; W2 across events (those at risk, when given)."""
    out = {}
    for name, cells in burden["W1_cells"].items():
        per_event = burden["W2_per_event"][name]
        events = [e for e in sorted(per_event) if at_risk is None or e in at_risk]
        out[name] = {
            "W1_unresolved": _spread([c["count"] for c in cells]),
            "W1_share": _spread([c["share"] for c in cells if c["share"] is not None]),
            "W1_new_per_cycle": _spread([c["new"] for c in cells]),
            "W1_actionable_share": _spread(
                [c["actionable_share"] for c in cells if c.get("actionable_share") is not None]
            ),
            "W1_unique_review_items": burden.get("unique_review_items", {}).get(name),
            "W2_unresolved_per_event": _spread([per_event[e] for e in events]),
        }
    return out


def review_sample(
    burden: dict[str, Any], size: int = REVIEW_SAMPLE, seed: int = BOOTSTRAP_SEED
) -> dict[str, list[dict[str, Any]]]:
    """W3's items: a seeded random draw of each review policy's unresolved summaries.

    An item is one (inventory, reference, cycle) the policy left
    unresolved, drawn without replacement; every one in the window can be
    drawn, so the sample weights cycles as W1 does.
    """
    rng = random.Random(seed)
    out = {}
    for name in REVIEW_POLICIES:
        pool = [
            {"inventory": c["inventory"], "reference": i, "cycle": c["cycle"]}
            for c in burden["W1_cells"].get(name, [])
            for i in c["unresolved"]
        ]
        out[name] = rng.sample(pool, min(size, len(pool)))
    return out


def review_minutes(
    reviews: list[dict[str, Any]],
    burden: dict[str, Any] | None = None,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """W3: mean minutes per timed review of an unresolved summary, by policy.

    Each record is ``{"policy", "item", "minutes"}``. Given the W1 summary,
    the implied reviewer hours per inventory and cycle are its median
    count times the mean minutes (and times each end of the interval).
    """
    out = {}
    for name in REVIEW_POLICIES:
        minutes = [float(r["minutes"]) for r in reviews if r["policy"] == name]
        entry: dict[str, Any] = {"items": len(minutes), "target": REVIEW_SAMPLE}
        entry["short_of_target"] = len(minutes) < REVIEW_SAMPLE
        if minutes:
            mean = sum(minutes) / len(minutes)
            ci = _bootstrap_mean(minutes, resamples, seed)
            entry.update({"mean_minutes": round(mean, 2), "ci95": ci})
            w1 = ((burden or {}).get(name) or {}).get("W1_unresolved")
            if w1 is not None:
                hours = [round(w1["median"] * m / 60, 2) for m in (mean, *ci)]
                entry["implied_hours_per_inventory_cycle"] = hours[0]
                entry["implied_hours_ci95"] = hours[1:]
        out[name] = entry
    return out


# --- attribution B -> R -> V -> C (section 2) --------------------------------------------


def attribution(
    rows: dict[str, list[dict[str, Any]]], burden: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Each step's resolution gain and W1 difference; reported, never tested."""
    steps = []
    for later, earlier in ATTRIBUTION:
        if later not in rows or earlier not in rows:
            continue
        gain = paired_difference(rows, later, earlier)
        step = {
            "step": f"{earlier} -> {later}",
            **{k: v for k, v in gain.items() if k not in ("draws", "x", "y")},
        }
        if burden is not None and later in burden and earlier in burden:
            a, b = burden[later]["W1_unresolved"], burden[earlier]["W1_unresolved"]
            step["W1_median_difference"] = (
                None if a is None or b is None else round(a["median"] - b["median"], 4)
            )
        steps.append(step)
    return steps


# --- encoding loss (sections 2 and 4) -----------------------------------------------------


def encoding_loss(events: dict[str, dict[str, Any]], encodings: dict[str, Any]) -> dict[str, Any]:
    """Loss codes per event and, per event class, the events encoded and lossless."""
    per_event = {
        name: sorted({x["code"] for x in encodings[name]["loss"]}) if name in encodings else None
        for name in sorted(events)
    }
    by_class: dict[str, dict[str, int]] = defaultdict(
        lambda: {"events": 0, "encoded": 0, "lossless": 0}
    )
    for name, spec in events.items():
        cell = by_class[str(spec["class"])]
        cell["events"] += 1
        cell["encoded"] += per_event[name] is not None
        cell["lossless"] += per_event[name] == []
    return {"per_event": per_event, "by_class": dict(sorted(by_class.items()))}


# --- reliability of admitted inputs D1-D2 (section 5a) --------------------------------------


def _final(record: dict[str, Any], allowed: tuple[str, ...]) -> str | None:
    """The adjudicated judgement, else the annotators' agreed one, else None."""
    judgements = record.get("judgements") or {}
    for value in (record.get("adjudicated"), *judgements.values()):
        if value is not None and value not in allowed:
            raise ValueError(f"judgement {value!r} not in {allowed}")
    if record.get("adjudicated"):
        return record["adjudicated"]
    values = set(judgements.values())
    return values.pop() if len(values) == 1 else None


def completeness_declarations(
    records: list[dict[str, Any]], admitted: dict[str, str] | None = None
) -> dict[str, Any]:
    """D1: under-inclusive declarations per completeness basis, never pooled.

    Each record is ``{"event", "basis", "judgements": {annotator: ...},
    "adjudicated"?}``. ``admitted`` names the events whose scope C admits
    for a negative, with their basis, so that an unjudged one is listed.
    """
    finals: dict[str, list[str]] = defaultdict(list)
    unsettled, agreed, paired = [], 0, 0
    for record in records:
        if record["basis"] not in DECLARATION_BASES:
            raise ValueError(f"{record['event']}: basis {record['basis']!r}")
        if len(record.get("judgements") or {}) >= 2:
            paired += 1
            agreed += len(set(record["judgements"].values())) == 1
        final = _final(record, DECLARATION_JUDGEMENTS)
        if final is None:
            unsettled.append(record["event"])
        else:
            finals[record["basis"]].append(final)
    per_basis = {}
    for basis in DECLARATION_BASES:
        values = finals.get(basis, [])
        per_basis[basis] = {
            "declarations": len(values),
            "judgements": {j: values.count(j) for j in DECLARATION_JUDGEMENTS},
            "under_inclusive": _proportion(values.count("under-inclusive"), len(values)),
            "fewer_than_minimum": len(values) < MIN_DECLARATIONS,
        }
    judged = {r["event"] for r in records}
    return {
        "per_basis": per_basis,
        "annotator_agreement": {"agreed": agreed, "of": paired},
        "unadjudicated": sorted(unsettled),
        "admitted_not_judged": sorted(set(admitted or {}) - judged),
    }


def _mapping(dep: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """The curated mapping a dependency's identity rests on, if any."""
    if dep["kind"] == "image":
        trust, key = resolution_trust(str(dep["ref"])), f"image:{dep['ref']}"
    else:
        ecosystem = str(dep.get("ecosystem") or "").lower()
        trust = package_trust(str(dep["package"]), dep.get("ecosystem"))
        key = f"package:{ecosystem}:{str(dep['package']).lower()}"
    if trust["via"] not in ("explicit", "catalog"):
        return None
    return key, trust


def identity_mappings(
    rows: dict[str, list[dict[str, Any]]], dependencies: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """D2's worksheet: every curated mapping that a decisive C or V verdict relies on."""
    sheet: dict[str, dict[str, Any]] = {}
    for policy in (SYSTEM, STRONG):
        for row in rows.get(policy, []):
            if row["outcome"] not in (AFFECTED, CLEARED):
                continue
            found = _mapping(dependencies[row["case"]])
            if found is None:
                continue
            key, trust = found
            entry = sheet.setdefault(
                key, {"slug": trust["slug"], "via": trust["via"], "verdicts": []}
            )
            entry["verdicts"].append(f"{policy}:{row['case']}:{row['outcome']}")
    return dict(sorted(sheet.items()))


def mapping_reliability(
    records: list[dict[str, Any]], worksheet: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """D2: wrong or stale curated mappings, with the verdicts that relied on them.

    Each record is ``{"mapping", "judgements": {checker: ...}, "adjudicated"?}``
    or ``{"mapping", "judgement"}``, keyed as in ``identity_mappings``.
    """
    finals, unsettled = {}, []
    for record in records:
        if "judgement" in record:
            record = {**record, "judgements": {"checker": record["judgement"]}}
        final = _final(record, MAPPING_JUDGEMENTS)
        if final is None:
            unsettled.append(record["mapping"])
        else:
            finals[record["mapping"]] = final
    errors = {k: v for k, v in finals.items() if v != "correct"}
    return {
        "judged": len(finals),
        "judgements": {j: sum(1 for v in finals.values() if v == j) for j in MAPPING_JUDGEMENTS},
        "error": _proportion(len(errors), len(finals)),
        "wrong_or_stale": [
            {"mapping": k, "judgement": v, "verdicts": worksheet.get(k, {}).get("verdicts", [])}
            for k, v in sorted(errors.items())
        ],
        "unadjudicated": sorted(unsettled),
        "relied_on_not_judged": sorted(set(worksheet) - set(finals) - set(unsettled)),
    }


# --- the registered analysis ------------------------------------------------------------


def analyse(
    rows: dict[str, list[dict[str, Any]]],
    independent_only: bool,
    comparators_complete: bool = True,
    encodings_complete: bool = True,
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """H1, H2, secondary tests (Holm-corrected), guardrails and reported measures.

    ``independent_only`` restricts every row to independently labelled
    pairs, the registered evaluation population; the development set has
    none, so its registered result is "not decidable" by design.

    ``inputs`` carries what the pairs do not: ``burden`` (from
    ``inventory_burden``), ``timed_reviews`` (W3), ``completeness_declarations``
    with ``admitted_declarations`` (D1), ``identity_mappings`` and
    ``dependencies`` by case (D2). A missing input leaves its table, and
    G4, empty and is listed under ``missing_inputs``.
    """
    inputs = inputs or {}
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
            "C_pair_level": pair_false_clears(c),
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
    existing = paired_difference(rows, SYSTEM, EXISTING) if EXISTING in rows else None
    has_existing = existing is not None and existing["difference"] is not None
    secondary_p = {
        "S1_C_vs_V_equivalence": tost_p,
        "S2_A_vs_C_false_clears": naive["p_greater_than_zero"]
        if naive["difference"] is not None
        else None,
        "S3_C_vs_R_resolution": existing["p_greater_than_zero"] if has_existing else None,
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
        "S3_C_vs_R_resolution": {
            "rule": "difference(C - R) > 0: one-sided 95% lower bound of the event-clustered "
            "paired bootstrap",
            **({k: v for k, v in existing.items() if k != "draws"} if existing else {}),
            "lower_bound_above_zero": existing["lower_one_sided_95"] > 0 if has_existing else None,
            **adjusted["S3_C_vs_R_resolution"],
        },
        # Descriptive only, never tested: A answers everything, so its
        # resolution rate can exceed C's while it clears in-scope pairs.
        "A_false_clears": event_false_clears(rows[NAIVE]),
        "C_vs_A_resolution": {
            k: v for k, v in paired_difference(rows, SYSTEM, NAIVE).items() if k != "draws"
        },
    }
    if EXISTING in rows:
        # Reported next to S3: R's own false clears, and S3 on lossless events.
        safety_r = event_false_clears(rows[EXISTING])
        lossless = {r["case"] for r in rows[EXISTING] if not r.get("encoding_loss", True)}
        subset = {k: [r for r in rows[k] if r["case"] in lossless] for k in (SYSTEM, EXISTING)}
        secondary["R_false_clears"] = safety_r
        secondary["S3_reading"] = (
            "trade-off: C has more false-clear events than R"
            if safety_c["events_with_false_clear"] > safety_r["events_with_false_clear"]
            else "no more false-clear events than R"
        )
        secondary["C_vs_R_resolution_lossless_events"] = {
            "cases": len(lossless),
            **{
                k: v for k, v in paired_difference(subset, SYSTEM, EXISTING).items() if k != "draws"
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

    # Review burden (W1-W3, G4), labels not needed; W2 over events at risk.
    at_risk = {name for r in c if r["label"] == IN for name in r["event"].split("+")}
    burden = burden_summary(inputs["burden"], at_risk) if "burden" in inputs else None
    w1_c, w1_b = (
        (burden.get(SYSTEM) or {}).get("W1_unresolved") if burden else None,
        (burden.get(PRIMARY_BASELINE) or {}).get("W1_unresolved") if burden else None,
    )
    guardrails["G4_review_burden"] = {
        "rule": "median W1 (unresolved references per inventory and cycle) of C <= B's",
        "C": w1_c,
        "B": w1_b,
        "pass": None if w1_c is None or w1_b is None else w1_c["median"] <= w1_b["median"],
    }
    reported: dict[str, Any] = {
        # Section 4: no completeness basis or identity status is trusted on
        # the strength of another's results.
        "by_completeness_basis": strata(rows, "basis"),
        "by_identity_status": strata(rows, "identity"),
        "attribution_B_R_V_C": attribution(rows, burden),
        "review_burden": burden,
        "W3_review_minutes": review_minutes(inputs["timed_reviews"], burden)
        if "timed_reviews" in inputs
        else None,
        "D1_completeness_declarations": completeness_declarations(
            inputs["completeness_declarations"], inputs.get("admitted_declarations")
        )
        if "completeness_declarations" in inputs
        else None,
    }
    sheet = identity_mappings(rows, inputs["dependencies"]) if "dependencies" in inputs else None
    reported["D2_identity_mappings"] = (
        mapping_reliability(inputs["identity_mappings"], sheet or {})
        if "identity_mappings" in inputs
        else None
    )
    reported["D2_worksheet"] = sheet
    missing = [
        name
        for name, key in (
            ("W1-W2 inventory run", "burden"),
            ("W3 timed reviews", "timed_reviews"),
            ("D1 completeness judgements", "completeness_declarations"),
            ("D2 mapping judgements", "identity_mappings"),
        )
        if key not in inputs
    ]
    # V and R decide with the pinned ecosystem comparators, and R reads
    # the frozen encodings; without all of them the result is not the
    # registered one.
    problems = []
    if not comparators_complete:
        problems.append("pinned ecosystem comparators unavailable")
    if not encodings_complete:
        problems.append("an event has no frozen R encoding")
    return {
        "valid": not problems,
        "validity": "valid"
        if not problems
        else f"invalid: {'; '.join(problems)} (REGISTRATION.md section 9)",
        "population": "independent labels only" if independent_only else "all labels",
        "pairs": len(c),
        "primary": primary,
        "secondary": secondary,
        "guardrails": guardrails,
        "reported": reported,
        "missing_inputs": missing,
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
        "existing_representation_baseline": EXISTING,
        "burden_policies": list(BURDEN_POLICIES),
        "review_policies": list(REVIEW_POLICIES),
        "review_sample": REVIEW_SAMPLE,
        "min_declarations_per_basis": MIN_DECLARATIONS,
        "alpha": ALPHA,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }
