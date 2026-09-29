"""Lifecycle finding -> OSSEvent -> dependency verdicts (brief §2, §6).

Proves lifecycle matching reuses the security verdict machinery:
Django 5.0 EOL as an analyst finding bridges to a scoped event, and
the same check_dependency call yields AFFECTS_VERSION / NOT_AFFECTED /
RELATED for pins 5.0 / 5.2 / unknown.
"""

from datetime import date

from analyzers.change_analyst import analyze_endoflife
from analyzers.lifecycle_events import finding_to_event
from core.risk.check import check_dependency

TODAY = date(2026, 9, 26)


def _django_finding():
    entries = [{
        "collector": "endoflife",
        "product": "django",
        "cycle": "5.0",
        "eol": "2026-09-01",
        "link": "https://endoflife.date/django",
    }]
    findings = analyze_endoflife(entries, today=TODAY)
    assert len(findings) == 1
    return findings[0]


def _dep(version):
    return {"kind": "package", "package": "django", "ecosystem": "PyPI",
            "version": version}


def test_bridge_carries_scope_and_dates():
    event = finding_to_event(_django_finding(), "django", today=TODAY)
    assert event.scope is not None
    assert event.scope.kind == "version"
    assert event.scope.versions == ["5.0"]
    assert event.event_type.value == "EOL"
    assert event.id == "evt-django-eol-5.0"
    assert len(event.evidences) >= 1


def test_django_50_is_affects_version():
    event = finding_to_event(_django_finding(), "django", today=TODAY)
    result = check_dependency(_dep("5.0"), [event])
    assert result.relationship == "AFFECTS_VERSION"
    assert result.affected is True


def test_django_52_is_not_affected():
    event = finding_to_event(_django_finding(), "django", today=TODAY)
    result = check_dependency(_dep("5.2"), [event])
    assert result.relationship == "NOT_AFFECTED"
    assert result.affected is False


def test_django_unknown_version_is_related():
    event = finding_to_event(_django_finding(), "django", today=TODAY)
    result = check_dependency(_dep(None), [event])
    assert result.relationship == "RELATED"
    assert result.affected is False


def test_bridged_event_never_smuggles_action():
    event = finding_to_event(_django_finding(), "django", today=TODAY)
    assert event.impact.value in ("REVIEW", "WATCH", "INFORMATIONAL")
