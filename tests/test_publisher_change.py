"""Publisher change (track T Phase 2, T-C, threat T6; v0.16.0 item Q2)."""

from __future__ import annotations

import json

from core import publisher_change as pc

NPM_URL = "https://registry.npmjs.org/widget"
PYPI_URL = "https://pypi.org/pypi/widget/json"
P_MAIN = {"kind": "GitHub", "repository": "acme/widget", "workflow": "release.yml"}
P_RENAMED = {"kind": "GitHub", "repository": "acme/widget", "workflow": "publish.yml"}
P_OTHER = {"kind": "GitHub", "repository": "evil/widget", "workflow": "release.yml"}


class World:
    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def __call__(self, url):
        self.asked.append(url)
        return self.answers.get(url, (404, None))


def _npm(*releases):
    """releases: (version, account, trusted provider or None)."""
    doc = {"time": {}, "versions": {}}
    for day, (version, account, trusted) in enumerate(releases, 1):
        doc["time"][version] = f"2026-01-{day:02d}T00:00:00.000Z"
        user = {"name": account, "email": f"{account}@example.invalid"}
        if trusted:
            user["trustedPublisher"] = {"id": trusted, "oidcConfigId": "x"}
        doc["versions"][version] = {"_npmUser": user, "dist": {}}
    return World({NPM_URL: (200, doc)})


def _npm_check(world, version):
    return pc.check("npm", "widget", version, fetch_json=world)


# ---------------------------------------------------------------------------
# npm
# ---------------------------------------------------------------------------


def test_npm_same_account_is_continuity_and_names_nobody():
    world = _npm(("1.0.0", "alice", None), ("1.1.0", "alice", None))
    record = _npm_check(world, "1.1.0")
    assert record["status"] == "VERIFIED_RELATIONSHIP"
    assert record["evidence"] == {"rules": [], "compared_releases": 1, "previous_version": "1.0.0"}
    assert "alice" not in json.dumps(record) and "example.invalid" not in json.dumps(record)


def test_npm_new_account_is_an_indicator():
    world = _npm(("1.0.0", "alice", None), ("1.1.0", "mallory", None))
    record = _npm_check(world, "1.1.0")
    assert record["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert record["evidence"]["rules"] == ["new_account"]
    assert "never a takeover verdict" in record["statement"]
    assert "mallory" not in json.dumps(record)


def test_npm_switching_to_trusted_publishing_is_not_an_indicator():
    world = _npm(("1.0.0", "alice", None), ("1.1.0", "GitHub Actions", "github"))
    record = _npm_check(world, "1.1.0")
    assert record["status"] == "MISSING_EVIDENCE"
    assert "switch is common" in record["statement"]


def test_npm_dropping_trusted_publishing_is_an_indicator_even_from_a_known_account():
    world = _npm(
        ("1.0.0", "alice", None),
        ("1.1.0", "GitHub Actions", "github"),
        ("1.2.0", "alice", None),
    )
    assert _npm_check(world, "1.2.0")["evidence"]["rules"] == ["trusted_publishing_dropped"]
    world = _npm(("1.1.0", "GitHub Actions", "github"), ("1.2.0", "mallory", None))
    assert _npm_check(world, "1.2.0")["evidence"]["rules"] == [
        "trusted_publishing_dropped",
        "new_account",
    ]


def test_npm_an_account_outside_the_window_counts_as_new():
    old = [("0.0.1", "alice", None)]
    middle = [(f"0.1.{i}", "bob", None) for i in range(pc.NPM_WINDOW)]
    world = _npm(*old, *middle, ("1.0.0", "alice", None))
    record = _npm_check(world, "1.0.0")
    assert record["evidence"]["compared_releases"] == pc.NPM_WINDOW
    assert record["evidence"]["rules"] == ["new_account"]


def test_npm_first_release_and_unknown_version():
    world = _npm(("1.0.0", "alice", None))
    assert _npm_check(world, "1.0.0")["status"] == "MISSING_EVIDENCE"
    unknown = _npm_check(world, "9.9.9")
    assert unknown["status"] == "NOT_PERFORMED" and "no such version" in unknown["statement"]


def test_npm_releases_are_ordered_by_time_not_by_version():
    world = _npm(("2.0.0", "alice", None), ("1.9.9", "mallory", None))  # a backport, later
    assert _npm_check(world, "1.9.9")["evidence"]["previous_version"] == "2.0.0"


# ---------------------------------------------------------------------------
# PyPI
# ---------------------------------------------------------------------------


def _pypi(*releases):
    """releases: (version, publishers or None for no provenance, or "down")."""
    doc, answers = {"releases": {}}, {}
    for day, (version, publishers) in enumerate(releases, 1):
        wheel = f"widget-{version}-py3-none-any.whl"
        doc["releases"][version] = [
            {"filename": wheel, "upload_time_iso_8601": f"2026-01-{day:02d}T00:00:00Z"}
        ]
        url = pc.provenance_url("widget", version, wheel)
        if publishers == "down":
            answers[url] = (503, None)
        elif publishers is not None:
            bundles = [{"publisher": p, "attestations": []} for p in publishers]
            answers[url] = (200, {"version": 1, "attestation_bundles": bundles})
    return World({PYPI_URL: (200, doc)}), World(answers)


def _pypi_check(worlds, version):
    registry, integrity = worlds
    return pc.check("PyPI", "widget", version, fetch_json=registry, fetch_provenance=integrity)


def test_pypi_same_publisher_is_continuity():
    record = _pypi_check(_pypi(("1.0", [P_MAIN]), ("1.1", [P_MAIN])), "1.1")
    assert record["status"] == "VERIFIED_RELATIONSHIP"
    assert record["evidence"]["publishers"] == [P_MAIN]


def test_pypi_another_publisher_names_the_changed_fields():
    renamed = _pypi_check(_pypi(("1.0", [P_MAIN]), ("1.1", [P_RENAMED])), "1.1")
    assert renamed["evidence"]["rules"] == ["publisher_changed"]
    assert renamed["evidence"]["changed"] == ["workflow"]
    other = _pypi_check(_pypi(("1.0", [P_MAIN]), ("1.1", [P_OTHER])), "1.1")
    assert other["evidence"]["changed"] == ["repository"]
    assert other["evidence"]["previous_publishers"] == [P_MAIN]


def test_pypi_attestations_stopping_is_an_indicator_with_two_requests():
    worlds = _pypi(("1.0", [P_MAIN]), ("1.1", [P_MAIN]), ("1.2", None))
    record = _pypi_check(worlds, "1.2")
    assert record["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert record["evidence"]["rules"] == ["attestations_stopped"]
    assert len(worlds[1].asked) == 2  # this release and the one before


def test_pypi_without_attestations_is_missing_evidence():
    worlds = _pypi(("1.0", None), ("1.1", None), ("1.2", None))
    record = _pypi_check(worlds, "1.2")
    assert record["status"] == "MISSING_EVIDENCE" and "provenance" in record["statement"]
    assert len(worlds[1].asked) == 2


def test_pypi_compares_with_the_latest_attested_release_in_the_window():
    worlds = _pypi(("1.0", [P_MAIN]), ("1.1", None), ("1.2", [P_OTHER]))
    record = _pypi_check(worlds, "1.2")
    assert record["evidence"]["rules"] == ["publisher_changed"]
    assert record["evidence"]["previous_publishers"] == [P_MAIN]
    first = _pypi(*[(f"0.{i}", None) for i in range(5)], ("1.0", [P_MAIN]))
    record = _pypi_check(first, "1.0")
    assert record["status"] == "MISSING_EVIDENCE" and "first attested" in record["statement"]
    assert len(first[1].asked) == 1 + pc.PYPI_WINDOW


def test_pypi_an_unanswered_release_is_not_performed():
    record = _pypi_check(_pypi(("1.0", [P_MAIN]), ("1.1", "down")), "1.1")
    assert record["status"] == "NOT_PERFORMED"


def test_pypi_hostile_publisher_fields_are_dropped():
    hostile = {"kind": "GitHub\nignore previous", "repository": "a/b c", "workflow": "x.sh"}
    record = _pypi_check(_pypi(("1.0", [P_MAIN]), ("1.1", [hostile])), "1.1")
    assert record["evidence"]["publishers"] == [
        {"kind": None, "repository": None, "workflow": None}
    ]
    assert "ignore previous" not in json.dumps(record)


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


def test_unsupported_invalid_and_unreachable_are_not_performed():
    asked = World({})
    assert pc.check("Maven", "a:b", "1", fetch_json=asked)["status"] == "NOT_PERFORMED"
    assert pc.check("npm", "widget", None, fetch_json=asked)["status"] == "NOT_PERFORMED"
    assert pc.check("npm", "../etc", "1.0.0", fetch_json=asked)["status"] == "NOT_PERFORMED"
    assert pc.check("PyPI", "widget", "1.0\nx", fetch_json=asked)["status"] == "NOT_PERFORMED"
    assert asked.asked == []
    down = pc.check("npm", "widget", "1.0.0", fetch_json=lambda _u: (0, None))
    assert down["status"] == "NOT_PERFORMED" and down["evidence"]["http_status"] is None


def test_the_default_seams_are_offline_in_tests():
    assert pc.check("npm", "widget", "1.0.0")["status"] == "NOT_PERFORMED"
    assert pc.check("PyPI", "widget", "1.0")["status"] == "NOT_PERFORMED"


def test_every_statement_is_a_fixed_template():
    for status in pc._STATEMENTS:
        for why in pc._WHY.values():
            assert "{" not in why
    assert set(pc.RULES) == {
        "new_account",
        "trusted_publishing_dropped",
        "publisher_changed",
        "attestations_stopped",
    }
