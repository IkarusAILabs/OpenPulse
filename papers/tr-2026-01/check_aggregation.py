"""Exhaustive check of cross-event aggregation (TR-2026-01, Table "Cross-event aggregation").

Run from the repository root:  python papers/tr-2026-01/check_aggregation.py

Checks that core.risk.check.winning_cause headlines the summary the
truth table specifies, over two input families:

1. every ordered sequence of 1..5 relationships, with repetition (19607);
2. every ordering of every non-empty *set* of the seven relationships
   (13699 = sum over k of C(7,k) * k!).

The seven ranks are distinct, so winning_cause is a max over a total
order followed by a filter: its result depends only on which
relationships are present, not on order or multiplicity. Family 2 covers
all 127 such sets, so together with that argument the check covers
inputs of any length, not only the enumerated ones.
Expected output: 19607 sequences, 13699 set orderings, 0 mismatches.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.risk.check import winning_cause  # noqa: E402

RELATIONSHIPS = (
    "UNKNOWN",
    "RELATED",
    "AFFECTS_PROJECT",
    "NOT_AFFECTED",
    "AFFECTS_PACKAGE",
    "AFFECTS_VERSION",
    "AFFECTS_ARTIFACT",
)
AFFECTED = {"AFFECTS_PACKAGE", "AFFECTS_VERSION", "AFFECTS_ARTIFACT"}
UNRESOLVED = {"RELATED", "AFFECTS_PROJECT"}


def summary(relationship: str) -> str:
    if relationship in AFFECTED:
        return "affected"
    if relationship in UNRESOLVED:
        return "unresolved"
    if relationship == "NOT_AFFECTED":
        return "cleared"
    return "no association"


def expected(results: tuple[str, ...]) -> str:
    present = set(results)
    if present & AFFECTED:
        return "affected"
    if present & UNRESOLVED:
        return "unresolved"
    if "NOT_AFFECTED" in present:
        return "cleared"
    return "no association"


def main() -> int:
    mismatches = 0

    def check(results: tuple[str, ...]) -> None:
        nonlocal mismatches
        got = summary(winning_cause([{"relationship": r} for r in results])["relationship"])
        if got != expected(results):
            mismatches += 1
            print("mismatch:", results, got)

    sequences = [
        results
        for size in range(1, 6)
        for results in itertools.product(RELATIONSHIPS, repeat=size)
    ]
    orderings = [
        results
        for size in range(1, len(RELATIONSHIPS) + 1)
        for subset in itertools.combinations(RELATIONSHIPS, size)
        for results in itertools.permutations(subset)
    ]
    for results in sequences + orderings:
        check(results)
    print(f"{len(sequences)} sequences, {len(orderings)} set orderings, {mismatches} mismatches")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
