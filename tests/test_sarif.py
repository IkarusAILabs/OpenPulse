"""SARIF 2.1.0 output for the GitHub Action (Phase C3).

Offline: every input is a repo fixture. The shape is checked against a
subset of the official SARIF 2.1.0 schema (the objects this converter
emits, with the official ``additionalProperties: false`` so a misspelt
property fails), using the repo's own fail-closed schema walker.
"""

import copy
import json

import pytest
from click.testing import CliRunner

from cli.main import cli
from core.evidence_contract import build_v1_contract, validate_v1_contract
from core.risk.check import check_dependency
from core.sarif import NO_EVIDENCE_RULE, build_sarif, contract_level, render_summary
from core.schema.models import OSSEvent

_STR = {"type": "string"}
_MESSAGE = {
    "type": "object",
    "required": ["text"],
    "additionalProperties": False,
    "properties": {"text": _STR},
}
_BAG = {"type": "object"}

#: Subset of https://json.schemastore.org/sarif-2.1.0.json: the
#: properties of each object type below are copied from the official
#: definitions (property names, required lists, level enum).
SARIF_SUBSET = {
    "type": "object",
    "required": ["version", "runs"],
    "additionalProperties": False,
    "properties": {
        "$schema": _STR,
        "version": {"const": "2.1.0"},
        "runs": {"type": "array", "items": {"$ref": "#/$defs/run"}},
    },
    "$defs": {
        "run": {
            "type": "object",
            "required": ["tool"],
            "additionalProperties": False,
            "properties": {
                "tool": {"$ref": "#/$defs/tool"},
                "invocations": {"type": "array", "items": {"$ref": "#/$defs/invocation"}},
                "results": {"type": "array", "items": {"$ref": "#/$defs/result"}},
                "properties": _BAG,
            },
        },
        "tool": {
            "type": "object",
            "required": ["driver"],
            "additionalProperties": False,
            "properties": {"driver": {"$ref": "#/$defs/toolComponent"}},
        },
        "toolComponent": {
            "type": "object",
            "required": ["name"],
            "additionalProperties": False,
            "properties": {
                "name": _STR,
                "informationUri": {"type": "string", "format": "uri"},
                "version": _STR,
                "semanticVersion": _STR,
                "rules": {"type": "array", "items": {"$ref": "#/$defs/reportingDescriptor"}},
            },
        },
        "reportingDescriptor": {
            "type": "object",
            "required": ["id"],
            "additionalProperties": False,
            "properties": {
                "id": _STR,
                "name": _STR,
                "shortDescription": _MESSAGE,
                "helpUri": {"type": "string", "format": "uri"},
                "properties": _BAG,
            },
        },
        "invocation": {
            "type": "object",
            "required": ["executionSuccessful"],
            "additionalProperties": False,
            "properties": {
                "executionSuccessful": {"type": "boolean"},
                "toolExecutionNotifications": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/notification"},
                },
            },
        },
        "notification": {
            "type": "object",
            "required": ["message"],
            "additionalProperties": False,
            "properties": {
                "level": {"enum": ["none", "note", "warning", "error"]},
                "message": _MESSAGE,
            },
        },
        "result": {
            "type": "object",
            "required": ["message"],
            "additionalProperties": False,
            "properties": {
                "ruleId": _STR,
                "ruleIndex": {"type": "integer"},
                "level": {"enum": ["none", "note", "warning", "error"]},
                "message": _MESSAGE,
                "locations": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/$defs/location"},
                },
                "partialFingerprints": _BAG,
                "properties": _BAG,
            },
        },
        "location": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"physicalLocation": {"$ref": "#/$defs/physicalLocation"}},
        },
        "physicalLocation": {
            "type": "object",
            "required": ["artifactLocation"],
            "additionalProperties": False,
            "properties": {"artifactLocation": {"$ref": "#/$defs/artifactLocation"}},
        },
        "artifactLocation": {
            "type": "object",
            "required": ["uri"],
            "additionalProperties": False,
            "properties": {"uri": {"type": "string", "minLength": 1}},
        },
    },
}

EVENTS = [
    "data/fixtures/django-eol/event.json",
    "data/fixtures/bitnami/event.json",
    "data/fixtures/itext-license/event.json",
]


def _event(path):
    return OSSEvent(**json.load(open(path, encoding="utf-8")))


def _contract(dep, event_path):
    event = _event(event_path)
    return build_v1_contract(event, check_dependency(dep, [event]))


def _pkg(name, version):
    return {"kind": "package", "package": name, "version": version, "ecosystem": "pypi"}


@pytest.fixture
def django_affected():
    doc = _contract(_pkg("django", "4.2"), EVENTS[0])
    assert doc["assessment"]["affected"] and doc["event_context"]["impact"] == "ACTION"
    return doc


def _with(doc, *, impact=None, relationship=None, affected=None):
    out = copy.deepcopy(doc)
    if impact is not None:
        out["event_context"]["impact"] = impact
    if relationship is not None:
        out["assessment"]["relationship"] = relationship
        out["affected_dependency"]["relationship"] = relationship
    if affected is not None:
        out["assessment"]["affected"] = affected
        out["affected_dependency"]["affected"] = affected
    return out


def test_level_mapping(django_affected):
    assert contract_level(django_affected) == "error"
    assert contract_level(_with(django_affected, impact="CRITICAL")) == "error"
    assert contract_level(_with(django_affected, impact="REVIEW")) == "warning"
    assert contract_level(_with(django_affected, impact="WATCH")) == "note"
    related = _with(django_affected, relationship="RELATED", affected=False)
    assert contract_level(related) == "note"
    unknown = _with(django_affected, relationship="UNKNOWN", affected=False)
    assert contract_level(unknown) == "note"
    not_affected = _with(django_affected, relationship="NOT_AFFECTED", affected=False)
    assert contract_level(not_affected) is None


def test_not_affected_is_omitted_and_counted():
    doc = _contract(_pkg("django", "5.0"), EVENTS[0])
    assert doc["assessment"]["relationship"] == "NOT_AFFECTED"
    run = build_sarif([(doc, "requirements.txt")], tool_version="0")["runs"][0]
    assert run["results"] == []
    assert run["properties"]["not_affected_omitted"] == 1


def test_result_cites_evidence_urls_and_content_hash(django_affected):
    sarif = build_sarif([(django_affected, "requirements.txt")], tool_version="0")
    (result,) = sarif["runs"][0]["results"]
    content_hash = django_affected["provenance"]["content_hash"]
    urls = [ref["url"] for ref in django_affected["evidence_refs"]]
    assert result["level"] == "error"
    assert result["ruleId"] == "openpulse/eol"
    assert result["properties"]["content_hash"] == content_hash
    assert result["properties"]["evidence_urls"] == urls
    assert content_hash in result["message"]["text"]
    assert all(url in result["message"]["text"] for url in urls)
    uri = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert uri == "requirements.txt"


def test_unknown_dependency_reported_once_never_dropped():
    dep = _pkg("boto3", "1.34.90")
    docs = [_contract(dep, path) for path in EVENTS]
    assert all(d["assessment"]["relationship"] == "UNKNOWN" for d in docs)
    results = build_sarif([(d, "req.txt") for d in docs], tool_version="0")["runs"][0]["results"]
    (result,) = results
    assert result["ruleId"] == NO_EVIDENCE_RULE
    assert result["level"] == "note"
    assert len(result["properties"]["content_hashes"]) == len(EVENTS)
    # Evidence of events that do not concern the dependency is not cited.
    assert "evidence_urls" not in result["properties"]


def test_unknown_pairs_superseded_by_a_real_verdict(django_affected):
    unrelated = _contract(_pkg("django", "4.2"), EVENTS[2])
    assert unrelated["assessment"]["relationship"] == "UNKNOWN"
    entries = [(django_affected, "r.txt"), (unrelated, "r.txt")]
    results = build_sarif(entries, tool_version="0")["runs"][0]["results"]
    assert [r["ruleId"] for r in results] == ["openpulse/eol"]


def test_partial_coverage_is_a_warning_never_a_pass(django_affected):
    coverage = {"status": "PARTIAL", "reasons": ["tree truncated"]}
    sarif = build_sarif([(django_affected, "r.txt")], tool_version="0", coverage=coverage)
    run = sarif["runs"][0]
    (note,) = run["invocations"][0]["toolExecutionNotifications"]
    assert note["level"] == "warning" and "PARTIAL" in note["message"]["text"]
    assert run["properties"]["inspection_coverage"] == "PARTIAL"
    summary = render_summary(sarif)
    assert "[!WARNING]" in summary and "tree truncated" in summary
    complete = build_sarif([(django_affected, "r.txt")], tool_version="0")
    assert "toolExecutionNotifications" not in complete["runs"][0]["invocations"][0]


def test_summary_escapes_untrusted_table_text(django_affected):
    doc = copy.deepcopy(django_affected)
    doc["affected_dependency"]["label"] = "evil|pkg\n| injected |"
    summary = render_summary(build_sarif([(doc, "r.txt")], tool_version="0"))
    row = next(line for line in summary.splitlines() if "evil" in line)
    assert "evil\\|pkg \\| injected \\|" in row


def _attest(tmp_path, name, extra=()):
    args = ["attest", "--manifest", "data/fixtures/manifests/requirements.txt"]
    args += ["--images", "data/fixtures/images/inventory_sample.txt"]
    for path in EVENTS:
        args += ["--event", path]
    sarif = tmp_path / f"{name}.sarif"
    jsonl = tmp_path / f"{name}.jsonl"
    result = CliRunner().invoke(
        cli, [*args, "--output", str(jsonl), "--sarif", str(sarif), *extra]
    )
    assert result.exit_code == 0, result.output
    return sarif, jsonl


def test_cli_sarif_validates_against_schema_subset(tmp_path):
    sarif_path, jsonl = _attest(tmp_path, "a")
    sarif = json.loads(sarif_path.read_text(encoding="utf-8"))
    assert validate_v1_contract(sarif, schema=SARIF_SUBSET) == []
    run = sarif["runs"][0]
    levels = {r["level"] for r in run["results"]}
    assert levels <= {"error", "warning", "note"}
    assert "error" in levels
    # Every result is backed by a contract that was actually emitted.
    hashes = {
        json.loads(line)["provenance"]["content_hash"]
        for line in jsonl.read_text(encoding="utf-8").splitlines()
    }
    for result in run["results"]:
        cited = result["properties"].get("content_hashes") or [result["properties"]["content_hash"]]
        assert set(cited) <= hashes
        rule = run["tool"]["driver"]["rules"][result["ruleIndex"]]
        assert rule["id"] == result["ruleId"]
        uri = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        assert uri.startswith("data/fixtures/") and "\\" not in uri


def test_cli_sarif_is_deterministic(tmp_path):
    first, _ = _attest(tmp_path, "a")
    second, _ = _attest(tmp_path, "b")
    assert first.read_bytes() == second.read_bytes()


def test_cli_summary_appends(tmp_path):
    summary = tmp_path / "summary.md"
    summary.write_text("previous step\n", encoding="utf-8")
    _attest(tmp_path, "a", ["--summary", str(summary)])
    text = summary.read_text(encoding="utf-8")
    assert text.startswith("previous step\n")
    assert "## OpenPulse dependency intelligence" in text


def test_check_fail_on_applies_without_digest():
    """--fail-on gated only the --digest branch; the Action relies on it."""
    args = ["check", "--manifest", "data/fixtures/manifests/requirements.txt"]
    args += ["--event", EVENTS[0], "--ledger", ""]
    assert CliRunner().invoke(cli, [*args, "--fail-on", "action"]).exit_code == 1
    assert CliRunner().invoke(cli, [*args, "--fail-on", "critical"]).exit_code == 0
    assert CliRunner().invoke(cli, args).exit_code == 0


def test_attest_fail_on_gates_after_writing_outputs(tmp_path):
    sarif = tmp_path / "out.sarif"
    base = ["attest", "--manifest", "data/fixtures/manifests/requirements.txt"]
    base += ["--event", EVENTS[0], "--output", str(tmp_path / "c.jsonl"), "--sarif", str(sarif)]
    breached = CliRunner().invoke(cli, [*base, "--fail-on", "action"])
    assert breached.exit_code == 1
    assert json.loads(sarif.read_text(encoding="utf-8"))["runs"][0]["results"]
    assert CliRunner().invoke(cli, [*base, "--fail-on", "critical"]).exit_code == 0
    # UNKNOWN never fails a threshold on its own.
    unknown = ["attest", "--manifest", "data/fixtures/manifests/requirements.txt"]
    unknown += ["--event", EVENTS[2], "--output", str(tmp_path / "u.jsonl")]
    assert CliRunner().invoke(cli, [*unknown, "--fail-on", "affected"]).exit_code == 0
