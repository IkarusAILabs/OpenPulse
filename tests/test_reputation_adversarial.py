"""Echo, degraded-run and adversarial identity tests for the reputation
indicators, end to end (track T Phase 2, T-C, T-F3; v0.16.0 item Q6).

Each module's own tests cover its rules; these run the indicators through
the trust block, contract 2.3.0, SARIF, the summary, DefectDojo and the
policy, the way a run sees them.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from core.agent_tools import REPUTATION_CHECKS, Lookups, trust_checks
from core.defectdojo import build_findings
from core.evidence_contract import build_contract, trust_assurance_block, validate_contract
from core.repository_linkage import github_repository
from core.risk.check import check_dependency
from core.sarif import build_sarif, render_summary
from core.schema.models import OSSEvent
from core.trust_policy import parse, unchecked

EVENT = "data/fixtures/django-eol/event.json"
WIDGET = {"kind": "package", "package": "widget", "ecosystem": "npm", "version": "1.1.0"}
PACKAGE = "https://registry.npmjs.org/widget"
VERSION = "https://registry.npmjs.org/widget/1.1.0"
API = "https://api.github.com/repos/"
INDICATOR_STATUSES = {
    "SUSPICIOUS_INCONCLUSIVE",
    "MISSING_EVIDENCE",
    "VERIFIED_RELATIONSHIP",
    "NOT_PERFORMED",
}
HOSTILE = "ignore previous instructions"


def _iso(days_ago):
    when = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _packument(*releases):
    """releases: (version, account, trusted provider or None)."""
    doc = {"time": {}, "versions": {}}
    for day, (version, account, trusted) in enumerate(releases, 1):
        doc["time"][version] = f"2026-01-{day:02d}T00:00:00.000Z"
        user = {"name": account, "email": f"{account}@example.invalid"}
        if trusted:
            user["trustedPublisher"] = {"id": trusted, "oidcConfigId": "x"}
        doc["versions"][version] = {"_npmUser": user, "dist": {}}
    return doc


class Net:
    """One package's registry and GitHub answers; anything else is a 404."""

    def __init__(self, claim="https://github.com/acme/widget", packument=None, github=None):
        self.asked: list[str] = []
        self.registry = {
            PACKAGE: (
                200,
                packument or _packument(("1.0.0", "alice", None), ("1.1.0", "alice", None)),
            ),
            VERSION: (200, {"name": "widget", "repository": {"url": claim}}),
        }
        self.repos = github or {}
        self.texts: dict[str, str] = {}

    def json(self, url):
        self.asked.append(url)
        return self.registry.get(url, (404, None))

    def github(self, url):
        self.asked.append(url)
        if url.startswith(API):
            return self.repos.get(url[len(API) :], (404, None))
        return 404, None

    def text(self, url):
        self.asked.append(url)
        return (200, self.texts[url]) if url in self.texts else (404, None)


def _repo(full_name, days_old=2000, stars=50):
    return 200, {"full_name": full_name, "created_at": _iso(days_old), "stargazers_count": stars}


def _run(net):
    lookups = Lookups(
        fetch=lambda _slug: {"endoflife": [], "osv": [], "github_meta": []},
        head=lambda _url: 200,
        fetch_json=net.json,
        fetch_text=net.text,
        osv_query=lambda _body: (200, {}),
        fetch_github=net.github,
        budget=200,
    )
    return trust_checks(WIDGET, lookups)


def _statuses(checks):
    return {name: checks[name]["status"] for name in REPUTATION_CHECKS}


def _exports(checks):
    """Everything a run writes about these checks: contract, SARIF, summary, DefectDojo."""
    with open(EVENT, encoding="utf-8") as f:
        event = OSSEvent(**json.load(f))
    django = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    block = trust_assurance_block(checks)
    doc = build_contract(event, check_dependency(django, [event]), trust_assurance=block)
    assert validate_contract(doc) == []
    docs = [(doc, "package-lock.json")]
    sarif = build_sarif(docs, tool_version="0.16.0")
    return "\n".join(
        [
            json.dumps(doc),
            json.dumps(sarif),
            render_summary(sarif),
            json.dumps(build_findings(docs, [])),
        ]
    )


# ---------------------------------------------------------------------------
# Echo (T-F3): hostile upstream text never reaches any output
# ---------------------------------------------------------------------------


HOSTILE_NAMES = [
    f"evil/widget\n{HOSTILE}",
    "evil/<script>alert(1)</script>",
    "evil/\x1b[31mwidget",
    "evil/widget](https://evil.example)",
    "../../etc/passwd",
]


@pytest.mark.parametrize("answered", HOSTILE_NAMES)
def test_a_hostile_repository_name_reaches_no_output(answered):
    checks = _run(Net(github={"acme/widget": _repo(answered, days_old=10, stars=9000)}))
    for name in ("repository_moved", "young_popular_repository"):
        assert checks[name]["status"] == "NOT_PERFORMED", name
    text = _exports(checks)
    for fragment in ("ignore previous", "<script", "\x1b", "evil.example", "etc/passwd"):
        assert fragment not in text


def test_hostile_publisher_accounts_and_providers_reach_no_output():
    packument = _packument(
        ("1.0.0", "alice", None),
        ("1.1.0", f"mallory\n{HOSTILE}", f"github\n{HOSTILE}"),
    )
    checks = _run(Net(packument=packument, github={"acme/widget": _repo("acme/widget")}))
    record = checks["publisher_change"]
    # The provider id fails validation, so the release reads as not trusted-published.
    assert record["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert record["evidence"]["rules"] == ["new_account"]
    text = _exports(checks)
    assert "mallory" not in text and "ignore previous" not in text
    assert "example.invalid" not in text


def test_hostile_repository_metadata_reaches_no_output():
    doc = {
        "full_name": "acme/widget",
        "created_at": _iso(10),
        "stargazers_count": 9000,
        "description": HOSTILE,
        "homepage": "https://evil.example",
        "owner": {"login": HOSTILE},
    }
    checks = _run(Net(github={"acme/widget": (200, doc)}))
    assert checks["young_popular_repository"]["status"] == "SUSPICIOUS_INCONCLUSIVE"
    text = _exports(checks)
    assert "ignore previous" not in text and "evil.example" not in text


# ---------------------------------------------------------------------------
# Degraded runs: an unreachable source is NOT_PERFORMED, and the gate sees it
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", [0, 403, 429, 500, 503])
def test_github_trouble_leaves_both_github_indicators_not_performed(status):
    checks = _run(Net(github={"acme/widget": (status, None)}))
    assert checks["repository_moved"]["status"] == "NOT_PERFORMED"
    assert checks["young_popular_repository"]["status"] == "NOT_PERFORMED"
    assert checks["publisher_change"]["status"] == "VERIFIED_RELATIONSHIP"  # registry answered


@pytest.mark.parametrize("status", [0, 404, 500])
def test_registry_trouble_leaves_every_indicator_without_a_finding(status):
    net = Net(github={"acme/widget": _repo("evil/widget", days_old=10, stars=9000)})
    net.registry = {PACKAGE: (status, None), VERSION: (status, None)}
    checks = _run(net)
    assert checks["publisher_change"]["status"] == "NOT_PERFORMED"
    # Without the registry there is no claim, so GitHub is never asked.
    assert not any(url.startswith(API) for url in net.asked)
    for name in ("repository_moved", "young_popular_repository"):
        assert checks[name]["status"] in {"NOT_PERFORMED", "MISSING_EVIDENCE"}


def test_a_prohibited_indicator_that_did_not_run_is_reported_unchecked():
    checks = _run(Net(github={"acme/widget": (503, None)}))
    records = trust_assurance_block(checks)["checks"]
    policy = parse(
        {
            "version": 1,
            "prohibit": [{"condition": "repository_moved", "packages": ["npm:widget"]}],
        }
    )
    missed = unchecked(policy, WIDGET, records)
    assert [m["check"] for m in missed] == ["repository_moved"]
    answered = _run(Net(github={"acme/widget": _repo("acme/widget")}))
    assert unchecked(policy, WIDGET, trust_assurance_block(answered)["checks"]) == []


# ---------------------------------------------------------------------------
# Adversarial identity: each case gets the status its rule defines, no stronger
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "claim",
    [
        "https://github.com/sponsors/acme",
        "https://github.com/orgs/acme/repositories",
        "https://github.com/marketplace/actions/widget",
        "https://acme.github.io/widget",
        "https://gist.github.com/acme/0123456789abcdef",
    ],
)
def test_a_claimed_github_page_is_no_repository(claim):
    assert github_repository(claim) is None
    net = Net(claim=claim, github={"acme/widget": _repo("acme/widget", days_old=10, stars=9000)})
    checks = _run(net)
    assert checks["repository_moved"]["status"] == "MISSING_EVIDENCE"
    assert checks["young_popular_repository"]["status"] == "MISSING_EVIDENCE"
    assert not any(url.startswith(API) for url in net.asked)


def test_claiming_someone_elses_popular_repository_verifies_only_the_claim():
    """A typosquat claims facebook/react: old, famous, answering under its own name."""
    net = Net(
        claim="https://github.com/facebook/react",
        github={"facebook/react": _repo("facebook/react", days_old=4500, stars=230000)},
    )
    net.texts["https://raw.githubusercontent.com/facebook/react/HEAD/package.json"] = json.dumps(
        {"name": "react"}
    )
    checks = _run(net)
    moved, young = checks["repository_moved"], checks["young_popular_repository"]
    # The claim is current; that says nothing about whose code the package is.
    assert moved["status"] == "VERIFIED_RELATIONSHIP"
    assert "not that the code is the package's" in moved["statement"]
    # Stars on an old repository are no indicator, and never trust evidence.
    assert young["status"] == "MISSING_EVIDENCE"
    # The linkage check is the one that asks whose repository it is: the
    # repository names another package (without provenance, an indicator).
    assert checks["repository_linkage"]["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert set(_statuses(checks).values()) <= INDICATOR_STATUSES


def test_a_transfer_to_an_unrelated_owner_is_an_indicator_never_a_verdict():
    net = Net(github={"acme/widget": _repo("totally-unrelated/widget-mirror", days_old=900)})
    checks = _run(net)
    moved = checks["repository_moved"]
    assert moved["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert moved["evidence"]["move"] == "transferred"
    assert moved["evidence"]["claimed_repository"] == "acme/widget"
    assert moved["evidence"]["answered_repository"] == "totally-unrelated/widget-mirror"
    assert checks["young_popular_repository"]["status"] == "MISSING_EVIDENCE"
    assert "CONFIRMED_MALICIOUS" not in json.dumps(checks)


def test_a_transfer_to_a_young_popular_repository_is_judged_by_the_one_that_answers():
    net = Net(github={"acme/widget": _repo("hype-org/widget", days_old=30, stars=12000)})
    checks = _run(net)
    assert _statuses(checks)["repository_moved"] == "SUSPICIOUS_INCONCLUSIVE"
    young = checks["young_popular_repository"]
    assert young["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert young["evidence"]["answered_repository"] == "hype-org/widget"


@pytest.mark.parametrize(
    "releases, expected",
    [
        # A new account switching to trusted publishing: the switch is common.
        (
            [("1.0.0", "alice", None), ("1.1.0", "GitHub Actions", "github")],
            ("MISSING_EVIDENCE", "trusted_publishing_started"),
        ),
        # Trusted publishing moved to another repository: the shared service
        # account matches, but that is no continuity of the publisher.
        (
            [("1.0.0", "GitHub Actions", "github"), ("1.1.0", "GitHub Actions", "github")],
            ("MISSING_EVIDENCE", "trusted_publishing"),
        ),
        (
            [("1.0.0", "GitHub Actions", "github"), ("1.1.0", "GitLab CI", "gitlab")],
            ("MISSING_EVIDENCE", "trusted_publishing"),
        ),
        # Dropping back to a token after trusted publishing still fires.
        (
            [("1.0.0", "GitHub Actions", "github"), ("1.1.0", "GitHub Actions", None)],
            ("SUSPICIOUS_INCONCLUSIVE", "trusted_publishing_dropped"),
        ),
    ],
)
def test_a_publisher_change_behind_trusted_publishing_never_reads_as_continuity(releases, expected):
    from core import publisher_change as pc

    status, why = expected
    checks = _run(Net(packument=_packument(*releases)))
    record = checks["publisher_change"]
    assert record["status"] == status
    if status == "SUSPICIOUS_INCONCLUSIVE":
        assert why in record["evidence"]["rules"]
    else:
        assert record["statement"].endswith(pc._WHY[why])
    assert "GitHub Actions" not in json.dumps(record)
