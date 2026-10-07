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


def test_golden_kafka_eol_pins_and_namespaces():
    """Kafka 3.8 EOL: version truth across two pins, plus the
    packaged-image identity split, end to end from the offline
    raw-bundle fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- cycle 3.8 reached EOL, scoped to that cycle
       only; the 4.3 cycle (no announced date yet) stays silent;
    Q2 evidence -- the bridged event passes the claim gate, dated
       effective 2024-11-06, single secondary source so EMERGING;
    Q3 identity -- kafka and apache/kafka resolve to the kafka
       project; the bitnami-packaged image and the confluent
       distribution are their own projects;
    Q4 what dependency -- kafka==3.8 is the affected pin;
    Q5 which versions/artifacts -- 3.8 pin affected, 4.3 pin not,
       and the bitnami image carrying the same cycle tag is not;
    Q6 when it matters -- effective 2024-11-06, already in force;
    Q7 investigate -- the verdict reason names the scope version;
    Q8 why OpenPulse -- the endoflife.date row carries no support
       date at all for 3.8, and a plain EOL record cannot tell the
       apache pin from the confluent or bitnami packaged images on
       the same cycle; version scope plus identity resolution can.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/kafka/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 9, 26)

    # Q1 -- what changed: one EOL finding, scoped to cycle 3.8.
    # The 4.3 cycle has no announced date, so it yields no finding.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert len(findings) == 1
    assert findings[0]["scope"] == {"kind": "version", "versions": ["3.8"]}
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"

    event = finding_to_event(findings[0], "kafka", today=today)

    # Q2 -- evidence: claim gate accepts it; dated, single-source EMERGING.
    assert gate(event) == []
    assert any(e.effective_date == date(2024, 11, 6) for e in event.evidences)

    # Q3 -- identity: project spellings resolve; packaged images do not.
    assert event.project_slug == "kafka"
    for spelling in ("kafka", "apache/kafka"):
        assert resolve_project(spelling) == "kafka", spelling
    assert resolve_project("docker.io/bitnami/kafka:3.8.1") == "bitnami-kafka"
    assert resolve_project("docker.io/confluentinc/cp-kafka:3.8") != "kafka"

    # Q4 + Q5 -- dependency verdicts: version truth and attribution.
    pinned_old = check_dependency(
        {"kind": "package", "package": "kafka", "ecosystem": "", "version": "3.8"}, [event]
    )
    pinned_new = check_dependency(
        {"kind": "package", "package": "kafka", "ecosystem": "", "version": "4.3"}, [event]
    )
    bitnami_cycle = check_dependency(
        {"kind": "image", "ref": "docker.io/bitnami/kafka:3.8"}, [event]
    )
    bitnami_old = check_dependency(
        {"kind": "image", "ref": "docker.io/bitnami/kafka:3.8.1"}, [event]
    )
    assert (pinned_old.affected, pinned_old.relationship) == (True, "AFFECTS_VERSION")
    assert pinned_old.confidence == "EMERGING"
    assert (pinned_new.affected, pinned_new.relationship) == (False, "NOT_AFFECTED")
    assert (bitnami_cycle.affected, bitnami_cycle.relationship) == (False, "NOT_AFFECTED")
    assert (bitnami_old.affected, bitnami_old.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: effective in the past, in force now.
    assert findings[0]["effective_at"] == "2024-11-06"

    # Q7 -- investigate: the reason names the scope version.
    assert "3.8" in pinned_old.reason

    # Q8 -- why OpenPulse: the same cycle, three identities, three
    # verdicts -- a plain EOL record cannot make this call, and the
    # 3.8 row carries no support date to reason from either.
    assert pinned_old.reason != bitnami_old.reason
    assert "bitnami-kafka" in bitnami_old.reason
    # The cycle-tag exclusion is the load-bearing one: the tag equals
    # the scope version exactly, so only identity resolution can
    # exclude it -- with the project binding dropped the control run
    # turns it AFFECTS_VERSION.
    assert "bitnami-kafka" in bitnami_cycle.reason
    assert all(e.get("support") is None for e in raw["endoflife"])


def test_golden_cert_manager_eol_pins_and_namespaces():
    """cert-manager 1.19 and 1.18 EOL: version truth across three
    pins and two effective cycles, plus the bitnami tag-collision
    exclusion, end to end from the offline raw-bundle fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- cycles 1.19 and 1.18 reached EOL, each
       scoped to its own cycle; the 1.21 cycle (no announced date
       yet) stays silent;
    Q2 evidence -- both bridged events pass the claim gate, dated
       effective 2026-07-08 and 2026-03-10, single secondary source
       so EMERGING;
    Q3 identity -- cert-manager resolves to the cert-manager
       project; the bitnami-packaged image on the same cycle tag is
       its own project;
    Q4 what dependency -- cert-manager==1.19 and cert-manager==1.18
       are the affected pins;
    Q5 which versions/artifacts -- 1.19 and 1.18 pins affected
       against their own cycles, 1.21 pin not affected, a 1.18 pin
       checked against the 1.19 event is not affected, and the
       bitnami image carrying the 1.18 tag is not affected either;
    Q6 when it matters -- effective 2026-07-08 and 2026-03-10,
       both already in force;
    Q7 investigate -- the verdict reason names the scope version;
    Q8 why OpenPulse -- an EOL database row cannot tell the
       upstream pin from the packaged image on the same tag, and
       cannot keep the two EOL'd cycles apart in one check; scope
       binding plus identity resolution can.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/cert-manager/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 9, 26)

    # Q1 -- what changed: two EOL findings, one per effective cycle.
    # The 1.21 cycle has no announced date, so it yields no finding.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert [f["scope"]["versions"] for f in findings] == [["1.19"], ["1.18"]]
    assert all(f["lifecycle_state"] == "EFFECTIVE" for f in findings)

    by_cycle = {f["scope"]["versions"][0]: f for f in findings}
    event_19 = finding_to_event(by_cycle["1.19"], "cert-manager", today=today)
    event_18 = finding_to_event(by_cycle["1.18"], "cert-manager", today=today)

    # Q2 -- evidence: claim gate accepts both; dated, single-source EMERGING.
    assert gate(event_19) == []
    assert gate(event_18) == []
    assert any(e.effective_date == date(2026, 7, 8) for e in event_19.evidences)
    assert any(e.effective_date == date(2026, 3, 10) for e in event_18.evidences)

    # Q3 -- identity: project spelling resolves; bitnami does not.
    assert event_19.project_slug == "cert-manager"
    assert resolve_project("cert-manager") == "cert-manager"
    assert resolve_project("docker.io/bitnami/cert-manager:1.18") == "bitnami-cert-manager"

    # Q4 + Q5 -- dependency verdicts: version truth, cross-cycle
    # exclusion, and attribution.
    pin = {"kind": "package", "package": "cert-manager", "ecosystem": ""}
    pinned_19 = check_dependency({**pin, "version": "1.19"}, [event_19])
    pinned_18 = check_dependency({**pin, "version": "1.18"}, [event_18])
    pinned_21 = check_dependency({**pin, "version": "1.21"}, [event_19])
    cross_cycle = check_dependency({**pin, "version": "1.18"}, [event_19])
    bitnami_18 = check_dependency(
        {"kind": "image", "ref": "docker.io/bitnami/cert-manager:1.18"}, [event_18]
    )
    assert (pinned_19.affected, pinned_19.relationship) == (True, "AFFECTS_VERSION")
    assert pinned_19.confidence == "EMERGING"
    assert (pinned_18.affected, pinned_18.relationship) == (True, "AFFECTS_VERSION")
    assert (pinned_21.affected, pinned_21.relationship) == (False, "NOT_AFFECTED")
    assert (cross_cycle.affected, cross_cycle.relationship) == (False, "NOT_AFFECTED")
    assert (bitnami_18.affected, bitnami_18.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: both effective in the past, in force now.
    assert by_cycle["1.19"]["effective_at"] == "2026-07-08"
    assert by_cycle["1.18"]["effective_at"] == "2026-03-10"

    # Q7 -- investigate: the reasons name their scope versions.
    assert "1.19" in pinned_19.reason
    assert "1.18" in pinned_18.reason

    # Q8 -- why OpenPulse: two effective cycles and a packaged image
    # on the same tag -- one EOL row cannot separate any of them.
    assert pinned_18.reason != cross_cycle.reason
    assert pinned_18.reason != bitnami_18.reason
    assert "bitnami-cert-manager" in bitnami_18.reason


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


def test_golden_traefik_ownership_move():
    """Traefik's repository moved from containous/traefik to
    traefik/traefik when Traefik Labs replaced the Containous
    company identity (2020): a recorded github.com/containous/traefik
    require or remote now names a redirect while the moved-to repo
    ships actively. End to end from the offline raw-bundle fixture
    (repo_meta + latest release probed live 2026-10-07). Third real
    move through the same rule: not shaped around capa or etcd, and
    not around dead projects either -- the destination is alive.

    M2 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- the repository moved from containous/traefik
       to traefik/traefik; the queried path no longer names the
       owner;
    Q2 evidence -- the bridged event passes the claim gate; single
       primary source (the repository itself) so EMERGING;
    Q3 identity -- github.com/containous/traefik and
       github.com/traefik/traefik are different repository
       identities; the recorded old path is the stale one;
    Q4 what dependency -- a github.com/containous/traefik source
       reference (go.mod require, git remote) is the affected
       dependency;
    Q5 which versions/artifacts -- old path affected (it names a
       redirect), new path UNKNOWN (not a match), bare package pin
       stays contextual (AFFECTS_PROJECT);
    Q6 when it matters -- the move already happened; the moved-to
       repo is actively shipping (v3.7.14 released 2026-10-06), so
       the stale reference is live drift, not history;
    Q7 investigate -- the finding names both paths, and the verdict
       reason names the affected artifact;
    Q8 why OpenPulse -- an EOL/CVE database has no slot for "your
       recorded source path changed owner"; nothing about v3.7.14 is
       unusual, only the identity comparison catches it.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.evidence.policy import gate
    from core.risk.impact import evaluate_impact

    raw = json.load(open("data/fixtures/traefik-move/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 10, 7)

    # Q1 -- what changed: one ownership finding, project-scoped, no
    # archived finding (the repository is alive).
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "OWNERSHIP_CHANGE"]
    assert len(findings) == 1
    assert all(f["event_type"] != "PROJECT_ARCHIVED" for f in analyze(raw, today=today))
    assert findings[0]["scope"] == {"kind": "project", "versions": []}
    assert findings[0]["detection_method"] == "repository_observation"
    assert findings[0]["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/containous/traefik"}
    ]

    event = finding_to_event(findings[0], "traefik", today=today)

    # Q2 -- evidence: claim gate accepts it; single primary source so
    # EMERGING, never CONFIRMED off one observation.
    assert gate(event) == []
    assert event.confidence.value == "EMERGING"
    assert [e.source.authority for e in event.evidences] == ["secondary"]

    # Q3 + Q4 + Q5 -- identity and dependency verdicts: the old path
    # is the affected dependency; the new path is a non-match.
    old_ref = check_dependency({"kind": "image", "ref": "github.com/containous/traefik"}, [event])
    new_ref = check_dependency({"kind": "image", "ref": "github.com/traefik/traefik"}, [event])
    package_pin = check_dependency(
        {"kind": "package", "package": "traefik", "ecosystem": "", "version": None}, [event]
    )
    assert (old_ref.affected, old_ref.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (new_ref.affected, new_ref.relationship) == (False, "UNKNOWN")
    assert (package_pin.affected, package_pin.relationship) == (False, "AFFECTS_PROJECT")
    assert old_ref.confidence == "EMERGING"

    # Q6 -- when: the move already happened; the moved-to repo pushed
    # and released v3.7.14 the day before the probe.
    assert findings[0]["lifecycle_state"] == "EFFECTIVE"
    assert raw["github"][0]["tag"] == "v3.7.14"
    assert raw["github_meta"][0]["pushed_at"].startswith("2026-10-06")

    # Q7 -- investigate: the finding and verdict name what moved.
    assert "containous/traefik" in findings[0]["title"]
    assert "traefik/traefik" in findings[0]["title"]
    assert "github.com/containous/traefik" in old_ref.reason
    assert "verify" in findings[0]["summary"]

    # Q8 -- why OpenPulse: ownership drift is a repository-identity
    # fact, not a lifecycle row; review-framed, never auto-action.
    assessed = evaluate_impact(findings[0], today=today)
    assert assessed["assessment"] == "PROJECT_CHANGE"
    assert assessed["eligibility"] == "REVIEW"
    assert old_ref.reason != new_ref.reason


def test_golden_fbsdk_archive_and_move():
    """facebook/react-native-fbsdk was moved into the facebookarchive
    org and archived when maintenance ended (2021): one recorded
    repository now carries both signals at once -- the queried path
    names a redirect (ownership) and the destination is read-only
    (archived). The final release v3.0.0 (2020-11-23) predates the
    archive, so every pin is a pin of a dead project. End to end from
    the offline raw-bundle fixture (repo_meta + final release probed
    live 2026-10-07). First combined case: archive and ownership are
    independent findings, not one folded event.

    M2 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- the repository moved from facebook to
       facebookarchive AND was archived; both findings fire;
    Q2 evidence -- both bridged events pass the claim gate;
       single primary source each, so EMERGING;
    Q3 identity -- github.com/facebook/react-native-fbsdk and
       github.com/facebookarchive/react-native-fbsdk are different
       repository identities; the archive org IS the moved-to
       identity, visible in the recorded release URL;
    Q4 what dependency -- the old source path is the affected
       artifact; an npm package pin is contextual;
    Q5 which versions/artifacts -- v3.0.0 is the last release;
       no version escapes the archive (scope: project, versions []);
    Q6 when it matters -- archived 2021, last push 2021-03-26;
       in force now, nothing upcoming;
    Q7 investigate -- the archived finding names the read-only state
       and last push; the ownership finding names both paths;
    Q8 why OpenPulse -- no EOL row covers a GitHub archive, and no
       CVE database records that the recorded path moved; the
       combination (dead + moved) is only visible by observation.
    """
    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.evidence.policy import gate
    from core.risk.impact import evaluate_impact

    raw = json.load(open("data/fixtures/fbsdk-archive-move/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 10, 7)

    # Q1 -- what changed: exactly two findings, one archived, one
    # ownership move; the archive org is the moved-to identity.
    all_findings = analyze(raw, today=today)
    assert sorted(f["event_type"] for f in all_findings) == [
        "OWNERSHIP_CHANGE",
        "PROJECT_ARCHIVED",
    ]
    archived = next(f for f in all_findings if f["event_type"] == "PROJECT_ARCHIVED")
    moved = next(f for f in all_findings if f["event_type"] == "OWNERSHIP_CHANGE")
    assert archived["impact"] == "ACTION"
    assert moved["affected_artifacts"] == [
        {"kind": "source-repository", "ref": "github.com/facebook/react-native-fbsdk"}
    ]
    assert raw["github_meta"][0]["full_name"] == "facebookarchive/react-native-fbsdk"
    assert raw["github_meta"][0]["archived"] is True

    arch_event = finding_to_event(archived, "react-native-fbsdk", today=today)
    move_event = finding_to_event(moved, "react-native-fbsdk", today=today)

    # Q2 -- evidence: both events pass the gate; EMERGING each.
    assert gate(arch_event) == []
    assert gate(move_event) == []
    assert arch_event.confidence.value == "EMERGING"
    assert move_event.confidence.value == "EMERGING"

    # Q3 + Q4 + Q5 -- identity and dependency verdicts: old path is
    # the stale artifact on the move event; an npm pin is contextual
    # on the archive event (the project itself is read-only).
    old_ref = check_dependency(
        {"kind": "image", "ref": "github.com/facebook/react-native-fbsdk"}, [move_event]
    )
    new_ref = check_dependency(
        {"kind": "image", "ref": "github.com/facebookarchive/react-native-fbsdk"}, [move_event]
    )
    npm_pin = check_dependency(
        {
            "kind": "package",
            "package": "react-native-fbsdk",
            "ecosystem": "npm",
            "version": "3.0.0",
        },
        [arch_event],
    )
    assert (old_ref.affected, old_ref.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (new_ref.affected, new_ref.relationship) == (False, "UNKNOWN")
    assert (npm_pin.affected, npm_pin.relationship) == (False, "AFFECTS_PROJECT")
    assert moved["scope"] == {"kind": "project", "versions": []}

    # Q6 -- when: archived 2021, last push recorded in the finding;
    # effective now, nothing upcoming.
    assert archived["lifecycle_state"] == "EFFECTIVE"
    assert moved["lifecycle_state"] == "EFFECTIVE"
    assert "2021-03-26" in archived["summary"]
    # the last release predates the archive: no version escapes it
    assert raw["github"][0]["tag"] == "v3.0.0"
    assert raw["github"][0]["published_at"].startswith("2020-11-23")
    assert raw["github"][0]["url"].startswith(
        "https://github.com/facebookarchive/react-native-fbsdk/"
    )

    # Q7 -- investigate: each finding names its own fact.
    assert "archived" in archived["title"].lower()
    assert "facebook/react-native-fbsdk" in moved["title"]
    assert "facebookarchive/react-native-fbsdk" in moved["title"]

    # Q8 -- why OpenPulse: the dead-and-moved combination is an
    # observed identity fact. The analyst proposes ACTION for the
    # archive (read-only is final); the eligibility layer still caps
    # it at REVIEW -- "archived upstream is a project-level change,
    # not proof any deployment is affected" -- while the move stays
    # review-framed end to end. Neither is ever an auto-action.
    assert archived["impact"] == "ACTION"
    assert evaluate_impact(archived, today=today)["eligibility"] == "REVIEW"
    assert evaluate_impact(moved, today=today)["eligibility"] == "REVIEW"
    assert old_ref.reason != new_ref.reason


def test_golden_bitnami_spark_empty_mainline():
    """docker.io/bitnami/spark now answers with an empty tag set: not
    `latest`-only, zero names on both the Hub API and the v2 protocol
    (probed live 2026-10-07), while docker.io/bitnamilegacy/spark
    holds all 936 historical tags with digests and no pushes since
    2025-08-08. This is the shape the Bitnami catalog deletion
    (announced 2025-07-16, effective 2025-08-28, postponed to
    2025-09-29) actually produced for repos outside the kept subset:
    a distribution removal one step past latest-only. End to end:
    the producer-side rule fires off the recorded probe pair, the
    curated event passes the gate, and pinned refs are told apart.

    M2 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- the bitnami/spark mainline publishes no tags
       at all; the versioned distribution lives in bitnamilegacy;
    Q2 evidence -- the curated event passes the claim gate
       (official Bitnami announcement + primary registry probes),
       CONFIRMED/ACTION; the producer-side finding bridges only as
       EMERGING with a date violation -- weak evidence holds back;
    Q3 identity -- docker.io/bitnami/spark and bitnamilegacy/spark
       are distributions, not upstream: docker.io/apache/spark is
       the upstream image and must NOT match;
    Q4 what dependency -- a pinned docker.io/bitnami/spark:<version>
       reference no longer resolves; a bitnamilegacy pin resolves
       against a frozen, unsupported snapshot;
    Q5 which versions/artifacts -- both namespace refs affected,
       upstream apache/spark NOT_AFFECTED;
    Q6 when it matters -- announced 2025-07-16, effective 2025-08-28
       (deletion postponed to 2025-09-29); in force now;
    Q7 investigate -- the finding names both namespaces and the
       migration need; the verdict reason names the pinned ref;
    Q8 why OpenPulse -- an EOL database records Spark's cycle; no
       database row says "your pinned distribution tag answers
       empty"; only a probe comparison can catch a removal.
    """
    from analyzers.change_analyst import analyze, analyze_registries
    from analyzers.lifecycle_events import finding_to_event
    from core.evidence.policy import gate
    from core.risk.impact import evaluate_impact

    fixture = "data/fixtures/spark-mainline-empty"
    today = date(2026, 10, 7)

    # Q1 -- what changed: the split rule fires on the recorded probe
    # pair. The empty mainline is the producer-side gap this case
    # formalizes: pristine main required latest_only on the mainline
    # side and stayed silent on exactly this shape. The probe flags
    # are what parse_tags emits for the recorded answers, not
    # hand-tuned booleans.
    main = json.load(open(f"{fixture}/mainline_probe.json", encoding="utf-8"))
    legacy = json.load(open(f"{fixture}/legacy_probe.json", encoding="utf-8"))
    assert main["tags_sample"] == [] and main["count"] == 0 and not main["truncated"]
    assert main["latest_only"] is False and main["has_versioned_tags"] is False
    assert legacy["count"] == 936 and legacy["has_versioned_tags"] is True
    findings = analyze({"registries": [main, legacy]}, today=today)
    assert len(findings) == 1
    finding = findings[0]
    assert finding["event_type"] == "DISTRIBUTION_CHANGE"
    assert finding["title"] == (
        "bitnami mainline publishes no tags at all; versioned tags live in bitnamilegacy"
    )
    assert finding["affected_artifacts"] == [
        {"kind": "docker-image", "ref": "docker.io/bitnami/spark:<version>"},
        {"kind": "docker-image", "ref": "docker.io/bitnamilegacy/spark:<version>"},
    ]

    # Q2 -- evidence: weak producer evidence holds itself back -- the
    # bridged producer finding cannot pass the gate (no dates), and
    # impact caps at REVIEW. The curated event (official announcement
    # + primary probes) is the reportable form: CONFIRMED/ACTION.
    producer_event = finding_to_event(finding, "bitnami-spark", today=today)
    assert gate(producer_event) == [
        "DISTRIBUTION_CHANGE requires announcement_date or effective_date in at least one evidence"
    ]
    assert evaluate_impact(finding, today=today)["eligibility"] == "REVIEW"
    event = _load("spark-mainline-empty")
    assert gate(event) == []
    assert event.confidence.value == "CONFIRMED"
    assert [e.source.authority for e in event.evidences] == ["official", "primary"]

    # Q3 + Q4 + Q5 -- identity and dependency verdicts: both
    # distribution namespaces are affected; the upstream apache image
    # is explicitly NOT affected.
    pin_main = check_dependency({"kind": "image", "ref": "docker.io/bitnami/spark:3.5.4"}, [event])
    pin_legacy = check_dependency(
        {"kind": "image", "ref": "docker.io/bitnamilegacy/spark:3.5.4"}, [event]
    )
    upstream = check_dependency({"kind": "image", "ref": "docker.io/apache/spark:3.5.4"}, [event])
    assert (pin_main.affected, pin_main.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (pin_legacy.affected, pin_legacy.relationship) == (True, "AFFECTS_ARTIFACT")
    assert (upstream.affected, upstream.relationship) == (False, "NOT_AFFECTED")
    assert "docker.io/bitnami/spark:3.5.4" in pin_main.reason

    # Q6 -- when: announced 2025-07-16, effective 2025-08-28, catalog
    # deletion postponed to 2025-09-29 -- dates carried by the event
    # evidence, in force now.
    announce = next(e for e in event.evidences if e.source.name.startswith("github/bitnami"))
    assert announce.effective_date == date(2025, 8, 28)
    assert announce.announcement_date == date(2025, 7, 16)
    assert event.impact.value == "ACTION"

    # Q7 -- investigate: the producer finding names both namespaces
    # (namespace form) and the migration need; the curated event
    # names both full image refs and what a pin now resolves to.
    assert "docker.io/bitnami" in finding["summary"]
    assert "docker.io/bitnamilegacy" in finding["summary"]
    assert "migration plan" in finding["summary"]
    assert "no tags at all" in finding["title"]
    assert "docker.io/bitnami/spark" in event.summary
    assert "docker.io/bitnamilegacy/spark" in event.summary
    assert "frozen, unsupported snapshot" in event.summary

    # Q8 -- why OpenPulse: a removal that answers empty is only
    # visible by probing; the split rule treats it as the
    # distribution-model change it is, not a missing-repo error.
    assert analyze_registries([main], today=today) == []
    assert analyze_registries([legacy], today=today) == []


def test_golden_grafana_eol_pins_and_distribution():
    """Grafana 12.3 EOL: the upstream image and the enterprise
    distribution of the same release cycle, end to end from the
    offline raw-bundle fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- cycle 12.3 reached EOL on 2026-08-19, scoped
       to that cycle only; the 12.2 cycle (EOL 2026-06-23) is a
       separate earlier finding, and 13.0 (EOL 2027-01-09) stays
       UPCOMING;
    Q2 evidence -- the bridged event passes the claim gate, dated
       effective 2026-08-19, single secondary source so EMERGING;
    Q3 identity -- grafana, grafana/grafana and the docker.io
       upstream image resolve to the grafana project, and so does
       the grafana-enterprise image: it is the closed-source
       distribution of the same release cycle, not a fork with its
       own version line;
    Q4 what dependency -- docker.io/grafana/grafana:12.3.0 is the
       affected pin;
    Q5 which versions/artifacts -- the 12.3.0 pin on the upstream
       image is affected, the 13.0.0 pin is not, and the enterprise
       image on the same tag is affected through the same scope;
    Q6 when it matters -- effective 2026-08-19, already in force;
    Q7 investigate -- the verdict reason names the scope version;
    Q8 why OpenPulse -- an EOL database row for Grafana 12.3 cannot
       say whether a pinned docker.io/grafana/grafana-enterprise:12.3
       tag is covered: identity resolution maps the distribution to
       the upstream cycle, and version scope keeps the 13.0 pin
       silent."""

    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/grafana/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 10, 7)

    # Q1 -- what changed: three EOL findings, each scoped to its own
    # cycle; 12.3 and 12.2 are in force, 13.0 is still upcoming.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert [f["scope"]["versions"] for f in findings] == [["12.3"], ["12.2"], ["13.0"]]
    by_cycle = {f["scope"]["versions"][0]: f for f in findings}
    assert by_cycle["12.3"]["lifecycle_state"] == "EFFECTIVE"
    assert by_cycle["13.0"]["lifecycle_state"] == "UPCOMING"

    event = finding_to_event(by_cycle["12.3"], "grafana", today=today)

    # Q2 -- evidence: claim gate accepts it; dated, single-source EMERGING.
    assert gate(event) == []
    assert any(e.effective_date == date(2026, 8, 19) for e in event.evidences)

    # Q3 -- identity: spellings and both image lines resolve to grafana.
    assert event.project_slug == "grafana"
    for spelling in ("grafana", "grafana/grafana", "Grafana"):
        assert resolve_project(spelling) == "grafana", spelling
    assert resolve_project("docker.io/grafana/grafana:12.3.0") == "grafana"
    assert resolve_project("docker.io/grafana/grafana-enterprise:12.3.0") == "grafana"

    # Q4 + Q5 -- dependency verdicts: the distribution is not a fork.
    upstream_old = check_dependency(
        {"kind": "image", "ref": "docker.io/grafana/grafana:12.3.0"}, [event]
    )
    enterprise_old = check_dependency(
        {"kind": "image", "ref": "docker.io/grafana/grafana-enterprise:12.3.0"}, [event]
    )
    upstream_new = check_dependency(
        {"kind": "image", "ref": "docker.io/grafana/grafana:13.0.0"}, [event]
    )
    assert (upstream_old.affected, upstream_old.relationship) == (True, "AFFECTS_VERSION")
    assert upstream_old.confidence == "EMERGING"
    assert (enterprise_old.affected, enterprise_old.relationship) == (True, "AFFECTS_VERSION")
    assert (upstream_new.affected, upstream_new.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: effective in the past, in force now.
    assert by_cycle["12.3"]["effective_at"] == "2026-08-19"

    # Q7 -- investigate: the reason names the scope version.
    assert "12.3" in upstream_old.reason
    assert "12.3" in enterprise_old.reason

    # Q8 -- why OpenPulse: the enterprise image inherits the upstream
    # cycle EOL through identity, and the 13.0 pin stays silent
    # through scope -- two calls a bare EOL row cannot make.
    assert upstream_old.reason != upstream_new.reason
    assert enterprise_old.match_method == "event_scope:version"


def test_golden_terraform_eol_pins_and_fork_line():
    """Terraform 1.14 EOL: core versioning with a numerically
    colliding fork line, end to end from the offline raw-bundle
    fixture.

    M4 eight questions, one scenario (mapping per acceptance):
    Q1 what changed -- cycle 1.14 reached EOL on 2026-08-26, scoped
       to that cycle only; 1.13 (EOL 2026-04-29) is a separate
       earlier finding, and 1.16 has no EOL date at all (eol: false)
       so it yields no finding;
    Q2 evidence -- the bridged event passes the claim gate, dated
       effective 2026-08-26, single secondary source so EMERGING;
    Q3 identity -- terraform, hashicorp/terraform and the
       docker.io/hashicorp/terraform image resolve to the terraform
       project; ghcr.io/opentofu/opentofu is a fork with its own
       version line whose 1.14 numerically collides with core 1.14;
    Q4 what dependency -- a terraform 1.14 pin is the affected
       dependency;
    Q5 which versions/artifacts -- the 1.14 pin is affected, the
       1.16 pin is not, and the OpenTofu image on the same 1.14 tag
       is not, because it is a different project;
    Q6 when it matters -- effective 2026-08-26, already in force;
    Q7 investigate -- the verdict reason names the scope version
       and the fork exclusion names the fork project;
    Q8 why OpenPulse -- an EOL database row for Terraform 1.14
       cannot tell a pinned ghcr.io/opentofu/opentofu:1.14 tag apart
       from hashicorp/terraform:1.14: identity resolution can, and
       version scope keeps the 1.16 pin silent."""

    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.entities.resolve import resolve_project
    from core.evidence.policy import gate

    raw = json.load(open("data/fixtures/terraform/raw_bundle.json", encoding="utf-8"))
    today = date(2026, 10, 7)

    # Q1 -- what changed: the two dated cycles yield findings, the
    # undated 1.16 row does not.
    findings = [f for f in analyze(raw, today=today) if f["event_type"] == "EOL"]
    assert [f["scope"]["versions"] for f in findings] == [["1.14"], ["1.13"]]
    assert all(f["lifecycle_state"] == "EFFECTIVE" for f in findings)
    assert "1.16" not in {f["scope"]["versions"][0] for f in findings}

    event = finding_to_event(findings[0], "terraform", today=today)

    # Q2 -- evidence: claim gate accepts it; dated, single-source EMERGING.
    assert gate(event) == []
    assert any(e.effective_date == date(2026, 8, 26) for e in event.evidences)

    # Q3 -- identity: spellings resolve; the fork does not.
    assert event.project_slug == "terraform"
    for spelling in ("terraform", "hashicorp/terraform", "Terraform"):
        assert resolve_project(spelling) == "terraform", spelling
    assert resolve_project("docker.io/hashicorp/terraform:1.14") == "terraform"
    assert resolve_project("ghcr.io/opentofu/opentofu:1.14") != "terraform"

    # Q4 + Q5 -- dependency verdicts: the fork colliding tag is excluded.
    pinned_old = check_dependency(
        {"kind": "image", "ref": "docker.io/hashicorp/terraform:1.14"}, [event]
    )
    pinned_new = check_dependency(
        {"kind": "image", "ref": "docker.io/hashicorp/terraform:1.16"}, [event]
    )
    fork_same_tag = check_dependency(
        {"kind": "image", "ref": "ghcr.io/opentofu/opentofu:1.14"}, [event]
    )
    assert (pinned_old.affected, pinned_old.relationship) == (True, "AFFECTS_VERSION")
    assert pinned_old.confidence == "EMERGING"
    assert (pinned_new.affected, pinned_new.relationship) == (False, "NOT_AFFECTED")
    assert (fork_same_tag.affected, fork_same_tag.relationship) == (False, "NOT_AFFECTED")

    # Q6 -- when: effective in the past, in force now.
    assert findings[0]["effective_at"] == "2026-08-26"

    # Q7 -- investigate: the reason names the scope version, and the
    # fork exclusion names the fork own project.
    assert "1.14" in pinned_old.reason
    assert "ghcr.io/opentofu/opentofu" in fork_same_tag.reason

    # Q8 -- why OpenPulse: the fork image on the same 1.14 tag is
    # excluded by project identity, and the 1.16 pin by version
    # scope -- two calls a bare EOL row cannot make.
    assert pinned_old.reason != fork_same_tag.reason
    assert "terraform" in fork_same_tag.reason
