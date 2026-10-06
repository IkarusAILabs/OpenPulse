"""Golden scenarios — the canonical end-to-end proofs.

Each scenario answers the five product questions (what changed, is it
evidenced, what is affected, when does it matter, does it affect my
org) with a non-lifecycle story where one exists. These are the tests
a lifecycle database alone could never pass.
"""

import json
from datetime import date

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


def test_golden_redis_eol_pins_and_namespaces():
    """Redis 6.2 EOL: version truth across two pins, plus the
    docker.io/redis vs docker.io/bitnami/redis attribution split,
    end to end from the offline raw-bundle fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed — cycle 6.2 reached EOL, scoped to that cycle only;
    Q2 evidence — the bridged event passes the claim gate, dated
       effective 2024-01-01, single secondary source so EMERGING;
    Q3 identity — upstream and bitnami images resolve to different
       projects (redis vs bitnami-redis-stack);
    Q4 what dependency — docker.io/redis:6.2 is the affected pin;
    Q5 which versions/artifacts — 6.2 pin affected, 8.0 pin not, and
       the bitnami image carrying the same tag is not;
    Q6 when it matters — effective 2024-01-01, already in force;
    Q7 investigate — the verdict reason names the scope version;
    Q8 why OpenPulse — an EOL database row cannot tell the two images
       apart on the same tag; identity resolution + version scope can.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/redis/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 9, 26)

    # Q1 -- what changed: one lifecycle finding, scoped to cycle 6.2.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert len(findings) == 1
    assert findings[0]["scope"] == {"kind": "version", "versions": ["6.2"]}
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"

    event = finding_to_event(findings[0], "redis", today=today)

    # Q2 -- evidence: claim gate accepts it; dated, single-source EMERGING.
    assert gate(event) == []
    assert any(e.effective_date == date(2024, 1, 1) for e in event.evidences)

    # Q3 -- identity: two redis images, two different projects.
    assert event.project_slug == "redis"
    assert resolve_project("docker.io/redis:6.2") == "redis"
    assert resolve_project("docker.io/bitnami/redis:6.2") == "bitnami-redis-stack"

    # Q4 + Q5 -- dependency verdicts: version truth and attribution.
    upstream_old = check_dependency({"kind": "image", "ref": "docker.io/redis:6.2"}, [event])
    upstream_new = check_dependency({"kind": "image", "ref": "docker.io/redis:8.0"}, [event])
    bitnami_old = check_dependency({"kind": "image", "ref": "docker.io/bitnami/redis:6.2"}, [event])
    assert (upstream_old.affected, upstream_old.relationship) == (True, "AFFECTS_VERSION")
    assert upstream_old.confidence == "EMERGING"
    assert (upstream_new.affected, upstream_new.relationship) == (False, "NOT_AFFECTED")
    assert (bitnami_old.affected, bitnami_old.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: effective in the past, in force now.
    assert findings[0]["effective_at"] == "2024-01-01"

    # Q7 -- investigate: the reason names the scope version.
    assert "6.2" in upstream_old.reason

    # Q8 -- why OpenPulse: same tag, different project, different verdict
    # -- a plain EOL record cannot make this call.
    assert upstream_old.reason != bitnami_old.reason
    assert "bitnami-redis-stack" in bitnami_old.reason


def test_golden_postgresql_eol_pins_and_namespaces():
    """PostgreSQL 13 EOL: version truth across two pins, plus the
    alias breadth (postgres/postgresql/library spellings) and the
    docker.io/bitnami/postgresql tag-collision exclusion, end to end
    from the offline raw-bundle fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- cycle 13 reached EOL, scoped to that cycle only;
    Q2 evidence -- the bridged event passes the claim gate, dated
       effective 2025-11-13, single secondary source so EMERGING;
    Q3 identity -- postgres, postgresql, docker.io/postgres and
       docker.io/library/postgres all resolve to postgresql, while
       docker.io/bitnami/postgresql is its own project;
    Q4 what dependency -- docker.io/postgres:13 is the affected pin;
    Q5 which versions/artifacts -- 13 pin affected, 17 pin not, and
       the bitnami image carrying the same tag is not;
    Q6 when it matters -- effective 2025-11-13, already in force;
    Q7 investigate -- the verdict reason names the scope version;
    Q8 why OpenPulse -- an EOL database row cannot tell the two images
       apart on the same tag; identity resolution + version scope can.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/postgresql/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 9, 26)

    # Q1 -- what changed: one lifecycle finding, scoped to cycle 13.
    # The 17 cycle (EOL 2029) is far out, so it yields no finding.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert len(findings) == 1
    assert findings[0]["scope"] == {"kind": "version", "versions": ["13"]}
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"

    event = finding_to_event(findings[0], "postgresql", today=today)

    # Q2 -- evidence: claim gate accepts it; dated, single-source EMERGING.
    assert gate(event) == []
    assert any(e.effective_date == date(2025, 11, 13) for e in event.evidences)

    # Q3 -- identity: four upstream spellings, one project; bitnami is
    # a different one.
    assert event.project_slug == "postgresql"
    for spelling in (
        "postgres",
        "postgresql",
        "docker.io/postgres:13",
        "docker.io/library/postgres:13",
    ):
        assert resolve_project(spelling) == "postgresql", spelling
    assert resolve_project("docker.io/bitnami/postgresql:13") == "bitnami-postgresql"

    # Q4 + Q5 -- dependency verdicts: version truth and attribution.
    upstream_old = check_dependency({"kind": "image", "ref": "docker.io/postgres:13"}, [event])
    upstream_new = check_dependency({"kind": "image", "ref": "docker.io/postgres:17"}, [event])
    bitnami_old = check_dependency(
        {"kind": "image", "ref": "docker.io/bitnami/postgresql:13"}, [event]
    )
    assert (upstream_old.affected, upstream_old.relationship) == (True, "AFFECTS_VERSION")
    assert upstream_old.confidence == "EMERGING"
    assert (upstream_new.affected, upstream_new.relationship) == (False, "NOT_AFFECTED")
    assert (bitnami_old.affected, bitnami_old.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: effective in the past, in force now.
    assert findings[0]["effective_at"] == "2025-11-13"

    # Q7 -- investigate: the reason names the scope version.
    assert "13" in upstream_old.reason

    # Q8 -- why OpenPulse: same tag, different project, different verdict
    # -- a plain EOL record cannot make this call.
    assert upstream_old.reason != bitnami_old.reason
    assert "bitnami-postgresql" in bitnami_old.reason


def test_golden_kubernetes_eol_pins_and_skew():
    """Kubernetes 1.31 EOL: version truth across two pins, plus the
    skew-policy timing question, end to end from the offline
    raw-bundle fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- cycle 1.31 reached EOL, scoped to that cycle
       only; the 1.37 cycle (EOL 2027-10-28) stays silent;
    Q2 evidence -- the bridged event passes the claim gate, dated
       effective 2025-11-11, single secondary source so EMERGING;
    Q3 identity -- kubernetes, k8s and Kubernetes all resolve to the
       kubernetes project; docker.io/bitnami/kubernetes is its own
       bitnami-kubernetes project;
    Q4 what dependency -- kubernetes==1.31 is the affected pin;
    Q5 which versions/artifacts -- 1.31 pin affected, 1.37 pin not,
       and the bitnami-packaged control-plane image on the same tag
       is not;
    Q6 when it matters -- effective 2025-11-11, already in force;
    Q7 investigate -- the verdict reason names the scope version;
    Q8 why OpenPulse -- Kubernetes supports roughly four minors in
       flight and clusters routinely run N-2 or older, so a bare
       EOL row cannot tell a pinned 1.31 apart from the supported
       pin; version scope plus identity resolution can.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/kubernetes/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 9, 26)

    # Q1 -- what changed: one EOL finding, scoped to cycle 1.31.
    # The 1.37 cycle (EOL 2027) is far out, so it yields no finding.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert len(findings) == 1
    assert findings[0]["scope"] == {"kind": "version", "versions": ["1.31"]}
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"

    event = finding_to_event(findings[0], "kubernetes", today=today)

    # Q2 -- evidence: claim gate accepts it; dated, single-source EMERGING.
    assert gate(event) == []
    assert any(e.effective_date == date(2025, 11, 11) for e in event.evidences)

    # Q3 -- identity: alias and case spellings resolve; bitnami is a
    # different project.
    assert event.project_slug == "kubernetes"
    for spelling in ("kubernetes", "k8s", "Kubernetes"):
        assert resolve_project(spelling) == "kubernetes", spelling
    assert resolve_project("docker.io/bitnami/kubernetes") == "bitnami-kubernetes"

    # Q4 + Q5 -- dependency verdicts: version truth and attribution.
    pinned_old = check_dependency(
        {"kind": "package", "package": "kubernetes", "ecosystem": "", "version": "1.31"}, [event]
    )
    pinned_new = check_dependency(
        {"kind": "package", "package": "kubernetes", "ecosystem": "", "version": "1.37"}, [event]
    )
    bitnami_old = check_dependency(
        {"kind": "image", "ref": "docker.io/bitnami/kubernetes:1.31"}, [event]
    )
    assert (pinned_old.affected, pinned_old.relationship) == (True, "AFFECTS_VERSION")
    assert pinned_old.confidence == "EMERGING"
    assert (pinned_new.affected, pinned_new.relationship) == (False, "NOT_AFFECTED")
    assert (bitnami_old.affected, bitnami_old.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: effective in the past, in force now.
    assert findings[0]["effective_at"] == "2025-11-11"

    # Q7 -- investigate: the reason names the scope version.
    assert "1.31" in pinned_old.reason

    # Q8 -- why OpenPulse: the bitnami image on the same tag is
    # excluded by project identity, and the supported pin by version
    # scope -- two calls an EOL database row cannot make.
    assert pinned_old.reason != bitnami_old.reason
    assert "bitnami-kubernetes" in bitnami_old.reason


def test_golden_capa_ownership_move():
    """Mandiant acquired the FireEye products business in 2021 and
    moved capa to mandiant/capa: a recorded fireeye/capa reference
    now names a redirect, not a first-party source. End to end from
    the offline raw-bundle fixture (repo_meta probed live 2026-10-06).

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- the repository moved from fireeye/capa to
       mandiant/capa; the queried path no longer names the owner;
    Q2 evidence -- the bridged event passes the claim gate; single
       primary source (the repository itself) so EMERGING;
    Q3 identity -- github.com/fireeye/capa and
       github.com/mandiant/capa are different repository identities;
       the moved-from path is the one whose recorded references went
       stale;
    Q4 what dependency -- a go.mod/remote-style github.com/fireeye/capa
       source reference is the affected dependency;
    Q5 which versions/artifacts -- the old path is affected (it names
       a redirect), the new path is not (UNKNOWN, not a match), and a
       bare package pin stays contextual (AFFECTS_PROJECT);
    Q6 when it matters -- the move already happened; the stale
       reference is in force now, nothing is upcoming;
    Q7 investigate -- the finding names both paths, states the drift,
       and the verdict reason names the affected artifact;
    Q8 why OpenPulse -- an EOL/CVE database has no slot for "your
       recorded source path changed owner"; ownership drift is a
       repository-identity fact only the meta-vs-recorded-path
       comparison can catch.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.evidence.policy import gate
    from core.risk.impact import evaluate_impact

    raw = json.load(open("data/fixtures/capa-move/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 10, 6)

    # Q1 -- what changed: one ownership finding, project-scoped,
    # naming the moved repository as the affected artifact.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "OWNERSHIP_CHANGE"]
    assert len(findings) == 1
    assert findings[0]["scope"] == {"kind": "project", "versions": []}
    assert findings[0]["detection_method"] == "repository_observation"
    assert findings[0]["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/fireeye/capa"}
    ]

    event = finding_to_event(findings[0], "capa", today=today)

    # Q2 -- evidence: claim gate accepts it; single primary source so
    # EMERGING, never CONFIRMED off one observation.
    assert gate(event) == []
    assert event.confidence.value == "EMERGING"
    assert [e.source.authority for e in event.evidences] == ["secondary"]

    # Q3 -- identity: moved-from and moved-to paths are distinct
    # repository identities; only the old path is the stale one.
    assert event.project_slug == "capa"
    old_ref = check_dependency({"kind": "image", "ref": "github.com/fireeye/capa"}, [event])
    new_ref = check_dependency({"kind": "image", "ref": "github.com/mandiant/capa"}, [event])
    assert (old_ref.affected, old_ref.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (new_ref.affected, new_ref.relationship) == (False, "UNKNOWN")

    # Q4 + Q5 -- dependency verdicts: the old path is the affected
    # dependency; the new path and a bare package pin are not impact.
    package_pin = check_dependency(
        {"kind": "package", "package": "capa", "ecosystem": "", "version": None}, [event]
    )
    assert (package_pin.affected, package_pin.relationship) == (False, "AFFECTS_PROJECT")
    assert old_ref.confidence == "EMERGING"

    # Q6 -- when: the move already happened; nothing is upcoming.
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"

    # Q7 -- investigate: the finding and verdict name what moved.
    assert "fireeye/capa" in findings[0]["title"]
    assert "mandiant/capa" in findings[0]["title"]
    assert "github.com/fireeye/capa" in old_ref.reason
    assert "verify" in findings[0]["summary"]

    # Q8 -- why OpenPulse: ownership drift is a repository-identity
    # fact, not a lifecycle row; review-framed, never auto-action.
    assessed = evaluate_impact(findings[0], today=today)
    assert assessed["assessment"] == "PROJECT_CHANGE"
    assert assessed["eligibility"] == "REVIEW"
    assert old_ref.reason != new_ref.reason


def test_golden_etcd_namespace_move():
    """etcd moved from coreos/etcd to etcd-io/etcd when CoreOS wound
    down (transfer to the etcd-io org, 2018): a recorded
    github.com/coreos/etcd require or remote now names a redirect.
    End to end from the offline raw-bundle fixture (repo_meta probed
    live 2026-10-06). Proves the same detector on a second real move:
    the rule is not capa-shaped.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- the repository moved from coreos/etcd to
       etcd-io/etcd;
    Q2 evidence -- the bridged event passes the claim gate; single
       primary source so EMERGING;
    Q3 identity -- github.com/coreos/etcd and
       github.com/etcd-io/etcd are distinct repository identities;
       the recorded old path is the stale one;
    Q4 what dependency -- a github.com/coreos/etcd source reference
       (go.mod require, git remote) is the affected dependency;
    Q5 which versions/artifacts -- old path affected, new path
       UNKNOWN, bare package pin contextual;
    Q6 when it matters -- the move already happened; stale
       references are in force now;
    Q7 investigate -- the finding names both paths and the verdict
       reason names the affected artifact;
    Q8 why OpenPulse -- namespace moves are upstream-identity facts
       no dependency database records; the meta-vs-recorded-path
       comparison is the only signal.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.evidence.policy import gate
    from core.risk.impact import evaluate_impact

    raw = json.load(open("data/fixtures/etcd-move/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 10, 6)

    # Q1 -- what changed: one ownership finding, project-scoped.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "OWNERSHIP_CHANGE"]
    assert len(findings) == 1
    assert findings[0]["scope"] == {"kind": "project", "versions": []}
    assert findings[0]["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/coreos/etcd"}
    ]

    event = finding_to_event(findings[0], "etcd", today=today)

    # Q2 -- evidence: claim gate accepts it, single-source EMERGING.
    assert gate(event) == []
    assert event.confidence.value == "EMERGING"

    # Q3 + Q4 + Q5 -- identity and dependency verdicts.
    old_ref = check_dependency({"kind": "image", "ref": "github.com/coreos/etcd"}, [event])
    new_ref = check_dependency({"kind": "image", "ref": "github.com/etcd-io/etcd"}, [event])
    package_pin = check_dependency(
        {"kind": "package", "package": "etcd", "ecosystem": "", "version": None}, [event]
    )
    assert (old_ref.affected, old_ref.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (new_ref.affected, new_ref.relationship) == (False, "UNKNOWN")
    assert (package_pin.affected, package_pin.relationship) == (False, "AFFECTS_PROJECT")

    # Q6 -- when: the move already happened.
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"

    # Q7 -- investigate: the finding and verdict name what moved.
    assert "coreos/etcd" in findings[0]["title"]
    assert "etcd-io/etcd" in findings[0]["title"]
    assert "github.com/coreos/etcd" in old_ref.reason

    # Q8 -- why OpenPulse: namespace moves are upstream-identity facts.
    assessed = evaluate_impact(findings[0], today=today)
    assert assessed["assessment"] == "PROJECT_CHANGE"
    assert assessed["eligibility"] == "REVIEW"
    assert old_ref.reason != new_ref.reason
