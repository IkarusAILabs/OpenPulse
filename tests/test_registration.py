"""Registered analysis (evaluation/registration.py, REGISTRATION.md).

Pins the frozen thresholds, the statistics, and the decision rules on
synthetic results, so a change to any of them is a visible, reviewed
protocol amendment.
"""

import sys
from pathlib import Path

import pytest

EVALUATION = Path(__file__).resolve().parents[1] / "evaluation"
sys.path.insert(0, str(EVALUATION))

import registration as reg  # noqa: E402
from policies import AFFECTED, CLEARED, NONE, UNRESOLVED  # noqa: E402


def test_thresholds_are_the_registered_values():
    assert reg.thresholds() == {
        "system": "C-openpulse",
        "primary_baseline": "B-conservative",
        "delta_safety": 0.05,
        "min_events": 60,
        "min_gain": 0.10,
        "equivalence_margin": 0.05,
        "max_silent_miss": 0.02,
        "unresolved_slack": 0.05,
        "class_flag": 0.60,
        "alpha": 0.05,
        "bootstrap_resamples": 4000,
        "bootstrap_seed": 20261030,
    }


@pytest.mark.parametrize(
    "k, n, expected",
    [
        (0, 60, 0.0487),
        (0, 100, 0.0295),
        (1, 60, 0.0766),
        (1, 93, 0.05),
        (1, 95, 0.0490),
        (0, 0, None),
    ],
)
def test_clopper_pearson_upper_bound(k, n, expected):
    assert reg.clopper_pearson_upper(k, n) == expected


def test_holm_step_down():
    out = reg.holm({"a": 0.01, "b": 0.04, "c": None})
    assert out["a"] == {"p": 0.01, "p_holm": 0.02, "reject": True}
    assert out["b"] == {"p": 0.04, "p_holm": 0.04, "reject": True}
    assert out["c"]["reject"] is None


# --- synthetic results ------------------------------------------------------------


def _row(event, case, label, outcome, cls="lifecycle", independent=True):
    return {
        "event": event,
        "case": case,
        "label": label,
        "outcome": outcome,
        "class": cls,
        "independent": independent,
    }


def _results(events=60, c_false_clears=0, independent=True):
    """Per event: two in-scope pairs and one out-of-scope pair.

    C resolves all three, except where it falsely clears; B affects the
    listed in-scope pair and abstains on the rest; V equals C; A clears
    the second in-scope pair, which is a false clear in every event.
    """
    rows = {name: [] for name in (reg.SYSTEM, reg.PRIMARY_BASELINE, reg.STRONG, reg.NAIVE)}
    for e in range(events):
        ev = f"e{e}"
        cases = [(f"{ev}-1", "in_scope"), (f"{ev}-2", "in_scope"), (f"{ev}-3", "out_of_scope")]
        for i, (case, label) in enumerate(cases):
            c = AFFECTED if label == "in_scope" else CLEARED
            if e < c_false_clears and i == 1:
                c = CLEARED
            b = AFFECTED if i == 0 else UNRESOLVED
            a = AFFECTED if i == 0 else CLEARED
            for name, outcome in ((reg.SYSTEM, c), (reg.STRONG, c), (reg.PRIMARY_BASELINE, b)):
                rows[name].append(_row(ev, case, label, outcome, independent=independent))
            rows[reg.NAIVE].append(_row(ev, case, label, a, independent=independent))
    return rows


def test_primary_success_with_enough_events_and_no_false_clear():
    out = reg.analyse(_results(), independent_only=True)
    primary = out["primary"]
    assert primary["H1_safety_noninferiority"]["pass"] is True
    assert primary["H2_resolution_superiority"]["difference"] == pytest.approx(0.6667, abs=1e-4)
    assert primary["H2_resolution_superiority"]["pass"] is True
    assert primary["verdict"] == "success"
    assert out["secondary"]["S1_C_vs_V_equivalence"]["reject"] is True
    assert out["secondary"]["S2_A_vs_C_false_clears"]["reject"] is True


def test_one_false_clear_event_in_sixty_fails_the_safety_margin():
    """With delta 0.05 and 60 events, a single false-clear event already
    fails H1 (exact bound 0.0766); tolerating one needs at least 93 events."""
    out = reg.analyse(_results(c_false_clears=1), independent_only=True)
    assert out["primary"]["H1_safety_noninferiority"]["C"]["events_with_false_clear"] == 1
    assert out["primary"]["verdict"] == "failure: safety margin not met"


def test_too_few_events_is_not_decidable_never_a_pass():
    out = reg.analyse(_results(events=20), independent_only=True)
    assert out["primary"]["H1_safety_noninferiority"]["pass"] is None
    assert out["primary"]["verdict"].startswith("not decidable")


def test_registered_population_is_independent_labels_only():
    out = reg.analyse(_results(independent=False), independent_only=True)
    assert out["pairs"] == 0
    assert out["primary"]["verdict"].startswith("not decidable")


def test_guardrails_flag_silent_misses_and_excess_abstention():
    rows = _results()
    for r in rows[reg.SYSTEM][:6]:
        r["outcome"] = NONE if r["label"] == "in_scope" else UNRESOLVED
    out = reg.analyse(rows, independent_only=True)
    g = out["guardrails"]
    assert g["G1_silent_miss"]["pass"] is False and len(g["G1_silent_miss"]["cases"]) == 4
    assert g["G2_unresolved_vs_B"]["pass"] is True  # 2 of 180 unresolved, B abstains on 2/3


def test_development_set_is_not_decidable_under_the_registration():
    sys.path.insert(0, str(EVALUATION))
    import run

    result = run.run()["registration"]
    assert result["registered"]["pairs"] == 0
    assert result["registered"]["primary"]["verdict"].startswith("not decidable")
    illustrative = result["all_labels_illustrative"]
    assert illustrative["primary"]["H1_safety_noninferiority"]["C"]["events_with_false_clear"] == 0
