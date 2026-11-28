"""Compare one policy's pair outcomes across implementation versions.

    python research/scripts/compare.py [retro|dev] [--policy C-openpulse]

Reads the committed results of earlier versions (VERSIONED_RESULTS:
evaluation/run.py output, the frozen retrospective run and its "after
fixes" rerun) and research/results/<dataset>/evaluation.json for the
current code, checks that every version evaluated the same case file
(same SHA-256), and writes versions.json: each step's outcome
transitions and every changed pair with its label, so a change in a
headline number can be traced to the pairs that moved.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import _common  # noqa: F401
from _common import RESULTS, VERSIONED_RESULTS, load_json, relative, write_json
from evaluate import category

SAFETY = {"false_clear", "silent_miss"}


def _outcomes(results: dict[str, Any], policy: str) -> dict[str, dict[str, Any]]:
    if "policies" in results:  # evaluation/run.py format
        rows = results["pairs"].get(policy, [])
        return {r["case"]: {"label": r["label"], "outcome": r["outcome"], **r} for r in rows}
    return {p["case"]: p for p in results["pairs"] if p["policy"] == policy}


def compare(dataset: str, policy: str, results: Path = RESULTS) -> dict[str, Any]:
    versions = {name: load_json(path) for name, path in VERSIONED_RESULTS.get(dataset, {}).items()}
    versions["current (this tree)"] = load_json(results / dataset / "evaluation.json")
    hashes = {name: r["dataset_sha256"] for name, r in versions.items()}
    if len(set(hashes.values())) != 1:
        raise SystemExit(f"versions evaluated different case files: {hashes}")
    outcomes = {name: _outcomes(r, policy) for name, r in versions.items()}
    names = list(outcomes)
    steps = []
    for before, after in zip(names, names[1:]):
        a, b = outcomes[before], outcomes[after]
        changed = []
        for case in sorted(set(a) & set(b)):
            if a[case]["outcome"] != b[case]["outcome"]:
                changed.append(
                    {
                        "case": case,
                        "label": a[case]["label"],
                        "before": a[case]["outcome"],
                        "after": b[case]["outcome"],
                        "category_before": category(a[case]),
                        "category_after": category(b[case]),
                    }
                )
        steps.append(
            {
                "from": before,
                "to": after,
                "pairs": len(set(a) & set(b)),
                "changed": len(changed),
                "transitions": dict(Counter(f"{c['before']} -> {c['after']}" for c in changed)),
                "new_safety_errors": [c for c in changed if c["category_after"] in SAFETY],
                "fixed_safety_errors": [c for c in changed if c["category_before"] in SAFETY],
                "pairs_changed": changed,
            }
        )
    summary = {
        name: dict(Counter(category(o) for o in rows.values())) for name, rows in outcomes.items()
    }
    return {
        "dataset": dataset,
        "policy": policy,
        "dataset_sha256": next(iter(hashes.values())),
        "versions": {
            name: (
                relative(VERSIONED_RESULTS[dataset][name])
                if name in VERSIONED_RESULTS.get(dataset, {})
                else "research/results"
            )
            for name in names
        },
        "commits": {name: r.get("commit") for name, r in versions.items()},
        "categories": summary,
        "steps": steps,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", nargs="?", default="retro", choices=sorted(VERSIONED_RESULTS))
    parser.add_argument("--policy", default="C-openpulse")
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    result = compare(args.dataset, args.policy, args.results)
    write_json(args.results / args.dataset / "versions.json", result)
    for step in result["steps"]:
        print(
            f"{step['from']} -> {step['to']}: {step['changed']}/{step['pairs']} pairs changed "
            f"{step['transitions']}; new safety errors {len(step['new_safety_errors'])}, "
            f"fixed {len(step['fixed_safety_errors'])}"
        )


if __name__ == "__main__":
    main()
