"""``openpulse-consumer check FILE...``: validate JSONL files of evidence contracts.

Exit 0 when every document is a valid contract of the version it declares,
1 when any is not, 2 when a file cannot be read. One line per document,
then a count; never a pass by omission (an empty file is an error).
"""

from __future__ import annotations

import argparse
import sys

from openpulse_consumer import __version__
from openpulse_consumer.contract import check, read_jsonl, supported_versions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="openpulse-consumer",
        description="Validate OpenPulse evidence contracts without OpenPulse.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("check", help="validate JSONL files of contracts")
    run.add_argument("files", nargs="+", help="JSONL: one contract per line")
    sub.add_parser("versions", help="list the contract versions this consumer reads")
    args = parser.parse_args(argv)

    if args.command == "versions":
        for version in supported_versions():
            print(version)
        return 0

    valid = invalid = 0
    for name in args.files:
        try:
            documents = list(read_jsonl(name))
        except (OSError, ValueError) as exc:
            print(f"{name}: cannot be read: {exc}", file=sys.stderr)
            return 2
        if not documents:
            print(f"{name}: no contract in the file", file=sys.stderr)
            return 2
        for number, doc in documents:
            if doc is None:
                invalid += 1
                print(f"{name}:{number}: INVALID: not JSON")
                continue
            result = check(doc)
            if result.valid:
                valid += 1
                print(f"{name}:{number}: valid contract {result.version}")
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


if __name__ == "__main__":
    sys.exit(main())
