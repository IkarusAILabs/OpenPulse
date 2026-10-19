"""Fail when the lockfile drifts from the environment or the declared floors.

Two tripwires, both stdlib-only and deterministic:

1. Installed-tree drift: CI installs from pyproject floors, so a passing
   run might test dependency versions nobody reviewed. The lock is the
   reviewed set; this fails the run on drift.
2. Floor drift: a lock pin BELOW a pyproject ``>=`` floor means CI tests
   a version the project says it does not support (F4). Every floor must
   be satisfied by its lock pin, and every floor must be present in the
   lock at all.
"""

from __future__ import annotations

import importlib.metadata
import re
import sys
from pathlib import Path

_PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)")
#: pyproject ``"name>=1.2.3"`` requirement entries (runtime + dev extras).
_FLOOR = re.compile(r'"([A-Za-z0-9_.\-]+)\s*>=\s*([0-9][^"]*)"')


def _read_pins(lock_path: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in Path(lock_path).read_text(encoding="utf-8").splitlines():
        match = _PIN.match(line.strip())
        if match:
            pins[match.group(1).lower()] = match.group(2)
    return pins


def _read_floors(pyproject_path: str = "pyproject.toml") -> dict[str, str]:
    floors: dict[str, str] = {}
    lines = Path(pyproject_path).read_text(encoding="utf-8").splitlines()
    in_project = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            # Scan only the [project] table (runtime + optional deps);
            # build-system floors do not belong in requirements.lock.
            in_project = stripped.startswith("[project]") or stripped.startswith("[project.")
            continue
        if not in_project:
            continue
        for name, floor in _FLOOR.findall(line):
            floors[name.lower()] = floor
    return floors


def _version_tuple(value: str) -> tuple[int, ...]:
    """Leading numeric release segments of a version, for ``>=`` compare.

    Non-numeric suffixes (pre-release tags, local versions) are dropped:
    the floors under test are plain X.Y.Z minimums.
    """
    match = re.match(r"(\d+(?:\.\d+)*)", value.strip())
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def check(lock_path: str = "requirements.lock") -> list[str]:
    pins = _read_pins(lock_path)
    floors = _read_floors()
    problems: list[str] = []

    for name, pin in sorted(pins.items()):
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            problems.append(f"{name}=={pin} is locked but not installed")
            continue
        if installed != pin:
            problems.append(f"{name}: installed {installed} != locked {pin}")

    for name, floor in sorted(floors.items()):
        pin = pins.get(name)
        if pin is None:
            problems.append(f"{name}: pyproject floor >={floor} has no requirements.lock pin")
            continue
        if _version_tuple(pin) < _version_tuple(floor):
            problems.append(f"{name}: locked {pin} is below pyproject floor >={floor}")

    return problems


def main() -> int:
    problems = check()
    for problem in problems:
        print(f"lock drift: {problem}")
    if problems:
        print(f"{len(problems)} lock/pyproject problem(s) found")
        return 1
    print("lock verified: installed tree matches requirements.lock and pyproject floors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
