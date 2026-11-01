from pathlib import Path

import pytest
import yaml

from core.risk.check import DependencyVerdict, fail_on_threshold

WORKFLOWS = sorted((Path(__file__).resolve().parents[1] / ".github" / "workflows").glob("*.yml"))


def verdict(affected, *impacts):
    return DependencyVerdict(
        dependency="x",
        affected=affected,
        relationship="AFFECTS_VERSION" if affected else "UNKNOWN",
        verdicts=[{"affected": True, "impact": impact} for impact in impacts],
    )


def test_fail_on_affected():
    assert fail_on_threshold([verdict(True, "WATCH")], "affected")
    assert not fail_on_threshold([verdict(False, "CRITICAL")], "affected")


def test_fail_on_review_includes_action_and_critical():
    assert fail_on_threshold([verdict(True, "REVIEW")], "review")
    assert fail_on_threshold([verdict(True, "ACTION")], "review")
    assert fail_on_threshold([verdict(True, "CRITICAL")], "review")


def test_fail_on_action_preserves_strict_semantics():
    assert not fail_on_threshold([verdict(True, "REVIEW")], "action")
    assert fail_on_threshold([verdict(True, "ACTION")], "action")


def test_fail_on_critical_is_narrowest():
    assert not fail_on_threshold([verdict(True, "ACTION")], "critical")
    assert fail_on_threshold([verdict(True, "CRITICAL")], "critical")


def _checkouts(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for name, job in doc["jobs"].items():
        for step in job.get("steps", []):
            if step.get("uses", "").startswith("actions/checkout@"):
                yield name, step


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_every_checkout_drops_the_job_token(workflow):
    """#141: no checkout leaves GITHUB_TOKEN in .git/config for later steps."""
    for job, step in _checkouts(workflow):
        assert (step.get("with") or {}).get("persist-credentials") is False, (
            f"{workflow.name}: job {job!r} checks out without persist-credentials: false"
        )


def test_the_policy_test_sees_the_workflows():
    assert {p.name for p in WORKFLOWS} >= {"ci.yml", "release.yml"}
    assert sum(1 for p in WORKFLOWS for _ in _checkouts(p)) >= 5
