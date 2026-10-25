"""`python -m cli`: the interpreter entry point MCP clients fall back to.

Every subprocess runs from a temporary directory, never the OpenPulse
checkout, so `cli` must resolve through the installed package - the
situation a real MCP client is in (it starts servers inside the user's
project). Kept out of test_packaging.py, whose tomllib skip would hide
these tests on Python 3.10.
"""

import subprocess
import sys

#: `-P` (3.11+) drops only the working directory; `-I` (3.10+) also drops
#: user site-packages and PYTHON* env vars. Either keeps a project's own
#: `cli/` package from shadowing OpenPulse's.
SAFE_PATH = "-P" if sys.version_info >= (3, 11) else "-I"
TIMEOUT = 60


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def test_python_m_cli_prints_the_version(tmp_path):
    res = _run([SAFE_PATH, "-m", "cli", "--version"], tmp_path)
    assert res.returncode == 0, res.stderr
    assert "openpulse, version" in res.stdout


def test_python_m_cli_names_itself_openpulse(tmp_path):
    """prog_name: usage lines say `openpulse`, not `python -m cli`."""
    res = _run([SAFE_PATH, "-m", "cli", "--help"], tmp_path)
    assert res.returncode == 0, res.stderr
    assert res.stdout.startswith("Usage: openpulse ")


def _project_with_own_cli(tmp_path):
    pkg = tmp_path / "cli"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__main__.py").write_text('print("PROJECT CLI RAN")\n', encoding="utf-8")
    return tmp_path


def test_safe_path_flag_runs_openpulse_inside_a_project_with_its_own_cli(tmp_path):
    """Regression for docs/MCP.md: with -P/-I, a project's `cli/` cannot win."""
    project = _project_with_own_cli(tmp_path)
    res = _run([SAFE_PATH, "-m", "cli", "--version"], project)
    assert res.returncode == 0, res.stderr
    assert "openpulse, version" in res.stdout
    assert "PROJECT CLI RAN" not in res.stdout


def test_bare_python_m_cli_is_shadowed_by_a_project_cli(tmp_path):
    """Why the docs insist on -I: without it the project's package runs."""
    project = _project_with_own_cli(tmp_path)
    res = _run(["-m", "cli", "--version"], project)
    assert "PROJECT CLI RAN" in res.stdout
