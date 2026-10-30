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
    assert full["silent_miss_rate"] == 0.0 < ablated["silent_miss_rate"]
