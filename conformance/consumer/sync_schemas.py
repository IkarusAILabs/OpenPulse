"""Copy OpenPulse's published contract schemas into the consumer package.

    python conformance/consumer/sync_schemas.py          # copy
    python conformance/consumer/sync_schemas.py --check  # fail if they differ

The consumer ships the schemas byte for byte as published in
``schemas/evidence-contract/<dir>/schema.json``; OpenPulse's test suite runs
``--check`` so a new or changed schema cannot ship without the consumer.
Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "schemas" / "evidence-contract"
TARGET = HERE / "openpulse_consumer" / "schemas"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def differences() -> list[str]:
    """Schemas that are missing, extra or different in the consumer."""
    published = {p.parent.name: p for p in SOURCE.glob("*/schema.json")}
    bundled = {p.parent.name: p for p in TARGET.glob("*/schema.json")}
    found = [f"missing: {name}" for name in sorted(set(published) - set(bundled))]
    found += [f"extra: {name}" for name in sorted(set(bundled) - set(published))]
    found += [
        f"different: {name}"
        for name in sorted(set(published) & set(bundled))
        if _text(published[name]) != _text(bundled[name])
    ]
    return found


def main(argv: list[str]) -> int:
    if "--check" in argv:
        found = differences()
        for line in found:
            print(line, file=sys.stderr)
        return 1 if found else 0
    for source in sorted(SOURCE.glob("*/schema.json")):
        target = TARGET / source.parent.name / "schema.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_text(source), encoding="utf-8", newline="\n")
    print(f"copied {len(list(SOURCE.glob('*/schema.json')))} schemas")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
