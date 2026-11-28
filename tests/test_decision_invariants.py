"""Decision invariants I1-I8 (conformance/invariants.py, research/RESEARCH_PROTOCOL.md §3).

Three things are pinned: the invariants hold on generated cases; every
invariant is actually exercised (a property that is never tested cannot
fail); and each safety rule, disabled on its own, is caught by the
invariant written for it -- not by an unrelated failure.
"""

import sys
from collections import Counter
from pathlib import Path

import pytest

CONFORMANCE = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(CONFORMANCE))

import invariants  # noqa: E402
from mutation import mutated  # noqa: E402

SEEDS = (11, 12, 13)
CASES = 1500


def _violations(cases: int, seeds: tuple[int, ...]) -> tuple[Counter, Counter, list]:
    exercised, violated, examples = Counter(), Counter(), []
    for seed in seeds:
        for index, dep, specs in invariants.generate(seed, cases):
            for name, why in invariants.check_case(dep, specs, exercised):
                violated[name] += 1
                examples.append((seed, index, name, why))
    return exercised, violated, examples


def test_invariants_hold_on_generated_cases():
    exercised, violated, examples = _violations(CASES, SEEDS)
    assert not violated, examples[:5]
    # Every invariant had cases to bite on.
    assert all(exercised[name] >= 50 for name in invariants.INVARIANTS), exercised


def test_generation_is_reproducible_from_the_seed():
    first = list(invariants.generate(11, 50))
    assert first == list(invariants.generate(11, 50))
    assert first != list(invariants.generate(12, 50))


def test_heuristic_references_really_are_untrusted():
    from core.entities.identity import resolution_trust

    for repo in invariants.HEURISTIC_REPOS:
        trust = resolution_trust(f"{repo}:16")
        assert (trust["via"], trust["identity_status"]) == ("namespace_rule", "REVIEW_REQUIRED")


#: (rule disabled, module, function, old, new, the invariants that must fire)
MUTANTS = [
    (
        "unresolved identity read as unrelated (D10)",
        "core.risk.match",
        "_unresolved_identity",
        """    if UNRESOLVED_IDENTITY.get() == "unrelated":
        return None""",
        """    if True:
        return None""",
        {"I1"},
    ),
    (
        "heuristic mapping read as proof of another project (D16)",
        "core.risk.match",
        "_unresolved_identity",
        """        if trust["identity_status"] == "VERIFIED":
            return None""",
        """        if True:
            return None""",
        {"I3"},
    ),
    (
        "completeness not required for a clearance (D4, N3)",
        "core.risk.match",
        "_exclusion",
        """    if event.scope is not None and event.scope.admits_negative():
        return result""",
        """    if True:
        return result""",
        {"I2"},
    ),
    (
        "a clearance headlines over an unresolved event (D3)",
        "core.risk.check",
        "winning_cause",
        """    if str(top.get("relationship")) != "NOT_AFFECTED":
        return top""",
        """    if True:
        return top""",
        {"I4"},
    ),
    (
        "a same-named repository elsewhere excludes (misleading name match)",
        "core.risk.match",
        "_artifact_candidates",
        """        if not match_artifact(ref, candidate):
            continue""",
        """        if not match_artifact(ref, candidate):
            if split_image_ref(ref)[2] == split_image_ref(candidate)[2] and not examples:
                return {"affected": False, "via": None, "relationship": "NOT_AFFECTED",
                        "detail": "name look-alike"}
            continue""",
        {"I6"},
    ),
]


@pytest.mark.parametrize("mutant", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_each_disabled_rule_is_caught_by_its_invariant(mutant):
    _, module, function, old, new, expected = mutant
    with mutated(module, function, old, new):
        _, violated, examples = _violations(600, (11,))
    # Caught by the invariant written for this rule. The run completed, so
    # no unrelated error stands in for a detection.
    assert expected <= set(violated), (violated, examples[:3])
