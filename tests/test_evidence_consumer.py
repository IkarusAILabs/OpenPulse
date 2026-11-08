"""The standalone evidence consumer stays in step with OpenPulse (v0.19.0 P1).

The consumer's own behaviour is tested by ``conformance/consumer/tests``
with OpenPulse absent (the ``consumer`` CI job). These tests run inside
OpenPulse's suite and keep the two from drifting apart: the bundled schemas
are the published ones, the lock is generated with the repository's pins,
and both validators agree on what ``openpulse attest`` emits.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "conformance" / "consumer"


def test_the_bundled_schemas_are_the_published_ones():
    done = subprocess.run(
        [sys.executable, str(CONSUMER / "sync_schemas.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr


def test_the_consumer_lock_uses_the_repository_pins():
    def pins(path):
        out = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "==" in line and not line.startswith((" ", "#")):
                name, version = line.split("==", 1)
                out[name.strip().lower()] = version.split()[0].split(";")[0]
        return out

    consumer = pins(CONSUMER / "requirements.lock")
    repo = pins(ROOT / "requirements.lock") | pins(ROOT / "requirements-mcp.lock")
    assert "jsonschema" in consumer
    assert {name: consumer[name] for name in consumer} == {name: repo[name] for name in consumer}


def _consumer():
    pytest.importorskip("jsonschema")
    sys.path.insert(0, str(CONSUMER))
    try:
        import openpulse_consumer
    finally:
        sys.path.remove(str(CONSUMER))
    return openpulse_consumer


def test_both_validators_agree_on_what_attest_emits(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli
    from core.evidence_contract import validate_contract

    consumer = _consumer()
    out = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli,
        [
            "attest",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/django-eol/event.json",
            "--replay",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert docs
    for doc in docs:
        assert validate_contract(doc) == []
        assert consumer.check(doc).valid, consumer.check(doc).errors
        broken = dict(doc, surprise=True)
        assert validate_contract(broken) and not consumer.check(broken).valid
