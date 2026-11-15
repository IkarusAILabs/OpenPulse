"""Release workflow guards (v0.10.0 item V1, #111)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml

from core.version import FALLBACK_VERSION
from scripts import build_release

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "release.yml"


@pytest.fixture(scope="module")
def workflow():
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    doc["on"] = doc.pop(True, doc.get("on"))  # YAML 1.1 reads `on` as a boolean
    return doc


def test_runs_only_on_version_tags(workflow):
    assert workflow["on"] == {"push": {"tags": ["v*"]}}


def test_permissions_are_per_job_and_minimal(workflow):
    assert workflow["permissions"] == {}
    jobs = workflow["jobs"]
    assert jobs["build"]["permissions"] == {"contents": "read"}
    assert jobs["attest"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
        "attestations": "write",
    }
    assert jobs["publish"]["permissions"] == {"contents": "write"}
    assert jobs["attest"]["needs"] == "build"
    assert set(jobs["publish"]["needs"]) == {"build", "attest"}


def test_every_action_is_pinned_by_commit_sha(workflow):
    uses = [s["uses"] for job in workflow["jobs"].values() for s in job["steps"] if "uses" in s]
    assert uses
    for ref in uses:
        assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", ref), ref
    text = WORKFLOW.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "uses:" in line:
            assert re.search(r"# v\d", line), f"pinned action without its version comment: {line}"


def test_attests_every_file_and_never_replaces_or_publishes_elsewhere(workflow):
    steps = [s for job in workflow["jobs"].values() for s in job["steps"]]
    provenance = [
        s for s in steps if s.get("uses", "").startswith("actions/attest-build-provenance@")
    ]
    assert provenance and provenance[0]["with"]["subject-path"] == "dist/*"
    commands = "\n".join(s.get("run", "") for s in steps)
    assert "--clobber" not in commands  # a re-run never swaps attested files
    assert "pypi" not in commands.lower() and "twine" not in commands  # decision 7 is open
    assert "--require-hashes -r .github/ci-tools.lock" in commands
    checkouts = [s for s in steps if s.get("uses", "").startswith("actions/checkout@")]
    assert all(s["with"]["persist-credentials"] is False for s in checkouts)


def test_tag_must_match_the_package_version():
    assert build_release.check(f"v{FALLBACK_VERSION}") == FALLBACK_VERSION
    with pytest.raises(SystemExit, match="does not match"):
        build_release.check("v99.0.0")
    with pytest.raises(SystemExit, match="does not match"):
        build_release.check(FALLBACK_VERSION)  # no leading v


def test_locked_setuptools_satisfies_the_build_floor():
    """Dependabot raised the floor to 84.2.1 while CI kept 84.1.0; never again."""
    floor = build_release.build_floor()
    locked = build_release.locked_setuptools()
    assert build_release._version_tuple(locked) >= build_release._version_tuple(floor)


def test_a_lock_below_the_build_floor_is_refused(tmp_path):
    (tmp_path / ".github").mkdir()
    shutil.copy(REPO / "pyproject.toml", tmp_path / "pyproject.toml")
    (tmp_path / ".github" / "ci-tools.lock").write_text(
        "setuptools==1.0 \\\n    --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="below the build floor"):
        build_release.check(f"v{FALLBACK_VERSION}", root=tmp_path)
