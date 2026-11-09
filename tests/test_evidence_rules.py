"""Evidence rules for change evidence beyond lifecycle (v0.20.0 item C5).

Exit criterion: every finding from C2-C4 states its confidence and what
it rests on. A difference OpenPulse observed is EMERGING; a flag the
publisher set on the registry is the publisher's own statement
(CONFIRMED, a classifier EMERGING); a license change GitHub detects is
CORROBORATED only when the registry's license agrees. Lead time is claimed
for lifecycle events only.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from analyzers.change_analyst import (
    BASIS_OBSERVED_DIFFERENCE,
    BASIS_PUBLISHER_STATEMENT,
    analyze_deprecations,
    analyze_release_license_changes,
    analyze_repository_changes,
    corroborate_repository_license,
    same_license,
)
from analyzers.report_analyst import finding_confidence
from core.leadtime import finding_lead_time
from core.observations.base import GitHubRepositoryObservation
from core.observations.repository import diff_repository_observations
from core.registry_deprecation import CHECKED, NPM_DEPRECATED, PACKAGE, PYPI_INACTIVE

T0 = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
TODAY = date(2026, 11, 9)


def _record(day=0, **facts):
    values = {
        "namespace": "example",
        "repository": "widget",
        "full_name": "example/widget",
        "archived": False,
        "license": "MIT",
        "observed_at": T0 + timedelta(days=day),
    }
    values.update(facts)
    return GitHubRepositoryObservation(**values).seal()


def _repository_findings(**after):
    changes = diff_repository_observations(_record(), _record(1, **after))
    return analyze_repository_changes(changes, today=TODAY)


def _relicensed():
    [finding] = _repository_findings(license="AGPL-3.0")
    return finding


# --- what each finding rests on ---------------------------------------------------------


def test_an_observed_repository_change_is_emerging():
    for finding in _repository_findings(license="AGPL-3.0", archived=True):
        assert finding["confidence"] == "EMERGING"
        assert finding["evidence_basis"] == BASIS_OBSERVED_DIFFERENCE
        assert finding_confidence(finding) == "EMERGING"


def test_a_release_license_transition_is_an_observed_difference():
    result = {
        "status": "COMPARED",
        "ecosystem": "npm",
        "name": "widget",
        "purl": "pkg:npm/widget",
        "transitions": [
            {
                "from_version": "1.0.0",
                "to_version": "2.0.0",
                "from_license": "MIT",
                "to_license": "BUSL-1.1",
                "published": "2026-10-01T00:00:00Z",
                "between_compared": True,
            }
        ],
    }
    [finding] = analyze_release_license_changes(result, today=TODAY)
    assert finding["confidence"] == "EMERGING"
    assert finding["evidence_basis"] == BASIS_OBSERVED_DIFFERENCE


@pytest.mark.parametrize(
    ("kind", "confidence"),
    [(NPM_DEPRECATED, "CONFIRMED"), (PYPI_INACTIVE, "EMERGING")],
)
def test_a_publisher_flag_is_the_publishers_statement(kind, confidence):
    result = {
        "status": CHECKED,
        "ecosystem": "npm" if kind == NPM_DEPRECATED else "PyPI",
        "name": "widget",
        "purl": "pkg:npm/widget",
        "latest": "2.0.0",
        "flags": [{"kind": kind, "level": PACKAGE, "version": "2.0.0", "message": None}],
    }
    [finding] = analyze_deprecations(result, today=TODAY)
    assert finding["evidence_basis"] == BASIS_PUBLISHER_STATEMENT
    assert finding["confidence"] == confidence
    assert finding_confidence(finding) == confidence


# --- GitHub's license detection needs the registry ----------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "same"),
    [
        ("MIT", "mit", True),
        ("AGPL-3.0", "AGPL-3.0-only", True),
        ("(MIT)", "MIT", True),
        ("MIT License", "MIT", True),
        ("Apache-2.0", "Apache Software License", False),
        ("GPL-3.0", "GPL-3.0-or-later", False),
        ("", "", False),
        (None, "MIT", False),
    ],
)
def test_same_license(a, b, same):
    assert same_license(a, b) is same


def test_registry_agreement_corroborates_a_github_license_change():
    finding = corroborate_repository_license(
        _relicensed(),
        [
            {"purl": "pkg:npm/widget", "license": "AGPL-3.0-only"},
            {"purl": "pkg:pypi/widget", "license": "MIT"},
        ],
    )
    assert finding["confidence"] == "CORROBORATED"
    assert finding["evidence_strength"] == "strong"
    assert finding["registry_agreement"]["agreeing"] == [
        {"purl": "pkg:npm/widget", "license": "AGPL-3.0-only"}
    ]
    assert "The registry agrees: pkg:npm/widget declares AGPL-3.0." in finding["summary"]


def test_a_registry_that_has_not_caught_up_leaves_it_emerging():
    original = _relicensed()
    finding = corroborate_repository_license(
        original, [{"purl": "pkg:npm/widget", "license": "MIT"}]
    )
    assert finding["confidence"] == "EMERGING"
    assert "does not agree yet (pkg:npm/widget declares MIT)" in finding["summary"]
    assert original["summary"] != finding["summary"]  # the input is not mutated
    assert "registry_agreement" not in original


def test_no_registry_license_leaves_it_emerging_and_says_so_in_the_record():
    finding = corroborate_repository_license(
        _relicensed(), [{"purl": "pkg:npm/w", "license": None}]
    )
    assert finding["confidence"] == "EMERGING"
    assert finding["registry_agreement"]["declared"] == []


def test_only_github_license_changes_are_corroborated():
    [archived] = _repository_findings(archived=True)
    registry = [{"purl": "pkg:npm/widget", "license": "MIT"}]
    assert corroborate_repository_license(archived, registry) is archived


def test_report_sweep_asks_the_registry_about_a_github_license_change(tmp_path, monkeypatch):
    from cli.main import _observe_catalog_repositories
    from collectors.github import collector

    meta = {"collector": "github", "kind": "repo_meta", "repo": "example/widget"}
    meta.update(full_name="example/widget", archived=False)
    metas = [dict(meta, license="MIT"), dict(meta, license="AGPL-3.0")]
    monkeypatch.setattr(collector.GitHubCollector, "fetch_repo_meta", lambda s, r: metas.pop(0))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    packument = {
        "versions": {"1.0.0": {"license": "MIT"}, "2.0.0": {"license": "AGPL-3.0-only"}},
        "time": {"1.0.0": "2026-01-01T00:00:00Z", "2.0.0": "2026-11-01T00:00:00Z"},
    }
    seen = []

    def fetch(url):
        seen.append(url)
        return (200, packument) if url == "https://registry.npmjs.org/widget" else (0, None)

    catalog = [
        {
            "slug": "widget",
            "github": "example/widget",
            "packages": [{"ecosystem": "npm", "name": "widget"}],
        }
    ]
    store = str(tmp_path / "store")
    assert _observe_catalog_repositories(catalog, store, None, (), fetch_json=fetch) == []
    assert seen == []  # no license change, no registry request
    [finding] = _observe_catalog_repositories(catalog, store, None, (), fetch_json=fetch)
    assert finding["confidence"] == "CORROBORATED"
    assert seen == ["https://registry.npmjs.org/widget"]


# --- lead time is lifecycle-only ----------------------------------------------------------


def test_a_repository_change_makes_no_lead_time_claim():
    finding = dict(_relicensed(), first_detected_at="2026-11-09", effective_at="2026-11-09")
    assert finding_lead_time(finding) == (None, None, None)


def test_a_lifecycle_event_keeps_its_lead_time():
    finding = {"event_type": "EOL", "first_detected_at": "2026-11-01", "effective_at": "2027-01-01"}
    assert finding_lead_time(finding) == (61, "2026-11-01", "2027-01-01")


def test_a_deprecation_flag_without_a_date_has_no_lead_time():
    finding = {"event_type": "DEPRECATION", "first_detected_at": "2026-11-01", "effective_at": None}
    assert finding_lead_time(finding) == (None, None, None)


def test_a_finding_without_an_event_type_is_read_as_before():
    finding = {"first_detected_at": "2026-11-01", "effective_at": "2026-11-11"}
    assert finding_lead_time(finding) == (10, "2026-11-01", "2026-11-11")
