"""The Action's pre-install gate: its `gate` input (track T, T-E2, v0.15.0 item Z3)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import action_gate  # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"
MAL = {"vulns": [{"id": "MAL-2026-0042"}]}
BLOCK_DJANGO = b"version: 1\nblocklist: ['PyPI:django']\n"
PROHIBIT_MALICIOUS = "version: 1\nprohibit: [confirmed_malicious]\n"


class Api:
    """Stub contents API: path -> body; records the paths asked for."""

    def __init__(self, files=None, status=None):
        self.files, self.status, self.asked = files or {}, status, []

    def __call__(self, url, token):
        path = url.split("/contents/", 1)[1].split("?", 1)[0]
        self.asked.append(path)
        if self.status is not None:
            return self.status, None
        return (200, self.files[path]) if path in self.files else (404, None)


@pytest.fixture
def work(tmp_path, monkeypatch):
    """A checkout with requirements.txt and a policy prohibiting malicious packages."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".openpulse").mkdir()
    (tmp_path / ".openpulse" / "policy.yml").write_text(PROHIBIT_MALICIOUS, encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("django==4.2\nevil-pkg==1.0\n", encoding="utf-8")
    return tmp_path


def _osv(monkeypatch, *bad):
    asked = []

    def query(body):
        asked.append(body["package"]["name"])
        return (200, MAL) if body["package"]["name"] in bad else (200, {})

    monkeypatch.setattr("core.malicious.default_query", query)
    return asked


def _run(tmp_path, api=None, base_sha=SHA, files=("requirements.txt",), policy=""):
    return action_gate.run(
        list(files),
        repo="acme/app",
        base_sha=base_sha,
        policy=policy,
        token="t",
        out_dir=str(tmp_path / "base"),
        get=api or Api(),
    )


# ---------------------------------------------------------------------------
# Pull requests: the base branch's copies and settings
# ---------------------------------------------------------------------------


def test_only_additions_are_checked_against_the_base_copy(work, monkeypatch):
    asked = _osv(monkeypatch, "evil-pkg")
    api = Api({"requirements.txt": b"django==4.2\n"})
    assert _run(work, api) == (0, True)
    assert asked == ["evil-pkg"]
    assert api.asked == [
        "requirements.txt",
        ".openpulse/policy.yml",
        ".openpulse/private-packages.txt",
    ]


def test_a_clean_pull_request_passes(work, monkeypatch):
    _osv(monkeypatch)
    api = Api({"requirements.txt": b"django==4.2\n"})
    assert _run(work, api) == (0, False)


def test_a_file_new_in_the_pull_request_is_checked_in_full(work, monkeypatch):
    asked = _osv(monkeypatch)
    assert _run(work, Api()) == (0, False)
    assert sorted(asked) == ["django", "evil-pkg"]


def test_an_unreadable_base_copy_never_narrows_the_checks(work, monkeypatch, capsys):
    asked = _osv(monkeypatch, "evil-pkg")
    assert _run(work, Api(status=500)) == (0, True)
    assert sorted(asked) == ["django", "evil-pkg"]
    assert "checking every dependency" in capsys.readouterr().out


def test_the_base_branch_policy_wins_over_the_pull_requests(work, monkeypatch, capsys):
    # The pull request weakens its policy to nothing; the base branch blocks django.
    (work / ".openpulse" / "policy.yml").write_text("version: 1\n", encoding="utf-8")
    api = Api({"requirements.txt": b"django==4.2\n", ".openpulse/policy.yml": BLOCK_DJANGO})
    assert _run(work, api) == (0, True)
    captured = capsys.readouterr()
    out = captured.out + captured.err
    assert "using the base branch's trust policy" in out
    assert "PROHIBITED blocklisted: PyPI:django==4.2" in out


def test_a_policy_deleted_by_the_pull_request_still_applies(work, monkeypatch):
    (work / ".openpulse" / "policy.yml").unlink()
    api = Api({"requirements.txt": b"django==4.2\n", ".openpulse/policy.yml": BLOCK_DJANGO})
    assert _run(work, api) == (0, True)


def test_the_base_branch_private_list_is_used(work, monkeypatch):
    _osv(monkeypatch)
    api = Api(
        {
            "requirements.txt": b"django==4.2\n",
            ".openpulse/private-packages.txt": b"PyPI:acme-internal\n",
        }
    )
    seen = []
    monkeypatch.setattr(action_gate, "_gate", lambda args: seen.append(args) or 0)
    assert _run(work, api) == (0, False)
    (args,) = seen
    private = args[args.index("--private-names") + 1]
    assert Path(private).read_text(encoding="utf-8") == "PyPI:acme-internal\n"


def test_a_policy_outside_the_repository_is_not_looked_up(work, monkeypatch, tmp_path_factory):
    _osv(monkeypatch)
    outside = tmp_path_factory.mktemp("policy") / "policy.yml"
    outside.write_bytes(BLOCK_DJANGO)
    api = Api({"requirements.txt": b"django==4.2\n"})
    assert _run(work, api, policy=str(outside)) == (0, True)
    assert api.asked == ["requirements.txt", ".openpulse/private-packages.txt"]


# ---------------------------------------------------------------------------
# Outside pull requests, and errors
# ---------------------------------------------------------------------------


def test_without_a_base_commit_every_dependency_is_checked(work, monkeypatch):
    asked = _osv(monkeypatch, "evil-pkg")
    api = Api()
    assert _run(work, api, base_sha="") == (0, True)
    assert sorted(asked) == ["django", "evil-pkg"] and api.asked == []


def test_without_a_policy_the_gate_passes(work, monkeypatch):
    (work / ".openpulse" / "policy.yml").unlink()
    assert _run(work, base_sha="") == (0, False)


def test_an_empty_gate_input_is_a_usage_error(work):
    assert _run(work, files=()) == (2, False)


def test_a_missing_policy_file_is_a_usage_error(work):
    assert _run(work, base_sha="", policy="no-such-policy.yml")[0] == 2


def test_main_writes_the_output_and_keeps_the_token_from_the_lookups(work, monkeypatch):
    output = work / "github_output"
    monkeypatch.setenv("IN_GATE", "requirements.txt")
    monkeypatch.setenv("IN_BASE_SHA", "")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_TOKEN", "job-token")
    monkeypatch.setenv("RUNNER_TEMP", str(work))
    seen = []

    def gate(args):
        import os

        seen.append(os.environ.get("GITHUB_TOKEN"))
        return 1

    monkeypatch.setattr(action_gate, "_gate", gate)
    assert action_gate.main() == 0
    assert output.read_text(encoding="utf-8") == "threshold-breached=true\n"
    assert seen == [None]


# ---------------------------------------------------------------------------
# action.yml wiring
# ---------------------------------------------------------------------------


def _action():
    return yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))


def test_the_gate_input_runs_only_the_gate():
    action = _action()
    assert action["inputs"]["gate"]["default"] == ""
    steps = {s.get("id") or s.get("name"): s for s in action["runs"]["steps"]}
    assert steps["gate"]["if"] == "inputs.gate != ''"
    assert steps["run"]["if"] == "inputs.gate == ''"
    assert "action_gate.py" in steps["gate"]["run"]
    upload = next(s for s in action["runs"]["steps"] if "upload-sarif" in s.get("uses", ""))
    assert "inputs.gate == ''" in upload["if"]
    assert steps["Enforce the gate"]["if"] == "steps.gate.outputs.threshold-breached == 'true'"
    assert "steps.gate.outputs.threshold-breached" in (
        action["outputs"]["threshold-breached"]["value"]
    )


def test_gate_inputs_reach_the_script_as_environment_only():
    step = next(s for s in _action()["runs"]["steps"] if s.get("id") == "gate")
    assert "${{" not in step["run"]
    assert step["env"]["IN_GATE"] == "${{ inputs.gate }}"
    assert step["env"]["IN_BASE_SHA"] == "${{ inputs.base-sha }}"
