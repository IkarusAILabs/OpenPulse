"""Metrics fixed by PROTOCOL.md, section 4, before any case was run.

Labels: ``in_scope``, ``out_of_scope``, ``undeterminable``. A pair is
determinable if its label is one of the first two. Outcomes come from
``policies``. A rate whose denominator is zero is ``None`` (undefined),
never zero.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from policies import AFFECTED, CLEARED, NONE, UNRESOLVED

IN, OUT, UNDET = "in_scope", "out_of_scope", "undeterminable"


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """One policy's rows -> the protocol's metrics.

    Each row has ``label``, ``outcome``, ``event`` (an id) and, for
    OpenPulse, ``justification``.
    """
    n = len(rows)
    by = Counter((r["label"], r["outcome"]) for r in rows)
    in_scope = sum(v for (lab, _), v in by.items() if lab == IN)
    out_scope = sum(v for (lab, _), v in by.items() if lab == OUT)
    undet = sum(v for (lab, _), v in by.items() if lab == UNDET)
    determinable = in_scope + out_scope
    false_clear = by[(IN, CLEARED)]
    silent_miss = by[(IN, NONE)]
    clears = sum(v for (_, o), v in by.items() if o == CLEARED)
    false_impact = by[(OUT, AFFECTED)]
    correct = by[(IN, AFFECTED)] + by[(OUT, CLEARED)]
    decisive = sum(v for (_, o), v in by.items() if o in (AFFECTED, CLEARED))
    abstained = sum(v for (_, o), v in by.items() if o == UNRESOLVED)
    unsupported = by[(UNDET, AFFECTED)] + by[(UNDET, CLEARED)]

    events_with_false_clear = {
        r["event"] for r in rows if (r["label"], r["outcome"]) == (IN, CLEARED)
    }
    events = {r["event"] for r in rows}

    result: dict[str, Any] = {
        "pairs": n,
        "events": len(events),
        "in_scope": in_scope,
        "out_of_scope": out_scope,
        "undeterminable": undet,
        "outcomes": {
            o: sum(v for (_, oo), v in by.items() if oo == o)
            for o in (AFFECTED, CLEARED, UNRESOLVED, NONE)
        },
        # Safety.
        "false_clears": false_clear,
        "fcr_affected": _rate(false_clear, in_scope),
        "fcr_clear": _rate(false_clear, clears),
        "silent_miss_rate": _rate(silent_miss, in_scope),
        "events_with_false_clear": len(events_with_false_clear),
        # Usefulness.
        "false_impact_rate": _rate(false_impact, out_scope),
        "resolution_rate": _rate(correct, determinable),
        "decisive_coverage": _rate(decisive, n),
        "abstention_rate": _rate(abstained, n),
        "no_association_rate": _rate(sum(v for (_, o), v in by.items() if o == NONE), n),
        "unsupported_decisiveness": _rate(unsupported, undet),
    }
    # With no false clear observed, the one-sided 95% upper bound on the
    # per-event failure probability is about 3 / n_events (rule of three),
    # stated over independent events, never over correlated pairs.
    if false_clear == 0 and events:
        result["per_event_false_clear_upper_95"] = round(3 / len(events), 4)
    justified = [r for r in rows if r["outcome"] in (AFFECTED, CLEARED) and "justification" in r]
    if justified:
        result["evidence_completeness"] = {
            key: _rate(sum(1 for r in justified if r["justification"][key]), len(justified))
            for key in justified[0]["justification"]
        }
    else:
        result["evidence_completeness"] = None  # the policy emits no justification
    return result


def stratify(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[str(r[key])].append(r)
    return {k: summarise(v) for k, v in sorted(groups.items())}
