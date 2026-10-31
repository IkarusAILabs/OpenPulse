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
        "existing_representation_baseline": "R-existing-representation",
        "burden_policies": [
            "C-openpulse",
            "V-strong-conservative",
            "R-existing-representation",
            "B-conservative",
        ],
        "review_policies": ["C-openpulse", "B-conservative"],
        "review_sample": 50,
        "min_declarations_per_basis": 10,
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


@pytest.mark.parametrize(
    "k, n, expected",
    [(0, 10, [0.0, 0.3085]), (5, 10, [0.1871, 0.8129]), (10, 10, [0.6915, 1.0]), (0, 0, None)],
)
def test_clopper_pearson_two_sided_interval(k, n, expected):
    assert reg.clopper_pearson_interval(k, n) == expected


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
        "encoding_loss": False,
    }


def _results(events=60, c_false_clears=0, independent=True):
    """Per event: two in-scope pairs and one out-of-scope pair.

    C resolves all three, except where it falsely clears; B affects the
    listed in-scope pair and abstains on the rest; R equals B; V equals C;
    A clears the second in-scope pair, which is a false clear in every event.
    """
    names = (reg.SYSTEM, reg.PRIMARY_BASELINE, reg.EXISTING, reg.STRONG, reg.NAIVE)
    rows = {name: [] for name in names}
    for e in range(events):
        ev = f"e{e}"
        cases = [(f"{ev}-1", "in_scope"), (f"{ev}-2", "in_scope"), (f"{ev}-3", "out_of_scope")]
        for i, (case, label) in enumerate(cases):
            c = AFFECTED if label == "in_scope" else CLEARED
            if e < c_false_clears and i == 1:
                c = CLEARED
            b = AFFECTED if i == 0 else UNRESOLVED
            a = AFFECTED if i == 0 else CLEARED
            pairs = ((reg.SYSTEM, c), (reg.STRONG, c), (reg.PRIMARY_BASELINE, b), (reg.EXISTING, b))
            for name, outcome in pairs:
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
    s3 = out["secondary"]["S3_C_vs_R_resolution"]
    assert s3["difference"] == pytest.approx(0.6667, abs=1e-4)
    assert s3["lower_bound_above_zero"] is True and s3["reject"] is True
    assert out["secondary"]["S3_reading"] == "no more false-clear events than R"


def test_s3_is_holm_corrected_with_s1_and_s2():
    out = reg.analyse(_results(), independent_only=True)["secondary"]
    tests = [out[k] for k in ("S1_C_vs_V_equivalence", "S2_A_vs_C_false_clears")]
    tests.append(out["S3_C_vs_R_resolution"])
    smallest = min(t["p"] for t in tests)
    assert min(t["p_holm"] for t in tests) == pytest.approx(min(1.0, 3 * smallest), abs=1e-4)


def test_s3_gain_with_more_false_clears_than_r_is_a_trade_off():
    out = reg.analyse(_results(c_false_clears=2), independent_only=True)["secondary"]
    assert out["R_false_clears"]["events_with_false_clear"] == 0
    assert out["S3_reading"].startswith("trade-off")


def test_s3_is_also_reported_on_lossless_events_only():
    rows = _results(events=10)
    for r in rows[reg.EXISTING]:
        r["encoding_loss"] = r["event"] != "e0"
    out = reg.analyse(rows, independent_only=True)["secondary"]
    lossless = out["C_vs_R_resolution_lossless_events"]
    assert (lossless["cases"], lossless["clusters"], lossless["pairs"]) == (3, 1, 3)


def test_attribution_runs_b_to_r_to_v_to_c():
    steps = reg.analyse(_results(), independent_only=True)["reported"]["attribution_B_R_V_C"]
    assert [s["step"] for s in steps] == [
        "B-conservative -> R-existing-representation",
        "R-existing-representation -> V-strong-conservative",
        "V-strong-conservative -> C-openpulse",
    ]
    assert [s["difference"] for s in steps] == [0.0, pytest.approx(0.6667, abs=1e-4), 0.0]


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


def test_missing_inputs_leave_g4_and_the_tables_empty():
    out = reg.analyse(_results(), independent_only=True)
    assert out["guardrails"]["G4_review_burden"]["pass"] is None
    assert out["reported"]["review_burden"] is None
    assert out["missing_inputs"] == [
        "W1-W2 inventory run",
        "W3 timed reviews",
        "D1 completeness judgements",
        "D2 mapping judgements",
    ]
    assert reg.analyse(_results(), True, encodings_complete=False)["valid"] is False


# --- review burden W1-W3 and G4 ----------------------------------------------------


def test_weekly_cycles_cover_the_window():
    from datetime import date

    cycles = reg.weekly_cycles(date(2026, 11, 2), date(2026, 11, 20))
    assert [c.date().isoformat() for c in cycles] == ["2026-11-08", "2026-11-15", "2026-11-22"]


def _burden():
    """Two inventories, two cycles. C leaves `x*` references unresolved, B every one."""
    from datetime import datetime, timezone

    def c(dep, events, **_):
        return {"outcome": UNRESOLVED if dep["ref"].startswith("x") else AFFECTED}

    def b(dep, events, **_):
        return {"outcome": UNRESOLVED}

    t1, t2 = (datetime(2026, 11, d, tzinfo=timezone.utc) for d in (8, 15))
    inventories = {
        "inv-1": [{"ref": "x1"}, {"ref": "y1"}],
        "inv-2": [{"ref": "x2"}, {"ref": "x3"}, {"ref": "y2"}, {"ref": "y3"}],
    }
    cycles = [(t1, {"e1": "event-1"}), (t2, {"e1": "event-1", "e2": "event-2"})]
    policies = {reg.SYSTEM: c, reg.PRIMARY_BASELINE: b}
    return reg.inventory_burden(policies, inventories, cycles)


def test_w1_and_w2_count_unresolved_references_without_labels():
    burden = _burden()
    cells = burden["W1_cells"][reg.SYSTEM]
    assert [(c["inventory"], c["count"], c["new"]) for c in cells] == [
        ("inv-1", 1, 1),
        ("inv-1", 1, 0),
        ("inv-2", 2, 2),
        ("inv-2", 2, 0),
    ]
    assert burden["W2_per_event"] == {
        reg.SYSTEM: {"e1": 3, "e2": 3},
        reg.PRIMARY_BASELINE: {"e1": 6, "e2": 6},
    }
    summary = reg.burden_summary(burden, at_risk={"e1"})
    assert summary[reg.SYSTEM]["W1_unresolved"] == {
        "n": 4,
        "median": 1.5,
        "iqr": [1.0, 2.0],
        "max": 2,
    }
    assert summary[reg.SYSTEM]["W1_share"]["median"] == 0.5
    assert summary[reg.SYSTEM]["W2_unresolved_per_event"]["n"] == 1


def test_g4_compares_median_w1_with_b():
    out = reg.analyse(_results(), independent_only=True, inputs={"burden": _burden()})
    g4 = out["guardrails"]["G4_review_burden"]
    assert (g4["C"]["median"], g4["B"]["median"], g4["pass"]) == (1.5, 3.0, True)
    swapped = _burden()
    w1 = swapped["W1_cells"]
    w1[reg.SYSTEM], w1[reg.PRIMARY_BASELINE] = w1[reg.PRIMARY_BASELINE], w1[reg.SYSTEM]
    out = reg.analyse(_results(), independent_only=True, inputs={"burden": swapped})
    assert out["guardrails"]["G4_review_burden"]["pass"] is False


def test_w3_items_are_a_seeded_draw_of_unresolved_summaries():
    burden = _burden()
    sample = reg.review_sample(burden, size=4)
    assert len(sample[reg.SYSTEM]) == 4 and len(sample[reg.PRIMARY_BASELINE]) == 4
    assert all(
        item["reference"] == 0 or item["inventory"] == "inv-2" for item in sample[reg.SYSTEM]
    )
    assert sample == reg.review_sample(burden, size=4)  # reproducible
    assert len(reg.review_sample(burden)[reg.SYSTEM]) == 6  # the whole pool when smaller


def test_w3_reports_minutes_and_implied_hours():
    reviews = [{"policy": reg.SYSTEM, "item": f"c{i}", "minutes": 6.0} for i in range(50)]
    reviews += [{"policy": reg.PRIMARY_BASELINE, "item": "b0", "minutes": 3.0}]
    burden = reg.burden_summary(_burden())
    out = reg.review_minutes(reviews, burden)
    c, b = out[reg.SYSTEM], out[reg.PRIMARY_BASELINE]
    assert (c["items"], c["mean_minutes"], c["ci95"], c["short_of_target"]) == (
        50,
        6.0,
        [6.0, 6.0],
        False,
    )
    assert c["implied_hours_per_inventory_cycle"] == 0.15  # 1.5 references x 6 minutes
    assert b["short_of_target"] is True and b["implied_hours_per_inventory_cycle"] == 0.15


# --- reliability D1-D2 -----------------------------------------------------------------


def test_d1_reports_under_inclusive_declarations_per_basis():
    agreed = {"a": "correct", "b": "correct"}
    records = [{"event": f"d{i}", "basis": "definitional", "judgements": agreed} for i in range(9)]
    records += [
        {
            "event": "u1",
            "basis": "definitional",
            "judgements": {"a": "under-inclusive", "b": "correct"},
            "adjudicated": "under-inclusive",
        },
        {
            "event": "x1",
            "basis": "announced",
            "judgements": {"a": "correct", "b": "over-inclusive"},
        },
    ]
    out = reg.completeness_declarations(records, admitted={"d0": "definitional", "zz": "announced"})
    definitional = out["per_basis"]["definitional"]
    assert definitional["under_inclusive"] == {
        "count": 1,
        "of": 10,
        "rate": 0.1,
        "ci95_exact": [0.0025, 0.445],
    }
    assert definitional["fewer_than_minimum"] is False
    assert out["per_basis"]["announced"]["declarations"] == 0  # its one record is unsettled
    assert out["per_basis"]["announced"]["fewer_than_minimum"] is True
    assert out["unadjudicated"] == ["x1"]
    assert out["admitted_not_judged"] == ["zz"]
    assert out["annotator_agreement"] == {"agreed": 9, "of": 11}
    bad = {"event": "e", "basis": "definitional", "judgements": {"a": "fine"}}
    with pytest.raises(ValueError):
        reg.completeness_declarations([bad])


def test_d2_lists_wrong_and_stale_mappings_with_their_verdicts():
    rows = _results(events=2)
    django = {"kind": "package", "package": "django", "ecosystem": "PyPI"}
    sheet = reg.identity_mappings(rows, {r["case"]: django for r in rows[reg.SYSTEM]})
    assert list(sheet) == ["package:pypi:django"]
    assert sheet["package:pypi:django"]["via"] == "catalog"
    assert len(sheet["package:pypi:django"]["verdicts"]) == 12  # 6 decisive C + 6 decisive V
    out = reg.mapping_reliability([{"mapping": "package:pypi:django", "judgement": "stale"}], sheet)
    assert out["error"]["count"] == 1 and out["error"]["ci95_exact"] == [0.025, 1.0]
    assert out["wrong_or_stale"][0]["verdicts"] == sheet["package:pypi:django"]["verdicts"]
    assert reg.mapping_reliability([], sheet)["relied_on_not_judged"] == ["package:pypi:django"]


# --- review 12: pair-level bounds, strata, deduplicated review items -------------------


def test_pair_level_false_clears_carry_both_bounds():
    rows = _results(events=10, c_false_clears=2)[reg.SYSTEM]
    out = reg.pair_false_clears(rows)
    assert (out["false_clears"], out["in_scope_pairs"], out["share"]) == (2, 20, 0.1)
    assert out["upper_one_sided_95_if_pairs_independent"] == reg.clopper_pearson_upper(2, 20)
    assert out["upper_one_sided_95_event_clustered"] >= out["share"]
    # Zero observed: the clustered bound would have zero width, so it is withheld.
    clean = reg.pair_false_clears(_results(events=10)[reg.SYSTEM])
    assert clean["upper_one_sided_95_event_clustered"] is None
    assert clean["upper_one_sided_95_if_pairs_independent"] > 0


def test_results_are_stratified_by_basis_and_identity():
    rows = _results(events=4)
    for policy_rows in rows.values():
        for r in policy_rows:
            r["basis"] = "definitional" if r["event"] in ("e0", "e1") else "partial"
            r["identity"] = "curated"
    out = reg.analyse(rows, independent_only=True)["reported"]
    assert set(out["by_completeness_basis"]) == {"definitional", "partial"}
    cell = out["by_completeness_basis"]["definitional"][reg.SYSTEM]
    assert (cell["pairs"], cell["resolution_rate"]) == (6, 1.0)
    assert set(out["by_identity_status"]) == {"curated"}


def test_burden_counts_actionable_summaries_and_unique_review_items():
    burden = _burden()
    assert burden["unique_review_items"] == {reg.SYSTEM: 3, reg.PRIMARY_BASELINE: 6}
    summary = reg.burden_summary(burden)
    assert summary[reg.SYSTEM]["W1_actionable_share"]["median"] == 0.5
    assert summary[reg.PRIMARY_BASELINE]["W1_actionable_share"]["max"] == 0.0
    assert summary[reg.SYSTEM]["W1_unique_review_items"] == 3
