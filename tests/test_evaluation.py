"""Evaluation harness (evaluation/PROTOCOL.md): policies, metrics, replay.

These pin the harness's definitions, not OpenPulse's effectiveness. The
development-set assertions at the end pin known results so that a
change in them is a deliberate, reviewed flip.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

EVALUATION = Path(__file__).resolve().parents[1] / "evaluation"
sys.path.insert(0, str(EVALUATION))

import metrics  # noqa: E402
import policies  # noqa: E402
import replay  # noqa: E402
import run  # noqa: E402

from core.schema.models import OSSEvent  # noqa: E402

BITNAMI = {"source": "event", "fixture": "bitnami", "class": "distribution", "as_of": "2026-10-02"}


def _bitnami() -> OSSEvent:
    event = replay.replay(BITNAMI)
    assert event is not None
    return event


# --- policies -------------------------------------------------------------


def test_naive_clears_what_is_unlisted_and_conservative_abstains():
    event = _bitnami()
    official = {"kind": "image", "ref": "docker.io/redis:7.2"}
    assert policies.naive(official, [event])["outcome"] == policies.CLEARED
    assert policies.conservative(official, [event])["outcome"] == policies.UNRESOLVED


def test_baselines_list_by_canonical_reference():
    event = _bitnami()
    for ref in ("docker.io/bitnami/nginx:1.25", "index.docker.io/bitnami/nginx:1.25"):
        dep = {"kind": "image", "ref": ref}
        assert policies.naive(dep, [event])["outcome"] == policies.AFFECTED
        assert policies.conservative(dep, [event])["outcome"] == policies.AFFECTED


def test_baselines_ignore_withdrawn_events():
    event = _bitnami().model_copy(update={"withdrawn": True})
    dep = {"kind": "image", "ref": "docker.io/bitnami/nginx:1.25"}
    assert policies.naive(dep, [event])["outcome"] == policies.CLEARED
    assert policies.conservative(dep, [event])["outcome"] == policies.NONE


def test_openpulse_policy_carries_its_justification():
    decision = policies.openpulse({"kind": "image", "ref": "docker.io/redis:7.2"}, [_bitnami()])
    assert decision["outcome"] == policies.CLEARED
    assert decision["justification"] == {
        "sources_named": True,
        "acquisition_time": True,
        "meaning_stated": True,
        "completeness_basis": True,
        "contracts_valid": True,
    }


def test_ablated_verdicts_never_reach_a_contract():
    dep = {"kind": "image", "ref": "docker.io/redis:7.2"}
    assert "justification" not in policies.openpulse_no_identity(dep, [_bitnami()])


def test_completeness_ablation_changes_inputs_not_code():
    event = _bitnami()
    scope = event.scope.model_copy(update={"exhaustive": False, "basis": None})
    partial = event.model_copy(update={"scope": scope})
    (closed,) = policies._assume_complete([partial])
    assert closed.scope.admits_negative() and not partial.scope.admits_negative()


# --- replay ---------------------------------------------------------------


def test_knowledge_cut_drops_later_evidence():
    event = _bitnami()
    before = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert replay.knowledge_cut(event, before) is None
    assert replay.knowledge_cut(event, datetime(2030, 1, 1, tzinfo=timezone.utc)) is event


def test_raw_bundle_replay_rederives_the_event():
    spec = {
        "source": "raw_bundle",
        "fixture": "redis",
        "event_type": "EOL",
        "versions": ["6.2"],
        "project": "redis",
        "as_of": "2026-09-26",
    }
    event = replay.replay(spec)
    assert event is not None and event.scope.versions == ["6.2"]


# --- metrics --------------------------------------------------------------


def _row(label, outcome, event="e1", **extra):
    return {"label": label, "outcome": outcome, "event": event, **extra}


def test_rates_with_empty_denominators_are_undefined_not_zero():
    out = metrics.summarise([_row(metrics.OUT, policies.UNRESOLVED)])
    assert out["fcr_affected"] is None
    assert out["fcr_clear"] is None
    assert out["unsupported_decisiveness"] is None
    assert out["evidence_completeness"] is None


def test_false_clear_and_silent_miss_are_counted_apart():
    rows = [
        _row(metrics.IN, policies.CLEARED, "e1"),
        _row(metrics.IN, policies.NONE, "e2"),
        _row(metrics.IN, policies.AFFECTED, "e3"),
        _row(metrics.OUT, policies.CLEARED, "e3"),
    ]
    out = metrics.summarise(rows)
    assert out["false_clears"] == 1
    assert out["fcr_affected"] == round(1 / 3, 4)
    assert out["fcr_clear"] == 0.5
    assert out["silent_miss_rate"] == round(1 / 3, 4)
    assert out["events_with_false_clear"] == 1
    assert "per_event_false_clear_upper_95" not in out


def test_zero_false_clears_report_the_event_level_bound():
    rows = [_row(metrics.IN, policies.AFFECTED, f"e{i}") for i in range(10)]
    assert metrics.summarise(rows)["per_event_false_clear_upper_95"] == 0.3


def test_abstention_on_undeterminable_pairs_is_not_unsupported():
    rows = [_row(metrics.UNDET, policies.UNRESOLVED), _row(metrics.UNDET, policies.AFFECTED)]
    assert metrics.summarise(rows)["unsupported_decisiveness"] == 0.5


# --- dataset validation -----------------------------------------------------


def _write(tmp_path, cases):
    data = {
        "dataset": "t",
        "version": "1",
        "status": "test",
        "events": {"bitnami-2025": BITNAMI},
        "cases": cases,
    }
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _case(**overrides):
    case = {
        "id": "c1",
        "events": ["bitnami-2025"],
        "dependency": {"kind": "image", "ref": "docker.io/redis:7.2"},
        "label": "out_of_scope",
        "rationale": "official image",
        "label_source": "bitnami/containers#83267",
    }
    return {**case, **overrides}


@pytest.mark.parametrize(
    "bad",
    [
        {"label": "maybe"},
        {"rationale": ""},
        {"events": ["nope"]},
    ],
)
def test_malformed_cases_fail_closed(tmp_path, bad):
    with pytest.raises(ValueError):
        run.run(_write(tmp_path, [_case(**bad)]))


def test_duplicate_case_ids_fail_closed(tmp_path):
    with pytest.raises(ValueError):
        run.run(_write(tmp_path, [_case(), _case()]))


# --- the development set ----------------------------------------------------


@pytest.fixture(scope="module")
def dev():
    return run.run()


def test_dev_set_runs_every_policy_on_every_case(dev):
    cases = json.loads(run.DEFAULT_CASES.read_text("utf-8"))["cases"]
    for rows in dev["pairs"].values():
        assert [r["case"] for r in rows] == [c["id"] for c in cases]
    assert dev["events_not_known_at_replay"] == []
    assert len(dev["dataset_sha256"]) == 64


def test_dev_set_openpulse_issues_no_false_clear_and_no_unsupported_decision(dev):
    overall = dev["policies"]["C-openpulse"]["overall"]
    assert overall["false_clears"] == 0
    assert overall["unsupported_decisiveness"] == 0.0


def test_dev_set_naive_baseline_false_clears(dev):
    assert dev["policies"]["A-naive"]["overall"]["false_clears"] > 0


def test_dev_set_combined_ablation_exposes_the_admission_premises(dev):
    """Either premise alone masks the other on rx-02 (react 18.3.1)."""
    outcome = {name: {r["case"]: r["outcome"] for r in rows} for name, rows in dev["pairs"].items()}
    assert outcome["C-ablate-completeness"]["rx-02"] == policies.UNRESOLVED
    assert outcome["C-ablate-freshness"]["rx-02"] == policies.UNRESOLVED
    assert outcome["C-ablate-both"]["rx-02"] == policies.CLEARED


def test_dev_set_f1_redis_py_is_not_the_redis_server(dev):
    """FLIPPED (F1, ROADMAP R-B3): the PyPI package ``redis`` is redis-py,
    curated as its own project, so Redis 6.2 end of life no longer marks
    redis==6.2.0 AFFECTS_VERSION. It has no association (UNKNOWN), on
    the evidence of a curated (ecosystem, name) mapping."""
    row = next(r for r in dev["pairs"]["C-openpulse"] if r["case"] == "re-06")
    assert (row["label"], row["relationship"]) == ("out_of_scope", "UNKNOWN")
    assert dev["policies"]["C-openpulse"]["overall"]["false_impact_rate"] == 0.0


# --- policy V, the strong conservative baseline (R-B4) ------------------------


def test_strong_baseline_clears_only_from_an_admissible_complete_scope():
    import strong_baseline

    event = _bitnami()
    official = {"kind": "image", "ref": "docker.io/redis:7.2"}
    assert strong_baseline.strong_conservative(official, [event])["outcome"] == "cleared"
    scope = event.scope.model_copy(update={"exhaustive": False})
    partial = event.model_copy(update={"scope": scope})
    assert strong_baseline.strong_conservative(official, [partial])["outcome"] == "unresolved"


def test_strong_baseline_withholds_negatives_from_stale_evidence():
    import strong_baseline

    event = _bitnami()
    official = {"kind": "image", "ref": "docker.io/redis:7.2"}
    later = datetime(2027, 6, 1, tzinfo=timezone.utc)
    decision = strong_baseline.strong_conservative(
        official, [event], as_of=later, max_evidence_age=timedelta(days=30)
    )
    assert decision["outcome"] == "unresolved"


def test_strong_baseline_envelope_membership_is_not_a_positive():
    import strong_baseline

    latest = {"kind": "image", "ref": "docker.io/bitnami/redis:latest"}
    assert strong_baseline.strong_conservative(latest, [_bitnami()])["outcome"] == "unresolved"


def test_strong_baseline_uses_pep440_for_pypi_and_abstains_elsewhere():
    import strong_baseline

    assert strong_baseline._in_line("4.2.11", "4.2", "pypi") is True
    assert strong_baseline._in_line("4.2rc1", "4.2", "pypi") is True
    assert strong_baseline._in_line("4.20.1", "4.2", "pypi") is False
    assert strong_baseline._in_line("1!4.2", "4.2", "pypi") is None  # epochs differ
    assert strong_baseline._in_line("13.16", "13", "") is True
    assert strong_baseline._in_line("13.16-alpine", "13", "") is None


def test_strong_baseline_unresolved_identity_never_excluded():
    import strong_baseline

    event = replay.replay(
        {
            "source": "raw_bundle",
            "fixture": "redis",
            "event_type": "EOL",
            "versions": ["6.2"],
            "project": "redis",
            "as_of": "2026-09-26",
        }
    )
    mirror = {"kind": "image", "ref": "docker.io/zzz/kvstore:7.2"}
    assert strong_baseline.strong_conservative(mirror, [event])["outcome"] == "unresolved"


# --- identity ablation (R-B5) ----------------------------------------------------


def test_identity_ablation_is_an_explicit_scoped_engine_switch():
    from core.entities.identity import UNRESOLVED_IDENTITY
    from core.risk.check import check_dependency

    mirror = {"kind": "image", "ref": "github.com/etcd-io/etcd"}
    event = replay.replay(
        {
            "source": "raw_bundle",
            "fixture": "etcd-move",
            "event_type": "OWNERSHIP_CHANGE",
            "project": "etcd",
            "as_of": "2026-10-06",
        }
    )
    assert check_dependency(mirror, [event]).relationship == "RELATED"
    ablated = check_dependency(mirror, [event], unresolved_identity="unrelated")
    assert ablated.relationship == "UNKNOWN"
    assert UNRESOLVED_IDENTITY.get() == "undetermined"  # reset after the call
    with pytest.raises(ValueError):
        check_dependency(mirror, [event], unresolved_identity="loose")


def test_dev_set_identity_ablation_trades_abstention_for_silent_misses(dev):
    full = dev["policies"]["C-openpulse"]["overall"]
    ablated = dev["policies"]["C-ablate-identity"]["overall"]
    assert ablated["abstention_rate"] < full["abstention_rate"]
    # FLIPPED (inventory discovery): the dev set's one ablation silent miss
    # was fa-01, a reference to the archived react-native-fbsdk repository.
    # An archived finding now names its repository, so the pair matches by
    # exact artifact under either identity mode (C resolves it, as V did).
    # The ablation's cost is still shown pair by pair in the test above.
    assert full["silent_miss_rate"] == 0.0 <= ablated["silent_miss_rate"]
    fa01 = {
        p: next(r for r in dev["pairs"][p] if r["case"] == "fa-01")["outcome"]
        for p in ("C-openpulse", "C-ablate-identity")
    }
    assert fa01 == {"C-openpulse": "affected", "C-ablate-identity": "affected"}


# --- policy R, the existing-representation baseline (REGISTRATION S3) -----------------


@pytest.mark.parametrize(
    "dep, purl",
    [
        ({"kind": "image", "ref": "index.docker.io/redis:7.2"}, "pkg:docker/library/redis@7.2"),
        ({"kind": "image", "ref": "docker.io/bitnami/redis"}, "pkg:docker/bitnami/redis@latest"),
        (
            {"kind": "image", "ref": "quay.io/coreos/etcd:v3.5.0"},
            "pkg:docker/coreos/etcd@v3.5.0?repository_url=quay.io",
        ),
        (
            {"kind": "image", "ref": "docker.io/redis@sha256:ab"},
            "pkg:docker/library/redis@sha256%3Aab",
        ),
        ({"kind": "image", "ref": "github.com/CoreOS/etcd"}, "pkg:github/coreos/etcd"),
        (
            {"kind": "package", "package": "Flare_Capa", "ecosystem": "PyPI", "version": "7.0.1"},
            "pkg:pypi/flare-capa@7.0.1",
        ),
        (
            {"kind": "package", "package": "@types/node", "ecosystem": "npm", "version": "20.1.0"},
            "pkg:npm/%40types/node@20.1.0",
        ),
        (
            {
                "kind": "package",
                "package": "com.itextpdf:kernel",
                "ecosystem": "Maven",
                "version": None,
            },
            "pkg:maven/com.itextpdf/kernel",
        ),
        (
            {
                "kind": "package",
                "package": "go.etcd.io/etcd/client/v3",
                "ecosystem": "Go",
                "version": "3.5.9",
            },
            "pkg:golang/go.etcd.io/etcd/client/v3@3.5.9",
        ),
        ({"kind": "package", "package": "etcd", "ecosystem": "", "version": None}, None),
    ],
)
def test_existing_representation_builds_one_purl_per_dependency(dep, purl):
    import existing_representation as er

    assert er.dependency_purl(dep) == purl


def _encoding(osv=(), statements=None, loss=()):
    vex = None if statements is None else {"statements": list(statements)}
    return {"osv": list(osv), "openvex": vex, "loss": list(loss)}


def _django_line(**extra):
    record = {
        "affected": [
            {
                "package": {"ecosystem": "PyPI", "name": "Django"},
                "ranges": [
                    {
                        "type": "ECOSYSTEM",
                        "events": [{"introduced": "4.2.dev0"}, {"fixed": "4.3.dev0"}],
                    }
                ],
                **extra,
            }
        ]
    }
    return _encoding(osv=[record])


@pytest.mark.parametrize(
    "version, outcome",
    [
        ("4.2.11", "affected"),
        ("4.2rc1", "affected"),  # a pre-release belongs to its own line
        ("4.3a1", "cleared"),
        ("5.1.2", "cleared"),
        ("4.1.9", "cleared"),
        (None, "unresolved"),
        ("not-a-version", "unresolved"),
    ],
)
def test_existing_representation_reads_an_osv_release_line(version, outcome):
    import existing_representation as er

    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": version}
    assert er.per_event(dep, _django_line()) == outcome


def test_existing_representation_identity_is_the_exact_package():
    import existing_representation as er

    other = {
        "kind": "package",
        "package": "djangorestframework",
        "ecosystem": "PyPI",
        "version": "3.14",
    }
    npm = {"kind": "package", "package": "django", "ecosystem": "npm", "version": "5.0.0"}
    assert er.per_event(other, _django_line()) == "unresolved"  # silence is not a clear
    assert er.per_event(npm, _django_line()) == "unresolved"
    listed = _django_line(versions=["5.0.1"])
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.0.1"}
    assert er.per_event(dep, listed) == "affected"
    assert er.per_event(dep, None) == "unresolved"  # no encoding


def test_existing_representation_reads_openvex_by_exact_purl():
    import existing_representation as er

    statements = [
        {"products": [{"@id": "pkg:docker/bitnami/redis@7.2"}], "status": "affected"},
        {"products": [{"@id": "pkg:github/etcd-io/etcd"}], "status": "not_affected"},
        {"products": [{"@id": "pkg:docker/library/redis@7.2"}], "status": "under_investigation"},
    ]
    enc = _encoding(statements=statements)

    def outcome(ref):
        return er.per_event({"kind": "image", "ref": ref}, enc)

    assert outcome("index.docker.io/bitnami/redis:7.2") == "affected"
    assert outcome("docker.io/bitnami/redis:7.2.5") == "unresolved"  # another tag: no match
    assert outcome("github.com/etcd-io/etcd") == "cleared"
    assert outcome("docker.io/redis:7.2") == "unresolved"
    conflicting = _encoding(
        statements=statements[:1] + [{**statements[0], "status": "not_affected"}]
    )
    ref = {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}
    assert er.per_event(ref, conflicting) == "affected"


def test_existing_representation_summarises_events_as_v():
    import existing_representation as er

    redis = replay.replay(
        {
            "source": "raw_bundle",
            "fixture": "redis",
            "event_type": "EOL",
            "versions": ["6.2"],
            "project": "redis",
            "as_of": "2026-09-26",
        }
    )
    bitnami = _bitnami()
    dep = {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}
    vex = _encoding(
        statements=[
            {
                "products": [{"@id": "pkg:docker/bitnami/redis@7.2"}],
                "status": "not_affected",
                "impact_statement": "x",
            }
        ]
    )
    try:
        er.use_encodings({bitnami.id: vex})
        assert er.existing_representation(dep, [bitnami]) == {
            "outcome": "cleared",
            "encoded": True,
            "encoding_loss": False,
        }
        # An event without an encoding leaves the pair unresolved, and is flagged.
        both = er.existing_representation(dep, [bitnami, redis])
        assert both == {"outcome": "unresolved", "encoded": False, "encoding_loss": True}
        withdrawn = bitnami.model_copy(update={"withdrawn": True})
        assert er.existing_representation(dep, [withdrawn])["outcome"] == policies.NONE
    finally:
        er.use_encodings(None)


def test_existing_representation_is_registered_after_b():
    names = list(policies.POLICIES)
    assert names.index("R-existing-representation") == names.index("B-conservative") + 1


def test_encodings_are_frozen_by_hash(tmp_path, monkeypatch):
    import existing_representation as er

    spec = json.loads(run.DEFAULT_CASES.read_text("utf-8"))["events"]["django-4.2-eol"]["encoding"]
    assert er.load_encoding(spec, "django-4.2-eol")["loss"] == []
    with pytest.raises(ValueError, match="SHA-256"):
        er.load_encoding({**spec, "sha256": "0" * 64}, "django-4.2-eol")
    with pytest.raises(ValueError, match="encodes"):
        er.load_encoding(spec, "react-18-breaking")


def test_malformed_encodings_are_refused():
    import existing_representation as er

    good = json.loads(
        (EVALUATION / "representations" / "dev-2026-10" / "etcd-move.json").read_text("utf-8")
    )
    assert er.validate_encoding(good) == []
    bare = json.loads(json.dumps(good))
    del bare["openvex"]["statements"][1]["impact_statement"]
    assert er.validate_encoding(bare) == [
        "not_affected without a justification or impact statement"
    ]
    lossy = {**good, "loss": [{"code": "L9", "what": "?"}]}
    assert er.validate_encoding(lossy)[0].startswith("loss entry")
    git = {
        **good,
        "osv": [
            {
                "affected": [
                    {
                        "package": {"ecosystem": "PyPI", "name": "x"},
                        "ranges": [{"type": "GIT", "events": []}],
                    }
                ]
            }
        ],
    }
    assert er.validate_encoding(git) == ["OSV range type 'GIT' is not read"]


def test_registered_run_requires_every_encoding():
    with pytest.raises(ValueError, match="no frozen R encoding"):
        run.run(require_encodings=True)


def test_dev_set_existing_representation(dev):
    """Illustrative only: six of 13 events are encoded, by the developer,
    after the other policies' results were seen (dataset revision 3)."""
    r = {row["case"]: row for row in dev["pairs"]["R-existing-representation"]}
    assert dev["policies"]["R-existing-representation"]["overall"]["false_clears"] == 0
    # OSV range and OpenVEX statement decide where the sources name the product.
    assert [r[c]["outcome"] for c in ("dj-01", "dj-03", "et-01", "et-02")] == [
        "affected",
        "cleared",
        "affected",
        "cleared",
    ]
    # A namespace (Bitnami) or a product name (iText) has no purl: unresolved, with loss.
    assert r["bn-01"]["outcome"] == r["it-01"]["outcome"] == "unresolved"
    assert r["bn-01"]["encoding_loss"] and not r["dj-01"]["encoding_loss"]
    # Unencoded events stay unresolved and are flagged.
    assert (r["tr-01"]["outcome"], r["tr-01"]["encoded"]) == ("unresolved", False)
    loss = dev["encodings"]["loss"]["per_event"]
    assert loss["bitnami-2025"] == ["L1", "L2", "L3"] and loss["traefik-move"] is None
    secondary = dev["registration"]["all_labels_illustrative"]["secondary"]
    assert secondary["C_vs_R_resolution_lossless_events"]["difference"] == 0.0


def test_inventory_run_and_annotations_reach_the_registered_tables(tmp_path):
    """W1-W2 over a whole inventory per weekly cycle, and W3/D1/D2 records,
    through run.py; an event joins the cycles from its first-observation date."""
    inventory = [
        {"kind": "image", "ref": "docker.io/redis:7.2"},
        {"kind": "image", "ref": "docker.io/bitnami/nginx:1.25"},
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2.11"},
        {"kind": "package", "package": "requests", "ecosystem": "PyPI", "version": "2.32.0"},
    ]
    inventories = tmp_path / "inventories.json"
    inventories.write_text(
        json.dumps(
            {
                "window": {"start": "2026-09-21", "end": "2026-10-04"},
                "inventories": {"i": inventory},
            }
        ),
        encoding="utf-8",
    )
    annotations = tmp_path / "annotations.json"
    reviews = [{"policy": "C-openpulse", "item": "x", "minutes": 4}]
    declarations = [
        {
            "event": "django-4.2-eol",
            "basis": "definitional",
            "judgements": {"a": "correct", "b": "correct"},
        }
    ]
    annotations.write_text(
        json.dumps({"timed_reviews": reviews, "completeness_declarations": declarations}),
        encoding="utf-8",
    )
    result = run.run(inventories=inventories, annotations=annotations)
    block = result["registration"]["all_labels_illustrative"]
    burden = block["reported"]["review_burden"]
    assert set(burden) == {
        "C-openpulse",
        "V-strong-conservative",
        "R-existing-representation",
        "B-conservative",
    }
    assert burden["C-openpulse"]["W1_unresolved"]["n"] == 2  # one inventory, two cycles
    assert block["guardrails"]["G4_review_burden"]["pass"] is not None
    assert block["reported"]["W3_review_minutes"]["C-openpulse"]["mean_minutes"] == 4.0
    d1 = block["reported"]["D1_completeness_declarations"]
    assert d1["per_basis"]["definitional"]["declarations"] == 1
    assert "bitnami-2025" in d1["admitted_not_judged"]
    assert block["missing_inputs"] == ["D2 mapping judgements"]
