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


def _ci():
    path = next(p for p in WORKFLOWS if p.name == "ci.yml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["on"] = doc.pop(True, doc.get("on"))  # YAML 1.1 reads `on` as a boolean
    return doc


def test_ci_runs_once_per_change():
    """A push to a PR branch must not start a second, identical run."""
    on = _ci()["on"]
    assert on["push"] == {"branches": ["main"]}
    assert "pull_request" in on


def test_ci_cancels_only_superseded_pull_request_runs():
    concurrency = _ci()["concurrency"]
    assert "pull_request.number" in concurrency["group"] and "github.sha" in concurrency["group"]
    assert concurrency["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"


def test_pip_cache_never_replaces_hash_checking():
    jobs = _ci()["jobs"]
    for name, job in jobs.items():
        steps = job.get("steps", [])
        if any(s.get("with", {}).get("cache") == "pip" for s in steps):
            installs = [s["run"] for s in steps if "pip install" in s.get("run", "")]
            assert installs, name
            for run in installs:
                for command in run.replace("\n", "&&").split("&&"):
                    if "pip install" in command and " -r " in command:
                        assert "--require-hashes" in command, (name, command)
