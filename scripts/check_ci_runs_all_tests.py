"""Fail CI when the test suite excludes files via pytest ``--ignore`` (F7).

A test that is written but not run is not a test. The suite is expected
to run whole; the only escape hatch would be an explicit, documented
allow-list, which this guard deliberately does not provide.

The flag literal is assembled at runtime so this guard never matches
itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

WORKFLOW = Path(".github/workflows/ci.yml")
_IGNORE_FLAG = "--" + "ignore"


def main() -> int:
    text = WORKFLOW.read_text(encoding="utf-8")
    offenders = [line.strip() for line in text.splitlines() if _IGNORE_FLAG in line]
    if offenders:
        for line in offenders:
            print(f"CI excludes tests: {line}")
        return 1
    print("no test exclusions in CI: the whole suite runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
