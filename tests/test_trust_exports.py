"""Trust records in SARIF and DefectDojo (track T, T-E1, v0.14.0 item Y4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from core.defectdojo import build_findings
from core.evidence_contract import build_contract, trust_assurance_block
from core.risk.check import check_dependency
from core.sarif import build_sarif, render_summary
from core.schema.models import OSSEvent

ROOT = Path(__file__).resolve().parents[1]
EVENT = ROOT / "data/fixtures/django-eol/event.json"
MANIFEST = str(ROOT / "data/fixtures/manifests/requirements.txt")
DJANGO = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
OSV = "https://osv.dev/vulnerability/MAL-2026-1"
URI = "requirements.txt"


def _checks():
    def record(status, statement, **extra):
        return {"status": status, "statement": statement, "evidence": extra}

    return {
        "malicious": record(
            "CONFIRMED_MALICIOUS", "OSV published 1 record", records=[{"url": OSV}]
        ),
        "registry_existence": [record("VERIFIED_RELATIONSHIP", "version found")],
        "provenance": record("MISSING_EVIDENCE", "no provenance published"),
        "lookalike": record("SUSPICIOUS_INCONCLUSIVE", "resembles 1 reference name"),
    }


@pytest.fixture
def docs():
    event = OSSEvent(**json.loads(EVENT.read_text(encoding="utf-8")))
    verdict = check_dependency(DJANGO, [event])
    block = trust_assurance_block(_checks())
    # Two events' worth of contracts for one dependency: trust must not repeat.
    return [(build_contract(event, verdict, trust_assurance=block), URI)] * 2


def _violation(condition, check=None, status=None):
    v = {"condition": condition, "uri": URI, "label": "django==4.2", "statement": "policy"}
    if check:
        v.update(check=check, status=status)
    return v


def _trust(sarif):
    return [r for r in sarif["runs"][0]["results"] if r["ruleId"].startswith("openpulse/trust/")]


# ---------------------------------------------------------------------------
# SARIF
# ---------------------------------------------------------------------------


def test_without_a_policy_levels_follow_the_status_never_a_score(docs):
    sarif = build_sarif(docs, tool_version="0.14.0")
    trust = {r["ruleId"]: r for r in _trust(sarif)}
    assert set(trust) == {"openpulse/trust/malicious", "openpulse/trust/lookalike"}
    assert trust["openpulse/trust/malicious"]["level"] == "warning"
    assert trust["openpulse/trust/lookalike"]["level"] == "note"
    assert trust["openpulse/trust/malicious"]["properties"]["references"] == [OSV]
    assert all(r["properties"]["used_in_verdict"] is False for r in trust.values())
    assert "security-severity" not in json.dumps(sarif)


def test_policy_violations_are_errors(docs):
    violations = [
        _violation("confirmed_malicious", "malicious", "CONFIRMED_MALICIOUS"),
        _violation("missing_provenance", "provenance", "MISSING_EVIDENCE"),
        _violation("blocklisted"),
    ]
    trust = {
        r["ruleId"]: r
        for r in _trust(build_sarif(docs, tool_version="0", trust_violations=violations))
    }
    assert trust["openpulse/trust/malicious"]["level"] == "error"
    assert trust["openpulse/trust/malicious"]["properties"]["policy_condition"] == (
        "confirmed_malicious"
    )
    assert trust["openpulse/trust/malicious"]["properties"]["references"] == [OSV]
    assert trust["openpulse/trust/provenance"]["level"] == "error"
    assert trust["openpulse/trust/blocklisted"]["level"] == "error"
    assert trust["openpulse/trust/lookalike"]["level"] == "note"  # not prohibited


def test_trust_results_never_change_the_verdict_results(docs):
    plain_docs = [(dict(d, trust_assurance=None), u) for d, u in docs]
    without = build_sarif(plain_docs, tool_version="0")["runs"][0]["results"]
    with_trust = build_sarif(docs, tool_version="0")["runs"][0]["results"]
    verdicts = [r for r in with_trust if not r["ruleId"].startswith("openpulse/trust/")]
    assert [r["level"] for r in verdicts] == [r["level"] for r in without]


def test_trust_rules_point_at_the_policy_docs(docs):
    rules = build_sarif(docs, tool_version="0")["runs"][0]["tool"]["driver"]["rules"]
    trust = [r for r in rules if r["id"].startswith("openpulse/trust/")]
    assert trust and all(r["helpUri"].endswith("docs/TRUST_POLICY.md") for r in trust)
    assert {r["name"] for r in trust} == {"TrustMalicious", "TrustLookalike"}


def test_the_sarif_is_deterministic(docs):
    a = build_sarif(docs, tool_version="0", trust_violations=[_violation("blocklisted")])
    b = build_sarif(docs, tool_version="0", trust_violations=[_violation("blocklisted")])
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_the_summary_has_its_own_trust_table(docs):
    summary = render_summary(
        build_sarif(docs, tool_version="0", trust_violations=[_violation("blocklisted")])
    )
    assert "### Trust checks" in summary
    assert "3 record(s) to review; 1 prohibited by the trust policy" in summary
    assert "| error | `requirements.txt` | `django==4.2` | blocklisted |" in summary
    assert "not a risk score" in summary


# ---------------------------------------------------------------------------
# DefectDojo
# ---------------------------------------------------------------------------


def test_defectdojo_severity_follows_the_policy(docs):
    findings = build_findings(
        docs, [_violation("confirmed_malicious", "malicious", "CONFIRMED_MALICIOUS")]
    )["findings"]
    trust = {f["vuln_id_from_tool"]: f for f in findings if "trust" in f["tags"]}
    assert trust["openpulse/trust/malicious"]["severity"] == "High"
    assert trust["openpulse/trust/lookalike"]["severity"] == "Info"
    assert "the severity reflects that policy" in trust["openpulse/trust/malicious"]["description"]
    assert trust["openpulse/trust/malicious"]["references"] == OSV
    unprohibited = {
        f["vuln_id_from_tool"]: f for f in build_findings(docs)["findings"] if "trust" in f["tags"]
    }
    assert unprohibited["openpulse/trust/malicious"]["severity"] == "Low"
    assert "not a risk score" in unprohibited["openpulse/trust/malicious"]["description"]


def test_defectdojo_and_sarif_share_identities(docs):
    sarif = {
        r["partialFingerprints"]["openpulseFinding/v1"]
        for r in _trust(build_sarif(docs, tool_version="0"))
    }
    dojo = {
        f["unique_id_from_tool"] for f in build_findings(docs)["findings"] if "trust" in f["tags"]
    }
    assert sarif == dojo and len(sarif) == 2


# ---------------------------------------------------------------------------
# attest end to end
# ---------------------------------------------------------------------------


def _attest(tmp_path, *extra):
    sarif, dojo = tmp_path / "out.sarif", tmp_path / "dojo.json"
    result = CliRunner().invoke(
        cli,
        ["attest", "--manifest", MANIFEST, "--event", str(EVENT), "--replay", "--trust"]
        + ["--output", str(tmp_path / "c.jsonl"), "--sarif", str(sarif)]
        + ["--defectdojo", str(dojo), *extra],
    )
    sarif_doc = json.loads(sarif.read_text(encoding="utf-8"))
    dojo_doc = json.loads(dojo.read_text(encoding="utf-8"))
    return result, sarif_doc, dojo_doc


def test_attest_marks_prohibited_trust_as_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.malicious.default_query",
        lambda body: (
            (200, {"vulns": [{"id": "MAL-2026-1"}]})
            if body["package"]["name"] == "django"
            else (200, {})
        ),
    )
    policy = tmp_path / "policy.yml"
    policy.write_text("version: 1\nprohibit: [confirmed_malicious]\n", encoding="utf-8")
    result, sarif, dojo = _attest(tmp_path, "--policy", str(policy))
    assert result.exit_code == 1
    malicious = [r for r in _trust(sarif) if r["ruleId"] == "openpulse/trust/malicious"]
    assert [(r["level"], r["properties"]["dependency"]) for r in malicious] == [
        ("error", "django==4.2")
    ]
    assert sarif["runs"][0]["properties"]["trust_policy_violations"] == 1
    assert [f["severity"] for f in dojo["findings"] if "malicious" in f["tags"]] == ["High"]


def test_attest_without_a_policy_reports_trust_as_warnings(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.malicious.default_query", lambda body: (200, {"vulns": [{"id": "MAL-2026-1"}]})
    )
    result, sarif, _ = _attest(tmp_path)
    assert result.exit_code == 0, result.output
    levels = {r["level"] for r in _trust(sarif) if r["ruleId"] == "openpulse/trust/malicious"}
    assert levels == {"warning"}


def test_reputation_indicators_are_notes_and_errors_only_when_prohibited():
    """v0.16.0 Q5: the indicators flow through like any trust check."""
    event = OSSEvent(**json.loads(EVENT.read_text(encoding="utf-8")))
    verdict = check_dependency(DJANGO, [event])
    moved = {
        "status": "SUSPICIOUS_INCONCLUSIVE",
        "statement": "the claimed repository answers under another name (transferred)",
        "evidence": {"url": "https://github.com/acme-org/widget"},
    }
    young = {"status": "MISSING_EVIDENCE", "statement": "no indicator to report", "evidence": {}}
    block = trust_assurance_block({"repository_moved": moved, "young_popular_repository": young})
    docs = [(build_contract(event, verdict, trust_assurance=block), URI)]
    trust = {r["ruleId"]: r for r in _trust(build_sarif(docs, tool_version="0.16.0"))}
    assert set(trust) == {"openpulse/trust/repository_moved"}
    result = trust["openpulse/trust/repository_moved"]
    assert result["level"] == "note"
    assert result["properties"]["references"] == ["https://github.com/acme-org/widget"]
    prohibited = [_violation("repository_moved", "repository_moved", "SUSPICIOUS_INCONCLUSIVE")]
    sarif = build_sarif(docs, tool_version="0.16.0", trust_violations=prohibited)
    assert _trust(sarif)[0]["level"] == "error"
    findings = build_findings(docs, prohibited)["findings"]
    assert any(f["vuln_id_from_tool"] == "openpulse/trust/repository_moved" for f in findings)
