"""The reputation indicators in the trust block, contract 2.3.0 and the policy
(track T Phase 2, T-C, T-D, T-F2, T-E1; v0.16.0 item Q5)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from core.agent_tools import REPUTATION_CHECKS, Lookups, trust_checks
from core.evidence_contract import (
    SCHEMA_V2_2_PATH,
    SCHEMA_V2_3_PATH,
    TRUST_CHECKS,
    TRUST_CHECKS_2_2,
    build_contract,
    load_v2_2_schema,
    trust_assurance_block,
    validate_contract,
    validate_v1_contract,
    verify_content_hash,
)
from core.risk.check import check_dependency
from core.schema.models import OSSEvent
from core.trust_policy import PolicyError, evaluate, parse

EVENT = "data/fixtures/django-eol/event.json"
WIDGET = {"kind": "package", "package": "widget", "ecosystem": "npm", "version": "1.1.0"}
REPO_URL = "https://api.github.com/repos/acme/widget"
PACKUMENT = {
    "time": {"1.0.0": "2026-01-01T00:00:00.000Z", "1.1.0": "2026-01-02T00:00:00.000Z"},
    "versions": {
        "1.0.0": {"_npmUser": {"name": "alice"}},
        "1.1.0": {"_npmUser": {"name": "mallory"}},
    },
}
VERSION_DOC = {"name": "widget", "repository": {"url": "git+https://github.com/acme/widget.git"}}


class Net:
    def __init__(self, github=None):
        self.asked: list[str] = []
        self.github_answer = github or (
            200,
            {
                "full_name": "acme-org/widget",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=20)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "stargazers_count": 4000,
            },
        )

    def json(self, url):
        self.asked.append(url)
        if url == "https://registry.npmjs.org/widget":
            return 200, PACKUMENT
        if url == "https://registry.npmjs.org/widget/1.1.0":
            return 200, VERSION_DOC
        return 404, None

    def github(self, url):
        self.asked.append(url)
        return self.github_answer if url == REPO_URL else (404, None)


def _lookups(net, budget=200):
    return Lookups(
        fetch=lambda _slug: {"endoflife": [], "osv": [], "github_meta": []},
        head=lambda _url: 200,
        fetch_json=net.json,
        fetch_text=lambda _url: (404, None),
        osv_query=lambda _body: (200, {}),
        fetch_github=net.github,
        budget=budget,
    )


def _statuses(checks):
    return {name: checks[name]["status"] for name in REPUTATION_CHECKS}


# ---------------------------------------------------------------------------
# The trust block
# ---------------------------------------------------------------------------


def test_every_indicator_is_in_the_trust_block():
    checks = trust_checks(WIDGET, _lookups(Net()))
    assert _statuses(checks) == dict.fromkeys(REPUTATION_CHECKS, "SUSPICIOUS_INCONCLUSIVE")
    assert checks["publisher_change"]["evidence"]["rules"] == ["new_account"]
    assert checks["repository_moved"]["evidence"]["move"] == "transferred"
    assert "mallory" not in json.dumps(checks)


def test_the_two_github_checks_share_one_request_and_answers_are_cached():
    net = Net()
    lookups = _lookups(net)
    trust_checks(WIDGET, lookups)
    assert net.asked.count(REPO_URL) == 1
    used, asked = lookups.used, len(net.asked)
    trust_checks(WIDGET, lookups)
    assert (lookups.used, len(net.asked)) == (used, asked)  # cache hits are free


def test_each_indicator_spends_one_lookup_and_a_spent_budget_is_not_performed():
    net = Net()
    lookups = _lookups(net, budget=0)
    checks = trust_checks(WIDGET, lookups)
    for name in REPUTATION_CHECKS:
        assert checks[name]["status"] == "NOT_PERFORMED"
        assert "budget" in checks[name]["statement"]
    assert net.asked == []


def test_github_trouble_is_not_cached():
    net = Net(github=(503, None))
    lookups = _lookups(net)
    first = trust_checks(WIDGET, lookups)
    assert first["repository_moved"]["status"] == "NOT_PERFORMED"
    assert net.asked.count(REPO_URL) == 2  # each GitHub check asked; neither answer kept
    trust_checks(WIDGET, lookups)
    assert net.asked.count(REPO_URL) == 4


def test_offline_private_and_unsupported_are_not_performed():
    offline = trust_checks(WIDGET, None)
    for name in REPUTATION_CHECKS:
        assert offline[name]["status"] == "NOT_PERFORMED"
        assert offline[name]["statement"].endswith("live lookups are off")
    private = trust_checks(WIDGET, _lookups(Net()), frozenset({("npm", "widget")}))
    for name in REPUTATION_CHECKS:
        assert private[name]["status"] == "NOT_PERFORMED"
        assert "private-name list" in private[name]["statement"]
    image = {"kind": "image", "ref": "nginx:1.25"}
    unsupported = trust_checks({**image, "package": "nginx"}, _lookups(Net()))
    assert {unsupported[n]["status"] for n in REPUTATION_CHECKS} == {"NOT_PERFORMED"}


# ---------------------------------------------------------------------------
# Evidence contract 2.3.0
# ---------------------------------------------------------------------------


@pytest.fixture
def event():
    with open(EVENT, encoding="utf-8") as f:
        return OSSEvent(**json.load(f))


def _doc(event, block):
    django = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    return build_contract(event, check_dependency(django, [event]), trust_assurance=block)


def test_a_2_3_document_carries_the_indicators_and_validates(event):
    block = trust_assurance_block(trust_checks(WIDGET, _lookups(Net())))
    assert {r["check"] for r in block["checks"]} >= set(REPUTATION_CHECKS)
    moved = next(r for r in block["checks"] if r["check"] == "repository_moved")
    assert moved["references"] == ["https://github.com/acme-org/widget"]
    doc = _doc(event, block)
    assert doc["contract_version"] == "2.3.0"
    assert validate_contract(doc) == [] and verify_content_hash(doc)
    assert '"evidence":' not in json.dumps(doc["trust_assurance"])


def test_a_2_2_consumer_rejects_the_new_check_names_and_2_2_documents_still_validate(event):
    block = trust_assurance_block(trust_checks(WIDGET, _lookups(Net())))
    as_2_2 = _doc(event, block)
    as_2_2["contract_version"] = as_2_2["provenance"]["contract_version"] = "2.2.0"
    assert any("check" in e for e in validate_v1_contract(as_2_2, load_v2_2_schema()))
    old = {c: r for c, r in trust_checks(WIDGET, None).items() if c in TRUST_CHECKS_2_2}
    still = _doc(event, trust_assurance_block(old))
    still["contract_version"] = still["provenance"]["contract_version"] = "2.2.0"
    assert validate_contract(still) == []


def test_the_2_3_schema_is_2_2_with_three_more_check_names():
    v22 = json.loads(SCHEMA_V2_2_PATH.read_text(encoding="utf-8"))
    v23 = json.loads(SCHEMA_V2_3_PATH.read_text(encoding="utf-8"))
    names = v23["$defs"]["trust_record"]["properties"]["check"]["enum"]
    assert tuple(names) == TRUST_CHECKS == (*TRUST_CHECKS_2_2, *REPUTATION_CHECKS)
    assert v23["properties"]["contract_version"]["const"] == "2.3.0"
    v23["$defs"]["trust_record"]["properties"]["check"] = v22["$defs"]["trust_record"][
        "properties"
    ]["check"]
    for schema in (v22, v23):
        for key in ("$id", "title", "description"):
            schema.pop(key)
        schema["properties"]["contract_version"].pop("const")
        schema["properties"]["provenance"]["properties"]["contract_version"].pop("const")
        schema["properties"]["trust_assurance"].pop("description")
    assert v23 == v22


# ---------------------------------------------------------------------------
# Trust policy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition", REPUTATION_CHECKS)
def test_every_indicator_needs_a_package_scope(condition):
    with pytest.raises(PolicyError, match="name the packages"):
        parse({"version": 1, "prohibit": [condition]})


def test_a_scoped_indicator_is_a_violation_and_young_popular_is_experimental():
    policy = parse(
        {
            "version": 1,
            "prohibit": [
                {"condition": name, "packages": ["npm:widget"]} for name in REPUTATION_CHECKS
            ],
        }
    )
    assert policy.experimental == ["young_popular_repository"]
    checks = trust_checks(WIDGET, _lookups(Net()))
    records = [{"check": name, **checks[name]} for name in REPUTATION_CHECKS]
    violations = evaluate(policy, WIDGET, records)
    assert [v["condition"] for v in violations] == list(REPUTATION_CHECKS)
    assert [v["label"] for v in violations] == ["indicator", "indicator", "experimental"]
    other = {**WIDGET, "package": "gadget"}
    assert evaluate(policy, other, records) == []
