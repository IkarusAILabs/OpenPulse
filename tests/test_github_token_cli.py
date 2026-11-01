"""CLI regression tests for GitHub credential handling."""

import sys

import pytest
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.parametrize("command", ["check", "digest", "warnings", "attest"])
def test_github_token_file_is_available_on_all_repo_commands(command, monkeypatch, tmp_path):
    from core import github_reader

    token_file = tmp_path / "github-token"
    token_file.write_text("file-token\n", encoding="utf-8")
    calls = []
    inspected = []

    def capture(cli_token=None, token_file=None):
        calls.append((cli_token, token_file))
        return "resolved-token"

    def fake_inspect(repo, cli_token=None, **_kwargs):
        inspected.append((repo, cli_token))
        return github_reader.RepoInspection()

    monkeypatch.setattr(github_reader, "get_github_token", capture)
    monkeypatch.setattr(github_reader, "inspect_github_repo", fake_inspect)
    result = CliRunner().invoke(
        cli,
        [
            command,
            "--github-repo",
            "owner/repo",
            "--github-token-file",
            str(token_file),
            "--event",
            "data/fixtures/bitnami/event.json",
        ],
    )

    assert len(calls) == 1
    assert not calls[0][0]
    assert calls[0][1] == str(token_file)
    # The resolved token is what the repository inspection actually receives.
    assert inspected == [("owner/repo", "resolved-token")]
    assert "file-token" not in result.output


@pytest.mark.parametrize("command", ["check", "digest", "warnings", "attest"])
def test_token_file_is_not_read_without_github_repo(command, monkeypatch, tmp_path):
    """Regression: the token file was opened and validated even when no
    repository was inspected, so a bad path failed unrelated runs."""
    from core import github_reader

    oversized = tmp_path / "github-token"
    oversized.write_bytes(b"x" * 10_000)

    def must_not_resolve(*_args, **_kwargs):
        raise AssertionError("token must not be resolved without --github-repo")

    monkeypatch.setattr(github_reader, "get_github_token", must_not_resolve)
    result = CliRunner().invoke(
        cli,
        [
            command,
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
            "--github-token-file",
            str(oversized),
        ],
    )

    assert not isinstance(result.exception, AssertionError), result.output
    assert "token file" not in result.output


@pytest.mark.parametrize("command", ["check", "digest", "warnings", "attest"])
def test_deprecated_argv_token_warns_without_echoing_value(command):
    secret = "ghp_" + "not-a-real-token-value"
    result = CliRunner().invoke(cli, [command, "--github-token", secret])

    assert "--github-token is deprecated" in result.output
    assert secret not in result.output


# ---------------------------------------------------------------------------
# #139: warn when other users can read the token file
# ---------------------------------------------------------------------------


class _Mode:
    def __init__(self, mode):
        self.st_mode = mode


@pytest.mark.parametrize(("mode", "warns"), [(0o100644, True), (0o100640, True), (0o100600, False)])
def test_token_file_mode_warning(monkeypatch, capsys, mode, warns):
    """Every OS: the permission rule itself, through the stat seam."""
    import cli.main as main

    monkeypatch.setattr(main, "_POSIX_MODES", True)
    main._warn_if_token_file_shared(
        "/home/u/.config/openpulse/github-token", lambda _p: _Mode(mode)
    )
    err = capsys.readouterr().err
    assert ("readable by other users" in err) is warns
    if warns:
        assert "chmod 600 /home/u/.config/openpulse/github-token" in err


def test_token_file_mode_is_not_checked_on_windows(monkeypatch, capsys):
    import cli.main as main

    monkeypatch.setattr(main, "_POSIX_MODES", False)
    main._warn_if_token_file_shared("token", lambda _p: _Mode(0o100666))
    assert capsys.readouterr().err == ""


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
@pytest.mark.parametrize(("mode", "warns"), [(0o644, True), (0o600, False)])
def test_shared_token_file_warns_end_to_end(monkeypatch, tmp_path, mode, warns):
    from core import github_reader

    token_file = tmp_path / "github-token"
    token_file.write_text("ghp_secret_value\n", encoding="utf-8")
    token_file.chmod(mode)
    monkeypatch.setattr(
        github_reader, "inspect_github_repo", lambda *_a, **_k: github_reader.RepoInspection()
    )
    result = CliRunner().invoke(
        cli,
        [
            "check",
            "--github-repo",
            "owner/repo",
            "--github-token-file",
            str(token_file),
            "--event",
            "data/fixtures/bitnami/event.json",
            "--ledger",
            "",
        ],
    )
    assert ("readable by other users" in result.output) is warns
    assert "ghp_secret_value" not in result.output
