"""Fail when installed distributions drift from requirements.lock pins.

Threat: floated transitive deps — CI installs from pyproject floors,
so a passing run might test dependency versions nobody reviewed. The
lock is the reviewed set; this tripwire fails the run on drift.
stdlib only, deterministic.
"""

from __future__ import annotations

import importlib.metadata
import re
import sys
from pathlib import Path

_PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)")


def check(lock_path: str = "requirements.lock") -> list[str]:
    pins: dict[str, str] = {}
    for line in Path(lock_path).read_text(encoding="utf-8").splitlines():
        match = _PIN.match(line.strip())
        if match:
            pins[match.group(1).lower()] = match.group(2)
    problems = []
    for name, pin in sorted(pins.items()):
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            problems.append(f"{name}=={pin} is locked but not installed")
            continue
        if installed != pin:
            problems.append(f"{name}: installed {installed} != locked {pin}")
    return problems


def main() -> int:
    problems = check()
    for problem in problems:
        print(f"lock drift: {problem}")
    if problems:
        print(f"{len(problems)} locked distribution(s) differ from the installed tree")
        return 1
    print("lock verified: installed tree matches requirements.lock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
