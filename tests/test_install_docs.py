"""Install instructions must install OpenPulse, not the PyPI `openpulse` project.

`openpulse` on PyPI is OpenQASM's pulse AST, an unrelated package; v0.6.x
docs told users to `pip install "openpulse[mcp]"`, which installed it.
OpenPulse ships as `ikarus-openpulse` (core.version.DISTRIBUTION).
"""

import re
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from core.version import DISTRIBUTION, install_hint, openpulse_version

REPO = Path(__file__).resolve().parents[1]
DOCS = [REPO / "README.md", REPO / "SECURITY.md", *sorted((REPO / "docs").rglob("*.md"))]

#: `pip install openpulse`, `pip install "openpulse[mcp]"`, `pip install openpulse==…`
_BARE_NAME = re.compile(r"pip\s+install\s+(?:-\S+\s+)*['\"]?openpulse(?![-\w])")
_FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)


def test_distribution_name_matches_pyproject():
    tomllib = pytest.importorskip("tomllib")  # stdlib on 3.11+ (CI)
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["name"] == DISTRIBUTION == "ikarus-openpulse"
    assert project["scripts"]["openpulse"] == "cli.main:cli"  # the command keeps its name


def test_no_doc_code_block_installs_the_pypi_openpulse_project():
    offenders = []
    for doc in DOCS:
        for _lang, body in _FENCE.findall(doc.read_text(encoding="utf-8")):
            for line in body.splitlines():
                if _BARE_NAME.search(line):
                    offenders.append(f"{doc.relative_to(REPO)}: {line.strip()}")
    assert offenders == [], offenders


def test_install_hint_is_pinned_and_never_the_bare_name():
    hint = install_hint("mcp")
    assert f'"{DISTRIBUTION}[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v' in hint
    assert hint.endswith(f'@v{openpulse_version()}"')
    assert not _BARE_NAME.search(hint)


def test_mcp_without_sdk_prints_the_right_install_command(monkeypatch):
    monkeypatch.setitem(sys.modules, "mcp.server.mcpserver", None)  # import -> ImportError
    result = CliRunner().invoke(cli, ["mcp", "--offline"])
    assert result.exit_code != 0
    assert install_hint("mcp") in result.output
    assert not _BARE_NAME.search(result.output)
