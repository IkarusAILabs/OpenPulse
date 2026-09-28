"""Golden scenarios — the canonical end-to-end proofs.

Each scenario answers the five product questions (what changed, is it
evidenced, what is affected, when does it matter, does it affect my
org) with a non-lifecycle story where one exists. These are the tests
a lifecycle database alone could never pass.
"""

import json

from core.risk.check import check_dependency
from core.schema.models import OSSEvent


def _load(name):
    return OSSEvent(**json.load(open(f"data/fixtures/{name}/event.json", encoding="utf-8")))


def test_golden_bitnami_distribution():
    """Distribution/support change no EOL record could express."""
    from core.evidence.policy import gate

    event = _load("bitnami")
    assert event.event_type.value == "DISTRIBUTION_CHANGE"
    assert gate(event) == []
    hit = check_dependency({"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}, [event])
    miss = check_dependency({"kind": "image", "ref": "docker.io/redis:7.2"}, [event])
    assert (hit.affected, hit.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (miss.affected, miss.relationship) == (False, "NOT_AFFECTED")
    assert event.confidence.value == "CONFIRMED"


def test_golden_itext_license():
    """Closed-source use without a commercial license: ACTION warning."""
    event = _load("itext-license")
    assert event.event_type.value == "LICENSE_CHANGE"
    assert event.confidence.value == "CONFIRMED"
    dep = {"kind": "package", "package": "itext-core", "ecosystem": "Maven", "version": "8.0.2"}
    result = check_dependency(dep, [event])
    assert result.affected is True
    assert result.relationship == "AFFECTS_PACKAGE"
    assert "commercial" in result.reason.lower() or "scope" in result.reason.lower()


def test_golden_minio_archived():
    """Archived upstream repo surfaces as a lifecycle ACTION finding."""
    from analyzers.change_analyst import analyze_github_meta
    from core.pulse import compute_pulse

    findings = analyze_github_meta(
        [{"collector": "github", "kind": "repo_meta", "repo": "minio/minio", "archived": True}]
    )
    assert findings[0]["event_type"] == "PROJECT_ARCHIVED"
    pulse = compute_pulse("minio", findings=findings)
    assert pulse["facets"]["activity"]["status"] == "action"


def test_golden_django_eol_versions():
    """Same project, different pins: version truth decides."""
    event = _load("django-eol")
    for version, relationship, affected in (
        ("4.2", "AFFECTS_VERSION", True),
        ("5.0", "NOT_AFFECTED", False),
        ("5.2", "NOT_AFFECTED", False),
        (None, "RELATED", False),
    ):
        dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": version}
        result = check_dependency(dep, [event])
        assert result.relationship == relationship, version
        assert result.affected is affected, version


def test_golden_five_questions_answered():
    """Every golden event exposes what/when/which/confidence/action."""
    from analyzers.report_analyst import render_event_md
    from core.evidence.policy import gate

    for name in ("bitnami", "itext-license", "django-eol"):
        event = _load(name)
        assert gate(event) == []
        assert event.title and event.summary  # what changed
        assert any(e.announcement_date or e.effective_date for e in event.evidences)  # when
        assert event.affected_versions or event.affected_artifacts  # which
        assert event.confidence.value in ("CONFIRMED", "CORROBORATED")  # how sure
        md = render_event_md(event)
        assert "Recommendation" in md and "Evidence" in md  # what to do
