# ruff: noqa: E501  (table rows)
"""Print REPORT.md's RQ-R1 tables from a results file (DESIGN.md §10).

    python evaluation/retrospective/report_tables.py results/openpulse-retro-2026-11.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MAIN = ("A-naive", "B-conservative", "V-strong-conservative", "C-openpulse")
ABLATIONS = ("C-ablate-completeness", "C-ablate-freshness", "C-ablate-both", "C-ablate-identity")
CLASSES = ("relocation", "deprecation", "distribution", "licence", "eol", "compromised")


def pct(x: float | None) -> str:
    return "–" if x is None else f"{100 * x:.1f}%"


def row(name: str, m: dict) -> str:
    return (
        f"| {name} | {m['events']} | {m['pairs']} | {m['false_clears']} ({m['events_with_false_clear']} ev.) "
        f"| {pct(m['silent_miss_rate'])} | {pct(m['false_impact_rate'])} | {pct(m['resolution_rate'])} "
        f"| {pct(m['abstention_rate'])} | {pct(m['unsupported_decisiveness'])} |"
    )


HEAD = (
    "| Policy | Events | Pairs | False clears | Silent miss | False impact | Resolved | Abstained | Unsupported decisive |\n"
    "|---|---|---|---|---|---|---|---|---|"
)


def main(path: str) -> int:
    r = json.loads(Path(path).read_text("utf-8"))
    pol = r["policies"]
    print("### All events\n\n" + HEAD)
    for p in MAIN + ABLATIONS:
        print(row(p, pol[p]["overall"]))
    for c in CLASSES:
        print(f"\n### {c}\n\n" + HEAD)
        for p in MAIN:
            print(row(p, pol[p]["by_class"][c]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
