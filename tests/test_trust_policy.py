"""Trust policy gates (track T, T-E1, v0.14.0 item Y2): offline, stubbed sources."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from core import trust_policy as tp
from core.trust_policy import Policy, PolicyError, applies, evaluate, load, parse, unchecked

ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")
MANIFEST = str(ROOT / "data/fixtures/manifests/requirements.txt")
LOCKFILE = str(ROOT / "data/fixtures/lockfiles/poetry.lock")
DJANGO = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
MAL = {"vulns": [{"id": "MAL-2026-0001"}]}


def _record(check, status, statement="fixed statement"):
    return {"check": check, "status": status, "statement": statement}


# ---------------------------------------------------------------------------
# Parsing and validation
# ---------------------------------------------------------------------------


def test_a_policy_parses_both_entry_forms():
    policy = parse(
        {
            "version": 1,
            "prohibit": [
                "confirmed_malicious",
                {"condition": "lookalike_name", "packages": ["npm:@acme/*"]},
            ],
            "blocklist": ["npm:event-stream", "PyPI:requests==2.19.0"],
        }
    )
    assert [r.condition for r in policy.rules] == ["confirmed_malicious", "lookalike_name"]
    assert policy.needs_trust and not policy.needs_digests
    assert policy.blocklist[1] == ("pypi", "requests", "2.19.0")


@pytest.mark.parametrize(
    ("doc", "reason"),
    [
        ({"version": 2, "prohibit": ["confirmed_malicious"]}, "version must be 1"),
        ({"version": 1, "prohibit": ["confirmed_malicious"], "allow": []}, "unknown key"),
        ({"version": 1, "prohibit": ["be_safe"]}, "unknown condition"),
        ({"version": 1, "prohibit": ["lookalike_name"]}, "name the packages"),
        ({"version": 1, "prohibit": ["missing_provenance"]}, "name the packages"),
        ({"version": 1, "blocklist": ["event-stream"]}, "ECOSYSTEM:NAME"),
        ({"version": 1}, "prohibits nothing"),
        (["confirmed_malicious"], "expected a mapping"),
    ],
)
def test_invalid_policies_are_refused_with_the_reason(doc, reason):
    with pytest.raises(PolicyError, match=reason):
        parse(doc)


def test_invalid_yaml_is_refused(tmp_path):
    path = tmp_path / "policy.yml"
    path.write_text("version: 1\nprohibit: [unclosed\n", encoding="utf-8")
    with pytest.raises(PolicyError, match="not valid YAML"):
        load(path)


def test_experimental_conditions_are_named():
    policy = parse(
        {
            "version": 1,
            "prohibit": [
                {"condition": "public_private_name", "packages": ["npm:@acme/*"]},
                "confirmed_malicious",
            ],
        }
    )
    assert policy.experimental == ["public_private_name"]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _policy(*prohibit, blocklist=None):
    doc = {"version": 1, "prohibit": list(prohibit)}
    if blocklist:
        doc["blocklist"] = blocklist
    return parse(doc)


def test_a_prohibited_status_is_a_violation_with_its_statement():
    policy = _policy("confirmed_malicious")
    violations = evaluate(policy, DJANGO, [_record("malicious", "CONFIRMED_MALICIOUS", "cited")])
    assert violations == [
        {
            "condition": "confirmed_malicious",
            "dependency": "PyPI:django==4.2",
            "check": "malicious",
            "status": "CONFIRMED_MALICIOUS",
            "statement": "cited",
            "label": "measured",
        }
    ]


def test_other_statuses_are_not_violations():
    policy = _policy("confirmed_malicious", "not_found_in_registry")
    records = [
        _record("malicious", "MISSING_EVIDENCE"),
        _record("registry_existence", "NOT_PERFORMED"),
        _record("lookalike", "SUSPICIOUS_INCONCLUSIVE"),
    ]
    assert evaluate(policy, DJANGO, records) == []


def test_scoped_conditions_apply_only_to_their_packages():
    policy = _policy({"condition": "missing_provenance", "packages": ["PyPI:acme-*"]})
    records = [_record("provenance", "MISSING_EVIDENCE")]
    acme = {"kind": "package", "package": "Acme_Billing", "ecosystem": "pypi", "version": "1"}
    assert evaluate(policy, DJANGO, records) == []
    assert [v["condition"] for v in evaluate(policy, acme, records)] == ["missing_provenance"]


def test_blocklist_matches_names_and_pinned_versions():
    policy = _policy(blocklist=["PyPI:Django==4.2", "npm:event-stream"])
    assert [v["condition"] for v in evaluate(policy, DJANGO, [])] == ["blocklisted"]
    other = dict(DJANGO, version="5.0")
    assert evaluate(policy, other, []) == []
    stream = {"kind": "package", "package": "event-stream", "ecosystem": "npm", "version": "3.3.6"}
    assert evaluate(policy, stream, [])


def test_images_are_never_matched_by_package_patterns():
    policy = Policy(rules=[], blocklist=(("pypi", "*", None),))
    assert evaluate(policy, {"kind": "image", "ref": "postgres:13"}, []) == []


# ---------------------------------------------------------------------------
# check and attest
# ---------------------------------------------------------------------------


def _write_policy(tmp_path, text):
    path = tmp_path / "policy.yml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def _check(*extra):
    args = ["check", "--manifest", MANIFEST, "--event", EVENT, "--replay", "--ledger", ""]
    return CliRunner().invoke(cli, args + list(extra))


def test_without_a_policy_check_is_unchanged(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("core.malicious.default_query", lambda _body: (200, MAL))
    result = _check()
    assert result.exit_code == 0, result.output
    assert "policy" not in result.output


def test_a_prohibited_condition_fails_check(monkeypatch, tmp_path):
    monkeypatch.setattr("core.malicious.default_query", lambda _body: (200, MAL))
    policy = _write_policy(tmp_path, "version: 1\nprohibit: [confirmed_malicious]\n")
    result = _check("--policy", policy)
    assert result.exit_code == 1, result.output
    assert "PROHIBITED confirmed_malicious: PyPI:django==4.2" in result.output
    assert "gate failed" in result.output


def test_unreachable_sources_never_fail_a_policy(monkeypatch, tmp_path):
    """NOT_PERFORMED is not a prohibited status: the policy cannot fail on silence."""
    policy = _write_policy(
        tmp_path, "version: 1\nprohibit: [confirmed_malicious, not_found_in_registry]\n"
    )
    assert _check("--policy", policy).exit_code == 0


def test_a_blocklist_needs_no_network(monkeypatch, tmp_path):
    asked = []
    monkeypatch.setattr("core.malicious.default_query", lambda body: asked.append(body))
    policy = _write_policy(tmp_path, "version: 1\nblocklist: ['PyPI:django']\n")
    result = _check("--policy", policy)
    assert result.exit_code == 1 and "PROHIBITED blocklisted" in result.output
    assert asked == []


def test_the_default_policy_file_is_used_when_present(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".openpulse").mkdir()
    (tmp_path / ".openpulse" / "policy.yml").write_text(
        "version: 1\nblocklist: ['PyPI:django']\n", encoding="utf-8"
    )
    result = _check()
    assert result.exit_code == 1 and "policy: .openpulse" in result.output.replace("\\", "/")


def test_a_missing_or_invalid_policy_is_an_error(tmp_path):
    assert "policy file not found" in _check("--policy", str(tmp_path / "nope.yml")).output
    bad = _write_policy(tmp_path, "version: 1\nprohibit: [lookalike_name]\n")
    result = _check("--policy", bad)
    assert result.exit_code != 0 and "name the packages" in result.output


def test_digest_mismatch_fails_on_a_lockfile(monkeypatch, tmp_path):
    published = {"urls": [{"filename": "x.whl", "digests": {"sha256": "f" * 64}}]}
    monkeypatch.setattr("core.digest_integrity.default_fetch", lambda _url: (200, published))
    policy = _write_policy(tmp_path, "version: 1\nprohibit: [digest_mismatch]\n")
    args = ["check", "--lockfile", LOCKFILE, "--event", EVENT, "--replay", "--ledger", ""]
    result = CliRunner().invoke(cli, [*args, "--policy", policy])
    assert result.exit_code == 1, result.output
    assert "PROHIBITED digest_mismatch" in result.output


def test_attest_writes_every_output_then_fails(monkeypatch, tmp_path):
    monkeypatch.setattr("core.malicious.default_query", lambda _body: (200, MAL))
    policy = _write_policy(tmp_path, "version: 1\nprohibit: [confirmed_malicious]\n")
    out = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli,
        ["attest", "--manifest", MANIFEST, "--event", EVENT, "--replay"]
        + ["--output", str(out), "--policy", policy],
    )
    assert result.exit_code == 1, result.output
    assert out.read_text(encoding="utf-8").strip()
    assert "PROHIBITED confirmed_malicious" in result.output


def test_experimental_conditions_warn(monkeypatch, tmp_path):
    policy = _write_policy(
        tmp_path,
        "version: 1\nprohibit:\n  - condition: unconfirmed_repository\n"
        "    packages: ['PyPI:acme-*']\n",
    )
    result = _check("--policy", policy)
    assert "unconfirmed_repository is experimental" in result.output


# ---------------------------------------------------------------------------
# Unchecked: a prohibited check that applied but did not run
# ---------------------------------------------------------------------------


def test_unchecked_defaults_to_fail_and_only_takes_fail_or_pass():
    assert _policy("confirmed_malicious").unchecked == "fail"
    doc = {"version": 1, "prohibit": ["confirmed_malicious"], "unchecked": "pass"}
    assert parse(doc).unchecked == "pass"
    with pytest.raises(PolicyError, match="unchecked must be fail or pass"):
        parse({**doc, "unchecked": "ignore"})


def test_a_check_that_did_not_run_is_unchecked_and_one_that_ran_is_not():
    policy = _policy("confirmed_malicious", "not_found_in_registry")
    down = [
        _record("malicious", "NOT_PERFORMED", "OSV gave no usable answer"),
        _record("registry_existence", "VERIFIED_RELATIONSHIP"),
    ]
    (only,) = unchecked(policy, DJANGO, down)
    assert only["condition"] == "unchecked confirmed_malicious"
    assert only["statement"] == "OSV gave no usable answer"
    assert unchecked(policy, DJANGO, []) and len(unchecked(policy, DJANGO, [])) == 2
    ran = [
        _record("malicious", "MISSING_EVIDENCE"),
        _record("registry_existence", "VERIFIED_FAILURE"),
    ]
    assert unchecked(policy, DJANGO, ran) == []


@pytest.mark.parametrize(
    ("check", "dep", "private", "expected"),
    [
        ("provenance", {"ecosystem": "npm", "version": "1.0.0"}, False, False),
        ("provenance", {"ecosystem": "PyPI", "version": None}, False, False),
        ("provenance", {"ecosystem": "PyPI", "version": "1.0"}, False, True),
        ("registry_existence", {"ecosystem": "PyPI", "version": "1.0"}, True, False),
        ("dependency_confusion", {"ecosystem": "PyPI", "version": "1.0"}, False, False),
        ("dependency_confusion", {"ecosystem": "PyPI", "version": "1.0"}, True, True),
        ("malicious", {"ecosystem": "npm", "version": None}, True, True),
        ("publisher_change", {"ecosystem": "npm", "version": None}, False, False),
    ],
)
def test_checks_that_do_not_apply_are_never_unchecked(check, dep, private, expected):
    assert applies(check, dep, private) is expected


def test_unchecked_respects_the_package_scope():
    policy = parse(
        {
            "version": 1,
            "prohibit": [{"condition": "missing_provenance", "packages": ["PyPI:acme-*"]}],
        }
    )
    assert unchecked(policy, DJANGO, []) == []
    acme = {**DJANGO, "package": "acme-core"}
    assert [v["condition"] for v in unchecked(policy, acme, [])] == ["unchecked missing_provenance"]


def test_the_gate_implies_digest_mismatch_for_every_package():
    policy = tp.parse({"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    gated, added = tp.with_gate_implied(policy)
    assert added == ["digest_mismatch"] and gated.needs_digests and not policy.needs_digests
    assert gated.blocklist == policy.blocklist and gated.unchecked == policy.unchecked


def test_a_scoped_digest_rule_is_widened_not_doubled():
    policy = tp.parse(
        {"version": 1, "prohibit": [{"condition": "digest_mismatch", "packages": ["PyPI:django"]}]}
    )
    gated, added = tp.with_gate_implied(policy)
    assert added == ["digest_mismatch"]
    assert [(r.condition, r.packages) for r in gated.rules] == [("digest_mismatch", ())]


def test_an_unscoped_digest_rule_is_left_as_it_is():
    policy = tp.parse({"version": 1, "prohibit": ["digest_mismatch"]})
    assert tp.with_gate_implied(policy) == (policy, [])
