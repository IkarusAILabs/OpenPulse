"""The real pinned comparator bridges, against documented ecosystem semantics.

Each bridge runs its ecosystem's own reference implementation (node-semver,
Go's x/mod/semver, Maven's ComparableVersion). The vectors below restate
documented behaviour: the SemVer 2.0 precedence example, Go's short forms,
build metadata and pseudo-versions, and Maven's qualifier order and release
aliases. Where a toolchain is absent the tests skip; the CI `comparators`
job sets OPENPULSE_REQUIRE_COMPARATORS=1, which turns every skip into a
failure, so the bridges are exercised for real on every change.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation"))

import ecosystem_versions as ev  # noqa: E402

REQUIRED = os.environ.get("OPENPULSE_REQUIRE_COMPARATORS") == "1"


@pytest.fixture(scope="module")
def comparators():
    found = ev.Comparators()
    yield found
    found.close()


def _bridge(comparators, name):
    if name not in comparators.bridges:
        reason = f"{name} comparator unavailable: {comparators.status[name].get('error')}"
        if REQUIRED:
            pytest.fail(reason)
        pytest.skip(reason)
    return comparators.bridges[name]


def _ascending(bridge, versions):
    for a, b in zip(versions, versions[1:]):
        assert bridge.compare(a, b) == -1, (a, b)
        assert bridge.compare(b, a) == 1, (b, a)


SEMVER_PRECEDENCE = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
    "2.0.0",
    "2.1.0",
    "2.1.1",
]


def test_bridges_report_their_pins(comparators):
    for name in ev.PINS:
        _bridge(comparators, name)
        assert comparators.status[name]["reported"] == ev.PINS[name]


def test_npm_semver_precedence_and_strictness(comparators):
    npm = _bridge(comparators, "npm")
    _ascending(npm, SEMVER_PRECEDENCE)
    assert npm.compare("1.0.0+build.1", "1.0.0") == 0  # build metadata has no precedence
    assert npm.parse("v1.2.3")["core"] == [1, 2, 3]
    for invalid in ("1.2", "01.2.3", "1.2.3.4", "a.b.c"):
        assert npm.parse(invalid)["valid"] is False, invalid
    assert comparators.in_line("npm", "6.2.0-rc.1", "6.2") is True
    assert comparators.in_line("npm", "6.20.1", "6.2") is False


def test_go_semver_forms(comparators):
    go = _bridge(comparators, "go")
    _ascending(go, ["v" + v for v in SEMVER_PRECEDENCE])
    assert go.compare("v1.2", "v1.2.0") == 0  # short forms are valid
    assert go.compare("v1.2.3+incompatible", "v1.2.3") == 0
    assert go.parse("1.2.3")["valid"] is False  # Go requires the prefix
    assert go.parse("v1.2.3.4")["valid"] is False
    pseudo = "v0.0.0-20210101000000-abcdefabcdef"
    assert go.compare(pseudo, "v0.0.0") == -1  # a pseudo-version is a pre-release
    assert comparators.in_line("Go", "v1.2.4-0.20210101000000-abcdefabcdef", "1.2") is True
    assert comparators.in_line("Go", "3.5.9", "3.5") is True  # adapter adds the prefix


def test_maven_comparable_version_order(comparators):
    maven = _bridge(comparators, "maven")
    _ascending(maven, ["1-alpha", "1-beta", "1-milestone", "1-rc", "1-snapshot", "1", "1-sp"])
    for same in ("1.0", "1.0.0", "1-ga", "1-final"):
        assert maven.compare(same, "1") == 0, same
    assert maven.compare("1.0-alpha-1", "1.0") == -1
    assert maven.parse("3.9-rc1")["core"] == [3, 9]
    assert comparators.in_line("Maven", "3.9-rc1", "3.9") is True
    assert comparators.in_line("Maven", "3.9-rc1", "3.8") is False
    assert comparators.in_line("Maven", "1.0.0", "1.0") is True  # trailing zeros trimmed
    for undecidable in ("LATEST", "RELEASE", "${project.version}"):
        assert maven.parse(undecidable)["valid"] is False, undecidable
