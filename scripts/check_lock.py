"""Fail when the lockfile drifts from the environment or the declared floors.

Two tripwires, both stdlib-only and deterministic:

1. Installed-tree drift: CI installs from pyproject floors, so a passing
   run might test dependency versions nobody reviewed. The lock is the
   reviewed set; this fails the run on drift.
2. Floor drift: a lock pin BELOW a pyproject ``>=`` floor means CI tests
   a version the project says it does not support (F4). Every floor must
   be satisfied by its lock pin, and every floor must be present in the
   lock at all.

Optional extras keep their own lock beside the core one
(``requirements-mcp.lock`` for ``openpulse[mcp]``). Floors are checked
against every lock file in the repository; the installed tree only
against the locks named on the command line (default: the core lock), so
the main CI job need not install the extra. Pins may carry an environment
marker (``; sys_platform == 'win32'``, ``; python_full_version < '3.11'``)
and are only required where it holds. The lock files are hash-pinned
(``--hash`` continuation lines; see scripts/compile_locks.py).

3. With ``--exact`` (CI): the installed tree must also not contain any
   distribution the named locks don't list. "Locked but missing" alone let
   an unlisted transitive dependency (``typing-inspection``) float freely.
"""

from __future__ import annotations

import importlib.metadata
import re
import sys
from pathlib import Path

#: `name==version` up to whitespace, a marker, a comment or a line continuation.
_PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#\\]+)")
_MARKER = re.compile(r";\s*([^\\#]+)")
_PLATFORM = re.compile(r"sys_platform\s*==\s*[\"']([^\"']+)[\"']")
#: Installed by CI bootstrap, not by the project: never "unlocked" drift.
_TOOLING = {"pip", "setuptools", "wheel", "ikarus-openpulse", "openpulse"}
#: Every lock file the floors may be satisfied by (core first).
LOCK_FILES = ("requirements.lock", "requirements-mcp.lock")
#: pyproject ``"name>=1.2.3"`` requirement entries (runtime + dev extras).
_FLOOR = re.compile(r'"([A-Za-z0-9_.\-]+)\s*>=\s*([0-9][^"]*)"')


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _applies(marker: str) -> bool:
    """Does an environment marker hold here? (`packaging` is in the lock;
    without it, only `sys_platform == ...` is understood and anything else
    is assumed to apply.)"""
    try:
        from packaging.markers import Marker
    except ImportError:
        platform = _PLATFORM.search(marker)
        return platform is None or platform.group(1) == sys.platform
    return Marker(marker).evaluate()


def _read_pins(lock_path: str, this_platform_only: bool = False) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in Path(lock_path).read_text(encoding="utf-8").splitlines():
        match = _PIN.match(line.strip())
        if not match:
            continue
        marker = _MARKER.search(line)
        if this_platform_only and marker and not _applies(marker.group(1).strip()):
            continue
        pins[_normalize(match.group(1))] = match.group(2)
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


def check(*lock_paths: str, exact: bool = False) -> list[str]:
    lock_paths = lock_paths or ("requirements.lock",)
    installed_pins: dict[str, str] = {}
    for path in lock_paths:
        installed_pins.update(_read_pins(path, this_platform_only=True))
    pins: dict[str, str] = {}
    for path in LOCK_FILES:
        if Path(path).exists():
            pins.update(_read_pins(path))
    floors = {_normalize(k): v for k, v in _read_floors().items()}
    problems: list[str] = []

    for name, pin in sorted(installed_pins.items()):
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            problems.append(f"{name}=={pin} is locked but not installed")
            continue
        if installed != pin:
            problems.append(f"{name}: installed {installed} != locked {pin}")

    if exact:
        for dist in importlib.metadata.distributions():
            name = _normalize(dist.metadata["Name"] or "")
            if name and name not in installed_pins and name not in _TOOLING:
                problems.append(f"{name}=={dist.version} is installed but not locked")

    for name, floor in sorted(floors.items()):
        pin = pins.get(name)
        if pin is None:
            problems.append(f"{name}: pyproject floor >={floor} has no lock pin")
            continue
        if _version_tuple(pin) < _version_tuple(floor):
            problems.append(f"{name}: locked {pin} is below pyproject floor >={floor}")

    return problems


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--exact"]
    problems = check(*args, exact="--exact" in sys.argv[1:])
    for problem in problems:
        print(f"lock drift: {problem}")
    if problems:
        print(f"{len(problems)} lock/pyproject problem(s) found")
        return 1
    checked = ", ".join(args) or "requirements.lock"
    print(f"lock verified: installed tree matches {checked} and pyproject floors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
