"""M2 discovery replays — accepted cases re-fire from recorded evidence.

Each test replays one formalized discovery (see docs/DISCOVERIES.md)
from its recorded inputs and asserts the full acceptance shape:
finding type, impact, scope, evidence identity, and dates. If a case
cannot replay, it does not count — remove it from the ledger, do not
weaken the test.
"""

import json
from datetime import date
from pathlib import Path

from analyzers.change_analyst import analyze_github_meta

# Recorded live 2026-10-02: minio/minio repo_meta (archived, owner unchanged).
MINIO_META = {
    "collector": "github",
    "kind": "repo_meta",
    "repo": "minio/minio",
    "full_name": "minio/minio",
    "archived": True,
    "pushed_at": "2026-04-24T17:54:39Z",
    "default_branch": "master",
    "license": "AGPL-3.0",
    "stargazers": 54000,
    "url": "https://github.com/minio/minio",
}


def test_minio_archived_replays():
    findings = analyze_github_meta([MINIO_META])
    assert len(findings) == 1
    finding = findings[0]
    assert finding["event_type"] == "PROJECT_ARCHIVED"
    assert finding["impact"] == "ACTION"
    assert finding["lifecycle_state"] == "EFFECTIVE"
    assert finding["scope"] == {"kind": "project", "versions": []}
    assert finding["supporting"] == [MINIO_META]


def test_minio_shows_no_ownership_drift():
    """The detector must not hallucinate on the verified case: same
    owner in, no OWNERSHIP_CHANGE out."""
    findings = analyze_github_meta([MINIO_META])
    assert all(f["event_type"] != "OWNERSHIP_CHANGE" for f in findings)


def test_bitnami_digest_mainline_gap_closed():
    """The version-aware latest-only rule derives the Bitnami split
    from the recorded probe shapes: bitnami/redis serves `latest` +
    hundreds of `sha256-*` digest tags (recorded full-set observation,
    2026-10-02), which is distribution machinery, not a versioned
    distribution — so the mainline counts as latest-only and the
    model-change finding fires against bitnamilegacy/redis holding
    the 919+ version-like tags (see docs/DISCOVERIES.md case 2).
    The flags below are exactly what `parse_tags` produces for those
    two recorded tag sets (see `test_parse_tags_version_aware_flags`),
    not hand-tuned to force the firing.
    """
    from analyzers.change_analyst import analyze_registries
    from collectors.registries.docker import parse_tags

    bitnami_tags = ["latest"] + [f"sha256-{i}" for i in range(5)]
    legacy_tags = ["latest", "7.2.0", "5.0.4", "5.0.3-r75"]
    bitnami_probe = parse_tags(
        "bitnami",
        "redis",
        {"count": len(bitnami_tags), "results": [{"name": t} for t in bitnami_tags]},
    )
    legacy_probe = parse_tags(
        "bitnamilegacy",
        "redis",
        {"count": len(legacy_tags), "results": [{"name": t} for t in legacy_tags]},
    )
    assert bitnami_probe["latest_only"] is True
    assert bitnami_probe["has_versioned_tags"] is False
    assert legacy_probe["latest_only"] is False
    assert legacy_probe["has_versioned_tags"] is True

    findings = analyze_registries([bitnami_probe, legacy_probe])
    fired = [f for f in findings if f.get("distribution_model_change")]
    assert len(fired) == 1
    assert fired[0]["event_type"] == "DISTRIBUTION_CHANGE"
    assert "bitnami" in fired[0]["title"]
    assert "bitnamilegacy" in fired[0]["title"]


def test_versioned_mainlines_do_not_trigger_the_split():
    """No false positives on versioned mainlines: a namespace serving
    real version tags (the `library/nginx` full-set shape) is not
    latest-only, so no model-change finding fires — even when a
    legacy-marked namespace exists for the same repo.
    """
    from analyzers.change_analyst import analyze_registries
    from collectors.registries.docker import parse_tags

    mainline_tags = ["latest", "1.30-alpine3.24", "1.30.5-alpine", "stable"]
    mainline_probe = parse_tags(
        "library",
        "nginx",
        {"count": len(mainline_tags), "results": [{"name": t} for t in mainline_tags]},
    )
    legacy_probe = parse_tags(
        "librarylegacy", "nginx", {"count": 2, "results": [{"name": "1.30"}, {"name": "1.29"}]}
    )
    assert mainline_probe["latest_only"] is False
    assert mainline_probe["has_versioned_tags"] is True

    findings = analyze_registries([mainline_probe, legacy_probe])
    assert all(not f.get("distribution_model_change") for f in findings)



# --- Phase 14 (v0.20.0 C6): change evidence beyond lifecycle --------------------------
#
# Cases 11-16 replay the registry responses recorded 2026-11-09 under
# data/fixtures/ (trimmed to the fields the checks read, values verbatim)
# through the same checks and analysts the CLI runs.

_FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"
_DAY = date(2026, 11, 9)


def _recorded(urls):
    """A fetch that answers only the recorded URLs, from their fixture files."""

    def fetch(url):
        if url not in urls:
            return 0, None
        recorded = json.loads((_FIXTURES / urls[url]).read_text(encoding="utf-8"))
        assert recorded["source_url"] == url
        return 200, recorded["response"]

    return fetch


def _license_case(ecosystem, name, version, urls):
    from analyzers.change_analyst import analyze_release_license_changes
    from core.release_license import check

    result = check(ecosystem, name, version, fetch_json=_recorded(urls))
    return analyze_release_license_changes(result, today=_DAY)


def _flag_case(ecosystem, name, version, urls):
    from analyzers.change_analyst import analyze_deprecations
    from core.registry_deprecation import check

    result = check(ecosystem, name, version, fetch_json=_recorded(urls))
    return analyze_deprecations(result, today=_DAY)


def test_case_11_react_relicensed_bsd_to_mit_replays():
    [finding] = _license_case(
        "npm",
        "react",
        "15.6.1",
        {"https://registry.npmjs.org/react": "react-relicense/packument.json"},
    )
    assert finding["event_type"] == "LICENSE_CHANGE"
    assert finding["title"] == "react (npm) changed its license from BSD-3-Clause to MIT in 15.6.2"
    assert finding["effective_at"] == "2017-09-26T00:10:25.817Z"
    assert finding["registry_evidence"]["between_compared"] is True
    assert finding["confidence"] == "EMERGING"
    assert finding["support"] == "verified" and finding["verified_cases"] == ["Case 11"]


def test_case_12_psycopg2_dropped_zpl_replays():
    [finding] = _license_case(
        "PyPI",
        "psycopg2",
        "2.7",
        {
            "https://pypi.org/pypi/psycopg2/json": "psycopg2-license/project.json",
            "https://pypi.org/pypi/psycopg2/2.7/json": "psycopg2-license/release-2.7.json",
        },
    )
    assert finding["registry_evidence"]["from_license"] == "LGPL with exceptions or ZPL"
    assert finding["registry_evidence"]["to_license"] == "LGPL with exceptions"
    # Two releases read: the change is somewhere after 2.7, at the latest in 2.9.13.
    assert finding["registry_evidence"]["between_compared"] is False
    assert "somewhere after 2.7, at the latest in 2.9.13" in finding["summary"]
    assert finding["support"] == "verified" and finding["verified_cases"] == ["Case 12"]


def test_case_13_request_deprecated_replays():
    [finding] = _flag_case(
        "npm",
        "request",
        None,
        {"https://registry.npmjs.org/request/latest": "request-deprecated/latest.json"},
    )
    assert finding["event_type"] == "DEPRECATION"
    assert finding["title"] == "request (npm) is deprecated by its publisher"
    assert finding["scope"]["versions"] == [] and finding["affected_versions"] == ["*"]
    assert "github.com/request/request/issues/3142" in finding["registry_evidence"]["message"]
    assert finding["confidence"] == "CONFIRMED"
    assert finding["support"] == "verified"


def test_case_14_uuid_old_line_deprecated_while_latest_is_not_replays():
    [finding] = _flag_case(
        "npm",
        "uuid",
        "3.4.0",
        {
            "https://registry.npmjs.org/uuid/latest": "uuid-version-deprecated/latest.json",
            "https://registry.npmjs.org/uuid/3.4.0": "uuid-version-deprecated/3.4.0.json",
        },
    )
    assert finding["title"] == "uuid 3.4.0 (npm) is deprecated by its publisher"
    assert finding["scope"]["versions"] == ["3.4.0"]
    assert finding["registry_evidence"]["latest"] == "14.0.3"
    assert finding["support"] == "verified"


def test_case_15_urllib3_2_0_0_yanked_replays():
    [finding] = _flag_case(
        "PyPI",
        "urllib3",
        "2.0.0",
        {"https://pypi.org/pypi/urllib3/json": "urllib3-yanked/project.json"},
    )
    assert finding["title"] == "urllib3 2.0.0 (PyPI) was yanked by its publisher"
    assert finding["scope"]["versions"] == ["2.0.0"]
    assert "Upgrade to at least 2.0.2" in finding["registry_evidence"]["message"]
    assert finding["confidence"] == "CONFIRMED"
    assert finding["support"] == "verified"


def test_case_16_attrdict_declares_itself_inactive_replays():
    [finding] = _flag_case(
        "PyPI",
        "attrdict",
        None,
        {"https://pypi.org/pypi/attrdict/json": "attrdict-inactive/project.json"},
    )
    assert finding["title"] == "attrdict (PyPI) declares itself inactive"
    assert finding["confidence"] == "EMERGING"
    assert finding["support"] == "verified"


def test_every_named_case_is_a_verified_entry_in_the_ledger():
    from analyzers.change_analyst import VERIFIED_CASES

    ledger = (Path(__file__).resolve().parent.parent / "docs" / "DISCOVERIES.md").read_text(
        encoding="utf-8"
    )
    for cases in VERIFIED_CASES.values():
        for case in cases:
            heading = next(
                (line for line in ledger.splitlines() if line.startswith(f"## {case} ")), None
            )
            assert heading is not None, case
            assert "✅ VERIFIED" in heading, heading


def test_a_class_without_a_verified_case_ships_as_experimental():
    from analyzers.change_analyst import VERIFIED_CASES, analyze_repository_changes
    from analyzers.report_analyst import render_finding_md

    assert VERIFIED_CASES["repository_history"] == ()
    change = {
        "type": "archived",
        "namespace": "example",
        "repository": "widget",
        "previous": False,
        "current": True,
        "observed_at": "2026-11-09T00:00:00+00:00",
    }
    [finding] = analyze_repository_changes([change], today=_DAY)
    assert finding["support"] == "experimental" and finding["verified_cases"] == []
    assert finding["summary"].endswith(
        "Experimental: no verified case of this detection yet (docs/DISCOVERIES.md)."
    )
    assert "**[PROJECT_ARCHIVED, experimental]**" in render_finding_md(finding)
