"""Validate a labelled case set against research/dataset/schema.json (DATASET_CARD.md).

    python research/scripts/validate_dataset.py [retro|dev|<path> ...]

Checks what JSON Schema cannot: unique case ids, every case's events
exist, every event fixture directory exists and names its sources, the
case file matches its recorded SHA-256 (when one is recorded), and the
label vocabulary. Exits 1 with every problem listed; never repairs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from _common import DATASETS, RESEARCH, ROOT, load_json, relative, sha256

SCHEMA = RESEARCH / "dataset" / "schema.json"
LABELS = ("in_scope", "out_of_scope", "undeterminable")
#: Event classes in use. The two case sets use different taxonomies (the
#: development set says lifecycle where the retrospective study says eol;
#: DATASET_CARD.md §3), so per-class results do not compare across them.
CLASSES = (
    "archival",
    "breaking-change",
    "compromised",
    "deprecation",
    "distribution",
    "eol",
    "licence",
    "lifecycle",
    "relocation",
)


def _schema_problems(data: Any) -> list[str]:
    try:
        import jsonschema
    except ImportError:  # the runtime lock does not carry it; structural checks below still run
        return []
    validator = jsonschema.Draft202012Validator(load_json(SCHEMA))
    return [
        f"schema: {'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def _fixture_dir(path: Path, fixture: str) -> Path:
    """Fixtures are named relative to the case file, or as data/fixtures names."""
    local = (path.parent / fixture).resolve()
    return local if local.exists() else ROOT / "data" / "fixtures" / fixture


def validate(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        data = load_json(path)
    except (OSError, ValueError) as exc:
        return [f"unreadable: {exc}"]
    problems += _schema_problems(data)
    events = data.get("events") or {}
    cases = data.get("cases") or []
    for field in ("dataset", "version", "status", "events", "cases"):
        if field not in data:
            problems.append(f"missing top-level field {field!r}")
    for name, spec in events.items():
        if spec.get("source") == "event":
            fixture = _fixture_dir(path, str(spec.get("fixture", "")))
            if not (fixture / "event.json").exists():
                problems.append(f"event {name}: fixture {spec.get('fixture')} has no event.json")
        if spec.get("class") not in CLASSES:
            problems.append(f"event {name}: class {spec.get('class')!r} not in {CLASSES}")
        if not spec.get("as_of"):
            problems.append(f"event {name}: no as_of (knowledge cut)")
    seen: set[str] = set()
    for case in cases:
        cid = case.get("id", "<no id>")
        if cid in seen:
            problems.append(f"case {cid}: duplicate id")
        seen.add(cid)
        if case.get("label") not in LABELS:
            problems.append(f"case {cid}: label {case.get('label')!r} not in {LABELS}")
        for field in ("rationale", "label_source"):
            if not str(case.get(field) or "").strip():
                problems.append(f"case {cid}: empty {field}")
        for event in case.get("events") or []:
            if event not in events:
                problems.append(f"case {cid}: unknown event {event}")
        if not case.get("events"):
            problems.append(f"case {cid}: no events")
        dep = case.get("dependency") or {}
        if dep.get("kind") == "image" and not dep.get("ref"):
            problems.append(f"case {cid}: image dependency without ref")
        if dep.get("kind") == "package" and not dep.get("package"):
            problems.append(f"case {cid}: package dependency without name")
        if case.get("independent_label") and case.get("labelled_by") in (None, "L1"):
            problems.append(
                f"case {cid}: marked independent but labelled by {case.get('labelled_by')}"
            )
    recorded = path.with_name(path.name + ".sha256")
    if recorded.exists():
        expected = recorded.read_text(encoding="utf-8").split()[0]
        if sha256(path) != expected:
            problems.append(f"SHA-256 {sha256(path)} differs from recorded {expected}")
    return problems


def summary(path: Path) -> dict[str, Any]:
    data = load_json(path)
    return {
        "file": relative(path),
        "dataset": data["dataset"],
        "version": data["version"],
        "sha256": sha256(path),
        "sha256_recorded": path.with_name(path.name + ".sha256").exists(),
        "events": len(data["events"]),
        "cases": len(data["cases"]),
        "independent_labels": sum(1 for c in data["cases"] if c.get("independent_label")),
    }


def main(argv: list[str]) -> int:
    targets = [DATASETS.get(a, Path(a)) for a in argv] or list(DATASETS.values())
    failed = False
    for path in targets:
        problems = validate(Path(path))
        if problems:
            failed = True
            print(f"INVALID {relative(Path(path))}: {len(problems)} problem(s)")
            for problem in problems:
                print(f"  - {problem}")
        else:
            s = summary(Path(path))
            print(
                f"valid {s['file']}: {s['dataset']} v{s['version']}, {s['events']} events, "
                f"{s['cases']} cases, {s['independent_labels']} independently labelled, "
                f"sha256 {s['sha256'][:12]}"
            )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
