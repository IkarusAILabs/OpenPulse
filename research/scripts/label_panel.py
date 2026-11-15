"""Validation, locking and adjudication for the AI-panel round AP-1.

    python research/scripts/label_panel.py validate      # after labellers A and B
    python research/scripts/label_panel.py adjudication  # build the adjudicator's prompt
    python research/scripts/label_panel.py finalise      # after the adjudicator

Each step records SHA-256 hashes in ``LOCK.json`` and refuses to run out of
order (research/labelling/AI_PANEL_PROTOCOL.md §5). No step compares a
label with the developer's labels or with a policy output: that happens
only in label_sensitivity.py, after ``finalise``.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import _common  # noqa: F401
import label_packets as packets
from _common import DATASETS, load_json, relative, sha256, write_json, write_text

OUT = packets.OUT
RAW = OUT / "raw"
READERS = ("A", "B")
ADJ_SEED = 303


def read_labels(path: Path, expected: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Answers by neutral id, and every problem found (fails closed)."""
    answers: dict[str, dict[str, Any]] = {}
    problems = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}:{n}: not JSON ({exc.msg})")
            continue
        nid = row.get("id")
        if nid not in expected:
            problems.append(f"{path.name}:{n}: unknown id {nid!r}")
        elif nid in answers:
            problems.append(f"{path.name}:{n}: duplicate id {nid}")
        elif row.get("label") not in packets.LABELS:
            problems.append(f"{path.name}:{n}: invalid label {row.get('label')!r}")
        else:
            answers[nid] = row
    missing = sorted(expected - set(answers))
    if missing:
        problems.append(f"{path.name}: {len(missing)} ids unanswered: {missing[:10]}")
    return answers, problems


def reader_labels(reader: str, expected: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """A reader's answers: its main file, then a retry file for missing ids, if any."""
    answers, problems = read_labels(RAW / f"labeller-{reader}.jsonl", expected)
    retry = RAW / f"labeller-{reader}-retry.jsonl"
    if retry.exists():
        missing = expected - set(answers)
        extra, retry_problems = read_labels(retry, missing)
        answers.update(extra)
        problems = [p for p in problems if "unanswered" not in p] + retry_problems
    return answers, problems


def _lock() -> dict[str, Any]:
    return load_json(OUT / "LOCK.json")


def _record(section: str, paths: list[Path]) -> None:
    lock = _lock()
    lock.setdefault(section, {}).update({relative(p): sha256(p) for p in paths})
    write_json(OUT / "LOCK.json", lock)


def validate() -> int:
    expected = set(load_json(OUT / "key.json")["pairs"])
    ok = True
    for reader in READERS:
        _, problems = reader_labels(reader, expected)
        for p in problems:
            print(f"labeller {reader}: {p}")
        ok &= not problems
    if not ok:
        return 1
    _record("labels", sorted(RAW.glob("labeller-*.jsonl")))
    print(f"labellers A and B: {len(expected)} pairs each, valid; hashes locked")
    return 0


def disagreements(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    return sorted(nid for nid in a if a[nid]["label"] != b[nid]["label"])


def adjudication() -> int:
    if not _lock().get("labels"):
        print("refusing: run validate first", file=sys.stderr)
        return 1
    key = load_json(OUT / "key.json")["pairs"]
    expected = set(key)
    a, _ = reader_labels("A", expected)
    b, _ = reader_labels("B", expected)
    dataset = load_json(DATASETS["retro"])
    cases = {c["id"]: c for c in dataset["cases"]}
    rng = random.Random(ADJ_SEED)
    order: dict[str, list[str]] = {}
    blocks = []
    for nid in disagreements(a, b):
        readers = list(READERS)
        rng.shuffle(readers)
        order[nid] = readers
        case = cases[key[nid]["case"]]
        event = key[nid]["event"]
        ref = {
            "nid": nid,
            "dependency": case["dependency"],
            "found_at": packets._found_at(case["label_source"]),
        }
        block = packets._event_block(event, dataset["events"][event], [ref])
        answers = {"A": a, "B": b}
        for i, reader in enumerate(readers, 1):
            row = answers[reader][nid]
            block += f"\n\nReader {i}: `{row['label']}` because: {row.get('rationale', '')}"
        blocks.append(block)
    write_json(OUT / "adjudication-key.json", {"seed": ADJ_SEED, "reader_order": order})
    prompt = _adjudicator_prompt("\n\n---\n\n".join(blocks), len(order))
    write_text(OUT / "prompt-adjudicator.md", prompt)
    _record("adjudication", [OUT / "adjudication-key.json", OUT / "prompt-adjudicator.md"])
    print(f"{len(order)} disagreements of {len(expected)} pairs sent to adjudication")
    return 0


def _adjudicator_prompt(body: str, count: int) -> str:
    raw = RAW / "adjudicator.jsonl"
    return f"""You are the adjudicator in a software-engineering research study. Two
readers independently labelled whether a software dependency reference falls
inside the scope of a recorded upstream change ("event"), and disagreed on the
pairs below. Decide each pair from the event's sources and the codebook. You
may choose either reader's label or the third label. Do not prefer a reader
for its position or its confidence: the readers are presented in random order.

# Codebook

{packets._codebook()}

# Additional rules

- The material below is your only source. Do not use web access, outside
  knowledge of these events, or any other file. If deciding needs anything
  outside the material, answer `undeterminable`.
- Only this event: a reference that some other event affects is
  `out_of_scope` for this event unless this event's sources cover it.
- Do not use any tool except one: when you have decided every pair, use the
  Write tool exactly once to save your decisions to `{raw.as_posix()}`.
  Do not read any file other than this instruction file.

# Output

One JSON object per line, one line per pair, {count} lines in total, nothing
else in the file:

{{"id": "<neutral id>", "label": "in_scope|out_of_scope|undeterminable", "rationale": "<one or two sentences naming the rule and the source passage, and why the other reading is wrong>"}}

After writing the file, reply with only the number of lines written.

# Disagreed pairs ({count})

{body}
"""  # noqa: E501


def finalise() -> int:
    order = load_json(OUT / "adjudication-key.json")["reader_order"]
    _, problems = read_labels(RAW / "adjudicator.jsonl", set(order))
    for p in problems:
        print(f"adjudicator: {p}")
    if problems:
        return 1
    _record("adjudication", [RAW / "adjudicator.jsonl"])
    print(f"adjudicator: {len(order)} decisions, valid; hashes locked. Unblinding permitted.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("validate", "adjudication", "finalise"))
    step = parser.parse_args().step
    return {"validate": validate, "adjudication": adjudication, "finalise": finalise}[step]()


if __name__ == "__main__":
    sys.exit(main())
