"""The pre-commit hook: `openpulse gate --base-ref HEAD` on staged dependency files
(track T, T-E2, v0.15.0 item Z2)."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli

ROOT = Path(__file__).resolve().parents[1]
MAL = {"vulns": [{"id": "MAL-2026-0042"}]}


def _hook() -> dict:
    hooks = yaml.safe_load((ROOT / ".pre-commit-hooks.yaml").read_text(encoding="utf-8"))
    assert [h["id"] for h in hooks] == ["openpulse-gate"]
    return hooks[0]


# ---------------------------------------------------------------------------
# The hook definition
# ---------------------------------------------------------------------------


def test_the_hook_runs_the_gate_against_head_on_the_files_it_is_given():
    hook = _hook()
    assert shlex.split(hook["entry"]) == ["openpulse", "gate", "--base-ref", "HEAD"]
    assert hook["language"] == "python" and hook["pass_filenames"] is True


def test_the_entry_point_is_the_installed_cli():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'openpulse = "cli.main:cli"' in text


@pytest.mark.parametrize(
    "name",
    [
        "requirements.txt",
        "requirements-dev.txt",
        "services/api/requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "web/package-lock.json",
        "Cargo.toml",
        "Cargo.lock",
        "go.mod",
        "pom.xml",
    ],
)
def test_the_hook_selects_dependency_files(name):
    assert re.search(_hook()["files"], name)


@pytest.mark.parametrize(
    "name",
    [
        "README.md",
        "docs/requirements.md",
        "package.json",  # not read by OpenPulse; package-lock.json is
        "pyproject.toml.bak",
        "my-poetry.lock",
        "requirements/base.in",
    ],
)
def test_the_hook_leaves_other_files_alone(name):
    assert not re.search(_hook()["files"], name)


# ---------------------------------------------------------------------------
# What pre-commit does with it: staged files, compared with HEAD
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return done.stdout.decode("utf-8")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "hook@example.invalid")
    _git(tmp_path, "config", "user.name", "hook test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    (tmp_path / ".openpulse").mkdir()
    (tmp_path / ".openpulse" / "policy.yml").write_text(
        "version: 1\nprohibit: [confirmed_malicious]\n", encoding="utf-8"
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _run_hook(repo: Path):
    """Run the hook the way pre-commit does: its entry plus the staged files it selects."""
    hook = _hook()
    staged = _git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR").split()
    files = [f for f in staged if re.search(hook["files"], f)]
    if not files:
        return None
    return CliRunner().invoke(cli, [*shlex.split(hook["entry"])[1:], *files])


def _osv(*bad):
    asked = []

    def query(body):
        asked.append(body["package"]["name"])
        return (200, MAL) if body["package"]["name"] in bad else (200, {})

    query.asked = asked
    return query


def test_a_staged_malicious_addition_blocks_the_commit(repo, monkeypatch):
    osv = _osv("evil-pkg")
    monkeypatch.setattr("core.malicious.default_query", osv)
    (repo / "requirements.txt").write_text("django==4.2\nevil-pkg==1.0\n", encoding="utf-8")
    _git(repo, "add", "requirements.txt")
    result = _run_hook(repo)
    assert result.exit_code == 1
    assert "PROHIBITED confirmed_malicious: PyPI:evil-pkg==1.0" in result.output
    assert osv.asked == ["evil-pkg"]  # the policy came from .openpulse/policy.yml


def test_a_clean_staged_change_passes(repo, monkeypatch):
    monkeypatch.setattr("core.malicious.default_query", _osv())
    (repo / "requirements.txt").write_text("django==4.2\nflask==3.0.3\n", encoding="utf-8")
    _git(repo, "add", "requirements.txt")
    result = _run_hook(repo)
    assert result.exit_code == 0, result.output
    assert "1 added or changed" in result.output


def test_a_newly_added_dependency_file_is_checked_in_full(repo, monkeypatch):
    osv = _osv()
    monkeypatch.setattr("core.malicious.default_query", osv)
    sub = repo / "services" / "api"
    sub.mkdir(parents=True)
    (sub / "requirements.txt").write_text("pytest==8.0.0\n", encoding="utf-8")
    _git(repo, "add", "services/api/requirements.txt")
    result = _run_hook(repo)
    assert result.exit_code == 0, result.output
    assert osv.asked == ["pytest"]


def test_the_first_commit_of_a_repository_is_checked_in_full(tmp_path, monkeypatch):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    osv = _osv("evil-pkg")
    monkeypatch.setattr("core.malicious.default_query", osv)
    _git(tmp_path, "init", "-q")
    (tmp_path / "requirements.txt").write_text("django==4.2\nevil-pkg==1.0\n", encoding="utf-8")
    (tmp_path / "policy.yml").write_text(
        "version: 1\nprohibit: [confirmed_malicious]\n", encoding="utf-8"
    )
    _git(tmp_path, "add", "requirements.txt")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        cli, ["gate", "--base-ref", "HEAD", "--policy", "policy.yml", "requirements.txt"]
    )
    assert result.exit_code == 1, result.output  # no HEAD yet: everything is added
    assert sorted(osv.asked) == ["django", "evil-pkg"]


def test_an_unknown_ref_in_a_repository_without_commits_is_still_an_error(
    tmp_path, monkeypatch
):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    _git(tmp_path, "init", "-q")
    (tmp_path / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    (tmp_path / "policy.yml").write_text("version: 1\nblocklist: ['PyPI:x']\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        cli, ["gate", "--base-ref", "origin/main", "--policy", "policy.yml", "requirements.txt"]
    )
    assert result.exit_code == 2 and "not a commit" in result.output


def test_a_commit_without_dependency_files_does_not_run_the_gate(repo):
    (repo / "README.md").write_text("# hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    assert _run_hook(repo) is None
