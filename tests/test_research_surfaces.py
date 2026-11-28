"""Invariant I5 across surfaces: one verdict, read the same way everywhere.

The engine (``check_dependency``), the agent/MCP tool answer
(``core.agent_tools``, which ``openpulse mcp`` serves), the evidence
contract a consumer receives, and the evaluation's outcome mapping must
agree on the relationship and on what it means -- in particular, an
unresolved verdict is never presented as a clearance on any of them
(research/RESEARCH_PROTOCOL.md §3, I4-I5).
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core import agent_tools
from core.evidence_contract import build_v1_contract, validate_v1_contract
from core.risk.check import check_dependency
from core.verdict_meaning import DIRECT_SCOPE

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation"))

import policies  # noqa: E402

AS_OF = datetime(2026, 10, 30, tzinfo=timezone.utc)
MAX_AGE_DAYS = 90

#: Dependencies against the curated events (Bitnami, Spark, Django, iText):
#: members, non-members, a curated other project, a heuristic mapping (D16)
#: and an unmapped reference.
DEPENDENCIES = [
    {"image": "docker.io/bitnami/redis:7.2"},
    {"image": "docker.io/bitnami/postgresql:16"},
    {"image": "docker.io/redis:7.2"},
    {"image": "docker.io/zzz/kvstore:1.0"},
    {"image": "apache/spark:3.5.1"},
    {"package": "django", "ecosystem": "PyPI", "version": "4.2.11"},
    {"package": "django", "ecosystem": "PyPI", "version": "5.1"},
    {"package": "itextpdf", "ecosystem": "Maven", "version": "5.5.13"},
    {"package": "com.itextpdf:itextpdf", "ecosystem": "Maven", "version": "7.2.0"},
    {"package": "left-pad", "ecosystem": "npm", "version": "1.3.0"},
]
_UNRESOLVED = {"RELATED", "AFFECTS_PROJECT"}


def _engine_dep(spec):
    if "image" in spec:
        return {"kind": "image", "ref": spec["image"]}
    return {"kind": "package", **spec}


@pytest.mark.parametrize("spec", DEPENDENCIES, ids=lambda s: s.get("image") or s["package"])
@pytest.mark.parametrize("mode", ["current", "replay"])
def test_agent_answer_engine_and_contract_agree(spec, mode):
    bounded = mode == "current"
    answer = agent_tools.dependency_status(
        spec.get("package"),
        spec.get("version"),
        spec.get("ecosystem"),
        spec.get("image"),
        live=False,
        mode=mode,
        as_of=AS_OF if bounded else None,
        max_evidence_age_days=MAX_AGE_DAYS if bounded else None,
    )
    events = agent_tools.curated_events()
    max_age = timedelta(days=MAX_AGE_DAYS) if bounded else None
    engine = check_dependency(
        _engine_dep(spec), events, as_of=AS_OF if bounded else None, max_evidence_age=max_age
    )
    verdict = answer["verdict"]
    # Same relationship, same closed-vocabulary meaning.
    assert verdict["relationship"] == engine.relationship
    assert verdict["meaning"]["direct_scope"] == DIRECT_SCOPE[engine.relationship]
    if engine.relationship in _UNRESOLVED | {"UNKNOWN", "NOT_AFFECTED"}:
        assert "Not a clearance" in verdict["meaning"]["statement"] or (
            "not a clearance" in verdict["meaning"]["statement"]
        )
    # The evaluation reads it the same way: unresolved stays unresolved.
    outcome = policies._OPENPULSE_OUTCOME[engine.relationship]
    if engine.relationship in _UNRESOLVED:
        assert outcome == policies.UNRESOLVED
    # Each cause the agent sees matches the contract for that event.
    by_id = {e.id: e for e in events}
    for cause in answer["causes"]:
        event = by_id[cause["event"]]
        single = check_dependency(
            _engine_dep(spec),
            [event],
            as_of=AS_OF if bounded else None,
            max_evidence_age=max_age,
        )
        contract = build_v1_contract(
            event, single, as_of=AS_OF if bounded else None, max_evidence_age=max_age
        )
        assert validate_v1_contract(contract) == []
        assert cause["relationship"] == single.relationship
        assert cause["direct_scope"] == contract["verdict_meaning"]["direct_scope"]
        assert cause["scope_completeness"] == contract["scope"]["completeness"]


def test_an_offline_answer_says_what_it_did_not_consult():
    answer = agent_tools.dependency_status(image="docker.io/zzz/kvstore:1.0", live=False)
    assert "live lookups" in answer["not_established"]
    assert answer["verdict"]["relationship"] != "NOT_AFFECTED"


@pytest.mark.parametrize("spec", DEPENDENCIES, ids=lambda s: s.get("image") or s["package"])
def test_every_agent_verdict_carries_its_causes_and_evidence(spec):
    """I8 on the agent surface: a verdict never arrives without the cause and
    evidence behind it. docker.io/bitnami/redis used to be AFFECTS_ARTIFACT
    with no cause, because the event's project ("bitnami") is not the
    image's slug ("bitnami-redis-stack") and causes were filtered by slug."""
    answer = agent_tools.dependency_status(
        spec.get("package"),
        spec.get("version"),
        spec.get("ecosystem"),
        spec.get("image"),
        live=False,
        mode="replay",
    )
    relationship = answer["verdict"]["relationship"]
    if relationship == "UNKNOWN":
        return
    support = [c for c in answer["causes"] if c["relationship"] == relationship]
    assert support, answer["causes"]
    assert all(c["evidence_urls"] for c in support)
