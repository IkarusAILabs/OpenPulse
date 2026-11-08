"""The standalone evidence consumer stays in step with OpenPulse (v0.19.0 P1).

The consumer's own behaviour is tested by ``conformance/consumer/tests``
with OpenPulse absent (the ``consumer`` CI job). These tests run inside
OpenPulse's suite and keep the two from drifting apart: the bundled schemas
are the published ones, the lock is generated with the repository's pins,
and both validators agree on what ``openpulse attest`` emits.
"""

from __future__ import annotations

import json
import shutil
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


def test_verify_mjs_accepts_exactly_the_published_2x_versions():
    """verify.mjs's VERSIONS list is the 2.x schemas, so a new schema needs it too."""
    import re

    script = (ROOT / "conformance" / "evidence-contract" / "verify.mjs").read_text("utf-8")
    listed = re.search(r"export const VERSIONS = \[([^\]]*)\]", script)
    assert listed, "verify.mjs has no VERSIONS list"
    versions = re.findall(r'"([0-9.]+)"', listed.group(1))
    published = sorted(
        json.loads(p.read_text("utf-8"))["properties"]["contract_version"]["const"]
        for p in (ROOT / "schemas" / "evidence-contract").glob("*/schema.json")
    )
    assert versions == [v for v in published if v.startswith("2.")]


def _attest_docs(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

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
    return [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]


def _mutants(doc):
    """Documents built to be rejected, one rule each (P2)."""
    import copy

    def mutate(change):
        bad = copy.deepcopy(doc)
        change(bad)
        return bad

    return {
        "unknown version": mutate(lambda d: d.update(contract_version="2.9.0")),
        "short version": mutate(lambda d: d.update(contract_version="2.4")),
        "provenance version": mutate(lambda d: d["provenance"].update(contract_version="2.3.0")),
        "unknown field": mutate(lambda d: d.update(surprise=True)),
        "bad date": mutate(lambda d: d["temporal"].update(announcement_date="1st April")),
        "bad date-time": mutate(lambda d: d["provenance"].update(generation_timestamp="now")),
        "bad uri": mutate(lambda d: d["evidence_refs"][0].update(url="no-scheme")),
        "older schema": mutate(lambda d: d.update(contract_version="2.3.0")),
    }


def test_the_consumer_and_openpulse_reject_the_same_documents(tmp_path):
    from core.evidence_contract import validate_contract

    consumer = _consumer()
    doc = _attest_docs(tmp_path)[0]
    for name, bad in _mutants(doc).items():
        assert validate_contract(bad), f"OpenPulse accepted: {name}"
        assert not consumer.check(bad).valid, f"the consumer accepted: {name}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_verify_mjs_rejects_unknown_and_mismatched_versions(tmp_path):
    doc = _attest_docs(tmp_path)[0]
    script = str(ROOT / "conformance" / "evidence-contract" / "verify.mjs")
    cases = {
        "good": (doc, 0, "OK"),
        "unknown": ({**doc, "contract_version": "2.9.0"}, 1, "unsupported contract_version"),
        "mismatch": (
            {**doc, "provenance": {**doc["provenance"], "contract_version": "2.3.0"}},
            1,
            "provenance.contract_version differs",
        ),
    }
    for name, (document, code, text) in cases.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        done = subprocess.run(["node", script, str(path)], capture_output=True, text=True)
        assert done.returncode == code, (name, done.stdout, done.stderr)
        assert text in done.stdout, (name, done.stdout)


def test_openpulse_verifies_a_genuine_1_0_document():
    """Fixed in P3: 1.0 hashes eleven fields; the 1.1 field list made every
    1.0 document fail verify_content_hash (no inspection_coverage)."""
    from core.evidence_contract import verify_content_hash

    v1 = [
        json.loads(line)
        for line in (CONSUMER / "tests" / "fixtures" / "openpulse-1.x.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    v10 = [d for d in v1 if d["contract_version"] == "1.0.0"]
    assert v10 and all(verify_content_hash(d) for d in v10)
    tampered = dict(v10[0], identity={**v10[0]["identity"], "dependency": "someone-else"})
    assert not verify_content_hash(tampered)


def test_the_consumer_and_openpulse_compute_the_same_hashes(tmp_path):
    import copy

    from core.evidence_contract import verify_content_hash

    consumer = _consumer()
    from openpulse_consumer import hashes  # noqa: E402  (loaded by _consumer)

    docs = _attest_docs(tmp_path) + [
        json.loads(line)
        for line in (CONSUMER / "tests" / "fixtures" / "openpulse-1.x.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    for doc in docs:
        assert verify_content_hash(doc) and hashes.hash_problem(doc) is None
        tampered = copy.deepcopy(doc)
        tampered["identity"]["dependency"] = "someone-else"
        assert not verify_content_hash(tampered)
        assert hashes.hash_problem(tampered) is not None
        assert not consumer.check(tampered).valid
