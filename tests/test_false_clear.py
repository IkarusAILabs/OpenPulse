"""False-clear regressions (TR-2026-01 conformance audit, D1-D6, D8).

A NOT_AFFECTED verdict is a clearance: it is admissible only when the
event scope is exhaustive and every scope element is decisively
excluded. Each test below pins one path that used to clear a
dependency that was in scope (or headline a clearance over an
unresolved cause).
"""

from datetime import datetime, timezone

from analyzers.security_analyst import correlate
from core.risk.check import check_dependency
from core.schema.models import Artifact, Evidence, OSSEvent, Scope, Source
from core.versions import osv_applicable

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64


def _event(event_id: str, **kwargs) -> OSSEvent:
    evidence = Evidence(
        source=Source(
            name="acme/announcement",
            url="https://example.org/acme",
            authority="official",
            fetched_at=datetime(2026, 10, 28, tzinfo=timezone.utc),
        ),
        excerpt="acme changed",
    )
    return OSSEvent(
        id=event_id,
        project_slug="acme",
        event_type="DISTRIBUTION_CHANGE",
        title=event_id,
        summary=event_id,
        confidence="CONFIRMED",
        impact="ACTION",
        evidences=[evidence],
        **kwargs,
    )


def _image(ref: str) -> dict:
    return {"kind": "image", "ref": ref}


# D1 -- every named digest is evaluated, not just the first repo match


def test_d1_second_affected_artifact_digest_is_affected():
    event = _event(
        "d1-artifacts",
        affected_artifacts=[
            Artifact(kind="docker-image", ref=f"docker.io/acme/app@{D1}"),
            Artifact(kind="docker-image", ref=f"docker.io/acme/app@{D2}"),
        ],
    )
    verdict = check_dependency(_image(f"docker.io/acme/app@{D2}"), [event])
    assert (verdict.relationship, verdict.affected) == ("AFFECTS_ARTIFACT", True)


def test_d1_second_scope_digest_is_affected():
    event = _event(
        "d1-scope",
        scope=Scope(
            kind="artifact",
            artifacts=[f"docker.io/acme/app@{D1}", f"docker.io/acme/app@{D2}"],
        ),
    )
    verdict = check_dependency(_image(f"docker.io/acme/app@{D2}"), [event])
    assert (verdict.relationship, verdict.affected) == ("AFFECTS_ARTIFACT", True)


def test_d1_digest_outside_every_named_digest_is_undetermined():
    # Interim measure: OCI object levels are not recorded, so a different
    # digest of the same repository may be a child manifest of a named index.
    event = _event(
        "d1-clear",
        scope=Scope(
            kind="artifact",
            artifacts=[f"docker.io/acme/app@{D1}", f"docker.io/acme/app@{D2}"],
            exhaustive=True,
        ),
    )
    verdict = check_dependency(_image(f"docker.io/acme/app@{D3}"), [event])
    assert verdict.relationship == "RELATED"


def test_d1_undetermined_element_blocks_the_clear():
    # D3 differs from the pinned digest, but the tag element may point
    # at the pinned bytes: no decisive exclusion, so no clearance.
    event = _event(
        "d1-mixed",
        scope=Scope(
            kind="artifact",
            artifacts=[f"docker.io/acme/app@{D3}", "docker.io/acme/app:1.0"],
        ),
    )
    verdict = check_dependency(_image(f"docker.io/acme/app@{D1}"), [event])
    assert verdict.relationship == "RELATED"


# D2 -- OSV ranges are unions of intervals; unsupported semantics are undetermined


def _range(events: list[dict], kind: str = "ECOSYSTEM") -> dict:
    return {"ranges": [{"type": kind, "events": events}]}


DISJOINT = [{"introduced": "1.0"}, {"fixed": "1.2"}, {"introduced": "2.0"}, {"fixed": "2.3"}]


def test_d2_first_interval_of_a_disjoint_range_is_affected():
    assert osv_applicable("1.1", _range(DISJOINT)) is True
    assert osv_applicable("2.1", _range(DISJOINT)) is True


def test_d2_gap_and_tail_of_a_disjoint_range_are_outside():
    assert osv_applicable("1.5", _range(DISJOINT)) is False
    assert osv_applicable("2.3", _range(DISJOINT)) is False
    assert osv_applicable("0.9", _range(DISJOINT)) is False


def test_d2_events_out_of_order_are_sorted():
    shuffled = [DISJOINT[2], DISJOINT[1], DISJOINT[3], DISJOINT[0]]
    assert osv_applicable("1.1", _range(shuffled)) is True


def test_d2_last_affected_is_inclusive():
    events = [{"introduced": "0"}, {"last_affected": "3.4"}]
    assert osv_applicable("3.4", _range(events)) is True
    assert osv_applicable("3.4.1", _range(events)) is False


def test_d2_git_ranges_are_undetermined():
    events = [{"introduced": "1a2b3c"}, {"fixed": "4d5e6f"}]
    assert osv_applicable("1.0", _range(events, kind="GIT")) is None


def test_d2_unknown_range_type_is_undetermined():
    assert osv_applicable("1.1", _range(DISJOINT, kind="NUGET_EXOTIC")) is None


def test_d2_limit_never_clears_a_version_at_or_past_it():
    events = [{"introduced": "1.0"}, {"limit": "2.0"}]
    assert osv_applicable("1.5", _range(events)) is True
    assert osv_applicable("2.5", _range(events)) is None


def _osv_bundle(affected: list[dict], **extra) -> dict:
    return {
        "osv": [
            {
                "collector": "osv",
                "package": "acme",
                "ecosystem": "PyPI",
                "id": "GHSA-acme-0001",
                "cve_id": "CVE-2026-9001",
                "severity": [{"score": 8.0}],
                "affected": affected,
                **extra,
            }
        ]
    }


def _acme_context(version: str) -> dict:
    return {"slug": "acme", "package": "acme", "ecosystem": "PyPI", "version": version}


def test_d2_undetermined_affected_entry_blocks_the_clear():
    # One affected entry clears 1.5, a second one cannot be evaluated
    # (GIT range): the advisory is not established as NOT_AFFECTED.
    bundle = _osv_bundle(
        [
            {"package": "acme", "ecosystem": "PyPI", **_range(DISJOINT)},
            {"package": "acme", "ecosystem": "PyPI", **_range([{"introduced": "abc"}], "GIT")},
        ]
    )
    findings = correlate(bundle, _acme_context("1.5"))
    assert findings
    assert all(f["relationship"] != "NOT_AFFECTED" for f in findings)


def test_d2_withdrawn_advisory_never_asserts_impact():
    bundle = _osv_bundle(
        [{"package": "acme", "ecosystem": "PyPI", **_range(DISJOINT)}],
        withdrawn="2026-10-01T00:00:00Z",
    )
    findings = correlate(bundle, _acme_context("1.1"))
    assert all(f["relationship"] not in ("AFFECTS_VERSION", "AFFECTS_PACKAGE") for f in findings)


# D3 -- a negative for one event never headlines over an unresolved one


def test_d3_unresolved_event_beats_a_clear_from_another_event():
    cleared = _event("d3-cleared", scope=Scope(kind="version", versions=["9"], exhaustive=True))
    unresolved = _event("d3-project-wide")
    verdict = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "8.1"},
        [cleared, unresolved],
    )
    assert verdict.relationship != "NOT_AFFECTED"
    assert verdict.affected is False
    assert {c["event_id"]: c["relationship"] for c in verdict.verdicts} == {
        "d3-cleared": "NOT_AFFECTED",
        "d3-project-wide": "RELATED",
    }


def test_d3_unrelated_event_does_not_block_a_clear():
    cleared = _event(
        "d3-image-cleared", scope=Scope(kind="version", versions=["9"], exhaustive=True)
    )
    unrelated = OSSEvent(**{**_event("d3-other").model_dump(), "project_slug": "zzz-other"})
    verdict = check_dependency(_image("docker.io/acme/app:8.1"), [cleared, unrelated])
    relationships = {c["event_id"]: c["relationship"] for c in verdict.verdicts}
    assert relationships["d3-other"] == "UNKNOWN"
    assert verdict.relationship == relationships["d3-image-cleared"]


def test_package_scoped_event_has_no_association_with_other_projects_images():
    # Found while fixing D3: a package-scoped event used to mark EVERY
    # image RELATED, which now (correctly) blocks clearances -- so the
    # spurious association itself had to go.
    licence = _event("pkg-scope", scope=Scope(kind="package", packages=["acme-core"]))
    verdict = check_dependency(_image("docker.io/redis:7.2"), [licence])
    assert verdict.relationship == "UNKNOWN"


def test_d3_all_causes_negative_still_clears():
    first = _event("d3-a", scope=Scope(kind="version", versions=["9"], exhaustive=True))
    second = _event("d3-b", scope=Scope(kind="version", versions=["10"], exhaustive=True))
    verdict = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "8.1"},
        [first, second],
    )
    assert verdict.relationship == "NOT_AFFECTED"


# D4 -- a scope declared non-exhaustive never yields NOT_AFFECTED


def test_d4_scope_defaults_to_partial():
    # Interim measure: unspecified completeness is partial, never a clearance.
    assert Scope().exhaustive is False


def test_d4_non_exhaustive_version_scope_is_related():
    event = _event("d4-version", scope=Scope(kind="version", versions=["9"], exhaustive=False))
    package = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "8.1"}, [event]
    )
    image = check_dependency(_image("docker.io/acme/app:8.1"), [event])
    assert package.relationship == "RELATED"
    assert image.relationship != "NOT_AFFECTED"


def test_d4_non_exhaustive_artifact_scope_is_related():
    event = _event(
        "d4-artifact",
        scope=Scope(kind="artifact", artifacts=["docker.io/acme/app:1.0"], exhaustive=False),
    )
    verdict = check_dependency(_image("docker.io/acme/other:1.0"), [event])
    assert verdict.relationship == "RELATED"


def test_d4_non_exhaustive_scope_still_finds_members():
    event = _event("d4-member", scope=Scope(kind="version", versions=["9"], exhaustive=False))
    verdict = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "9.2"}, [event]
    )
    assert (verdict.relationship, verdict.affected) == ("AFFECTS_VERSION", True)


# D5 -- identity exclusion needs a VERIFIED resolution


def test_d5_namespace_rule_identity_cannot_exclude():
    # docker.io/bitnami/<unlisted> resolves through the generic Bitnami
    # namespace heuristic (REVIEW_REQUIRED): not proof of a different project.
    event = _event("d5-version", scope=Scope(kind="version", versions=["9"]))
    verdict = check_dependency(_image("docker.io/bitnami/acme-unlisted-image:8.1"), [event])
    assert verdict.relationship == "RELATED"


def test_d5_verified_identity_still_excludes():
    event = _event("d5-verified", scope=Scope(kind="version", versions=["6.2"], exhaustive=True))
    verdict = check_dependency(_image("docker.io/redis:6.2"), [event])
    assert verdict.relationship == "NOT_AFFECTED"


# D6 -- version epochs are not comparable, never read as extra dotted segments


def test_d6_debian_epoch_bound_never_clears():
    # 2.5 sorts below 1:1.0 (epoch 1 beats every epoch-0 version), so it
    # is inside the range; reading "1:1.0" as "1.1.0" used to clear it.
    events = [{"introduced": "0"}, {"fixed": "1:1.0"}]
    assert osv_applicable("2.5", _range(events)) is None


def test_d6_epoch_versions_are_not_comparable():
    from core.versions import compare, detect_scheme, in_release_line

    for epoch_version in ("1:2.3", "2!1.0"):
        assert detect_scheme(epoch_version) == "unknown"
        assert compare(epoch_version, "1.5") is None
        assert in_release_line(epoch_version, "2") is None


def test_d6_epoch_dependency_is_related_not_cleared():
    event = _event("d6-version", scope=Scope(kind="version", versions=["9"]))
    verdict = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "1:8.1"}, [event]
    )
    assert verdict.relationship == "RELATED"


# D8 -- a numeric suffix is never folded into the core; prerelease numbers order


def test_d8_numeric_prerelease_never_clears():
    # SemVer 1.0.0-1 and 1.0.0-0 are prereleases below 1.0.0, so inside
    # the range; reading them as 1.0.0.1 / 1.0.0.0 used to clear them.
    events = [{"introduced": "0"}, {"fixed": "1.0.0"}]
    for version in ("1.0.0-1", "1.0.0-0"):
        assert osv_applicable(version, _range(events)) is None


def test_d8_numeric_and_build_suffixes_are_not_comparable():
    from core.versions import compare, detect_scheme

    # SemVer prerelease, Debian revision, build metadata: the orderings
    # disagree, so none of them is generic.
    for version in ("1.0.0-1", "2.4.1-1", "1.0.0+5", "1.0.0-alpha.beta"):
        assert detect_scheme(version) == "unknown"
        assert compare(version, "1.0.0") is None


def test_d8_prerelease_number_orders_within_a_marker():
    from core.versions import compare

    # rc1 < rc2: ignoring the number made them equal, so a fix in rc2
    # cleared rc1.
    events = [{"introduced": "0"}, {"fixed": "1.0.0-rc2"}]
    assert osv_applicable("1.0.0-rc1", _range(events)) is True
    assert osv_applicable("1.0.0-rc2", _range(events)) is False
    assert compare("1.0.0-rc.1", "1.0.0-rc.2") == -1
    assert compare("1.0b2", "1.0b10") == -1


def test_d8_known_prerelease_forms_stay_comparable():
    from core.versions import compare

    assert compare("2.0.0-rc1", "2.0.0") == -1
    assert compare("1.0.dev1", "1.0a1") == -1
    assert compare("v1.2", "1.2.0") == 0


# Interim conservative measures (TR-2026-01 rev. 5, Table 8)


def test_interim_oci_digest_of_another_repository_still_clears():
    # Repository triples differ: decisive regardless of OCI level.
    event = _event(
        "oci-other-repo",
        scope=Scope(kind="artifact", artifacts=[f"docker.io/acme/app@{D1}"], exhaustive=True),
    )
    verdict = check_dependency(_image(f"docker.io/other/app@{D2}"), [event])
    assert verdict.relationship == "NOT_AFFECTED"


def test_interim_oci_named_artifact_digest_inequality_is_undetermined():
    event = _event(
        "oci-named",
        affected_artifacts=[Artifact(kind="docker-image", ref=f"docker.io/acme/app@{D1}")],
        scope=Scope(kind="artifact", artifacts=[f"docker.io/acme/app@{D1}"], exhaustive=True),
    )
    verdict = check_dependency(_image(f"docker.io/acme/app@{D2}"), [event])
    assert verdict.relationship == "RELATED"


def test_interim_unspecified_completeness_never_clears():
    event = _event("partial-default", scope=Scope(kind="version", versions=["9"]))
    package = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "8.1"}, [event]
    )
    assert package.relationship == "RELATED"


def test_interim_declared_complete_scope_still_clears():
    event = _event("declared", scope=Scope(kind="version", versions=["9"], exhaustive=True))
    package = check_dependency(
        {"kind": "package", "package": "acme", "ecosystem": "", "version": "8.1"}, [event]
    )
    assert package.relationship == "NOT_AFFECTED"


def test_interim_unlisted_bitnami_image_is_not_cleared_by_example_scope():
    # The curated Bitnami event used to list five example images of a
    # catalogue-wide change, read as complete: an unlisted bitnami image was
    # cleared. Its scope is now the namespaces the announcement covers.
    import json

    event = OSSEvent(**json.load(open("data/fixtures/bitnami/event.json", encoding="utf-8")))
    unlisted = check_dependency(_image("docker.io/bitnami/nginx:1.25"), [event])
    upstream = check_dependency(_image("docker.io/redis:7.2"), [event])
    assert (unlisted.relationship, unlisted.affected) == ("AFFECTS_ARTIFACT", True)
    assert upstream.relationship == "NOT_AFFECTED"


def test_namespace_scope_element_covers_every_repository_under_it():
    event = _event(
        "ns-scope",
        scope=Scope(kind="artifact", artifacts=["docker.io/acme/*"], exhaustive=True),
    )
    inside = check_dependency(_image(f"docker.io/acme/anything@{D1}"), [event])
    outside = check_dependency(_image("docker.io/other/anything:1.0"), [event])
    assert inside.relationship == "AFFECTS_ARTIFACT"
    assert outside.relationship == "NOT_AFFECTED"


def test_interim_definitional_lifecycle_scope_is_declared_complete():
    from analyzers.lifecycle_events import finding_to_event

    finding = {
        "analyst": "change",
        "event_type": "EOL",
        "title": "acme 9 is end-of-life",
        "summary": "acme 9 is end-of-life",
        "impact": "ACTION",
        "effective_at": "2026-01-01",
        "observed_at": "2026-10-29",
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "version", "versions": ["9"], "exhaustive": True},
        "affected_versions": ["9"],
        "affected_artifacts": [],
        "supporting": [],
    }
    event = finding_to_event(finding, "acme")
    assert event.scope is not None and event.scope.exhaustive is True


def test_interim_unmapped_reference_named_like_the_project_is_undetermined():
    # github.com/etcd-io/etcd resolves only to itself, yet names the project:
    # its identity is unresolved, not "another project".
    event = _event("named-like", scope=Scope(kind="version", versions=["9"], exhaustive=True))
    unresolved = check_dependency(_image("ghcr.io/someorg/acme:8.1"), [event])
    assert unresolved.relationship == "RELATED"


def test_interim_unmapped_reference_named_like_the_project_blocks_project_wide_drop():
    project_wide = _event("project-wide")
    verdict = check_dependency(_image("github.com/someorg/acme"), [project_wide])
    assert verdict.relationship == "RELATED"


def test_interim_unmapped_reference_with_unrelated_name_stays_unassociated():
    project_wide = _event("project-wide-2")
    verdict = check_dependency(_image("ghcr.io/someorg/billing-service:1.0"), [project_wide])
    assert verdict.relationship == "UNKNOWN"
