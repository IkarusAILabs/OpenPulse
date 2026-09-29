"""Impact eligibility + assessment (brief §2-§4, §7)."""

from datetime import date

from core.risk.impact import evaluate_impact

TODAY = date(2026, 9, 26)


def _eol(version="5.0", state="EFFECTIVE", impact="ACTION"):
    return {
        "analyst": "change",
        "event_type": "EOL",
        "signal": "lifecycle",
        "impact": impact,
        "lifecycle_state": state,
        "effective_at": "2026-09-01",
        "observed_at": "2026-09-26",
        "scope": {"kind": "version", "versions": [version]},
        "affected_versions": [version],
    }


def test_effective_scoped_eol_is_project_change_action_framed():
    out = evaluate_impact(_eol(), today=TODAY)
    assert out["assessment"] == "PROJECT_CHANGE"
    assert out["eligibility"] == "ACTION"
    assert out["reasons"]


def test_upcoming_eol_is_watch():
    out = evaluate_impact(_eol(state="UPCOMING"), today=TODAY)
    assert (out["assessment"], out["eligibility"]) == ("PROJECT_CHANGE", "WATCH")


def test_archived_is_review_never_automatic_action():
    finding = {
        "analyst": "change", "event_type": "PROJECT_ARCHIVED",
        "signal": "lifecycle", "impact": "ACTION",
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "project", "versions": []},
    }
    out = evaluate_impact(finding, today=TODAY)
    assert out["assessment"] == "PROJECT_CHANGE"
    assert out["eligibility"] == "REVIEW"


def test_unscoped_lifecycle_capped_at_review():
    finding = {"analyst": "change", "event_type": "EOL", "impact": "ACTION"}
    out = evaluate_impact(finding, today=TODAY)
    assert out["eligibility"] == "REVIEW"
    assert out["assessment"] == "PROJECT_SIGNAL"


def test_affected_version_with_policy_is_action_required():
    context = {"verdict": "AFFECTS_VERSION", "affected": True,
               "confidence": "CORROBORATED", "reason": "pin matches scope"}
    out = evaluate_impact(_eol(), dependency_context=context, today=TODAY)
    assert out["assessment"] == "ACTION_REQUIRED"
    assert out["eligibility"] == "ACTION"


def test_affected_but_weak_confidence_is_not_action_required():
    context = {"verdict": "AFFECTS_VERSION", "affected": True,
               "confidence": "EMERGING", "reason": "pin matches scope"}
    out = evaluate_impact(_eol(), dependency_context=context, today=TODAY)
    assert out["assessment"] == "AFFECTS_DEPENDENCY"
    assert out["eligibility"] == "ACTION"


def test_not_affected_is_informational_with_reason():
    context = {"verdict": "NOT_AFFECTED", "affected": False,
               "confidence": "CORROBORATED",
               "reason": "django==5.2 is outside scope versions ['5.0']"}
    out = evaluate_impact(_eol(), dependency_context=context, today=TODAY)
    assert out["assessment"] == "AFFECTS_DEPENDENCY"
    assert out["eligibility"] == "INFORMATIONAL"
    assert "5.2" in out["reasons"][0]


def test_eol_detected_is_not_action_required():
    # The central rule: no inventory -> never ACTION_REQUIRED.
    out = evaluate_impact(_eol(), today=TODAY)
    assert out["assessment"] != "ACTION_REQUIRED"
