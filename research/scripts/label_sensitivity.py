"""How the retrospective results depend on who, or what, labelled the pairs.

    python research/scripts/label_sensitivity.py [--results DIR]

The analysis pre-specified in research/labelling/AI_PANEL_PROTOCOL.md §6.
Reads the developer's labels (L1, the case file), the AI-panel raw labels
(their hashes checked against LOCK.json, so an edited label fails), the
pilot rounds, and every policy's recorded outcome (results/retro/
evaluation.json). Outcomes do not depend on labels, so each label set
re-scores the same outcomes. Writes results/retro/label_sensitivity.json.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import _common  # noqa: F401
import label_packets as packets
import label_panel as panel
from _common import DATASETS, RESULTS, ROOT, load_json, relative, sha256, write_json
from evaluate import CATEGORY

IN, OUT, UND = packets.LABELS
LABELS = packets.LABELS
SEED = 20261101
RESAMPLES = 10000
PILOTS = {
    "pilot round 1": ROOT / "evaluation/retrospective/labelling/round-1/L2-labels.jsonl",
    "pilot round 2": ROOT / "evaluation/retrospective/labelling/round-2/L2-labels.jsonl",
}
POLICIES = (
    "A-naive",
    "B-conservative",
    "V-strong-conservative",
    "C-openpulse",
    "C-posthoc-binary",
)
#: Sets compared in agreement statistics: (first, second).
AGREEMENT = (
    ("AI-A", "AI-B"),
    ("AI-A", "L1"),
    ("AI-B", "L1"),
    ("AI-AP", "L1"),
)


def _verify_lock() -> None:
    """Fail unless every AI-panel file matches the hash locked before unblinding."""
    lock = panel._lock()
    for section in ("labels", "adjudication"):
        if not lock.get(section):
            raise SystemExit(f"LOCK.json has no {section!r}: the panel is not finalised")
        for path, digest in lock[section].items():
            if sha256(ROOT / path) != digest:
                raise SystemExit(f"{path} differs from its locked hash: labels were changed")


def label_sets() -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """Full-coverage label sets by case id, and the AI rationales by case id."""
    _verify_lock()
    key = load_json(panel.OUT / "key.json")["pairs"]
    expected = set(key)
    a, _ = panel.reader_labels("A", expected)
    b, _ = panel.reader_labels("B", expected)
    adj, _ = panel.read_labels(panel.RAW / "adjudicator.jsonl", set(panel.disagreements(a, b)))
    l1 = {c["id"]: c["label"] for c in load_json(DATASETS["retro"])["cases"]}
    sets: dict[str, dict[str, str]] = {"L1": l1, "AI-A": {}, "AI-B": {}, "AI-AP": {}}
    notes: dict[str, Any] = {}
    for nid, entry in key.items():
        case = entry["case"]
        sets["AI-A"][case] = a[nid]["label"]
        sets["AI-B"][case] = b[nid]["label"]
        sets["AI-AP"][case] = adj[nid]["label"] if nid in adj else a[nid]["label"]
        notes[case] = {
            "neutral_id": nid,
            "A": a[nid].get("rationale"),
            "B": b[nid].get("rationale"),
            "adjudicator": adj[nid].get("rationale") if nid in adj else None,
        }
    readings = [sets[s] for s in ("L1", "AI-A", "AI-B")]
    sets["bound against C"] = {
        c: IN
        if any(r[c] == IN for r in readings)
        else (OUT if any(r[c] == OUT for r in readings) else UND)
        for c in l1
    }
    sets["bound against A"] = {
        c: IN
        if all(r[c] == IN for r in readings)
        else (OUT if all(r[c] == OUT for r in readings) else UND)
        for c in l1
    }
    return sets, notes


# --- agreement -------------------------------------------------------------------


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    n = len(pairs)
    if not n:
        return None
    observed = sum(1 for x, y in pairs if x == y) / n
    first, second = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    expected = sum(first[k] * second[k] for k in LABELS) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def agreement(
    first: dict[str, str], second: dict[str, str], events: dict[str, str]
) -> dict[str, Any]:
    cases = sorted(set(first) & set(second))
    pairs = [(first[c], second[c]) for c in cases]
    by_event: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for c in cases:
        by_event[events[c]].append((first[c], second[c]))
    names = sorted(by_event)
    rng = random.Random(SEED)  # noqa: S311 - seeded, reproducible sampling; not a secret
    draws = []
    for _ in range(RESAMPLES):
        sample = [p for _ in names for p in by_event[rng.choice(names)]]
        k = kappa(sample)
        if k is not None:
            draws.append(k)
    draws.sort()
    k = kappa(pairs)
    return {
        "pairs": len(pairs),
        "agree": sum(1 for x, y in pairs if x == y),
        "kappa": None if k is None else round(k, 3),
        "kappa_event_bootstrap_95": (
            [round(draws[int(0.025 * len(draws))], 3), round(draws[int(0.975 * len(draws)) - 1], 3)]
            if draws
            else None
        ),
        "confusion": {f"{x} / {y}": n for (x, y), n in sorted(Counter(pairs).items())},
    }


def _pilot(path: Path) -> dict[str, str]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {r["id"]: r["label"] for r in rows}


# --- re-scoring ------------------------------------------------------------------


def score(outcomes: list[dict[str, Any]], labels: dict[str, str]) -> dict[str, Any]:
    cats = Counter()
    fc_events, at_risk = set(), set()
    for row in outcomes:
        label = labels[row["case"]]
        cats[CATEGORY[(label, row["outcome"])]] += 1
        if label == IN:
            at_risk.add(row["event"])
            if row["outcome"] == "cleared":
                fc_events.add(row["event"])
    in_scope = sum(1 for r in outcomes if labels[r["case"]] == IN)
    out_scope = sum(1 for r in outcomes if labels[r["case"]] == OUT)
    return {
        "in_scope": in_scope,
        "out_of_scope": out_scope,
        "undeterminable": len(outcomes) - in_scope - out_scope,
        "false_clears": cats["false_clear"],
        "events_with_false_clear": len(fc_events),
        "events_at_risk": len(at_risk),
        "silent_misses": cats["silent_miss"],
        "false_positives": cats["false_positive"],
        "unresolved": cats["unresolved"] + cats["abstained_undeterminable"],
        "correct": cats["correct_affected"] + cats["correct_unaffected"],
        "categories": dict(sorted(cats.items())),
    }


def run(results: Path) -> dict[str, Any]:
    evaluation = load_json(results / "retro" / "evaluation.json")
    sets, notes = label_sets()
    pairs = [p for p in evaluation["pairs"] if p["policy"] in POLICIES]
    events = {p["case"]: p["event"] for p in pairs}
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in pairs:
        by_policy[p["policy"]].append(p)

    agree = {f"{x} vs {y}": agreement(sets[x], sets[y], events) for x, y in AGREEMENT}
    for name, path in PILOTS.items():
        agree[f"{name} vs L1"] = agreement(_pilot(path), sets["L1"], events)
        agree[f"{name} vs AI-AP"] = agreement(_pilot(path), sets["AI-AP"], events)

    kinds: Counter = Counter()
    by_class: dict[str, Counter] = defaultdict(Counter)
    classes = {p["case"]: p["class"] for p in pairs}
    changed = []
    c_outcome = {p["case"]: p["outcome"] for p in by_policy["C-openpulse"]}
    a_outcome = {p["case"]: p["outcome"] for p in by_policy["A-naive"]}
    for case in sorted(sets["L1"]):
        l1, ap = sets["L1"][case], sets["AI-AP"][case]
        if l1 == ap:
            continue
        kind = " / ".join(sorted((l1, ap)))
        kinds[kind] += 1
        by_class[classes[case]][kind] += 1
        changed.append(
            {
                "case": case,
                "event": events[case],
                "L1": l1,
                "AI-A": sets["AI-A"][case],
                "AI-B": sets["AI-B"][case],
                "AI-AP": ap,
                "C outcome": c_outcome[case],
                "A outcome": a_outcome[case],
                **{f"rationale {k}": v for k, v in notes[case].items() if k != "neutral_id"},
            }
        )
    rescored = {
        name: {policy: score(by_policy[policy], labels) for policy in POLICIES}
        for name, labels in sets.items()
    }
    c_fc = {name: block["C-openpulse"]["false_clears"] for name, block in rescored.items()}
    return {
        "dataset": evaluation["dataset"],
        "dataset_sha256": evaluation["dataset_sha256"],
        "protocol": relative(panel.OUT.parent / "AI_PANEL_PROTOCOL.md"),
        "lock": relative(panel.OUT / "LOCK.json"),
        "bootstrap": {"unit": "event", "resamples": RESAMPLES, "seed": SEED},
        "label_counts": {n: dict(sorted(Counter(s.values()).items())) for n, s in sets.items()},
        "agreement": agree,
        "disagreements_L1_vs_AP": {
            "count": len(changed),
            "by_kind": dict(sorted(kinds.items())),
            "by_class": {k: dict(sorted(v.items())) for k, v in sorted(by_class.items())},
            "pairs": changed,
        },
        "rescored": rescored,
        "reading": {
            "C_zero_false_clears_robust": all(
                c_fc[s] == 0 for s in ("L1", "AI-A", "AI-B", "AI-AP")
            ),
            "A_exceeds_C_under_every_set": all(
                block["A-naive"]["false_clears"] > block["C-openpulse"]["false_clears"]
                for block in rescored.values()
            ),
            "C_false_clears_by_set": c_fc,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    result = run(args.results)
    write_json(args.results / "retro" / "label_sensitivity.json", result)
    for name, block in result["agreement"].items():
        print(f"{name:26} {block['agree']}/{block['pairs']} kappa={block['kappa']}")
    for name, block in result["rescored"].items():
        a, c = block["A-naive"], block["C-openpulse"]
        print(
            f"{name:16} A FC={a['false_clears']:3}/{a['in_scope']:3} "
            f"C FC={c['false_clears']:2} C unres={c['unresolved']:3}"
        )


if __name__ == "__main__":
    main()
