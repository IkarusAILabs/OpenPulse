"""Golden scenario matrix (§14): semantic categories with explicit contracts.

Every scenario defines input, expected relationship, expected
confidence, expected impact, and expected reason. These pin the
intelligence semantics — a lifecycle database with extra collectors
could not pass them.
"""

from datetime import date

TODAY = date(2026, 9, 26)


# --- Lifecycle --------------------------------------------------------


def _eol_entry(product="django", cycle="5.0", eol="2026-09-01"):
    return {
        "collector": "endoflife",
        "product": product,
        "cycle": cycle,
        "eol": eol,
        "link": f"https://endoflife.date/{product}",
    }


def test_matrix_eol_upcoming():
    from analyzers.change_analyst import analyze_endoflife
    from core.risk.impact import evaluate_impact

    out = analyze_endoflife([_eol_entry(eol="2026-12-01")], today=TODAY)
    assert out[0]["lifecycle_state"] == "UPCOMING"
    assert out[0]["scope"] == {"kind": "version", "versions": ["5.0"]}
    assessed = evaluate_impact(out[0], today=TODAY)
    assert assessed["assessment"] == "PROJECT_CHANGE"
    assert assessed["eligibility"] == "WATCH"


def test_matrix_eol_effective():
    from analyzers.change_analyst import analyze_endoflife
    from core.risk.impact import evaluate_impact

    out = analyze_endoflife([_eol_entry()], today=TODAY)
    assert out[0]["lifecycle_state"] == "EFFECTIVE"
    assert out[0]["effective_at"] == "2026-09-01"
    assert out[0]["observed_at"] == "2026-09-26"
    assessed = evaluate_impact(out[0], today=TODAY)
    assert assessed["assessment"] == "PROJECT_CHANGE"
    assert assessed["eligibility"] == "ACTION"


def test_matrix_eol_already_passed():
    from analyzers.change_analyst import analyze_endoflife
    from core.risk.impact import evaluate_impact

    out = analyze_endoflife([_eol_entry(eol="2024-01-15")], today=TODAY)
    assessed = evaluate_impact(out[0], today=TODAY)
    assert (assessed["assessment"], assessed["eligibility"]) == (
        "PROJECT_CHANGE", "ACTION")


def test_matrix_not_affected_version_has_reason():
    from analyzers.change_analyst import analyze_endoflife
    from analyzers.lifecycle_events import finding_to_event
    from core.risk.check import check_dependency

    finding = analyze_endoflife([_eol_entry()], today=TODAY)[0]
    event = finding_to_event(finding, "django", today=TODAY)
    result = check_dependency(
        {"kind": "package", "package": "django", "ecosystem": "PyPI",
         "version": "5.2"},
        [event],
    )
    assert result.relationship == "NOT_AFFECTED"
    assert result.affected is False
    assert "5.2" in result.reason and "5.0" in result.reason
    # Exclusion proven by a single secondary source: EMERGING, not the
    # old match-implied CORROBORATED (§5).
    assert result.confidence == "EMERGING"


def test_matrix_unknown_version_is_related_not_unknown_impact():
    from analyzers.change_analyst import analyze_endoflife
    from analyzers.lifecycle_events import finding_to_event
    from core.risk.check import check_dependency

    finding = analyze_endoflife([_eol_entry()], today=TODAY)[0]
    event = finding_to_event(finding, "django", today=TODAY)
    result = check_dependency(
        {"kind": "package", "package": "django", "ecosystem": "PyPI",
         "version": None},
        [event],
    )
    assert result.relationship == "RELATED"
    assert result.affected is False


# --- Registry ---------------------------------------------------------


def test_matrix_tag_disappeared():
    from analyzers.change_analyst import analyze_diffs
    from core.risk.impact import evaluate_impact

    out = analyze_diffs([{
        "type": "tag_disappeared", "namespace": "library", "repository": "redis",
        "tag": "7.2", "observed_at": "2026-09-20",
    }], today=TODAY)
    assert out[0]["impact"] == "REVIEW"
    assert out[0]["significance"] == "high"
    assert out[0]["scope"] == {
        "kind": "artifact", "artifacts": ["docker.io/library/redis:7.2"]}
    assessed = evaluate_impact(out[0], today=TODAY)
    assert assessed["eligibility"] == "REVIEW"


def test_matrix_digest_changed_is_low():
    from analyzers.change_analyst import analyze_diffs
    from core.risk.impact import evaluate_impact

    out = analyze_diffs([{
        "type": "tag_digest_changed", "namespace": "library",
        "repository": "redis", "tag": "7.2", "observed_at": "2026-09-20",
    }], today=TODAY)
    assert out[0]["significance"] == "low"
    assert evaluate_impact(out[0], today=TODAY)["eligibility"] == "WATCH"


def test_matrix_repository_removed_never_action():
    from analyzers.change_analyst import analyze_diffs
    from core.risk.impact import evaluate_impact

    out = analyze_diffs([{
        "type": "repo_missing", "namespace": "acme", "repository": "gone",
        "observed_at": "2026-09-20",
    }], today=TODAY)
    assert out[0]["impact"] == "REVIEW"
    assert out[0]["significance"] == "high"
    assert evaluate_impact(out[0], today=TODAY)["eligibility"] == "REVIEW"


def test_matrix_distribution_moved_generic():
    from analyzers.change_analyst import analyze_registries

    raw = [
        {"collector": "registries", "namespace": "acme",
         "repo": "widget", "latest_only": True},
        {"collector": "registries", "namespace": "acmelegacy",
         "repo": "widget", "has_versioned_tags": True},
    ]
    out = analyze_registries(raw, today=TODAY)
    assert len(out) == 1
    assert out[0]["event_type"] == "DISTRIBUTION_CHANGE"
    assert out[0]["significance"] == "high"
    assert "acme" in out[0]["title"] and "acmelegacy" in out[0]["title"]


# --- Security ---------------------------------------------------------


def test_matrix_cve_exact_version():
    from analyzers.security_analyst import correlate

    raw = {
        "osv": [{
            "collector": "osv", "id": "CVE-2026-0001",
            "package": "django", "ecosystem": "PyPI",
            "affected": [{"versions": ["5.0"]}],
            "severity": [{"score": 9.0}],
            "references": [],
        }],
        "kev": [], "nvd": [], "cve": [],
    }
    out = correlate(raw, {"slug": "django", "package": "django",
                          "ecosystem": "PyPI", "version": "5.0"})
    assert out[0]["relationship"] == "AFFECTS_VERSION"
    assert out[0]["match_method"] == "osv_package+version_range"
    assert "5.0" in str(out[0].get("affected_version"))


def test_matrix_cve_version_unknown_is_package_attribution():
    from analyzers.security_analyst import correlate

    raw = {
        "osv": [{
            "collector": "osv", "id": "CVE-2026-0002",
            "package": "django", "ecosystem": "PyPI",
            "severity": [{"score": 9.8}],
            "references": [],
        }],
        "kev": [], "nvd": [], "cve": [],
    }
    out = correlate(raw, {"slug": "django", "package": "django",
                          "ecosystem": "PyPI", "version": None})
    # Package attribution without a version claim: the package is
    # affected, the version dimension stays open.
    assert out[0]["relationship"] == "AFFECTS_PACKAGE"
    assert out[0]["match_method"] == "osv_package"


def test_matrix_unrelated_keyword_hit_not_affected():
    from analyzers.security_analyst import correlate

    raw = {
        "nvd": [{
            "collector": "nvd", "id": "CVE-2026-0003",
            "keyword": "redis", "severity": [{"score": 9.8}],
            "references": [],
        }],
        "osv": [], "kev": [], "cve": [],
    }
    out = correlate(raw, {"slug": "django", "package": "django",
                          "ecosystem": "PyPI", "version": "5.0"})
    assert out[0]["relationship"] in ("UNKNOWN", "RELATED")
    assert out[0]["impact"] in ("REVIEW", "WATCH", "INFORMATIONAL")


def test_matrix_kev_weak_match_never_confirms():
    from analyzers.security_analyst import correlate

    raw = {
        "osv": [{
            "collector": "osv", "id": "CVE-2026-0004",
            "package": "django", "ecosystem": "PyPI",
            "severity": [{"score": 7.0}],
            "references": [],
        }],
        "kev": [{"collector": "kev", "cve_id": "CVE-2026-0004",
                 "match": "weak"}],
        "nvd": [], "cve": [],
    }
    out = correlate(raw, {"slug": "django", "package": "django",
                          "ecosystem": "PyPI", "version": "5.0"})
    assert out[0]["in_kev"] is False


# --- Identity ---------------------------------------------------------


def test_matrix_official_library_image_identity():
    from core.risk.match import match_artifact, split_image_ref

    assert split_image_ref("redis:7.2")[0:2] == ("docker.io", "library")
    assert match_artifact("redis:7.2", "docker.io/library/redis:7.2") is True
    assert match_artifact("docker.io/bitnami/redis:7.2", "redis:7.2") is False


# --- Evidence ---------------------------------------------------------


def test_matrix_official_source_is_confirmed():
    from analyzers.evidence_analyst import assess_confidence

    assert assess_confidence([{
        "source": {"name": "vendor", "authority": "official"}}]) == "CONFIRMED"


def test_matrix_independent_secondaries_corroborate():
    from analyzers.evidence_analyst import assess_confidence

    assert assess_confidence([
        {"source": {"name": "a", "authority": "secondary"}},
        {"source": {"name": "b", "authority": "secondary"}},
    ]) == "CORROBORATED"


def test_matrix_no_evidence_is_unverified():
    from analyzers.evidence_analyst import assess_confidence

    assert assess_confidence([]) == "UNVERIFIED"
