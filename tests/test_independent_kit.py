"""Independent-oracle kit (conformance/independent/, ROADMAP R-B7).

The kit is handed to an outside author, so its validator must fail
closed, its vocabulary must match the curated catalog, and the team-side
comparison must agree with itself before anyone else's oracle is run.
"""

import json
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1] / "conformance" / "independent"
sys.path.insert(0, str(KIT))

import kit  # noqa: E402


def _examples():
    return kit._read_jsonl(KIT / "examples.jsonl")


def test_examples_are_valid_and_every_source_agrees():
    cases = _examples()
    assert [p for c in cases for p in kit.validate_case(c)] == []
    result = kit.compare(cases)
    assert result["disagreements"] == []
    assert result["judgement_vs_rules"] == []
    assert len(result["spec_sha256"]) == 64


def test_vocabulary_matches_the_curated_catalog():
    vocabulary = json.loads((KIT / "vocabulary.json").read_text("utf-8"))
    for ref, owner in vocabulary["image_repositories"].items():
        assert kit._curated_project({"kind": "image", "ref": ref}) == owner, ref
    for name, owner in vocabulary["packages"].items():
        assert kit._curated_project({"kind": "package", "package": name}) == owner, name


def _case(**overrides):
    case = json.loads(json.dumps(_examples()[0]))
    case.update(overrides)
    return case


@pytest.mark.parametrize(
    "overrides, fragment",
    [
        ({"belongs_to": "mysql"}, "curated catalog says"),
        ({"surprise": 1}, "unknown field"),
        ({"events": []}, "non-empty list"),
        ({"dependency": {"kind": "vm"}}, "dependency must be"),
    ],
)
def test_validator_fails_closed(overrides, fragment):
    assert any(fragment in p for p in kit.validate_case(_case(**overrides)))


def test_validator_rejects_bad_events_and_expectations():
    case = _case()
    case["events"][0]["completeness"] = "partial"  # with a basis still set
    assert any("partial scope has no basis" in p for p in kit.validate_case(case))
    case = _case()
    case["expected"] = {"per_event": {"e1": "MAYBE"}, "summary": "affected"}
    problems = kit.validate_case(case)
    assert any("not in" in p for p in problems)
    assert any("rationale is required" in p for p in problems)


def test_export_is_seeded_and_the_team_sources_agree():
    first, again = kit.export_cases(400, 5), kit.export_cases(400, 5)
    assert first == again
    assert [p for c in first for p in kit.validate_case(c)] == []
    result = kit.compare(first)
    assert result["agreement"]["team_oracle vs implementation"] == {
        "summary agree": 400,
        "per-event agree": 400,
    }


def test_an_independent_disagreement_is_reported():
    cases = _examples()
    wrong = {c["id"]: kit.team_oracle(c) for c in cases}
    wrong["ex-1"] = {"per_event": {"e1": "NOT_AFFECTED"}, "summary": "cleared"}
    result = kit.compare(cases, wrong)
    flagged = [d for d in result["disagreements"] if d["id"] == "ex-1"]
    assert {tuple(d["between"]) for d in flagged} >= {("expected", "independent")}
    assert any(d["severity"] == "unsafe" for d in flagged)


def test_judgement_that_contradicts_the_rules_is_surfaced():
    case = _case()
    case["expected"] = dict(case["expected"], judgement="out_of_scope")
    result = kit.compare([case])
    assert [r["id"] for r in result["judgement_vs_rules"]] == ["ex-1"]


def test_cli_validate_and_compare(tmp_path, capsys):
    assert kit.main(["validate", str(KIT / "examples.jsonl")]) == 0
    out = tmp_path / "report.json"
    assert kit.main(["compare", "--cases", str(KIT / "examples.jsonl"), "--out", str(out)]) == 0
    assert json.loads(out.read_text("utf-8"))["cases"] == 3
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps(_case(belongs_to="mysql")) + "\n", encoding="utf-8")
    assert kit.main(["validate", str(bad)]) == 1
