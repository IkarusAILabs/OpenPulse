"""Track T measurement harness (v0.14.0 item Y1): offline, quick sample."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import trust  # noqa: E402


@pytest.fixture(scope="module")
def results():
    return trust.measure(sample=20)


def test_every_synthetic_case_gets_its_expected_status(results):
    mismatches = [r for r in results["synthetic"]["rows"] if r["observed"] != r["expected"]]
    assert mismatches == []


def test_every_check_has_positives_and_negatives(results):
    for check, stats in results["synthetic"]["per_check"].items():
        assert stats["positives"] >= 1 and stats["negatives"] >= 1, check


def test_degraded_sources_never_claim_anything(results):
    for mode, stats in results["degraded"].items():
        assert stats["claims_without_evidence"] == 0, mode
        assert stats["cases_fully_unresolved"] == stats["cases"], mode


def test_hostile_text_is_refused_and_never_echoed(results):
    echo = results["echo"]
    assert echo["refused_before_any_request"] == echo["hostile_names"]
    assert echo["echoed"] == 0 and echo["upstream_instruction_echoed"] is False


def test_the_organic_control_is_leave_one_out(results):
    npm = results["organic_lookalike"]["npm"]
    assert npm["sampled"] == 20 and npm["reference_names"] > 10000
    assert 0 <= npm["false_positive_rate_without_scope"] <= npm["false_positive_rate"] <= 1


def test_synthetic_names_stay_in_the_reserved_namespace():
    """Live-check cases use opfx- names only; lookalike cases use real names locally."""
    for case in trust.CASES:
        name = case["dep"][1]
        if case["category"] != "lookalike":
            assert name.lstrip("@").startswith("opfx"), case["id"]
    for eco, name in trust.WORLD:
        assert name.lstrip("@").startswith("opfx"), name


def test_every_policy_condition_names_a_measured_check(results):
    checks = set(results["synthetic"]["per_check"])
    for _condition, check, _status, _organic in trust.CONDITIONS:
        assert check in checks


def test_the_committed_report_matches_the_committed_results():
    """The report is generated: regenerate it, never edit it by hand."""
    committed = json.loads(trust.RESULTS.read_text(encoding="utf-8"))
    assert trust.REPORT.read_text(encoding="utf-8") == trust.render(committed)


def test_the_committed_results_are_a_full_run():
    committed = json.loads(trust.RESULTS.read_text(encoding="utf-8"))
    assert committed["organic_sample"] >= 1000
    assert all(r["observed"] == r["expected"] for r in committed["synthetic"]["rows"])
