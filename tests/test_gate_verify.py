"""Verifying a gate receipt before install (track T, T-E2; v0.17.0 item G2).

`openpulse gate --verify-receipt RECEIPT FILE...` exits 0 only when every
FILE is a file a passing gate recorded, with the same SHA-256 now.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli
from core import gate_receipt


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("pytest==8.0\n", encoding="utf-8")
    (tmp_path / "policy.yml").write_text(
        yaml.safe_dump({"version": 1, "blocklist": ["PyPI:evil-pkg"]}), encoding="utf-8"
    )
    return tmp_path


def _run(*args):
    return CliRunner().invoke(cli, ["gate", *args])


def _gate(path, receipt):
    return _run(path, "--policy", "policy.yml", "--receipt", receipt)


def test_the_gated_bytes_verify(work):
    assert _gate("requirements.txt", "r.json").exit_code == 0
    result = _run("--verify-receipt", "r.json", "requirements.txt")
    assert result.exit_code == 0, result.output
    assert "verified 1 file(s) against 1 passing receipt(s)" in result.output


def test_a_file_changed_after_the_gate_is_refused(work):
    assert _gate("requirements.txt", "r.json").exit_code == 0
    (work / "requirements.txt").write_text("django==4.2\nevil-pkg==1.0\n", encoding="utf-8")
    result = _run("--verify-receipt", "r.json", "requirements.txt")
    assert result.exit_code == 1
    assert "REFUSED requirements.txt: changed since the gate; run the gate again" in result.output


def test_a_file_the_gate_never_saw_is_refused(work):
    assert _gate("requirements.txt", "r.json").exit_code == 0
    result = _run("--verify-receipt", "r.json", "requirements.txt", "requirements-dev.txt")
    assert result.exit_code == 1
    assert "requirements-dev.txt: not in the receipt" in result.output


def test_a_failed_gate_never_verifies(work):
    (work / "requirements.txt").write_text("evil-pkg==1.0\n", encoding="utf-8")
    assert _gate("requirements.txt", "r.json").exit_code == 1
    result = _run("--verify-receipt", "r.json", "requirements.txt")
    assert result.exit_code == 1
    assert "the gate did not pass" in result.output


def test_a_deleted_file_is_refused(work):
    assert _gate("requirements.txt", "r.json").exit_code == 0
    (work / "requirements.txt").unlink()
    result = _run("--verify-receipt", "r.json", "requirements.txt")
    assert result.exit_code == 1 and "missing now" in result.output


def test_the_same_file_spelt_another_way_matches(work):
    assert _gate("requirements.txt", "r.json").exit_code == 0
    (work / "sub").mkdir()  # Linux resolves `sub/..` only through a real directory
    spelt = str(Path(".") / "sub" / ".." / "requirements.txt")
    assert _run("--verify-receipt", "r.json", spelt).exit_code == 0
    assert _run("--verify-receipt", "r.json", str(work / "requirements.txt")).exit_code == 0


def test_a_directory_of_receipts_one_per_gated_file(work):
    (work / "receipts").mkdir()
    assert _gate("requirements.txt", "receipts/0.json").exit_code == 0
    assert _gate("requirements-dev.txt", "receipts/1.json").exit_code == 0
    both = ("requirements.txt", "requirements-dev.txt")
    result = _run("--verify-receipt", "receipts", *both)
    assert result.exit_code == 0, result.output
    assert "against 2 passing receipt(s)" in result.output
    # One failing gate in the directory refuses everything.
    (work / "requirements-dev.txt").write_text("evil-pkg==1.0\n", encoding="utf-8")
    assert _gate("requirements-dev.txt", "receipts/1.json").exit_code == 1
    assert _run("--verify-receipt", "receipts", "requirements.txt").exit_code == 1


def test_a_file_recorded_twice_must_match_both(work):
    assert _gate("requirements.txt", "a.json").exit_code == 0
    (work / "requirements.txt").write_text("django==4.2.1\n", encoding="utf-8")
    assert _gate("requirements.txt", "b.json").exit_code == 0
    result = _run("--verify-receipt", "a.json", "--verify-receipt", "b.json", "requirements.txt")
    assert result.exit_code == 1 and "changed since the gate" in result.output


def test_a_file_the_gate_could_not_read_is_refused(work):
    receipt = gate_receipt.build(
        files=[{"path": "requirements.txt", "sha256": None, "status": "unreadable"}],
        decision="passed",
        version="0",
        policy=None,
        private_names=None,
        base_ref=None,
        base_files=None,
        dependencies=0,
        added=None,
        violations=[],
    )
    gate_receipt.write(receipt, work / "r.json")
    result = _run("--verify-receipt", "r.json", "requirements.txt")
    assert result.exit_code == 1 and "recorded as not gated" in result.output


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        json.dumps({"receipt_version": "2.0", "files": []}),
        json.dumps({"receipt_version": "1.0", "files": [{"path": "x", "sha256": "nothex"}]}),
        json.dumps([1, 2]),
    ],
)
def test_an_unreadable_receipt_is_an_error_not_a_pass(work, content):
    (work / "r.json").write_text(content, encoding="utf-8")
    assert _run("--verify-receipt", "r.json", "requirements.txt").exit_code == 2


def test_an_empty_receipt_directory_is_an_error(work):
    (work / "receipts").mkdir()
    assert _run("--verify-receipt", "receipts", "requirements.txt").exit_code == 2


def test_verification_takes_no_gating_options(work):
    assert _gate("requirements.txt", "r.json").exit_code == 0
    result = _run("--verify-receipt", "r.json", "--policy", "policy.yml", "requirements.txt")
    assert result.exit_code == 2 and "takes no" in result.output
