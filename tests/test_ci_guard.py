"""scripts/check_ci_runs_all_tests.py: every silent test exclusion fails CI (F7, #104)."""

from __future__ import annotations

import pytest

from scripts.check_ci_runs_all_tests import main, offenders

# Assembled so this file never reads as an exclusion itself.
IGNORE, DESELECT, CI = "--" + "ignore", "--" + "deselect", "collect_" + "ignore"


def _workflow(root, run):
    path = root / ".github" / "workflows" / "ci.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"jobs:\n  test:\n    steps:\n      - run: {run}\n", encoding="utf-8")


@pytest.mark.parametrize(
    "run",
    [
        f"pytest -q {IGNORE}=tests/test_slow.py",
        f"pytest -q {IGNORE}-glob='tests/*_live.py'",
        f"pytest -q {DESELECT} tests/test_x.py::test_y",
        'pytest -q -k "not slow"',
        "pytest -q -k 'fast and not flaky'",
        "python -m pytest -k='not network'",
    ],
)
def test_workflow_exclusions_are_reported_with_file_and_line(tmp_path, run, capsys):
    _workflow(tmp_path, run)
    assert main(tmp_path) == 1
    assert ".github/workflows/ci.yml:4:" in capsys.readouterr().out


@pytest.mark.parametrize(
    "run",
    [
        "pytest -q",
        "pytest -q tests/test_mcp_server.py tests/test_agent_tools.py",
        'pytest -q -k "slow"',
        "curl -k https://example.invalid/not-a-test",
        "pytest -q -k=not_network",  # selects names containing not_network
    ],
)
def test_whole_suite_runs_are_not_reported(tmp_path, run):
    _workflow(tmp_path, run)
    assert offenders(tmp_path) == []


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("pyproject.toml", f'[tool.pytest.ini_options]\naddopts = "-q {DESELECT} tests/a.py::b"\n'),
        (
            "pyproject.toml",
            f'[tool.pytest.ini_options]\naddopts = [\n  "-q",\n  "{IGNORE}=x",\n]\n',
        ),
        ("pytest.ini", '[pytest]\naddopts = -k "not slow"\n'),
    ],
)
def test_addopts_exclusions_are_reported(tmp_path, name, text):
    (tmp_path / name).write_text(text, encoding="utf-8")
    found = offenders(tmp_path)
    assert found and found[0].startswith(f"{name}:") and "addopts" in found[0]


def test_flags_outside_the_pytest_section_are_not_reported(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        f'[tool.other]\nargs = "{DESELECT}"\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        encoding="utf-8",
    )
    assert offenders(tmp_path) == []


@pytest.mark.parametrize("assignment", [f'{CI} = ["test_live.py"]', f'{CI}_glob = ["*_live.py"]'])
def test_conftest_collect_ignore_is_reported(tmp_path, assignment):
    (tmp_path / "tests" / "sub").mkdir(parents=True)
    (tmp_path / "tests" / "sub" / "conftest.py").write_text(assignment + "\n", encoding="utf-8")
    assert offenders(tmp_path) == ["tests/sub/conftest.py:1: conftest collect-ignore drops files"]


def test_conftests_inside_virtualenvs_are_not_ours(tmp_path):
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "conftest.py").write_text(f"{CI} = ['x']\n", encoding="utf-8")
    assert offenders(tmp_path) == []


def test_comment_lines_in_workflows_are_not_reported(tmp_path):
    _workflow(tmp_path, "pytest -q")
    path = tmp_path / ".github" / "workflows" / "ci.yml"
    path.write_text(
        path.read_text(encoding="utf-8") + f"      # was: pytest {DESELECT} tests/a.py\n",
        encoding="utf-8",
    )
    assert offenders(tmp_path) == []
