"""Every policy, registered and post hoc, over one labelled case set.

    python research/scripts/evaluate.py [retro|dev] [--comparators off|required]

Writes research/results/<dataset>/evaluation.json:

- ``registered``: the policies of evaluation/policies.py (A, B, R, V, C and
  C's four registered ablations), run by the existing harness
  (evaluation/run.py) unchanged;
- ``post_hoc``: ablations added by the research-readiness work
  (BASELINES.md §4). They were defined after the registered results were
  known, so they are exploratory and reported apart, never as tests;
- ``pairs``: every pair's outcome under every policy, with its error
  category (METRICS.md §2), so each error can be inspected.

``--comparators off`` (default) runs baseline V without the pinned
npm/Go/Maven bridges on every machine alike, so the output is
deterministic; ``required`` is the registered configuration and refuses
to run without them. The frozen retrospective results were produced with
them (evaluation/retrospective/REPORT.md).
"""

from __future__ import annotations

import argparse
import contextlib
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from typing import Any

import _common  # noqa: F401  (first: puts evaluation/ and conformance/ on sys.path)
import metrics
import policies
import replay
import run as harness
from _common import DATASETS, RESULTS, load_json, relative, sha256, write_json
from ecosystem_versions import PINS, Comparators

AFFECTED, CLEARED, UNRESOLVED, NONE = (
    policies.AFFECTED,
    policies.CLEARED,
    policies.UNRESOLVED,
    policies.NONE,
)

#: (label, outcome) -> error category (METRICS.md §2). Every pair falls in one.
CATEGORY = {
    (metrics.IN, AFFECTED): "correct_affected",
    (metrics.IN, CLEARED): "false_clear",
    (metrics.IN, UNRESOLVED): "unresolved",
    (metrics.IN, NONE): "silent_miss",
    (metrics.OUT, CLEARED): "correct_unaffected",
    (metrics.OUT, AFFECTED): "false_positive",
    (metrics.OUT, UNRESOLVED): "unresolved",
    (metrics.OUT, NONE): "no_association",
    (metrics.UNDET, AFFECTED): "unsupported_decision",
    (metrics.UNDET, CLEARED): "unsupported_decision",
    (metrics.UNDET, UNRESOLVED): "abstained_undeterminable",
    (metrics.UNDET, NONE): "abstained_undeterminable",
}
#: Baseline R's pairs whose event its representation could not encode: a
#: missing representation, not an abstention and not an error (BASELINES.md).
NOT_ENCODED = "not_encoded"
CATEGORIES = (*dict.fromkeys(CATEGORY.values()), NOT_ENCODED)


def category(row: dict[str, Any]) -> str:
    if row.get("encoded") is False:
        return NOT_ENCODED
    return CATEGORY[(row["label"], row["outcome"])]


# --- comparators ------------------------------------------------------------


def disabled_comparators() -> Comparators:
    """No bridge on any machine, recorded as such (never "complete")."""
    comparators = Comparators(names=())
    comparators.status = {
        name: {
            "pinned": pin,
            "available": False,
            "error": "not used: research run with --comparators off (research/REPRODUCIBILITY.md)",
        }
        for name, pin in PINS.items()
    }
    return comparators


@contextlib.contextmanager
def comparators_for(mode: str) -> Iterator[Comparators]:
    comparators = Comparators(required=True) if mode == "required" else disabled_comparators()
    harness.strong_baseline.use_comparators(comparators)
    harness.existing_representation.use_comparators(comparators)
    try:
        yield comparators
    finally:
        harness.strong_baseline.use_comparators(None)
        harness.existing_representation.use_comparators(None)
        harness.existing_representation.use_encodings(None)
        comparators.close()


# --- post-hoc ablations (BASELINES.md §4) ------------------------------------


@contextlib.contextmanager
def no_curated_identity() -> Iterator[None]:
    """Curated identity off: no explicit alias, no catalogue mapping.

    Every reference then resolves to itself (or by the namespace
    heuristic), as it would for a project nobody curated. The engine's
    code is unchanged; only its identity knowledge is removed.
    """
    from core.entities import catalog, resolve

    aliases = dict(resolve.EXPLICIT_ALIASES)
    original = catalog.load_catalog
    resolve.EXPLICIT_ALIASES.clear()  # the same dict object identity.py imported
    catalog.load_catalog = lambda path=None: []
    resolve._catalog_map.cache_clear()
    try:
        yield
    finally:
        catalog.load_catalog = original
        resolve.EXPLICIT_ALIASES.update(aliases)
        resolve._catalog_map.cache_clear()


def binary(dep: dict[str, Any], events: list[Any], **kw: Any) -> dict[str, Any]:
    """C without an unresolved outcome: whatever is not affected is cleared.

    The engine is unchanged; its verdict is read by a binary consumer, the
    way a tool without a third value reports it.
    """
    decision = policies.openpulse(dep, events, **kw)
    outcome = AFFECTED if decision["outcome"] == AFFECTED else CLEARED
    return {"outcome": outcome, "relationship": decision["relationship"]}


def no_curated_identity_policy(dep: dict[str, Any], events: list[Any], **kw: Any):
    with no_curated_identity():
        decision = policies.openpulse(dep, events, **kw)
    return {k: v for k, v in decision.items() if k != "justification"}


def name_only_policy(dep: dict[str, Any], events: list[Any], **kw: Any):
    """No curated identity, and an unresolved identity read as unrelated:
    OpenPulse's scope and completeness rules over name-based identity."""
    with no_curated_identity():
        decision = policies.openpulse(dep, events, unresolved_identity="unrelated", **kw)
    return {k: v for k, v in decision.items() if k != "justification"}


POST_HOC = {
    "C-posthoc-binary": binary,
    "C-posthoc-no-curated-identity": no_curated_identity_policy,
    "C-posthoc-name-identity": name_only_policy,
}


def _post_hoc_rows(path: Path, max_age_days: int) -> dict[str, list[dict[str, Any]]]:
    dataset = load_json(path)
    known = {name: replay.replay(spec) for name, spec in dataset["events"].items()}
    max_age = timedelta(days=max_age_days)
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in POST_HOC}
    for case in dataset["cases"]:
        names = case["events"]
        events = [known[n] for n in names if known[n] is not None]
        as_of = max(replay.as_of_time(dataset["events"][n]) for n in names)
        for name, policy in POST_HOC.items():
            decision = policy(case["dependency"], events, as_of=as_of, max_evidence_age=max_age)
            rows[name].append(
                {
                    "case": case["id"],
                    "event": "+".join(names),
                    "class": dataset["events"][names[0]]["class"],
                    "independent": bool(case.get("independent_label", False)),
                    "basis": harness._completeness_basis(events),
                    "identity": harness._identity_status(case["dependency"]),
                    "label": case["label"],
                    **decision,
                }
            )
    return rows


# --- the run -----------------------------------------------------------------


def _block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    encoded = [r for r in rows if r.get("encoded") is not False]
    return {
        "overall": metrics.summarise(rows),
        # R only: its metrics where it had a representation at all.
        "overall_encoded_only": (
            None
            if len(encoded) == len(rows)
            else (metrics.summarise(encoded) if encoded else "not evaluable: no event encoded")
        ),
        "categories": {c: sum(1 for r in rows if category(r) == c) for c in CATEGORIES},
        "by_class": metrics.stratify(rows, "class"),
        "by_identity_status": metrics.stratify(rows, "identity"),
        "by_completeness_basis": metrics.stratify(rows, "basis"),
    }


def evaluate(path: Path, comparators: str = "off", max_age_days: int = 90) -> dict[str, Any]:
    with comparators_for(comparators) as bridges:
        registered = harness._run(path, max_age_days, bridges)
    post_hoc = _post_hoc_rows(path, max_age_days)
    pairs = []
    for name, rows in [*registered["pairs"].items(), *post_hoc.items()]:
        for row in rows:
            pairs.append(
                {
                    "policy": name,
                    "case": row["case"],
                    "event": row["event"],
                    "class": row["class"],
                    "identity": row["identity"],
                    "basis": row["basis"],
                    "label": row["label"],
                    "outcome": row["outcome"],
                    "category": category(row),
                    "relationship": row.get("relationship"),
                    "reason": row.get("reason"),
                }
            )
    return {
        "dataset": registered["dataset"],
        "dataset_version": registered["dataset_version"],
        "dataset_file": relative(path),
        "dataset_sha256": sha256(path),
        "max_evidence_age_days": max_age_days,
        "comparators": registered["comparators"],
        "encodings": {k: v for k, v in registered["encodings"].items() if k != "loss"},
        "events_not_known_at_replay": registered["events_not_known_at_replay"],
        "registered": {name: _block(rows) for name, rows in registered["pairs"].items()},
        "registered_analysis": {
            "all_labels_illustrative": registered["registration"]["all_labels_illustrative"],
            "independent_labels_only": {
                k: registered["registration"]["registered"][k]
                for k in ("valid", "validity", "population", "pairs")
            },
        },
        "post_hoc": {name: _block(rows) for name, rows in post_hoc.items()},
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", nargs="?", default="retro", choices=sorted(DATASETS))
    parser.add_argument("--comparators", choices=("off", "required"), default="off")
    parser.add_argument("--out", type=Path, default=RESULTS)
    args = parser.parse_args()
    result = evaluate(DATASETS[args.dataset], args.comparators)
    write_json(args.out / args.dataset / "evaluation.json", result)
    for group in ("registered", "post_hoc"):
        for name, block in result[group].items():
            c = block["categories"]
            print(
                f"{name:30} FC={c['false_clear']:3} FP={c['false_positive']:3} "
                f"unres={c['unresolved']:3} miss={c['silent_miss']:3} "
                f"ok={c['correct_affected'] + c['correct_unaffected']:3}"
            )


if __name__ == "__main__":
    main()
