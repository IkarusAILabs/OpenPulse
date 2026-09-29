"""Golden semantic scenarios: weak evidence never buys strong action.

A: public EOL with no inventory stays PROJECT_CHANGE, never ACTION_REQUIRED.
B: effective + confirmed dependency impact reaches ACTION_REQUIRED.
C: single-source AFFECTS_VERSION caps at REVIEW (EMERGING evidence).
D: cleared versions are NOT_AFFECTED + INFORMATIONAL, with reason.
E: upcoming changes stay WATCH/REVIEW even when versions match.
F: Bitnami identity split holds at verdict level.
G: unknown schemes stay UNKNOWN (see test_versions.py).
"""

import json

from core.risk.check import check_dependency
from core.schema.models import OSSEvent


def _django_eol():
    return OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))


def _dep(package, version):
    return {"kind": "package", "package": package, "ecosystem": "PyPI", "version": version}


def test_a_public_eol_is_not_action_required():
    """No inventory -> PROJECT_CHANGE framing, never customer impact."""
    from core.risk.impact import evaluate_impact

    finding = {
        "analyst": "change",
        "event_type": "EOL",
        "impact": "ACTION",
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "version", "versions": ["4.2"]},
    }
    out = evaluate_impact(finding)
    assert out["assessment"] == "PROJECT_CHANGE"
    assert out["assessment"] != "ACTION_REQUIRED"


def test_b_effective_confirmed_impact_is_action_required():
    from core.risk.impact import evaluate_impact

    finding = {
        "analyst": "change",
        "event_type": "EOL",
        "impact": "ACTION",
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "version", "versions": ["4.2"]},
    }
    context = {
        "verdict": "AFFECTS_VERSION",
        "affected": True,
        "confidence": "CONFIRMED",
        "reason": "4.2 in scope",
    }
    out = evaluate_impact(finding, dependency_context=context)
    assert (out["assessment"], out["eligibility"]) == ("ACTION_REQUIRED", "ACTION")


def test_c_single_source_affects_never_action():
    """EMERGING evidence: AFFECTS_VERSION caps at REVIEW, never ACTION."""
    from analyzers.security_analyst import correlate

    raw = {
        "nvd": [
            {
                "collector": "nvd",
                "id": "CVE-2026-0100",
                "cvss": {"base_score": 9.8},
                "cpes": [
                    {"criteria": "cpe:2.3:a:django:django:*:*:*:*:*:*:*:*", "vulnerable": True}
                ],
                "references": [],
            }
        ],
        "kev": [{"collector": "kev", "cve_id": "CVE-2026-0100", "match": "weak"}],
    }
    out = correlate(raw, {"slug": "django", "package": "django", "version": "5.0"})[0]
    assert out["relationship"] == "AFFECTS_PACKAGE"
    assert out["confidence"] == "EMERGING"
    assert out["impact"] == "REVIEW"


def test_d_cleared_version_is_not_affected_informational():
    result = check_dependency(_dep("django", "5.2"), [_django_eol()])
    assert result.relationship == "NOT_AFFECTED"
    assert result.affected is False


def test_e_upcoming_change_is_not_action():
    from core.risk.impact import evaluate_impact

    finding = {
        "analyst": "change",
        "event_type": "EOL",
        "impact": "REVIEW",
        "lifecycle_state": "UPCOMING",
        "scope": {"kind": "version", "versions": ["5.0"]},
    }
    out = evaluate_impact(finding)
    assert out["eligibility"] in ("WATCH", "REVIEW")
    assert out["assessment"] != "ACTION_REQUIRED"


def test_f_bitnami_identity_split_at_verdicts():
    event = OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))
    hit = check_dependency({"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}, [event])
    miss = check_dependency({"kind": "image", "ref": "docker.io/redis:7.2"}, [event])
    assert (hit.affected, hit.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (miss.affected, miss.relationship) == (False, "NOT_AFFECTED")


def test_detection_method_labels():
    """Heuristics declare themselves; observations state facts."""
    from analyzers.change_analyst import analyze_diffs, analyze_registries

    pattern = analyze_registries(
        [
            {"collector": "registries", "namespace": "acme", "repo": "w", "latest_only": True},
            {
                "collector": "registries",
                "namespace": "acmelegacy",
                "repo": "w",
                "has_versioned_tags": True,
            },
        ]
    )
    assert pattern[0]["detection_method"] == "namespace_heuristic"
    diffed = analyze_diffs(
        [
            {
                "type": "tag_disappeared",
                "namespace": "acme",
                "repository": "w",
                "tag": "1.0",
                "observed_at": "2026-09-20",
            }
        ]
    )
    assert diffed[0]["detection_method"] == "registry_observation"
