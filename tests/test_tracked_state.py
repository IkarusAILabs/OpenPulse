"""Local history committed to the repository is refused (observations, ledger,
webhook delivery state): anyone who can commit could forge it."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "state@example.invalid")
    _git(tmp_path, "config", "user.name", "state test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _commit_state(repo: Path, relative: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"alerts": {}}), encoding="utf-8")
    _git(repo, "add", "-f", relative)
    _git(repo, "commit", "-q", "-m", "forged state")


def _check(*extra):
    args = ["check", "--manifest", "requirements.txt", "--event", EVENT, "--replay", *extra]
    return CliRunner().invoke(cli, args)


@pytest.mark.parametrize(
    ("relative", "flag"),
    [
        (".openpulse/deliveries/alerts.json", "--delivery-state"),
        (".openpulse/detections/ledger.jsonl", "--ledger"),
    ],
)
def test_a_committed_store_is_refused(repo, relative, flag):
    _commit_state(repo, relative)
    # The test suite moves delivery state out of the checkout; name the store.
    result = _check(flag, str(Path(relative).parent))
    assert result.exit_code == 2, result.output
    assert "tracked by git" in result.output and flag in result.output


def test_an_untracked_store_and_a_moved_store_are_used(repo, tmp_path_factory):
    (repo / ".openpulse" / "detections").mkdir(parents=True)
    assert _check().exit_code == 0
    _commit_state(repo, ".openpulse/detections/ledger.jsonl")
    elsewhere = tmp_path_factory.mktemp("ledger")
    assert _check("--ledger", str(elsewhere)).exit_code == 0


def test_outside_a_git_checkout_nothing_is_refused(tmp_path_factory, monkeypatch):
    plain = tmp_path_factory.mktemp("plain")
    (plain / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    (plain / ".openpulse" / "detections").mkdir(parents=True)
    monkeypatch.chdir(plain)
    assert _check().exit_code == 0
