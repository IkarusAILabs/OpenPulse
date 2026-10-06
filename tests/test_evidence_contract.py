import json

from click.testing import CliRunner

from core.evidence_contract import (
    CONTRACT_VERSION,
    build_v1_contract,
    validate_v1_contract,
    verify_v1_content_hash,
)
from core.risk.check import check_dependency
from core.schema.models import OSSEvent


def event(path):
    with open(path, encoding="utf-8") as handle:
        return OSSEvent(**json.load(handle))


def test_v1_contract_schema_and_hash():
    event_data = event("data/fixtures/django-eol/event.json")
    dependency = {
        "kind": "package",
        "package": "django",
        "ecosystem": "PyPI",
        "version": "4.2",
    }
    doc = build_v1_contract(event_data, check_dependency(dependency, [event_data]))
    assert doc["contract_version"] == CONTRACT_VERSION == "1.0.0"
    assert not validate_v1_contract(doc), validate_v1_contract(doc)
    assert verify_v1_content_hash(doc)
    assert "event_context" in doc
    assert "evidence_refs" in doc
    assert "temporal" in doc


def test_v1_contract_rejects_tampering():
    event_data = event("data/fixtures/django-eol/event.json")
    dependency = {
        "kind": "package",
        "package": "django",
        "ecosystem": "PyPI",
        "version": "4.2",
    }
    doc = build_v1_contract(event_data, check_dependency(dependency, [event_data]))
    doc["assessment"]["reason"] = "tampered"
    assert not verify_v1_content_hash(doc)


def test_v1_contract_rejects_unknown_values():
    event_data = event("data/fixtures/django-eol/event.json")
    dependency = {
        "kind": "package",
        "package": "django",
        "ecosystem": "PyPI",
        "version": "4.2",
    }
    doc = build_v1_contract(event_data, check_dependency(dependency, [event_data]))
    doc["assessment"]["relationship"] = "NOT_REAL"
    assert validate_v1_contract(doc)


def test_attest_cli_emits_json():
    from cli.main import cli

    result = CliRunner().invoke(
        cli,
        [
            "attest",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
        ],
    )
    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.splitlines() if line.startswith("{")]
    assert len(lines) == 3
    for line in lines:
        doc = json.loads(line)
        assert not validate_v1_contract(doc)
        assert verify_v1_content_hash(doc)
