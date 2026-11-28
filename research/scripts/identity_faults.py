"""Wrong curated identity mappings, injected one reference at a time.

    python research/scripts/identity_faults.py [retro|dev]

OpenPulse trusts a curated (VERIFIED) mapping: it has no way to tell a
wrong one from a right one (TR-2026-01 §8; THREATS_TO_VALIDITY.md). This
script measures what that trust costs on the case set, with two faults:

- ``misattributed``: a reference that has a curated identity is curated to
  a project that is not the event's (an alias to an unrelated project);
- ``collided``: an out-of-scope image reference that does not resolve to
  the event's project is curated to it (a look-alike wrongly aliased).

Each fault is one explicit alias for one reference, set in the same table
the engine reads (``core.entities.resolve.EXPLICIT_ALIASES``) and removed
afterwards; the engine's code is unchanged. Package references are curated
through the catalogue's package map instead and are not injected: they are
counted as such. Writes research/results/<dataset>/identity_faults.json.
"""

from __future__ import annotations

import argparse
import contextlib
from collections import Counter
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from typing import Any

import _common  # noqa: F401  (first: puts evaluation/ and conformance/ on sys.path)
import policies
import replay
import run as harness
from _common import DATASETS, RESULTS, load_json, relative, sha256, write_json
from evaluate import category

#: A slug no catalogue entry or event uses: the target of a misattribution.
WRONG_PROJECT = "injected-unrelated-project"


@contextlib.contextmanager
def curated_alias(ref: str, slug: str) -> Iterator[None]:
    """One explicit (VERIFIED) alias from ``ref`` to ``slug``, then restored."""
    from core.entities.resolve import EXPLICIT_ALIASES, normalize_ref

    key = normalize_ref(ref)
    had, previous = key in EXPLICIT_ALIASES, EXPLICIT_ALIASES.get(key)
    EXPLICIT_ALIASES[key] = slug
    try:
        yield
    finally:
        if had:
            EXPLICIT_ALIASES[key] = previous
        else:
            del EXPLICIT_ALIASES[key]


def _resolved(dep: dict[str, Any]) -> str:
    from core.entities.resolve import resolve_project

    return resolve_project(str(dep["ref"]))


def run(path: Path, max_age_days: int = 90) -> dict[str, Any]:
    dataset = load_json(path)
    known = {name: replay.replay(spec) for name, spec in dataset["events"].items()}
    max_age = timedelta(days=max_age_days)
    faults: dict[str, list[dict[str, Any]]] = {"misattributed": [], "collided": []}
    skipped: Counter = Counter()
    for case in dataset["cases"]:
        dep, names = case["dependency"], case["events"]
        events = [known[n] for n in names if known[n] is not None]
        if not events:
            continue
        as_of = max(replay.as_of_time(dataset["events"][n]) for n in names)
        identity = harness._identity_status(dep)
        if dep["kind"] != "image":
            skipped["package reference (catalogue package map, not injected)"] += 1
            continue
        project = events[0].project_slug
        if identity == "curated":
            fault, target = "misattributed", WRONG_PROJECT
        elif case["label"] == "out_of_scope" and _resolved(dep) != project:
            fault, target = "collided", project
        else:
            skipped["image reference with no applicable fault"] += 1
            continue

        def decide() -> dict[str, Any]:
            return policies.openpulse(dep, events, as_of=as_of, max_evidence_age=max_age)

        before = decide()
        with curated_alias(str(dep["ref"]), target):
            after = decide()
        row = {"label": case["label"]}
        faults[fault].append(
            {
                "case": case["id"],
                "event": "+".join(names),
                "ref": dep["ref"],
                "label": case["label"],
                "aliased_to": target,
                "before": category({**row, "outcome": before["outcome"]}),
                "after": category({**row, "outcome": after["outcome"]}),
                "relationship_after": after["relationship"],
            }
        )
    summary = {
        name: {
            "injected": len(rows),
            "changed": sum(1 for r in rows if r["before"] != r["after"]),
            "transitions": dict(
                sorted(
                    Counter(
                        f"{r['before']} -> {r['after']}" for r in rows if r["before"] != r["after"]
                    ).items()
                )
            ),
            "after": dict(sorted(Counter(r["after"] for r in rows).items())),
        }
        for name, rows in faults.items()
    }
    return {
        "dataset": dataset["dataset"],
        "dataset_file": relative(path),
        "dataset_sha256": sha256(path),
        "wrong_project": WRONG_PROJECT,
        "summary": summary,
        "not_injected": dict(sorted(skipped.items())),
        "faults": faults,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", nargs="?", default="retro", choices=sorted(DATASETS))
    parser.add_argument("--results", type=Path, default=RESULTS)
    args = parser.parse_args()
    result = run(DATASETS[args.dataset])
    write_json(args.results / args.dataset / "identity_faults.json", result)
    for name, block in result["summary"].items():
        print(
            f"{name:14} injected={block['injected']:3} changed={block['changed']:3} "
            f"{block['after']}"
        )


if __name__ == "__main__":
    main()
