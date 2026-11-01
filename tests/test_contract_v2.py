"""Evidence contract 2.0.0: RFC 8785 (JCS) content hash (v0.9.0 item B7, finding L8)."""

import hashlib
import json
import math
import shutil
import subprocess

import pytest
from click.testing import CliRunner

from core.evidence_contract import (
    CONTENT_HASH_METHOD,
    CONTRACT_V2_1_VERSION,
    CONTRACT_V2_VERSION,
    build_contract,
    build_v1_contract,
    v2_content_hash,
    validate_contract,
    verify_content_hash,
    verify_v1_content_hash,
)
from core.jcs import JCSError, canonicalize
from core.risk.check import check_dependency
from core.schema.models import OSSEvent

# ---------------------------------------------------------------------------
# JCS (RFC 8785)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("number", "text"),
    [
        (1e30, "1e+30"),
        (4.5, "4.5"),
        (0.002, "0.002"),
        (1e-27, "1e-27"),
        (333333333.33333329, "333333333.3333333"),
        (-0.0, "0"),
        (1e21, "1e+21"),
        (1e20, "100000000000000000000"),
        (100.0, "100"),
        (1e-7, "1e-7"),
        (0.000001, "0.000001"),
        (5e-324, "5e-324"),
        (1.7976931348623157e308, "1.7976931348623157e+308"),
        (2**53, "9007199254740992"),
        (-42, "-42"),
    ],
)
def test_jcs_numbers_follow_ecmascript(number, text):
    assert canonicalize(number) == text.encode()


def test_jcs_sorts_members_by_utf16_code_units():
    """RFC 8785 section 3.2.3: an emoji (surrogates D83D DE00) sorts before U+FB33."""
    keys = ["€", "\r", "דּ", "1", "\U0001f600", "\u0080", "ö"]
    order = list(json.loads(canonicalize({k: 0 for k in keys}).decode("utf-8")))
    assert order == ["\r", "1", "\u0080", "ö", "€", "\U0001f600", "דּ"]


def test_jcs_escapes_strings_like_json_stringify():
    text = canonicalize({"s": 'a"b\\c\b\f\n\r\t\u0001\u001f\u007f é'}).decode("utf-8")
    assert text == '{"s":"a\\"b\\\\c\\b\\f\\n\\r\\t\\u0001\\u001f\u007f é"}'


@pytest.mark.parametrize(
    "value",
    [math.nan, math.inf, 2**53 + 1, "\ud800", {1: "x"}, {"a": {1, 2}}],
    ids=["nan", "inf", "big-int", "lone-surrogate", "int-key", "set"],
)
def test_jcs_rejects_what_it_cannot_represent(value):
    with pytest.raises(JCSError):
        canonicalize(value)


# ---------------------------------------------------------------------------
# Contract 2.0.0
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def django_event():
    with open("data/fixtures/django-eol/event.json", encoding="utf-8") as f:
        return OSSEvent(**json.load(f))


@pytest.fixture
def doc(django_event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    return build_contract(django_event, check_dependency(dep, [django_event]))


def test_v2_document_shape(doc):
    # attest emits 2.1.0 since v0.10.0 (#109): 2.0's hash and shape, one more coverage value.
    assert doc["contract_version"] == CONTRACT_V2_1_VERSION == "2.1.0"
    assert doc["provenance"]["contract_version"] == "2.1.0"
    assert CONTRACT_V2_VERSION == "2.0.0"
    assert doc["provenance"]["content_hash_method"] == CONTENT_HASH_METHOD == "jcs-sha256"
    assert validate_contract(doc) == []
    assert verify_content_hash(doc)


def test_v2_hash_recomputes_from_the_written_rule(doc):
    """The rule in docs/EVIDENCE_CONTRACT.md, applied by hand."""
    body = {k: v for k, v in doc.items() if k not in ("signature", "signing_key_id", "trust_root")}
    body["provenance"] = {
        k: v
        for k, v in doc["provenance"].items()
        if k not in ("content_hash", "generation_timestamp")
    }
    expected = "sha256:" + hashlib.sha256(canonicalize(body)).hexdigest()
    assert doc["provenance"]["content_hash"] == expected == v2_content_hash(doc)


def test_v2_values_are_the_v12_builders(django_event):
    """Only the version and the hash change; the 1.x builder is untouched."""
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    verdict = check_dependency(dep, [django_event])
    v1 = build_v1_contract(django_event, verdict)
    v2 = build_contract(django_event, verdict)
    assert v1["contract_version"] == "1.2.0" and verify_v1_content_hash(v1)
    assert verify_content_hash(v1)  # the dispatcher handles 1.x too
    for name in v1:
        if name != "provenance" and name != "contract_version":
            assert v1[name] == v2[name], name
    assert v1["provenance"]["content_hash"] != v2["provenance"]["content_hash"]


def test_v2_hash_ignores_build_time_and_catches_content(doc):
    later = json.loads(json.dumps(doc))
    later["provenance"]["generation_timestamp"] = "2030-01-01T00:00:00Z"
    assert verify_content_hash(later)
    edited = json.loads(json.dumps(doc))
    edited["assessment"]["relationship"] = "NOT_AFFECTED"
    assert not verify_content_hash(edited)
    wrong_method = json.loads(json.dumps(doc))
    wrong_method["provenance"]["content_hash_method"] = "sha256-sorted-json"
    assert not verify_content_hash(wrong_method)


def test_v2_documents_fail_the_v12_schema(doc):
    from core.evidence_contract import validate_v1_contract

    assert any("contract_version" in e for e in validate_v1_contract(doc))


def test_unknown_contract_version_is_refused(doc):
    assert validate_contract({**doc, "contract_version": "3.0.0"}) != []


def test_attest_cli_emits_v2(tmp_path):
    from cli.main import cli

    watchlist = tmp_path / "wl.yaml"
    watchlist.write_text(
        'version: 1\ndependencies:\n  - package: django\n    ecosystem: PyPI\n    version: "4.2"\n',
        encoding="utf-8",
    )
    out = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli,
        [
            "attest",
            "--watchlist",
            str(watchlist),
            "--event",
            "data/fixtures/django-eol/event.json",
            "--output",
            str(out),
            "--replay",
        ],
    )
    assert result.exit_code == 0, result.output
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert docs and all(d["contract_version"] == "2.1.0" for d in docs)
    assert all(validate_contract(d) == [] and verify_content_hash(d) for d in docs)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_node_verifier_agrees(doc, tmp_path):
    """conformance/evidence-contract/verify.mjs recomputes the hash with no OpenPulse code."""
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps(doc), encoding="utf-8")
    edited = json.loads(json.dumps(doc))
    edited["identity"]["dependency"] = "flask"
    bad.write_text(json.dumps(edited), encoding="utf-8")
    script = "conformance/evidence-contract/verify.mjs"
    ok = subprocess.run(["node", script, str(good)], capture_output=True, text=True, check=False)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert doc["provenance"]["content_hash"] in ok.stdout
    fail = subprocess.run(["node", script, str(bad)], capture_output=True, text=True, check=False)
    assert fail.returncode == 1
