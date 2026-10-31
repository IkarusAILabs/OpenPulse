"""Run every registered policy over a labelled case set (PROTOCOL.md).

Run from the repository root:

    python evaluation/run.py [--cases evaluation/cases/dev-2026-10.json]
                             [--max-evidence-age-days 90]
                             [--require-comparators] [--require-encodings]
                             [--inventories <file>] [--annotations <file>]

Writes ``evaluation/results/<dataset>.json``: the dataset's SHA-256 and
the commit, every policy's metrics overall and by event class and by
label independence, and every pair's outcome, so that each incorrect or
unresolved decision can be inspected. Offline and deterministic.

Policy R reads each event's frozen OSV/OpenVEX encoding, named in the
case set with its SHA-256 (``representations/ENCODING.md``). The review
burden W1-W2 needs the participating inventories (``--inventories``:
``{"window": {"start", "end"}, "inventories": {name: [dependency]}}``);
W3, D1 and D2 need the annotators' records (``--annotations``:
``{"timed_reviews": [...], "completeness_declarations": [...],
"identity_mappings": [...]}``, as ``registration`` documents them).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import existing_representation  # noqa: E402
import metrics  # noqa: E402
import policies  # noqa: E402
import registration  # noqa: E402
import replay  # noqa: E402
import strong_baseline  # noqa: E402
from ecosystem_versions import Comparators  # noqa: E402

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


def _completeness_basis(events: list[Any]) -> str:
    """The basis of each event's admitted completeness declaration, or partial.

    REGISTRATION.md section 4 stratifies every result by it, so that no
    basis is trusted on the strength of another's results.
    """
    bases = sorted(
        {
            str(e.scope.basis) if e.scope is not None and e.scope.admits_negative() else "partial"
            for e in events
        }
    )
    return "+".join(bases) or "none"


def _identity_status(dep: dict[str, Any]) -> str:
    """How the dependency's identity is established: curated, self or heuristic."""
    from core.entities.identity import package_trust, resolution_trust

    if dep["kind"] == "image":
        trust = resolution_trust(str(dep["ref"]))
    else:
        trust = package_trust(str(dep["package"]), dep.get("ecosystem"))
    if trust["identity_status"] != "VERIFIED":
        return "heuristic"
    return "curated" if trust["via"] in ("explicit", "catalog") else "self"


def load_encodings(dataset: dict[str, Any], required: bool = False) -> dict[str, dict[str, Any]]:
    """Every event's frozen R encoding, by event name, each hash verified.

    ``required`` is the registered run's setting: every event must name one.
    """
    encodings = {}
    for name, spec in dataset["events"].items():
        if "encoding" in spec:
            encodings[name] = existing_representation.load_encoding(spec["encoding"], name)
        elif required:
            raise ValueError(f"{name}: no frozen R encoding (REGISTRATION.md section 10)")
    return encodings


def _cycles(
    dataset: dict[str, Any], known: dict[str, Any], window: dict[str, str]
) -> list[tuple[datetime, dict[str, Any]]]:
    """Each weekly cycle's end and the events current then, as known then."""
    cycles = []
    for at in registration.weekly_cycles(
        date.fromisoformat(window["start"]), date.fromisoformat(window["end"])
    ):
        current = {}
        for name, event in known.items():
            if event is None or replay.as_of_time(dataset["events"][name]) > at:
                continue
            event = replay.knowledge_cut(event, at)
            if event is not None and event.is_current_record():
                current[name] = event
        cycles.append((at, current))
    return cycles


def run(
    path: Path = DEFAULT_CASES,
    max_evidence_age_days: int = 90,
    require_comparators: bool = False,
    require_encodings: bool = False,
    inventories: Path | None = None,
    annotations: Path | None = None,
) -> dict[str, Any]:
    """Every policy over one case set.

    ``require_comparators`` and ``require_encodings`` are the registered
    run's settings: it refuses to start unless every pinned ecosystem
    comparator is installed and every event has a frozen R encoding.
    """
    comparators = Comparators(required=require_comparators)
    strong_baseline.use_comparators(comparators)
    existing_representation.use_comparators(comparators)
    try:
        return _run(
            path,
            max_evidence_age_days,
            comparators,
            require_encodings,
            json.loads(inventories.read_text("utf-8")) if inventories else None,
            json.loads(annotations.read_text("utf-8")) if annotations else {},
        )
    finally:
        strong_baseline.use_comparators(None)
        existing_representation.use_comparators(None)
        existing_representation.use_encodings(None)
        comparators.close()


def _run(
    path: Path,
    max_evidence_age_days: int,
    comparators: Comparators,
    require_encodings: bool = False,
    inventories: dict[str, Any] | None = None,
    annotations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = path.read_bytes()
    dataset = json.loads(raw)
    validate(dataset)
    encodings = load_encodings(dataset, required=require_encodings)
    max_age = timedelta(days=max_evidence_age_days)
    known = {name: replay.replay(spec) for name, spec in dataset["events"].items()}
    existing_representation.use_encodings(
        {known[name].id: enc for name, enc in encodings.items() if known[name] is not None}
    )
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
                    "basis": _completeness_basis(events),
                    "identity": _identity_status(case["dependency"]),
                    "label": case["label"],
                    **decision,
                }
            )
    inputs: dict[str, Any] = {
        "dependencies": {case["id"]: case["dependency"] for case in dataset["cases"]},
        "admitted_declarations": {
            name: event.scope.basis
            for name, event in known.items()
            if event is not None and event.scope is not None and event.scope.admits_negative()
        },
        **{k: v for k, v in (annotations or {}).items() if k in _ANNOTATIONS},
    }
    if inventories is not None:
        burden_policies = {name: policies.POLICIES[name] for name in registration.BURDEN_POLICIES}
        inputs["burden"] = registration.inventory_burden(
            burden_policies,
            inventories["inventories"],
            _cycles(dataset, known, inventories["window"]),
            max_age,
        )
    encodings_complete = len(encodings) == len(dataset["events"])
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
                "by_completeness_basis": metrics.stratify(r, "basis"),
                "by_identity_status": metrics.stratify(r, "identity"),
            }
            for name, r in rows.items()
        },
        "comparators": {"complete": comparators.complete, "status": comparators.status},
        "encodings": {
            "complete": encodings_complete,
            "sha256": {
                name: spec["encoding"]["sha256"] if "encoding" in spec else None
                for name, spec in dataset["events"].items()
            },
            "loss": registration.encoding_loss(dataset["events"], encodings),
        },
        "registration": {
            "thresholds": registration.thresholds(),
            # The registered population: independently labelled pairs only.
            "registered": registration.analyse(
                rows,
                independent_only=True,
                comparators_complete=comparators.complete,
                encodings_complete=encodings_complete,
                inputs=inputs,
            ),
            # The same analysis over every label: illustrative, never evidence.
            "all_labels_illustrative": registration.analyse(
                rows, independent_only=False, inputs=inputs
            ),
        },
        "pairs": rows,
    }


_ANNOTATIONS = ("timed_reviews", "completeness_declarations", "identity_mappings")

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
    parser.add_argument(
        "--require-comparators",
        action="store_true",
        help="refuse to run without every pinned ecosystem comparator (the registered run)",
    )
    parser.add_argument(
        "--require-encodings",
        action="store_true",
        help="refuse to run unless every event has a frozen R encoding (the registered run)",
    )
    parser.add_argument("--inventories", type=Path, help="inventories and window for W1-W2")
    parser.add_argument("--annotations", type=Path, help="annotators' records for W3, D1, D2")
    args = parser.parse_args()
    result = run(
        args.cases,
        args.max_evidence_age_days,
        args.require_comparators,
        args.require_encodings,
        args.inventories,
        args.annotations,
    )
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
            f"{population} ({block['validity']}): {primary['verdict']}; "
            f"H2 gain {primary['H2_resolution_superiority'].get('difference')}; "
            f"G1 {guard['G1_silent_miss']['pass']}, G2 {guard['G2_unresolved_vs_B']['pass']}, "
            f"G4 {guard['G4_review_burden']['pass']}; "
            f"S3 C-R {block['secondary']['S3_C_vs_R_resolution'].get('difference')}"
        )
