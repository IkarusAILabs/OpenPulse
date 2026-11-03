"""The track T study's star-history indicators and calibration (TR4), offline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import track_t_study as study  # noqa: E402

W0 = 1_700_000_000
WEEK, DAY = study.WEEK, study.DAY


def _history(weeks, status=200):
    return {"status": status, "weeks": weeks}


def _steady(n_weeks, per_day=1, start=W0):
    return [[start + i * WEEK, *[per_day] * 7] for i in range(n_weeks)]


def test_a_steady_history_has_low_concentration():
    values = study.indicators(_history(_steady(20)))
    assert values["SH1"] == pytest.approx(1 / 20)
    assert values["SH2"] == pytest.approx(4 / 20)
    assert values["SH3"] == 1  # the busiest day is the first; its prior days are empty


def test_a_burst_is_measured_on_all_three():
    weeks = _steady(10) + [[W0 + 10 * WEEK, 0, 0, 200, 0, 0, 0, 0]]
    values = study.indicators(_history(weeks))
    assert values["SH1"] == pytest.approx(200 / 270)
    assert values["SH2"] == pytest.approx((200 + 21) / 270)
    assert values["SH3"] == 200  # median of the 8 prior weeks is 1


def test_zero_weeks_between_recorded_weeks_count_as_zero():
    weeks = [[W0, 10, 0, 0, 0, 0, 0, 0], [W0 + 10 * WEEK, 50, 0, 0, 0, 0, 0, 0]]
    values = study.indicators(_history(weeks))
    assert values["SH2"] == pytest.approx(50 / 60)  # the two weeks are not consecutive


def test_ineligible_histories_have_no_values():
    assert study.indicators(_history(_steady(5))) is None  # 35 stars
    assert study.indicators(_history(_steady(20), status="capped")) is None
    assert study.indicators({"status": 404}) is None


def test_the_split_is_fixed_by_names_and_seed_and_halves_the_set():
    names = [f"o/r{i}" for i in range(11)]
    calibration, held_out = study.split(names)
    assert study.split(list(reversed(names))) == (calibration, held_out)
    assert len(calibration) == 5 and len(held_out) == 6
    assert not set(calibration) & set(held_out)


def test_the_threshold_lets_at_most_one_percent_fire():
    values = [float(i) for i in range(1, 251)]  # 250 values: 2 may fire
    t = study.threshold(values)
    assert t == {"threshold": 248.0, "eligible": 250, "allowed_to_fire": 2, "fire": 2}
    small = study.threshold([0.5, 0.2, 0.9])  # fewer than 100: nothing may fire
    assert small["threshold"] == 0.9 and small["fire"] == 0


def test_calibration_never_reads_a_held_out_repository(monkeypatch):
    repositories = {f"o/r{i}": _history(_steady(10 + i)) for i in range(40)}
    calibration, held_out = study.split(list(repositories))
    read = []
    real = study.indicators
    monkeypatch.setattr(study, "indicators", lambda h: read.append(id(h)) or real(h))
    result = study.calibrate({"organic": {"repositories": repositories}})
    assert sorted(read) == sorted(id(repositories[n]) for n in calibration)
    assert result["split"]["organic"]["held_out"] == held_out
    assert result["thresholds"]["SH1"]["eligible"] == 20
