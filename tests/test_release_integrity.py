"""Release/CI integrity guards (F4, F7, F9)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from core.version import FALLBACK_VERSION, openpulse_version
from scripts.check_ci_runs_all_tests import main as ci_guard_main
from scripts.check_lock import _read_floors, _version_tuple
from scripts.check_lock import check as lock_check

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_fallback_matches_pyproject_version():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml has no project version"
    assert match.group(1) == FALLBACK_VERSION


def test_cli_version_flag_reports_package_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert openpulse_version() in result.output


def test_lock_floors_are_read_from_project_table():
    """The floor parser must agree with a real TOML parse of [project].

    Compared against pyproject.toml itself rather than pinned version
    literals: a hard-coded `ruff == "0.17.0"` broke every Dependabot floor
    bump (#126) without testing the parser any better.
    """
    tomllib = pytest.importorskip("tomllib")  # stdlib on 3.11+ (CI)
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        requirements += extra
    expected = {}
    for requirement in requirements:
        match = re.match(r"^([A-Za-z0-9_.\-]+)\s*>=\s*([0-9][^,;\s]*)", requirement)
        if match:
            expected[match.group(1).lower()] = match.group(2)
    assert {"pydantic", "ruff"} <= set(expected)
    assert _read_floors() == expected
    # build-system floors must not be treated as lock requirements
    assert "setuptools" not in _read_floors()


def test_version_tuple_compares_numerically():
    assert _version_tuple("2.14.1") < _version_tuple("2.14.2")
    assert _version_tuple("2.9.0") < _version_tuple("2.14.1")


def test_lock_check_is_clean_on_this_tree():
    assert lock_check() == []


def test_ci_does_not_exclude_tests():
    import os

    cwd = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        assert ci_guard_main() == 0
    finally:
        os.chdir(cwd)
