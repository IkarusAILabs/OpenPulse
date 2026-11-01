"""Fail CI when the test suite silently excludes tests (F7, #104).

A test that is written but not run is not a test. The suite is expected
to run whole; the only escape hatch would be an explicit, documented
allow-list, which this guard deliberately does not provide. It reports
every way pytest can drop tests without a failure:

- workflows (``.github/workflows/*.yml``): ``--ignore``,
  ``--ignore-glob``, ``--deselect``, and ``-k`` expressions containing
  ``not`` on a pytest command line;
- pytest configuration (``[tool.pytest.ini_options]`` in
  ``pyproject.toml``, ``[pytest]`` in ``pytest.ini``): the same flags in
  ``addopts``;
- any ``conftest.py``: ``collect_ignore`` and ``collect_ignore_glob``.

Each offender is printed as ``file:line: reason``. The flag literals are
assembled at runtime so this guard never matches itself. stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_IGNORE = re.compile(r"(?<![\w-])--" + "ignore" + r"(?:-glob)?\b")
_DESELECT = re.compile(r"(?<![\w-])--" + "deselect" + r"\b")
#: `-k "not slow"`, `-k=not_x`, `-k 'a and not b'`: any -k expression with `not`.
_K_NOT = re.compile(r"(?<![\w-])-k(?:\s*=\s*|\s+)(['\"]?)[^'\"\n]*\b" + "not" + r"\b")
_COLLECT_IGNORE = re.compile(r"\b" + "collect_" + r"ignore(?:_glob)?\b")
_SKIP_DIRS = {".git", ".venv", "venv", "env", "site-packages", "node_modules", "build", "dist"}


def _flag_reasons(text: str) -> list[str]:
    reasons = []
    if _IGNORE.search(text):
        reasons.append("pytest ignore flag excludes files")
    if _DESELECT.search(text):
        reasons.append("pytest deselect flag drops tests")
    if _K_NOT.search(text):
        reasons.append("pytest -k expression with `not` drops tests")
    return reasons


def _workflow_offenders(root: Path) -> list[str]:
    out = []
    for path in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            reasons = _flag_reasons(line)
            # -k is also a flag of unrelated tools (curl, ssh); count it only for pytest.
            if "pytest" not in line:
                reasons = [r for r in reasons if "-k" not in r]
            out += [f"{path.relative_to(root).as_posix()}:{number}: {r}" for r in reasons]
    return out


def _config_offenders(root: Path) -> list[str]:
    """Every line of the pytest section, so multi-line ``addopts`` is covered."""
    out = []
    for name, header in (
        ("pyproject.toml", "[tool.pytest.ini_options]"),
        ("pytest.ini", "[pytest]"),
    ):
        path = root / name
        if not path.is_file():
            continue
        inside = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("["):
                inside = stripped == header
                continue
            if inside and not stripped.startswith("#"):
                out += [f"{name}:{number}: {r} (addopts)" for r in _flag_reasons(line)]
    return out


def _conftest_offenders(root: Path) -> list[str]:
    out = []
    for path in sorted(root.rglob("conftest.py")):
        rel = path.relative_to(root)
        if _SKIP_DIRS & set(rel.parts[:-1]):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _COLLECT_IGNORE.search(line.split("#", 1)[0]):
                out.append(f"{rel.as_posix()}:{number}: conftest collect-ignore drops files")
    return out


def offenders(root: Path = Path(".")) -> list[str]:
    return _workflow_offenders(root) + _config_offenders(root) + _conftest_offenders(root)


def main(root: Path = Path(".")) -> int:
    found = offenders(root)
    if found:
        for line in found:
            print(f"CI excludes tests: {line}")
        return 1
    print("no test exclusions in CI: the whole suite runs")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")))
