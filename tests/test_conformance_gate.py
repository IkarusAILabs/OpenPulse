"""Conformance gate: the implementation must keep agreeing with the specification.

TR-2026-01's oracle (``conformance/oracle.py``) is written from the
report's text and imports nothing from the engine. These tests fail the
build if the implementation drifts from it: any disagreement other than
the documented label difference, on the generated matrix or on seeded
random cases, or any version-ordering disagreement with ``packaging``.
"""

import sys
from pathlib import Path

CONFORMANCE = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(CONFORMANCE))

import matrix  # noqa: E402
import randomized  # noqa: E402
import versions_differential  # noqa: E402

#: The one documented difference: for a package of the event's own
#: project, the specification's project tie (AFFECTS_PROJECT) against the
#: implementation's RELATED. Both are unresolved; both block a clearance.
_ALLOWED = {"conform", "label: both unresolved"}


def test_matrix_has_no_disagreement_beyond_documented_labels():
    result = matrix.run()
    severities = {r["severity"] for r in result["rows"]}
    assert severities <= _ALLOWED, sorted(severities - _ALLOWED)
    labels = [r for r in result["rows"] if r["severity"] != "conform"]
    # Packages of the event's own project: `redis`, and `redis-server`, whose
    # name is not the project's slug (F2).
    assert all(r["dependency"].split("==")[0] in ("redis", "redis-server") for r in labels)
    assert all(r["identity"] == "project" for r in labels)


def test_randomized_cases_conform():
    result = randomized.run(5000, 2026)
    assert result["summary_severity"] == {"conform": 5000}
    assert set(result["per_event_severity"]) == {"conform"}


def test_versions_agree_with_reference_implementations():
    result = versions_differential.run()
    assert result["pep440_pairs"]["disagreements"] == []
    assert result["pypi_ranges"]["disagreements"] == []
    assert result["semver"]["vector_failures"] == []
    assert result["semver"]["range_failures"] == []
    assert result["semver"]["order_inconsistencies"] == 0
