"""Run every registered policy over a labelled case set (PROTOCOL.md).

Run from the repository root:

    python evaluation/run.py [--cases evaluation/cases/dev-2026-10.json]
                             [--max-evidence-age-days 90]

Writes ``evaluation/results/<dataset>.json``: the dataset's SHA-256 and
the commit, every policy's metrics overall and by event class and by
label independence, and every pair's outcome, so that each incorrect or
unresolved decision can be inspected. Offline and deterministic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import metrics  # noqa: E402
import policies  # noqa: E402
import registration  # noqa: E402
import replay  # noqa: E402

DEFAULT_CASES = HERE / "cases" / "dev-2026-10.json"
LABELS = (metrics.IN, metrics.OUT, metrics.UNDET)


def _commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def validate(dataset: dict[str, Any]) -> None:
    """Fail closed on a malformed case set before anything is run."""
    events = dataset["events"]
    seen: set[str] = set()
    for case in dataset["cases"]:
        cid = case["id"]
        if cid in seen:
            raise ValueError(f"duplicate case id {cid}")
        seen.add(cid)
        if case["label"] not in LABELS:
            raise ValueError(f"{cid}: label {case['label']!r} not in {LABELS}")
        for name in case["events"]:
            if name not in events:
                raise ValueError(f"{cid}: unknown event {name}")
        if not case.get("rationale") or not case.get("label_source"):
            raise ValueError(f"{cid}: every label needs a rationale and a source")


def run(path: Path = DEFAULT_CASES, max_evidence_age_days: int = 90) -> dict[str, Any]:
    raw = path.read_bytes()
    dataset = json.loads(raw)
    validate(dataset)
    max_age = timedelta(days=max_evidence_age_days)
    known = {name: replay.replay(spec) for name, spec in dataset["events"].items()}
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in policies.POLICIES}
    for case in dataset["cases"]:
        names = case["events"]
        events = [known[n] for n in names if known[n] is not None]
        as_of = max(replay.as_of_time(dataset["events"][n]) for n in names)
        for name, policy in policies.POLICIES.items():
            decision = policy(case["dependency"], events, as_of=as_of, max_evidence_age=max_age)
            rows[name].append(
                {
                    "case": case["id"],
                    "event": "+".join(names),
                    "class": dataset["events"][names[0]]["class"],
                    "independent": bool(case.get("independent_label", False)),
                    "label": case["label"],
                    **decision,
                }
            )
    return {
        "dataset": dataset["dataset"],
        "dataset_version": dataset["version"],
        "dataset_status": dataset["status"],
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "commit": _commit(),
        "max_evidence_age_days": max_evidence_age_days,
        "events_not_known_at_replay": sorted(n for n, e in known.items() if e is None),
        "policies": {
            name: {
                "overall": metrics.summarise(r),
                "by_class": metrics.stratify(r, "class"),
                "by_label_independence": metrics.stratify(r, "independent"),
            }
            for name, r in rows.items()
        },
        "registration": {
            "thresholds": registration.thresholds(),
            # The registered population: independently labelled pairs only.
            "registered": registration.analyse(rows, independent_only=True),
            # The same analysis over every label: illustrative, never evidence.
            "all_labels_illustrative": registration.analyse(rows, independent_only=False),
        },
        "pairs": rows,
    }


_COLUMNS = [
    ("false_clears", "false clears"),
    ("fcr_affected", "FCR_aff"),
    ("silent_miss_rate", "silent miss"),
    ("false_impact_rate", "false impact"),
    ("resolution_rate", "resolved"),
    ("abstention_rate", "abstain"),
    ("unsupported_decisiveness", "unsupp. decisive"),
]


def _fmt(value: Any) -> str:
    return "undef" if value is None else str(value)


def table(result: dict[str, Any]) -> str:
    head = f"{'policy':24}" + "".join(f"{label:>17}" for _, label in _COLUMNS)
    lines = [head]
    for name, block in result["policies"].items():
        o = block["overall"]
        lines.append(f"{name:24}" + "".join(f"{_fmt(o[k]):>17}" for k, _ in _COLUMNS))
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--max-evidence-age-days", type=int, default=90)
    args = parser.parse_args()
    result = run(args.cases, args.max_evidence_age_days)
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / f"{result['dataset']}.json").write_text(
        json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8"
    )
    first = next(iter(result["policies"].values()))["overall"]
    print(
        f"{result['dataset']} {result['dataset_version']} ({result['dataset_status']}): "
        f"{first['pairs']} pairs over {first['events']} events"
    )
    print(table(result))
    for population in ("registered", "all_labels_illustrative"):
        block = result["registration"][population]
        primary, guard = block["primary"], block["guardrails"]
        print(
            f"{population}: {primary['verdict']}; "
            f"H2 gain {primary['H2_resolution_superiority'].get('difference')}; "
            f"G1 {guard['G1_silent_miss']['pass']}, G2 {guard['G2_unresolved_vs_B']['pass']}"
        )
