import json
from click.testing import CliRunner
from core.evidence_contract import CONTRACT_VERSION, build_v1_contract, load_schema, validate_v1_contract, verify_v1_content_hash
from core.risk.check import check_dependency
from core.schema.models import OSSEvent

def event(path):
    return OSSEvent(**json.load(open(path, encoding="utf-8")))

def test_v1_contract_schema_and_hash():
    e=event("data/fixtures/django-eol/event.json")
    dep={"kind":"package","package":"django","ecosystem":"PyPI","version":"4.2"}
    doc=build_v1_contract(e,check_dependency(dep,[e]))
    assert doc["contract_version"]==CONTRACT_VERSION=="1.0.0"
    assert not validate_v1_contract(doc), validate_v1_contract(doc)
    assert verify_v1_content_hash(doc)
    assert "event_context" in doc and "evidence_refs" in doc and "temporal" in doc

def test_v1_contract_rejects_tampering():
    e=event("data/fixtures/django-eol/event.json")
    dep={"kind":"package","package":"django","ecosystem":"PyPI","version":"4.2"}
    doc=build_v1_contract(e,check_dependency(dep,[e]))
    doc["assessment"]["reason"]="tampered"
    assert not verify_v1_content_hash(doc)

def test_v1_contract_rejects_unknown_values():
    e=event("data/fixtures/django-eol/event.json")
    dep={"kind":"package","package":"django","ecosystem":"PyPI","version":"4.2"}
    doc=build_v1_contract(e,check_dependency(dep,[e]))
    doc["assessment"]["relationship"]="NOT_REAL"
    assert validate_v1_contract(doc)

def test_attest_cli_emits_json():
    from cli.main import cli
    result=CliRunner().invoke(cli,["attest","--watchlist","data/fixtures/watchlist_sample.yaml","--event","data/fixtures/bitnami/event.json"])
    assert result.exit_code==0,result.output
    lines=[x for x in result.output.splitlines() if x.startswith("{")]
    assert len(lines)==3
    for line in lines:
        doc=json.loads(line)
        assert not validate_v1_contract(doc)
        assert verify_v1_content_hash(doc)
