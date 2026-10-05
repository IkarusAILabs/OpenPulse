"""Evidence contract tests (issue #53): convergence, round-trip, honesty."""

import json

import pytest

from core.attestation import (
    CONTRACT_SCHEMA_VERSION,
    PLANNED_FIELDS,
    EvidenceContract,
    build_contract,
    dump_contract,
    round_trip,
    verify_content_hash,
)
from core.risk.check import check_dependency
from core.schema.models import OSSEvent


@pytest.fixture(scope="module")
def django_event():
    return OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))


@pytest.fixture(scope="module")
def bitnami_event():
    return OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))


@pytest.fixture(scope="module")
def django_dep():
    return {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}


@pytest.fixture(scope="module")
def django_contract(django_event, django_dep):
    verdict = check_dependency(django_dep, [django_event])
    return build_contract(django_event, verdict)


def _check(django_event, django_dep, **kwargs):
    verdict = check_dependency(django_dep, [django_event])
    return build_contract(django_event, verdict, **kwargs)


def test_round_trip_byte_identical(django_contract):
    """dump -> validate -> back must be byte-identical (acceptance)."""
    rt = round_trip(django_contract)
    assert dump_contract(django_contract) == dump_contract(rt)
    assert rt == django_contract


def test_content_hash_verifies_and_breaks_on_edit(django_contract):
    """verify_content_hash passes on the built document and fails after a tamper."""
    assert verify_content_hash(django_contract)
    tampered = django_contract.model_copy(deep=True)
    tampered.assessment.reason = "no, everything is fine"
    assert not verify_content_hash(tampered)
    # clock drift must NOT break verification: only content matters
    drifted = django_contract.model_copy(deep=True)
    from datetime import datetime, timedelta, timezone

    drifted.provenance.generation_timestamp = datetime.now(timezone.utc) + timedelta(days=3)
    assert verify_content_hash(drifted)


def test_every_block_source_is_current_output(django_contract, django_event):
    """Convergence: each block carries what current outputs already hold."""
    # event context = event fields, verbatim
    assert django_contract.event["id"] == django_event.id
    assert django_contract.event["event_type"] == django_event.event_type.value
    assert django_contract.event["project_slug"] == django_event.project_slug
    assert django_contract.event["confidence"] == django_event.confidence.value
    assert django_contract.event["impact"] == django_event.impact.value
    # evidence references = event evidences, verbatim
    assert len(django_contract.evidence_references) == len(django_event.evidences)
    for ref, ev in zip(django_contract.evidence_references, django_event.evidences):
        assert ref.source_name == ev.source.name
        assert ref.url == str(ev.source.url)
        assert ref.authority == ev.source.authority
        assert ref.relation == ev.relation
        assert ref.excerpt == ev.excerpt
    # scope = event scope, verbatim
    assert django_contract.scope.kind == django_event.scope.kind
    assert django_contract.scope.versions == django_event.scope.versions


def test_dates_come_from_event_evidence(django_contract):
    """Announcement/effective dates are the evidence dates, never inferred."""
    assert django_contract.dates.announcement_date == "2026-04-01"
    assert django_contract.dates.effective_date == "2026-04-30"
    # no ledger record fed this verdict: unknown stays unknown
    assert django_contract.dates.first_detected is None


def test_unknown_unknown_stays_unknown(django_event, django_dep):
    """Missing detection history is stated, never backfilled."""
    contract = _check(django_event, django_dep)
    assert "first detection unknown (no durable ledger record)" in contract.unknowns.unknowns
    assert contract.dates.first_detected is None


def test_unknowns_not_fabricated_when_finding_present(django_event, django_dep):
    """A finding supplying last-observation removes exactly that unknown."""
    finding = {"last_observed_at": "2026-09-28"}
    contract = _check(django_event, django_dep, finding=finding)
    assert contract.dates.last_verified == "2026-09-28"
    assert not any("last verification" in u for u in contract.unknowns.unknowns)
    assert any("first detection" in u for u in contract.unknowns.unknowns)


def test_planned_fields_never_populated(django_contract):
    """Signature/key/trust-root stay None; the builder never invents them."""
    assert django_contract.signature is None
    assert django_contract.signing_key_id is None
    assert django_contract.trust_root is None
    assert PLANNED_FIELDS == {"signature", "signing_key_id", "trust_root"}


def test_extra_fields_rejected(django_contract):
    """Strict model: an unknown field fails validation (no silent passthrough)."""
    doc = json.loads(dump_contract(django_contract))
    doc["made_up_field"] = "x"
    with pytest.raises(Exception):
        EvidenceContract.model_validate(doc)


def test_exact_artifact_identity_is_selfidentity(bitnami_event):
    """Exact artifact equality: identity_via = exact-artifact, VERIFIED."""
    dep = {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}
    verdict = check_dependency(dep, [bitnami_event])
    contract = build_contract(bitnami_event, verdict)
    assert contract.assessment.relationship == "AFFECTS_ARTIFACT"
    assert contract.assessment.affected is True
    assert contract.identity.identity_status == "VERIFIED"
    assert contract.identity.identity_via == "exact-artifact"
    assert verify_content_hash(contract)
    assert dump_contract(contract) == dump_contract(round_trip(contract))


def test_untrusted_identity_limitation_stated(bitnami_event):
    """REVIEW_REQUIRED identity -> limitation line, never silent capping."""
    # docker.io/bitnami/redis:6.2 relies on the bitnami namespace rule
    dep = {"kind": "image", "ref": "docker.io/bitnami/nginx:1.27"}
    verdict = check_dependency(dep, [bitnami_event])
    contract = build_contract(bitnami_event, verdict)
    if contract.identity.identity_status != "VERIFIED":
        assert any("identity mapping is" in line for line in contract.unknowns.limitations)


def test_min_one_evidence_reference():
    """An event with zero evidences is impossible via OSSEvent; the
    contract model pins the same floor (min_length=1)."""
    from pydantic.fields import FieldInfo

    field: FieldInfo = EvidenceContract.model_fields["evidence_references"]
    metadata = field.metadata
    assert metadata, "evidence_references has no constraints"
    min_lengths = [
        m.min_length for m in metadata if hasattr(m, "min_length") and m.min_length is not None
    ]
    assert min_lengths and min(min_lengths) == 1


def test_unknown_relationship_stated(django_event):
    """A dep matching nothing yields UNKNOWN, and the contract says so.

    The version-scoped django event identity-EXCLUDES unrelated refs
    (NOT_AFFECTED, the #42 fix), so a true UNKNOWN needs the scopeless
    shape: an unscoped event and a dep from a different project."""
    scopeless = django_event.model_copy(update={"scope": None, "project_slug": "totally-other"})
    dep = {"kind": "image", "ref": "docker.io/unrelated/thing:1"}
    verdict = check_dependency(dep, [scopeless])
    contract = build_contract(scopeless, verdict)
    assert contract.assessment.relationship == "UNKNOWN"
    assert "relationship unknown: no applicable evidence" in contract.unknowns.unknowns


def test_deterministic_body_hash(django_event, django_dep):
    """Same inputs -> same content hash, despite different build clocks."""
    a = _check(django_event, django_dep)
    b = _check(django_event, django_dep)
    assert a.provenance.generation_timestamp != b.provenance.generation_timestamp
    assert a.provenance.content_hash == b.provenance.content_hash
    assert verify_content_hash(a) and verify_content_hash(b)


def test_schema_version_present(django_contract):
    assert django_contract.contract_schema_version == CONTRACT_SCHEMA_VERSION
    assert django_contract.provenance.contract_schema_version == CONTRACT_SCHEMA_VERSION
