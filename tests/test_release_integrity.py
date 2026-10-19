"""Release/CI integrity guards (F4, F7, F9)."""

from __future__ import annotations

import re
from pathlib import Path

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
    floors = _read_floors()
    assert floors["pydantic"] == "2.14.1"
    assert floors["ruff"] == "0.17.0"
    # build-system floors must not be treated as lock requirements
    assert "setuptools" not in floors


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
