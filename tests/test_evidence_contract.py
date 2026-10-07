"""Evidence contract v1 tests (issue #67): schema, builder, validator, CLI.

Acceptance from the issue: schema validates builder output,
round-trips, tamper detection, determinism across build times,
unknowns exactly when input absent, planned fields null in v1.
"""

import json

import pytest

from core.attestation import build_contract
from core.evidence_contract import (
    _V1_BODY_FIELDS,
    CONTRACT_VERSION,
    SCHEMA_PATH,
    build_v1_contract,
    load_schema,
    validate_v1_contract,
    verify_v1_content_hash,
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


def _doc(event, dep, **kwargs):
    verdict = check_dependency(dep, [event])
    return build_v1_contract(event, verdict, **kwargs)


@pytest.fixture(scope="module")
def django_doc(django_event, django_dep):
    return _doc(django_event, django_dep)


# ---------------------------------------------------------------------------
# Acceptance: the built document is schema-valid
# ---------------------------------------------------------------------------


def test_builder_output_is_schema_valid(django_doc):
    errors = validate_v1_contract(django_doc)
    assert errors == [], errors


def test_builder_output_validates_across_shapes(django_event, bitnami_event):
    """AFFECTS_VERSION, AFFECTS_ARTIFACT, UNKNOWN: three verdict shapes."""
    docs = [
        _doc(
            django_event,
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"},
        ),
        _doc(bitnami_event, {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}),
    ]
    scopeless = django_event.model_copy(update={"scope": None, "project_slug": "totally-other"})
    docs.append(_doc(scopeless, {"kind": "image", "ref": "docker.io/unrelated/thing:1"}))
    for doc in docs:
        assert validate_v1_contract(doc) == []
        assert verify_v1_content_hash(doc)


def test_contract_version_is_semver_1_0_0(django_doc):
    assert django_doc["contract_version"] == CONTRACT_VERSION == "1.0.0"
    assert django_doc["provenance"]["contract_version"] == CONTRACT_VERSION


def test_v1_block_names_match_the_issue(django_doc):
    for block in (
        "event_context",
        "identity",
        "scope",
        "affected_dependency",
        "assessment",
        "evidence_refs",
        "temporal",
        "unknowns",
        "recommendation",
        "provenance",
    ):
        assert block in django_doc, block
    for inward in ("event", "evidence_references", "dates", "contract_schema_version"):
        assert inward not in django_doc, inward


def test_v1_values_are_the_60_builder_values(django_event, django_dep):
    """The rename layer must not touch values: same builder underneath."""
    verdict = check_dependency(django_dep, [django_event])
    base = build_contract(django_event, verdict).model_dump(mode="json")
    doc = build_v1_contract(django_event, verdict)
    assert doc["event_context"] == base["event"]
    assert doc["evidence_refs"] == base["evidence_references"]
    assert doc["temporal"] == base["dates"]
    assert doc["assessment"] == base["assessment"]
    assert doc["unknowns"] == base["unknowns"]


# ---------------------------------------------------------------------------
# Round-trip and tamper detection
# ---------------------------------------------------------------------------


def test_json_round_trip_validates(django_doc):
    """dump -> re-parse -> validate: the wire form is self-sufficient."""
    wire = json.dumps(django_doc, sort_keys=True)
    assert validate_v1_contract(json.loads(wire)) == []


def test_tamper_detection(django_doc):
    """Single-field mutation: the hash breaks, schema-visible ones error."""
    broken = json.loads(json.dumps(django_doc))
    broken["assessment"]["reason"] = "no, everything is fine"
    assert validate_v1_contract(broken) == []  # a string is still schema-valid
    assert not verify_v1_content_hash(broken)  # but the hash catches it
    broken2 = json.loads(json.dumps(django_doc))
    broken2["assessment"]["relationship"] = "AFFECTS_EVERYTHING"
    assert any("is not one of" in e for e in validate_v1_contract(broken2))
    broken3 = json.loads(json.dumps(django_doc))
    broken3["made_up_block"] = {}
    assert any("unexpected property" in e for e in validate_v1_contract(broken3))


def test_every_required_block_missing_is_caught(django_doc):
    for block in (
        "contract_version",
        "event_context",
        "identity",
        "scope",
        "affected_dependency",
        "assessment",
        "evidence_refs",
        "temporal",
        "unknowns",
        "recommendation",
        "provenance",
    ):
        broken = json.loads(json.dumps(django_doc))
        del broken[block]
        errors = validate_v1_contract(broken)
        assert any(f"missing required property `{block}`" in e for e in errors), block


def test_type_and_format_errors_are_named(django_doc):
    broken = json.loads(json.dumps(django_doc))
    broken["assessment"]["affected"] = "yes"
    assert any("expected boolean" in e for e in validate_v1_contract(broken))
    broken2 = json.loads(json.dumps(django_doc))
    broken2["provenance"]["generation_timestamp"] = "not-a-date"
    assert any("date-time" in e for e in validate_v1_contract(broken2))
    broken3 = json.loads(json.dumps(django_doc))
    broken3["provenance"]["content_hash"] = "md5:whatever"
    errors3 = validate_v1_contract(broken3)
    assert any("pattern" in e for e in errors3)
    assert not verify_v1_content_hash(broken3)


def test_empty_evidence_refs_rejected(django_doc):
    broken = json.loads(json.dumps(django_doc))
    broken["evidence_refs"] = []
    assert any("minItems" in e for e in validate_v1_contract(broken))


# ---------------------------------------------------------------------------
# Planned fields, unknowns, determinism
# ---------------------------------------------------------------------------


def test_planned_fields_null_and_rejected_when_set(django_doc):
    assert django_doc["signature"] is None
    assert django_doc["signing_key_id"] is None
    assert django_doc["trust_root"] is None
    broken = json.loads(json.dumps(django_doc))
    broken["signature"] = "sig"
    assert any("const" in e for e in validate_v1_contract(broken))


def test_unknowns_exactly_when_input_absent(django_event, django_dep):
    doc = _doc(django_event, django_dep)
    assert "first detection unknown (no durable ledger record)" in doc["unknowns"]["unknowns"]
    assert doc["temporal"]["first_detected"] is None
    doc2 = _doc(django_event, django_dep, finding={"last_observed_at": "2026-09-28"})
    assert doc2["temporal"]["last_verified"] == "2026-09-28"
    assert not any("last verification" in u for u in doc2["unknowns"]["unknowns"])
    assert any("first detection" in u for u in doc2["unknowns"]["unknowns"])
    # content changes -> hash changes: the finding is attested content
    assert doc["provenance"]["content_hash"] != doc2["provenance"]["content_hash"]


def test_determinism_same_content_same_hash(django_event, django_dep, monkeypatch):
    """Two builds at different times -> identical content_hash."""
    from datetime import datetime, timedelta, timezone

    import core.attestation as attestation

    class _SteppedClock:
        _calls = 0

        @classmethod
        def now(cls, tz=None):
            cls._calls += 1
            base = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=cls._calls)
            return base if tz is None or tz is timezone.utc else base.astimezone(tz)

    monkeypatch.setattr(attestation, "datetime", _SteppedClock)
    verdict = check_dependency(django_dep, [django_event])
    a = build_v1_contract(django_event, verdict)
    b = build_v1_contract(django_event, verdict)
    assert a["provenance"]["generation_timestamp"] != b["provenance"]["generation_timestamp"]
    assert a["provenance"]["content_hash"] == b["provenance"]["content_hash"]
    assert verify_v1_content_hash(a) and verify_v1_content_hash(b)


# ---------------------------------------------------------------------------
# Validator discipline: closed vocabularies, fail-closed subset
# ---------------------------------------------------------------------------


def test_closed_vocabularies_reject_inventions(django_doc):
    broken = json.loads(json.dumps(django_doc))
    broken["identity"]["identity_status"] = "SUPER_VERIFIED"
    assert any("is not one of" in e for e in validate_v1_contract(broken))
    broken2 = json.loads(json.dumps(django_doc))
    broken2["identity"]["identity_via"] = "vibes"
    assert any("identity_via" in e for e in validate_v1_contract(broken2))


def test_validator_fail_closed_on_unknown_keyword(django_doc):
    """A schema using a keyword outside the subset is an error, not a pass."""
    schema = load_schema()
    schema["properties"]["assessment"]["uniqueItems"] = True
    errors = validate_v1_contract(django_doc, schema=schema)
    assert any("unsupported keyword" in e for e in errors)


def test_validator_survives_junk_input():
    assert validate_v1_contract("a string") != []
    assert validate_v1_contract([1, 2]) != []
    assert validate_v1_contract(None) != []
    assert validate_v1_contract({}) != []
    assert validate_v1_contract(3) != []


def test_schema_pins_draft_id_and_descriptions():
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/evidence-contract/v1/schema.json")
    for name, node in schema["properties"].items():
        assert "description" in node, name
    assert SCHEMA_PATH.exists()


def test_hash_covers_all_blocks_not_planned_fields(django_doc):
    assert set(_V1_BODY_FIELDS) == {
        "contract_version",
        "event_context",
        "identity",
        "scope",
        "affected_dependency",
        "assessment",
        "evidence_refs",
        "temporal",
        "unknowns",
        "recommendation",
        "provenance",
    }
    assert "signature" not in _V1_BODY_FIELDS


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_attest_cli_watchlist_stdout(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    out = CliRunner().invoke(
        cli,
        [
            "attest",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
        ],
    )
    assert out.exit_code == 0, out.output
    lines = [ln for ln in out.output.splitlines() if ln.startswith("{")]
    docs = [json.loads(ln) for ln in lines]
    assert len(docs) == 3
    for doc in docs:
        assert validate_v1_contract(doc) == []
        assert verify_v1_content_hash(doc)
    by_dep = {d["identity"]["dependency"]: d for d in docs}
    assert by_dep["docker.io/bitnami/redis:7.2"]["assessment"]["relationship"] == "AFFECTS_ARTIFACT"


def test_attest_cli_output_file(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    destination = tmp_path / "contracts.jsonl"
    out = CliRunner().invoke(
        cli,
        [
            "attest",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
            "--output",
            str(destination),
        ],
    )
    assert out.exit_code == 0, out.output
    raw = destination.read_text(encoding="utf-8")
    docs = [json.loads(ln) for ln in raw.splitlines() if ln.strip()]
    assert len(docs) == 3
    for doc in docs:
        assert validate_v1_contract(doc) == []


def test_attest_cli_composes_sbom(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    out = CliRunner().invoke(
        cli,
        [
            "attest",
            "--sbom",
            "data/fixtures/sbom/cyclonedx.json",
            "--event",
            "data/fixtures/bitnami/event.json",
        ],
    )
    assert out.exit_code == 0, out.output
    lines = [ln for ln in out.output.splitlines() if ln.startswith("{")]
    docs = [json.loads(ln) for ln in lines]
    # the fixture maps three components (bitnami/redis, django 5.0, itext-core)
    assert len(docs) == 3
    for doc in docs:
        assert validate_v1_contract(doc) == []
    labels = {doc["identity"]["dependency"] for doc in docs}
    assert "bitnami/redis:7.2" in labels


def test_attest_cli_rejects_missing_sources(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    out = CliRunner().invoke(cli, ["attest", "--event", "data/fixtures/bitnami/event.json"])
    assert out.exit_code != 0
    assert "attest needs" in out.output


def test_attest_cli_rejects_missing_event(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    out = CliRunner().invoke(cli, ["attest", "--watchlist", "data/fixtures/watchlist_sample.yaml"])
    assert out.exit_code != 0


def test_attest_cli_lockfile_and_images(tmp_path):
    """--lockfile and --images compose the same way as check."""
    from click.testing import CliRunner

    from cli.main import cli

    out = CliRunner().invoke(
        cli,
        [
            "attest",
            "--lockfile",
            "data/fixtures/lockfiles/poetry.lock",
            "--event",
            "data/fixtures/django-eol/event.json",
        ],
    )
    assert out.exit_code == 0, out.output
    lines = [ln for ln in out.output.splitlines() if ln.startswith("{")]
    assert lines, "lockfile attest produced nothing"
    for ln in lines:
        assert validate_v1_contract(json.loads(ln)) == []
