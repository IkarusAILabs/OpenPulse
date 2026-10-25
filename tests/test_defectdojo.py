"""DefectDojo Generic Findings export (core/defectdojo.py)."""

import json

import pytest
from click.testing import CliRunner

from cli.main import cli
from core.defectdojo import _component, build_findings, finding_severity
from core.sarif import _fingerprint

_ARGS = [
    "attest",
    "--manifest",
    "data/fixtures/manifests/requirements.txt",
    "--images",
    "data/fixtures/images/inventory_sample.txt",
    "--event",
    "data/fixtures/django-eol/event.json",
    "--event",
    "data/fixtures/bitnami/event.json",
]


def _export(tmp_path):
    dojo = tmp_path / "dojo.json"
    sarif = tmp_path / "out.sarif"
    jsonl = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli,
        [*_ARGS, "--defectdojo", str(dojo), "--sarif", str(sarif), "--output", str(jsonl)],
    )
    assert result.exit_code == 0, result.output
    docs = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
    return (
        json.loads(dojo.read_text(encoding="utf-8")),
        json.loads(sarif.read_text(encoding="utf-8")),
        docs,
    )


def test_findings_match_sarif_results_one_for_one(tmp_path):
    dojo, sarif, _ = _export(tmp_path)
    results = sarif["runs"][0]["results"]
    assert len(dojo["findings"]) == len(results)
    sarif_ids = {r["partialFingerprints"]["openpulseFinding/v1"] for r in results}
    assert {f["unique_id_from_tool"] for f in dojo["findings"]} == sarif_ids


def test_generic_findings_shape(tmp_path):
    dojo, _, _ = _export(tmp_path)
    required = {"title", "severity", "description", "date", "active", "verified"}
    for finding in dojo["findings"]:
        assert required <= set(finding)
        assert finding["severity"] in {"Critical", "High", "Medium", "Low", "Info"}
        assert len(finding["date"]) == 10
        assert finding["static_finding"] is True and finding["dynamic_finding"] is False


def test_affected_eol_is_high_with_evidence_and_mitigation(tmp_path):
    dojo, _, _ = _export(tmp_path)
    django = next(f for f in dojo["findings"] if f["component_name"] == "django")
    assert django["severity"] == "High"
    assert django["component_version"] == "4.2"
    assert django["vuln_id_from_tool"] == "evt-django-2026-eol-001"
    assert "https://endoflife.date/django" in django["references"].splitlines()
    assert django["mitigation"]
    assert "Evidence contract: sha256:" in django["description"]


def test_unknown_dependency_is_one_info_finding_never_dropped(tmp_path):
    dojo, _, _ = _export(tmp_path)
    boto = [f for f in dojo["findings"] if f["component_name"] == "boto3"]
    assert len(boto) == 1
    assert boto[0]["severity"] == "Info"
    assert "UNKNOWN is not NOT_AFFECTED" in boto[0]["description"]


def test_not_affected_pairs_are_omitted(tmp_path):
    """Per (dependency, event): a cleared pair never becomes a finding."""
    dojo, _, docs = _export(tmp_path)
    cleared = {
        (d["affected_dependency"]["label"], d["event_context"]["id"])
        for d in docs
        if d["assessment"]["relationship"] == "NOT_AFFECTED"
    }
    assert cleared
    reported = {f["unique_id_from_tool"] for f in dojo["findings"]}
    assert not {_fingerprint(label, event) for label, event in cleared} & reported


def test_export_is_deterministic(tmp_path):
    first, _, docs = _export(tmp_path)
    again = build_findings([(d, "x") for d in docs])
    assert build_findings([(d, "x") for d in docs]) == again
    assert first == _export(tmp_path)[0]


@pytest.mark.parametrize(
    "label,expected",
    [
        ("django==4.2", ("django", "4.2")),
        ("docker.io/postgres:13", ("docker.io/postgres:13", "13")),
        ("localhost:5000/team/redis:7", ("localhost:5000/team/redis:7", "7")),
        ("docker.io/redis@sha256:" + "a" * 64, ("docker.io/redis@sha256:" + "a" * 64, None)),
        ("nginx", ("nginx", None)),
    ],
)
def test_component_split(label, expected):
    assert _component(label) == expected


def test_severity_follows_impact():
    def doc(affected, impact, relationship="AFFECTS_VERSION"):
        return {
            "assessment": {"affected": affected, "relationship": relationship},
            "event_context": {"impact": impact},
        }

    assert finding_severity(doc(True, "CRITICAL")) == "Critical"
    assert finding_severity(doc(True, "ACTION")) == "High"
    assert finding_severity(doc(True, "REVIEW")) == "Medium"
    assert finding_severity(doc(True, "WATCH")) == "Low"
    assert finding_severity(doc(False, "ACTION", "RELATED")) == "Info"
    assert finding_severity(doc(False, "ACTION", "NOT_AFFECTED")) is None
