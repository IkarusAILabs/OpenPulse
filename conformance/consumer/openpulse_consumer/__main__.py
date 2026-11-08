"""``openpulse-consumer``: validate and summarise JSONL files of evidence contracts.

``check FILE...``: exit 0 when every document is a valid contract of the
version it declares and its content hash verifies, 1 when any is not, 2
when a file cannot be read. One line per document, then a count; never a
pass by omission (an empty file is an error).

``summary [--json] FILE...``: the outcome of every valid document, with
relationship, inspection coverage and trust counted apart (P4). The exit
codes are the same as ``check``'s: 0 means every document was read and
verified, not that any outcome is favourable.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from openpulse_consumer import __version__
from openpulse_consumer.contract import check, read_jsonl, supported_versions
from openpulse_consumer.summary import Summary


def _read(names: list[str]) -> list[tuple[str, int, Any]] | None:
    """Every (file, line, document), or None after reporting an unreadable file."""
    found = []
    for name in names:
        try:
            documents = list(read_jsonl(name))
        except (OSError, ValueError) as exc:
            print(f"{name}: cannot be read: {exc}", file=sys.stderr)
            return None
        if not documents:
            print(f"{name}: no contract in the file", file=sys.stderr)
            return None
        found.extend((name, number, doc) for number, doc in documents)
    return found


def _check(documents: list[tuple[str, int, Any]]) -> int:
    valid = invalid = 0
    for name, number, doc in documents:
        if doc is None:
            invalid += 1
            print(f"{name}:{number}: INVALID: not JSON")
            continue
        result = check(doc)
        if result.valid:
            valid += 1
            print(f"{name}:{number}: valid contract {result.version}, content hash verified")
            continue
        invalid += 1
        label = f"contract {result.version}" if result.version else "not a contract"
        print(f"{name}:{number}: INVALID ({label}): {len(result.errors)} problem(s)")
        for error in result.errors[:20]:
            print(f"  {error}")
        if len(result.errors) > 20:
            print(f"  ... and {len(result.errors) - 20} more")
    print(f"{valid} valid, {invalid} invalid")
    return 1 if invalid else 0


def _counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{name} {count}" for name, count in counts.items())


def _summary(documents: list[tuple[str, int, Any]], as_json: bool) -> int:
    summary = Summary()
    places = []
    for name, number, doc in documents:
        if summary.add(doc) is not None:
            places.append(f"{name}:{number}")
        elif not as_json:
            print(f"{name}:{number}: INVALID, not summarised (run check for the reasons)")
    if as_json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return 1 if summary.invalid else 0

    print(f"documents: {summary.valid} valid and summarised, {summary.invalid} invalid")
    print(f"relationship: {_counts(summary.relationships)}")
    print(f"inspection coverage: {_counts(summary.coverage)}")
    print(f"trust records: {_counts(summary.trust_records)}")
    print(f"trust not checked: {summary.trust_not_checked} document(s)")
    print(f"documents with open items: {summary.with_open_items} of {summary.valid}")
    for place, result in zip(places, summary.outcomes, strict=True):
        print(f"{place}: {result.dependency} / {result.event}: {result.relationship}")
        for item in result.open:
            print(f"  open: {item}")
    print("This is a summary of what the documents state, not a pass or fail.")
    return 1 if summary.invalid else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="openpulse-consumer",
        description="Validate and summarise OpenPulse evidence contracts without OpenPulse.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("check", help="validate JSONL files of contracts")
    run.add_argument("files", nargs="+", help="JSONL: one contract per line")
    summarise = sub.add_parser(
        "summary", help="count outcomes, coverage and trust apart, and list what is open"
    )
    summarise.add_argument("--json", action="store_true", help="machine-readable output")
    summarise.add_argument("files", nargs="+", help="JSONL: one contract per line")
    sub.add_parser("versions", help="list the contract versions this consumer reads")
    args = parser.parse_args(argv)

    if args.command == "versions":
        for version in supported_versions():
            print(version)
        return 0

    documents = _read(args.files)
    if documents is None:
        return 2
    if args.command == "check":
        return _check(documents)
    return _summary(documents, args.json)


if __name__ == "__main__":
    sys.exit(main())
