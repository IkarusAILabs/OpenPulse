"""CLI regression tests for GitHub credential handling."""

import pytest
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.parametrize("command", ["check", "digest", "warnings", "attest"])
def test_github_token_file_is_available_on_all_repo_commands(command, monkeypatch, tmp_path):
    from core import github_reader

    token_file = tmp_path / "github-token"
    token_file.write_text("file-token\n", encoding="utf-8")
    calls = []

    def capture(cli_token=None, token_file=None):
        calls.append((cli_token, token_file))
        return "resolved-token"

    monkeypatch.setattr(github_reader, "get_github_token", capture)
    result = CliRunner().invoke(cli, [command, "--github-token-file", str(token_file)])

    assert len(calls) == 1
    assert not calls[0][0]
    assert calls[0][1] == str(token_file)
    assert "file-token" not in result.output


@pytest.mark.parametrize("command", ["check", "digest", "warnings", "attest"])
def test_deprecated_argv_token_warns_without_echoing_value(command):
    secret = "ghp_" + "not-a-real-token-value"
    result = CliRunner().invoke(cli, [command, "--github-token", secret])

    assert "--github-token is deprecated" in result.output
    assert secret not in result.output
