"""The research pipeline (research/scripts/): it fails closed and computes
what METRICS.md defines. Pins definitions, not results; the results are
pinned by ``reproduce.py --check`` in CI."""

import itertools
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "scripts"))

import _common  # noqa: E402,F401
import evaluate  # noqa: E402
import identity_faults  # noqa: E402
import inference  # noqa: E402
import validate_dataset  # noqa: E402

from core.entities.resolve import EXPLICIT_ALIASES, resolve_project  # noqa: E402

RETRO = _common.DATASETS["retro"]


# --- dataset validation fails closed ----------------------------------------------


def test_committed_case_sets_are_valid():
    for path in _common.DATASETS.values():
        assert validate_dataset.validate(path) == [], path


def _corrupt(tmp_path, mutate):
    data = json.loads(RETRO.read_text(encoding="utf-8"))
    mutate(data)
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / RETRO.name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path  # fixtures are unreachable from here: more problems, never fewer


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda d: d["cases"][0].update(label="probably"), "label 'probably'"),
        (lambda d: d["cases"][0].pop("rationale"), "rationale"),
        (lambda d: d["cases"][0].update(label_source=" "), "empty label_source"),
        (lambda d: d["cases"][1].update(events=["NOPE-1"]), "unknown event NOPE-1"),
        (lambda d: d["cases"][2].update(id=d["cases"][3]["id"]), "duplicate id"),
        (lambda d: d["cases"][0].update(independent_label=True), "marked independent"),
        (lambda d: d.pop("version"), "version"),
    ],
)
def test_invalid_case_sets_are_refused(tmp_path, mutate, expected):
    problems = validate_dataset.validate(_corrupt(tmp_path / "cases", mutate))
    assert any(expected in p for p in problems), problems


def test_a_changed_frozen_file_fails_its_recorded_hash(tmp_path):
    path = tmp_path / RETRO.name
    path.write_bytes(RETRO.read_bytes() + b"\n")
    shutil.copy(RETRO.with_name(RETRO.name + ".sha256"), tmp_path)
    assert any("SHA-256" in p for p in validate_dataset.validate(path))


# --- every pair has exactly one error category ---------------------------------------


def test_every_label_outcome_pair_has_one_category():
    labels = ("in_scope", "out_of_scope", "undeterminable")
    outcomes = (evaluate.AFFECTED, evaluate.CLEARED, evaluate.UNRESOLVED, evaluate.NONE)
    for label, outcome in itertools.product(labels, outcomes):
        assert evaluate.category({"label": label, "outcome": outcome}) in evaluate.CATEGORIES
    assert evaluate.category({"label": "in_scope", "outcome": "cleared"}) == "false_clear"
    # A missing representation is neither an abstention nor an error.
    row = {"label": "in_scope", "outcome": "unresolved", "encoded": False}
    assert evaluate.category(row) == evaluate.NOT_ENCODED


def test_binary_reading_never_abstains():
    def unresolved(dep, events, **kw):
        return {"outcome": evaluate.UNRESOLVED, "relationship": "RELATED"}

    original = evaluate.policies.openpulse
    evaluate.policies.openpulse = unresolved
    try:
        assert evaluate.binary({}, [])["outcome"] == evaluate.CLEARED
    finally:
        evaluate.policies.openpulse = original


def test_curated_identity_is_restored_after_the_ablation():
    before = dict(EXPLICIT_ALIASES)
    assert resolve_project("postgres:16") == "postgresql"
    with evaluate.no_curated_identity():
        assert resolve_project("postgres:16") != "postgresql"
        assert not EXPLICIT_ALIASES
    assert resolve_project("postgres:16") == "postgresql"
    assert EXPLICIT_ALIASES == before


@pytest.mark.parametrize("ref", ["postgres:16", "hashicorp/terraform:1.6.4"])
def test_injected_curated_alias_is_verified_and_then_removed(ref):
    from core.entities.identity import resolution_trust

    before = dict(EXPLICIT_ALIASES)
    with identity_faults.curated_alias(ref, identity_faults.WRONG_PROJECT):
        trust = resolution_trust(ref)
        assert (trust["slug"], trust["via"], trust["identity_status"]) == (
            identity_faults.WRONG_PROJECT,
            "explicit",
            "VERIFIED",
        )
    assert EXPLICIT_ALIASES == before


def test_identity_faults_cover_every_curated_reference():
    result = identity_faults.run(RETRO)
    cases = json.loads(RETRO.read_text(encoding="utf-8"))["cases"]
    curated = [c for c in cases if evaluate.harness._identity_status(c["dependency"]) == "curated"]
    rows = result["faults"]["misattributed"]
    assert sorted(r["case"] for r in rows) == sorted(c["id"] for c in curated)
    assert all(r["aliased_to"] == identity_faults.WRONG_PROJECT for r in rows)
    assert all(r["label"] == "out_of_scope" for r in result["faults"]["collided"])
    # Every case is either injected or counted as not injected, never dropped.
    injected = sum(b["injected"] for b in result["summary"].values())
    assert injected + sum(result["not_injected"].values()) == len(cases)


def test_disabled_comparators_are_never_complete():
    comparators = evaluate.disabled_comparators()
    assert not comparators.complete
    assert not comparators.supports("npm")
    assert all("not used" in s["error"] for s in comparators.status.values())


# --- intervals and denominators -----------------------------------------------------


def _evaluation(rows):
    pairs = [{"policy": "C-openpulse", **r} for r in rows]
    pairs += [{"policy": "A-naive", **r, "category": r.get("a", r["category"])} for r in rows]
    return {"dataset": "t", "dataset_sha256": "0", "pairs": pairs}


def test_rates_use_their_named_denominators():
    rows = [
        {"event": "e1", "label": "in_scope", "category": "correct_affected", "a": "false_clear"},
        {"event": "e1", "label": "in_scope", "category": "unresolved", "a": "false_clear"},
        {"event": "e2", "label": "out_of_scope", "category": "correct_unaffected"},
        {"event": "e2", "label": "out_of_scope", "category": "false_positive"},
        {"event": "e3", "label": "undeterminable", "category": "abstained_undeterminable"},
    ]
    out = inference.infer(_evaluation(rows), resamples=200)
    c, a = out["policies"]["C-openpulse"], out["policies"]["A-naive"]
    assert (c["false_clear_rate"]["k"], c["false_clear_rate"]["n"]) == (0, 2)
    assert (a["false_clear_rate"]["k"], a["false_clear_rate"]["n"]) == (2, 2)
    assert (c["false_positive_rate"]["k"], c["false_positive_rate"]["n"]) == (1, 2)
    assert (c["resolution_rate"]["k"], c["resolution_rate"]["n"]) == (2, 4)
    assert (c["unresolved_rate"]["k"], c["unresolved_rate"]["n"]) == (2, 5)
    assert a["events_with_false_clear"] == {
        "k": 1,
        "n": 1,
        "clopper_pearson_95": [0.025, 1.0],
        "events": ["e1"],
    }
    assert out["paired_with_C"]["A-naive"]["events_false_clear_only_here"] == 1
    assert out["clusters"]["events"] == 3


def test_sign_test_is_exact():
    assert inference.sign_test(10, 0) == round(1 / 1024, 6)
    assert inference.sign_test(1, 1) == 0.75
    assert inference.sign_test(0, 0) is None


def test_bootstrap_is_reproducible_from_its_seed():
    a = inference.ClusterBootstrap(["e1", "e2", "e3"], 50, 7).weights
    assert a == inference.ClusterBootstrap(["e1", "e2", "e3"], 50, 7).weights
    assert a != inference.ClusterBootstrap(["e1", "e2", "e3"], 50, 8).weights
