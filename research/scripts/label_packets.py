"""Blinded packets and prompts for the AI-panel labelling round AP-1.

    python research/scripts/label_packets.py

Mechanical, so that whoever runs it cannot shape what a labeller sees
(research/labelling/AI_PANEL_PROTOCOL.md §3). Writes, under
research/labelling/ai-panel-2026-11/:

- ``key.json``: neutral id -> case id and event (never given to a labeller);
- ``packet-A.md``, ``packet-B.md``: the same pairs in two shuffled orders;
- ``prompt-labeller-A.md``, ``prompt-labeller-B.md``: codebook, rules, packet;
- ``LOCK.json``: SHA-256 of the protocol, packets and prompts, written before
  any labeller runs. It refuses to overwrite a lock that already records labels.

Fails if a withheld value (a label, a rationale, a case id, a role) appears
in the data part of a packet.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from typing import Any

import _common  # noqa: F401
from _common import DATASETS, RESEARCH, ROOT, load_json, relative, sha256, write_json, write_text

ROUND = "AP-1"
OUT = RESEARCH / "labelling" / "ai-panel-2026-11"
PROTOCOL = RESEARCH / "labelling" / "AI_PANEL_PROTOCOL.md"
GUIDE = RESEARCH / "LABELING_GUIDE.md"
EVENTS = ROOT / "evaluation" / "retrospective" / "events"
EVIDENCE = ROOT / "evaluation" / "retrospective" / "evidence"
#: Evidence files the developer's labels relied on, by event (PILOT.md).
EVENT_EVIDENCE = {
    "LIC-4": "mongodb-release-tags.txt",
    "DIS-3": "openjdk-2025-deleted-tags.txt",
}
SEEDS = {"A": 101, "B": 202}
LABELS = ("in_scope", "out_of_scope", "undeterminable")


def neutral_id(case_id: str) -> str:
    return hashlib.sha256(f"{ROUND}:{case_id}".encode()).hexdigest()[:8]


def _found_at(label_source: str) -> str:
    """Where the reference was found, without the developer's file pointer."""
    return label_source.split(";", 1)[1].strip().removeprefix("reference ").strip()


def _event_block(name: str, spec: dict[str, Any], refs: list[dict[str, Any]]) -> str:
    fixture = json.loads((EVENTS / name / "event.json").read_text(encoding="utf-8"))
    lines = [f"## Event {name}: {fixture['title']}", ""]
    lines += [f"Knowledge date (as_of): {spec['as_of']}", ""]
    lines.append("Sources:")
    for e in fixture["evidences"]:
        src = e["source"]
        lines.append(f"- **{src['name']}** <{src['url']}>")
        lines.append(f"  - archive record: {src['acquisition_method']}")
        lines.append(f'  - archived quotation: "{e["excerpt"]}"')
    if name in EVENT_EVIDENCE:
        text = (EVIDENCE / EVENT_EVIDENCE[name]).read_text(encoding="utf-8").strip()
        lines += ["", f"Archived evidence file `{EVENT_EVIDENCE[name]}`:", "```", text, "```"]
    lines += ["", "References to label for this event:", ""]
    for r in refs:
        lines.append(f"- `{r['nid']}`: `{json.dumps(r['dependency'], sort_keys=True)}`")
        lines.append(f"  - found in: {r['found_at']}")
    return "\n".join(lines)


def build_packets(dataset: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    refs: dict[str, list[dict[str, Any]]] = {}
    key: dict[str, Any] = {}
    for case in dataset["cases"]:
        nid = neutral_id(case["id"])
        if nid in key:
            raise SystemExit(f"neutral id collision: {nid}")
        event = case["events"][0]
        key[nid] = {"case": case["id"], "event": event}
        refs.setdefault(event, []).append(
            {
                "nid": nid,
                "dependency": case["dependency"],
                "found_at": _found_at(case["label_source"]),
            }
        )
    packets = {}
    for reader, seed in SEEDS.items():
        rng = random.Random(seed)  # noqa: S311 - seeded, reproducible sampling; not a secret
        events = sorted(refs)
        rng.shuffle(events)
        blocks = []
        for name in events:
            order = sorted(refs[name], key=lambda r: r["nid"])
            rng.shuffle(order)
            blocks.append(_event_block(name, dataset["events"][name], order))
        packets[reader] = "\n\n".join(blocks)
    _check_blind(dataset, packets)
    return key, packets


def _check_blind(dataset: dict[str, Any], packets: dict[str, str]) -> None:
    withheld = set()
    for case in dataset["cases"]:
        withheld |= {case["id"], case["rationale"]}
    withheld |= set(LABELS)
    for reader, text in packets.items():
        leaks = sorted(v for v in withheld if v and v in text)
        if re.search(r"\b[A-Z]{3}-\d+-[sn]\d+\b", text):
            leaks.append("a case id pattern")
        if leaks:
            raise SystemExit(f"packet {reader} leaks withheld values: {leaks[:5]}")


def _codebook() -> str:
    guide = GUIDE.read_text(encoding="utf-8")
    start, end = guide.index("## 1. What you are deciding"), guide.index("## 4. What to record")
    return guide[start:end].strip()


def prompt(reader: str, packet: str, count: int) -> str:
    raw = OUT / "raw" / f"labeller-{reader}.jsonl"
    return f"""You are an annotator in a software-engineering research study. You label
whether a software dependency reference falls inside the scope of a recorded
upstream change ("event"). Work carefully and independently: another annotator
labels the same pairs separately, and your answers will be compared.

# Codebook

{_codebook()}

# Additional rules for this round

- The packet below is your only source. Do not use web access, outside
  knowledge of these events, or any other file. If deciding needs anything outside
  the packet, answer `undeterminable`.
- Only this event: a reference that some other event affects is
  `out_of_scope` for this event unless this event's sources cover it.
- Do not use any tool except one: when you have labelled every reference,
  use the Write tool exactly once to save your answers to
  `{raw.as_posix()}`. Do not read any file other than this
  instruction file.

# Output

One JSON object per line, one line per reference, {count} lines in total,
nothing else in the file:

{{"id": "<neutral id>", "label": "in_scope|out_of_scope|undeterminable", "rationale": "<one or two sentences naming the rule and the source passage>", "sources_used": ["<source name>"]}}

After writing the file, reply with only the number of lines written.

# Packet ({count} references)

{packet}
"""  # noqa: E501


def main() -> int:
    lock_path = OUT / "LOCK.json"
    if lock_path.exists() and load_json(lock_path).get("labels"):
        print(f"refusing: {relative(lock_path)} already records labels", file=sys.stderr)
        return 1
    path = DATASETS["retro"]
    dataset = load_json(path)
    key, packets = build_packets(dataset)
    write_json(OUT / "key.json", {"round": ROUND, "dataset_sha256": sha256(path), "pairs": key})
    hashes = {relative(PROTOCOL): sha256(PROTOCOL)}
    for reader, packet in packets.items():
        for name, text in (
            (f"packet-{reader}.md", packet),
            (f"prompt-labeller-{reader}.md", prompt(reader, packet, len(key))),
        ):
            write_text(OUT / name, text)
            hashes[relative(OUT / name)] = sha256(OUT / name)
    write_json(
        lock_path,
        {
            "round": ROUND,
            "dataset": relative(path),
            "dataset_sha256": sha256(path),
            "pairs": len(key),
            "before_labelling": hashes,
            "labels": {},
        },
    )
    print(f"{len(key)} pairs, {len(packets)} packets; lock {relative(lock_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
