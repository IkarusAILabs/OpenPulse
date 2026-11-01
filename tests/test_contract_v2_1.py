"""Evidence contract 2.1.0: NOT_APPLICABLE inspection coverage (#109, v0.10.0 item V3)."""

from __future__ import annotations

import hashlib
import json

import pytest
from click.testing import CliRunner

from cli.main import cli
from core.evidence_contract import (
    SCHEMA_V2_1_PATH,
    load_v2_schema,
    validate_contract,
    validate_v1_contract,
    verify_content_hash,
)
from core.resources import schema_path
from core.sarif import build_sarif

EVENT = "data/fixtures/django-eol/event.json"

# Non-repository inputs, one per reader, each naming django 4.2 or close to it.
NON_REPO_INPUTS = {
    "watchlist": ["--watchlist", "data/fixtures/watchlist_sample.yaml"],
    "lockfile": ["--lockfile", "data/fixtures/lockfiles/poetry.lock"],
    "manifest": ["--manifest", "data/fixtures/manifests/requirements.txt"],
    "images": ["--images", "data/fixtures/images/inventory_sample.txt"],
}


def _attest(tmp_path, inputs, *extra):
    out = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli, ["attest", *inputs, "--event", EVENT, "--replay", "--output", str(out), *extra]
    )
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    return result, docs


@pytest.mark.parametrize("name", sorted(NON_REPO_INPUTS))
def test_non_repository_inputs_are_not_applicable(tmp_path, name):
    result, docs = _attest(tmp_path, NON_REPO_INPUTS[name])
    assert result.exit_code == 0, result.output
    assert docs
    for doc in docs:
        assert doc["contract_version"] == "2.1.0"
        assert doc["inspection_coverage"] == {"status": "NOT_APPLICABLE", "reasons": []}
        assert validate_contract(doc) == []
        assert verify_content_hash(doc)


def test_sbom_input_is_not_applicable(tmp_path):
    sbom = tmp_path / "bom.json"
    sbom.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.5",
                "components": [
                    {
                        "type": "library",
                        "name": "django",
                        "version": "4.2",
                        "purl": "pkg:pypi/django@4.2",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result, docs = _attest(tmp_path, ["--sbom", str(sbom)])
    assert result.exit_code == 0, result.output
    assert docs and {d["inspection_coverage"]["status"] for d in docs} == {"NOT_APPLICABLE"}


@pytest.mark.parametrize("coverage", ["COMPLETE", "PARTIAL", "FAILED"])
def test_repository_runs_keep_their_coverage(tmp_path, monkeypatch, coverage):
    from core import github_reader

    def fake_inspect(repo_spec, cli_token=None, timeout=30.0):
        return github_reader.RepoInspection(
            coverage=coverage,
            coverage_reasons=["reason"] if coverage != "COMPLETE" else [],
        )

    monkeypatch.setattr(github_reader, "inspect_github_repo", fake_inspect)
    result, docs = _attest(tmp_path, [*NON_REPO_INPUTS["watchlist"], "--github-repo", "owner/repo"])
    assert result.exit_code == 0, result.output
    assert docs and {d["inspection_coverage"]["status"] for d in docs} == {coverage}
    assert all(validate_contract(d) == [] for d in docs)


def test_not_applicable_never_trips_a_gate_or_a_warning(tmp_path):
    """Treated like COMPLETE: --fail-on decides on verdicts alone, SARIF stays quiet."""
    sarif = tmp_path / "r.sarif"
    result, docs = _attest(
        tmp_path, NON_REPO_INPUTS["watchlist"], "--fail-on", "critical", "--sarif", str(sarif)
    )
    assert result.exit_code == 0, result.output
    run = json.loads(sarif.read_text(encoding="utf-8"))["runs"][0]
    assert run["properties"]["inspection_coverage"] == "NOT_APPLICABLE"
    assert "toolExecutionNotifications" not in run["invocations"][0]


def test_build_sarif_warns_only_on_partial_and_failed(tmp_path):
    for status, warns in (
        ("COMPLETE", False),
        ("NOT_APPLICABLE", False),
        ("PARTIAL", True),
        ("FAILED", True),
    ):
        log = build_sarif([], tool_version="0", coverage={"status": status, "reasons": []})
        assert ("toolExecutionNotifications" in log["runs"][0]["invocations"][0]) is warns, status


def test_not_applicable_is_a_2_1_value_only(tmp_path):
    _result, docs = _attest(tmp_path, NON_REPO_INPUTS["watchlist"])
    doc = docs[0]
    as_2_0 = json.loads(json.dumps(doc))
    as_2_0["contract_version"] = as_2_0["provenance"]["contract_version"] = "2.0.0"
    errors = validate_v1_contract(as_2_0, load_v2_schema())
    assert any("inspection_coverage" in e for e in errors), errors
    complete = json.loads(json.dumps(as_2_0))
    complete["inspection_coverage"]["status"] = "COMPLETE"
    assert validate_v1_contract(complete, load_v2_schema()) == []


#: Line-ending-neutral SHA-256 of each published schema before 2.1. Sibling
#: schemas are never edited (docs/EVIDENCE_CONTRACT.md, versioning policy).
PUBLISHED = {
    "v1": "d9863e7ce6494800c1adf1338fddb1c8115466489f51a4b94f06fadf3692aee9",
    "v1.1": "517cd0dc367c9e06a5ee92e2bb4322fb6a8ad3a43760d6e13aac14f3352cd161",
    "v1.2": "ab48d7cf15a1b4e3d345990bcc910b13ecd529e637a919b5234a799ad1963718",
    "v2": "e15f19d3871d1d2571315a8208db33829f815002f55363529528ef723ec0ca46",
}


@pytest.mark.parametrize("version", sorted(PUBLISHED))
def test_earlier_schemas_are_byte_identical(version):
    raw = schema_path("evidence-contract", version, "schema.json").read_bytes()
    assert hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == PUBLISHED[version]


def test_the_2_1_schema_is_2_0_plus_one_value():
    v2 = load_v2_schema()
    v21 = json.loads(SCHEMA_V2_1_PATH.read_text(encoding="utf-8"))
    enum = v21["properties"]["inspection_coverage"]["properties"]["status"]["enum"]
    assert enum == [
        *v2["properties"]["inspection_coverage"]["properties"]["status"]["enum"],
        "NOT_APPLICABLE",
    ]
    assert v21["properties"]["contract_version"]["const"] == "2.1.0"
    assert set(v21["properties"]) == set(v2["properties"])
