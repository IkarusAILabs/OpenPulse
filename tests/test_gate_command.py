"""`openpulse gate`: the trust policy before install (track T, T-E2, v0.15.0 item Z1)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
MAL = {"vulns": [{"id": "MAL-2026-0042"}]}
SHA_GOOD, SHA_EVIL = "a" * 64, "e" * 64


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A git repository with requirements.txt committed, used as the working directory."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "gate@example.invalid")
    _git(tmp_path, "config", "user.name", "gate test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    _git(tmp_path, "add", "requirements.txt")
    _git(tmp_path, "commit", "-q", "-m", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _policy(repo: Path, doc: dict) -> str:
    path = repo / "policy.yml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return str(path)


def _gate(*args):
    return CliRunner().invoke(cli, ["gate", *args])


def _osv(*bad):
    asked = []

    def query(body):
        asked.append(body["package"]["name"])
        return (200, MAL) if body["package"]["name"] in bad else (200, {})

    query.asked = asked
    return query


def _poetry(*packages):
    return 'lock-version = "2.1"\n\n' + "\n".join(
        f'[[package]]\nname = "{n}"\nversion = "{v}"\n'
        f'files = [{{file = "{n}-{v}-py3-none-any.whl", hash = "sha256:{h}"}}]\n'
        for n, v, h in packages
    )


# ---------------------------------------------------------------------------
# Passing and failing
# ---------------------------------------------------------------------------


def test_without_a_policy_the_gate_passes(repo):
    result = _gate("requirements.txt")
    assert result.exit_code == 0 and "nothing is prohibited" in result.output


def test_only_added_dependencies_are_checked_against_the_ref(repo, monkeypatch):
    osv = _osv("evil-pkg")
    monkeypatch.setattr("core.malicious.default_query", osv)
    (repo / "requirements.txt").write_text("django==4.2\nevil-pkg==1.0\n", encoding="utf-8")
    policy = _policy(repo, {"version": 1, "prohibit": ["confirmed_malicious"]})
    result = _gate("requirements.txt", "--base-ref", "HEAD", "--policy", policy)
    assert result.exit_code == 1
    assert "PROHIBITED confirmed_malicious: PyPI:evil-pkg==1.0" in result.output
    assert osv.asked == ["evil-pkg"]  # django==4.2 is unchanged since HEAD


def test_a_clean_change_passes_with_a_summary(repo, monkeypatch):
    monkeypatch.setattr("core.malicious.default_query", _osv())
    (repo / "requirements.txt").write_text("django==4.2\nflask==3.0.3\n", encoding="utf-8")
    policy = _policy(repo, {"version": 1, "prohibit": ["confirmed_malicious"]})
    result = _gate("requirements.txt", "--base-ref", "HEAD", "--policy", policy)
    assert result.exit_code == 0, result.output
    assert "gate: passed (2 dependencies, 1 added or changed, no violation)" in result.output


def test_a_file_new_since_the_ref_counts_entirely_as_added(repo, monkeypatch):
    osv = _osv()
    monkeypatch.setattr("core.malicious.default_query", osv)
    (repo / "requirements-dev.txt").write_text("pytest==8.0.0\nflask==3.0.3\n", encoding="utf-8")
    policy = _policy(repo, {"version": 1, "prohibit": ["confirmed_malicious"]})
    result = _gate("requirements-dev.txt", "--base-ref", "HEAD", "--policy", policy)
    assert result.exit_code == 0, result.output
    assert sorted(osv.asked) == ["flask", "pytest"]


def test_the_blocklist_covers_unchanged_dependencies_too(repo):
    policy = _policy(repo, {"version": 1, "blocklist": ["PyPI:django"]})
    result = _gate("requirements.txt", "--base-ref", "HEAD", "--policy", policy)
    assert result.exit_code == 1 and "PROHIBITED blocklisted: PyPI:django==4.2" in result.output


def test_a_lockfile_hash_edited_in_place_is_caught(repo, monkeypatch):
    lock = repo / "poetry.lock"
    lock.write_text(_poetry(("django", "4.2", SHA_GOOD)), encoding="utf-8")
    _git(repo, "add", "poetry.lock")
    _git(repo, "commit", "-q", "-m", "lock")
    lock.write_text(_poetry(("django", "4.2", SHA_EVIL)), encoding="utf-8")
    published = {"urls": [{"filename": "x.whl", "digests": {"sha256": SHA_GOOD}}]}
    monkeypatch.setattr("core.digest_integrity.default_fetch", lambda _url: (200, published))
    policy = _policy(repo, {"version": 1, "prohibit": ["digest_mismatch"]})
    result = _gate("poetry.lock", "--base-ref", "HEAD", "--policy", policy)
    assert result.exit_code == 1, result.output
    assert "PROHIBITED digest_mismatch: PyPI:django==4.2" in result.output


def test_explicit_base_files_work_without_git(repo, monkeypatch, tmp_path_factory):
    monkeypatch.setattr("core.malicious.default_query", _osv("evil-pkg"))
    other = tmp_path_factory.mktemp("base")
    base = other / "requirements.txt"
    base.write_text("django==4.2\n", encoding="utf-8")
    (repo / "requirements.txt").write_text("django==4.2\nevil-pkg==1.0\n", encoding="utf-8")
    policy = _policy(repo, {"version": 1, "prohibit": ["confirmed_malicious"]})
    result = _gate("requirements.txt", "--base", str(base), "--policy", policy)
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Files a hook may pass, and usage errors
# ---------------------------------------------------------------------------


def test_deleted_and_non_dependency_files_are_skipped(repo):
    (repo / "README.md").write_text("# hello\n", encoding="utf-8")
    policy = _policy(repo, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    result = _gate("README.md", "gone.txt", "--base-ref", "HEAD", "--policy", policy)
    assert result.exit_code == 0, result.output
    assert "not present" in result.output and "not a dependency file" in result.output


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--base-ref", "no-such-ref"], "not a commit"),
        (["--base-ref", "HEAD", "--base", "requirements.txt"], "not both"),
    ],
)
def test_usage_errors_exit_2(repo, args, message):
    policy = _policy(repo, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    result = _gate("requirements.txt", "--policy", policy, *args)
    assert result.exit_code == 2 and message in result.output


def test_base_ref_outside_a_repository_is_a_usage_error(tmp_path_factory, monkeypatch):
    plain = tmp_path_factory.mktemp("plain")
    (plain / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    (plain / "policy.yml").write_text("version: 1\nblocklist: ['PyPI:x']\n", encoding="utf-8")
    monkeypatch.chdir(plain)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(plain.parent))
    result = _gate("requirements.txt", "--base-ref", "HEAD", "--policy", "policy.yml")
    assert result.exit_code == 2 and "not inside a git repository" in result.output
