"""The Action on pull requests: base files and trust on additions (v0.14.0 item Y3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import action_base_files as base_files  # noqa: E402

from cli.main import cli  # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")


class Api:
    """Stub contents API: path -> body; records (url, token)."""

    def __init__(self, files=None, status=None):
        self.files, self.status, self.asked = files or {}, status, []

    def __call__(self, url, token):
        self.asked.append((url, token))
        if self.status is not None:
            return self.status, None
        for path, body in self.files.items():
            if f"/contents/{path}?ref={SHA}" in url:
                return 200, body
        return 404, None


# ---------------------------------------------------------------------------
# scripts/action_base_files.py
# ---------------------------------------------------------------------------


def test_found_files_keep_their_name_and_new_files_are_new(tmp_path):
    api = Api({"app/requirements.txt": b"django==4.2\n"})
    out = base_files.fetch(
        "acme/app", SHA, tmp_path, ["./app/requirements.txt", "poetry.lock"], "t", api
    )
    (status, path, file), (status2, _, file2) = out
    assert status == "found" and Path(file).name == "requirements.txt"
    assert Path(file).read_bytes() == b"django==4.2\n"
    assert (status2, file2) == ("new", "")
    assert api.asked[0] == (
        f"https://api.github.com/repos/acme/app/contents/app/requirements.txt?ref={SHA}",
        "t",
    )


@pytest.mark.parametrize("status", [0, 403, 500])
def test_api_trouble_is_unavailable(tmp_path, status):
    out = base_files.fetch("acme/app", SHA, tmp_path, ["requirements.txt"], "", Api(status=status))
    assert out == [("unavailable", "requirements.txt", "")]


@pytest.mark.parametrize(
    ("repo", "ref", "path"),
    [
        ("acme/app\nx", SHA, "requirements.txt"),
        ("acme/app", "main", "requirements.txt"),
        ("acme/app", SHA, "../../etc/passwd"),
        ("acme/app", SHA, "/etc/passwd"),
        ("acme/app", SHA, "C:/x/requirements.txt"),
    ],
)
def test_bad_inputs_are_unavailable_and_never_requested(tmp_path, repo, ref, path):
    api = Api({"requirements.txt": b""})
    assert base_files.fetch(repo, ref, tmp_path, [path], "t", api)[0][0] == "unavailable"
    assert api.asked == []


def test_paths_are_url_quoted(tmp_path):
    api = Api()
    base_files.fetch("acme/app", SHA, tmp_path, ["dir with space/package.json"], "", api)
    assert "/contents/dir%20with%20space/package.json?" in api.asked[0][0]


def test_the_token_comes_from_the_environment_only(tmp_path, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(
        base_files, "http_get", lambda url, token: seen.append(token) or (404, None)
    )
    monkeypatch.setenv("GITHUB_TOKEN", "from-env")
    assert base_files.main(["acme/app", SHA, str(tmp_path), "requirements.txt"]) == 0
    assert capsys.readouterr().out == "new\trequirements.txt\t\n"
    assert seen == ["from-env"]


# ---------------------------------------------------------------------------
# attest --base-manifest / --base-lockfile
# ---------------------------------------------------------------------------


def _files(tmp_path, base, head):
    (tmp_path / "base").mkdir()
    base_path = tmp_path / "base" / "requirements.txt"
    head_path = tmp_path / "requirements.txt"
    base_path.write_text(base, encoding="utf-8")
    head_path.write_text(head, encoding="utf-8")
    return str(base_path), str(head_path)


def _attest(tmp_path, head, *extra):
    out = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli,
        ["attest", "--manifest", head, "--event", EVENT, "--replay", "--output", str(out)]
        + list(extra),
    )
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    return result, docs


def test_trust_runs_only_for_added_and_changed_dependencies(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(
        "core.malicious.default_query",
        lambda body: asked.append(body["package"]["name"]) or (200, {}),
    )
    base, head = _files(tmp_path, "django==4.2\nflask==3.0.0\n", "django==4.2\nflask==3.0.3\n")
    result, docs = _attest(tmp_path, head, "--trust", "--base-manifest", base)
    assert result.exit_code == 0, result.output
    assert asked == ["flask"]  # django==4.2 is unchanged
    assert "1 of 2 dependencies are added or changed" in result.output
    by_name = {d["affected_dependency"]["label"].split("==")[0]: d for d in docs}
    assert by_name["django"]["trust_assurance"] is None
    assert by_name["flask"]["trust_assurance"] is not None


def test_policy_trust_conditions_apply_to_additions_but_the_blocklist_to_all(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.malicious.default_query", lambda _body: (200, {"vulns": [{"id": "MAL-2026-1"}]})
    )
    base, head = _files(tmp_path, "django==4.2\n", "django==4.2\nflask==3.0.3\n")
    policy = tmp_path / "policy.yml"
    policy.write_text(
        "version: 1\nprohibit: [confirmed_malicious]\nblocklist: ['PyPI:django']\n",
        encoding="utf-8",
    )
    result, _ = _attest(tmp_path, head, "--base-manifest", base, "--policy", str(policy))
    assert result.exit_code == 1
    assert "PROHIBITED confirmed_malicious: PyPI:flask==3.0.3" in result.output
    assert "confirmed_malicious: PyPI:django" not in result.output
    assert "PROHIBITED blocklisted: PyPI:django==4.2" in result.output


def test_an_unreadable_base_file_is_an_error(tmp_path):
    base, head = _files(tmp_path, "not a dependency file {", "django==4.2\n")
    Path(base).rename(Path(base).with_name("weird.json"))
    weird = str(Path(base).with_name("weird.json"))
    Path(weird).write_text("{", encoding="utf-8")
    result = CliRunner().invoke(
        cli,
        ["attest", "--manifest", head, "--event", EVENT, "--replay", "--trust"]
        + ["--base-manifest", weird],
    )
    assert result.exit_code != 0 and "cannot read the base file" in result.output


def test_the_action_declares_the_new_inputs():
    import yaml

    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert action["inputs"]["trust"]["default"] == "off"
    assert action["inputs"]["policy"]["default"] == ""
    assert "pull_request.base.sha" in action["inputs"]["base-sha"]["default"]
    run = next(s for s in action["runs"]["steps"] if s.get("id") == "run")
    assert "unset IN_TOKEN" in run["run"]
    assert "${{" not in run["run"]  # inputs reach the script as env vars only
