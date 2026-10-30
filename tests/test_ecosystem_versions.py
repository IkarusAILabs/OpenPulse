"""Pinned ecosystem comparator adapter (evaluation/ecosystem_versions.py).

Uses a stand-in bridge (tests/support/fake_comparator.py) that speaks the
real bridges' protocol, so the adapter's handshake, pin check, fail-closed
mode and release-line rule are tested on every machine. The real bridges
are tested in tests/test_ecosystem_comparators.py.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

import ecosystem_versions as ev  # noqa: E402
import strong_baseline  # noqa: E402

FAKE = [sys.executable, str(ROOT / "tests" / "support" / "fake_comparator.py")]


@pytest.fixture
def fake(monkeypatch):
    """Route every bridge to the stand-in, reporting each one's pinned version."""

    def install(**overrides):
        for name, pin in ev.PINS.items():
            monkeypatch.setenv(f"OPENPULSE_COMPARATOR_{name.upper()}", json.dumps(FAKE))
        monkeypatch.setenv("FAKE_LIBRARY", overrides.get("library", "semver"))
        monkeypatch.setenv("FAKE_VERSION", overrides.get("version", "7.8.5"))
        if overrides.get("trim"):
            monkeypatch.setenv("FAKE_TRIM", "1")

    return install


def test_a_bridge_reporting_its_pin_is_used(fake):
    fake()
    comparators = ev.Comparators(names=("npm",))
    try:
        assert comparators.complete and comparators.supports("npm")
        assert comparators.status["npm"]["reported"] == ev.PINS["npm"]
    finally:
        comparators.close()


def test_a_bridge_reporting_another_version_is_refused(fake):
    fake(version="7.8.4")
    comparators = ev.Comparators(names=("npm",))
    assert not comparators.complete and not comparators.supports("npm")
    assert "differs from the pin" in comparators.status["npm"]["error"]
    with pytest.raises(ev.ComparatorUnavailable):
        ev.Comparators(required=True, names=("npm",))


def test_required_mode_refuses_missing_toolchains(monkeypatch):
    for name in ev.PINS:
        monkeypatch.delenv(f"OPENPULSE_COMPARATOR_{name.upper()}", raising=False)
    monkeypatch.setattr(ev, "default_command", lambda name: None)
    with pytest.raises(ev.ComparatorUnavailable, match="required but unavailable"):
        ev.Comparators(required=True)
    lenient = ev.Comparators()
    assert not lenient.complete
    assert all(s["error"] for s in lenient.status.values())


def test_release_line_rule_counts_prereleases_in_their_own_line(fake):
    fake()
    comparators = ev.Comparators(names=("npm",))
    try:
        assert comparators.in_line("npm", "6.2.0-rc.1", "6.2") is True  # unlike npm `satisfies`
        assert comparators.in_line("npm", "6.20.1", "6.2") is False
        assert comparators.in_line("npm", "not-a-version", "6.2") is None
        assert comparators.in_line("npm", "6.2.1", "six") is None
    finally:
        comparators.close()


def test_maven_trimmed_cores_are_zero_padded(fake):
    fake(library="org.apache.maven:maven-artifact", version="3.9.16", trim=True)
    comparators = ev.Comparators(names=("maven",))
    try:
        assert comparators.release_core("Maven", "1.0.0") == [1]
        assert comparators.in_line("Maven", "1.0.0", "1.0") is True
        assert comparators.in_line("Maven", "1.1", "1.0") is False
    finally:
        comparators.close()


def test_go_versions_get_their_prefix(fake):
    fake(library="golang.org/x/mod", version="v0.42.0")
    comparators = ev.Comparators(names=("go",))
    try:
        bridge = comparators.bridges["go"]
        assert comparators.in_line("Go", "3.5.9", "3.5") is True
        assert "v3.5.9" in bridge._cache  # asked in Go's own spelling
    finally:
        comparators.close()


def test_baseline_v_decides_through_the_bridges(fake):
    fake()
    comparators = ev.Comparators(names=("npm",))
    try:
        strong_baseline.use_comparators(comparators)
        assert strong_baseline._in_line("18.3.1-rc.1", "18", "npm") is True
        strong_baseline.use_comparators(None)
        # Without a bridge: plain dotted numbers only.
        assert strong_baseline._in_line("18.3.1-rc.1", "18", "npm") is None
    finally:
        strong_baseline.use_comparators(None)
        comparators.close()


def test_the_registered_run_refuses_without_comparators(monkeypatch):
    import run

    monkeypatch.setattr(ev, "default_command", lambda name: None)
    with pytest.raises(ev.ComparatorUnavailable):
        run.run(require_comparators=True)
    result = run.run()
    assert result["comparators"]["complete"] is False
    assert result["registration"]["registered"]["valid"] is False
    assert result["registration"]["all_labels_illustrative"]["valid"] is True
