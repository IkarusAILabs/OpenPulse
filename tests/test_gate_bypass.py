"""Gate bypass routes (track T evaluation category 8, v0.14.0 item Y5;
pre-install routes v0.15.0 item Z4).

Each test is one route an attacker or a careless agent could take past the
trust gate. A route the gate covers asserts that it fails the run; a route
it cannot cover asserts the documented limit, so the limit cannot change
silently. The routes and their status are listed in docs/TRUST_POLICY.md,
"Bypass routes".
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli
from core.agent_tools import Lookups, dependency_status

ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")
SHA_GOOD, SHA_EVIL = "a" * 64, "e" * 64
MAL = {"vulns": [{"id": "MAL-2026-0042"}]}


def _osv_flags(*names):
    """Stub OSV: a MAL- record for the named packages, nothing for the rest."""
    asked = []

    def query(body):
        asked.append(body["package"]["name"])
        return (200, MAL) if body["package"]["name"] in names else (200, {})

    query.asked = asked
    return query


def _poetry(*packages):
    blocks = []
    for name, version, sha in packages:
        blocks.append(
            f'[[package]]\nname = "{name}"\nversion = "{version}"\n'
            f'files = [{{file = "{name}-{version}-py3-none-any.whl", hash = "sha256:{sha}"}}]\n'
        )
    return 'lock-version = "2.1"\n\n' + "\n".join(blocks)


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def _policy(tmp_path, doc):
    return _write(tmp_path / "policy.yml", yaml.safe_dump(doc))


def _attest(*args):
    return CliRunner().invoke(cli, ["attest", "--event", EVENT, "--replay", *args])


# ---------------------------------------------------------------------------
# Routes the gate covers
# ---------------------------------------------------------------------------


def test_a_dependency_added_only_to_the_lockfile_is_checked(tmp_path, monkeypatch):
    osv = _osv_flags("evil-helper")
    monkeypatch.setattr("core.malicious.default_query", osv)
    base = _write(tmp_path / "base/poetry.lock", _poetry(("django", "4.2", SHA_GOOD)))
    head = _write(
        tmp_path / "poetry.lock",
        _poetry(("django", "4.2", SHA_GOOD), ("evil-helper", "0.1", SHA_GOOD)),
    )
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["confirmed_malicious"]})
    result = _attest("--lockfile", head, "--base-lockfile", base, "--policy", policy)
    assert result.exit_code == 1
    assert "PROHIBITED confirmed_malicious: PyPI:evil-helper==0.1" in result.output
    assert osv.asked == ["evil-helper"]  # the unchanged entry is not re-asked


def test_a_hash_edited_in_place_is_checked(tmp_path, monkeypatch):
    """Same name and version, a different artifact: not an "added" dependency,
    but its locked digest changed, so the digest check must still run."""
    published = {
        "urls": [{"filename": "django-4.2-py3-none-any.whl", "digests": {"sha256": SHA_GOOD}}]
    }
    monkeypatch.setattr("core.digest_integrity.default_fetch", lambda _url: (200, published))
    base = _write(tmp_path / "base/poetry.lock", _poetry(("django", "4.2", SHA_GOOD)))
    head = _write(tmp_path / "poetry.lock", _poetry(("django", "4.2", SHA_EVIL)))
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["digest_mismatch"]})
    result = _attest("--lockfile", head, "--base-lockfile", base, "--policy", policy)
    assert result.exit_code == 1, result.output
    assert "PROHIBITED digest_mismatch: PyPI:django==4.2" in result.output


def test_an_unchanged_lockfile_entry_is_not_rechecked(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(
        "core.digest_integrity.default_fetch", lambda url: asked.append(url) or (404, None)
    )
    lock = _poetry(("django", "4.2", SHA_GOOD))
    base = _write(tmp_path / "base/poetry.lock", lock)
    head = _write(tmp_path / "poetry.lock", lock)
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["digest_mismatch"]})
    assert _attest("--lockfile", head, "--base-lockfile", base, "--policy", policy).exit_code == 0
    assert asked == []


def test_a_respelled_blocklisted_name_is_caught(tmp_path):
    head = _write(tmp_path / "requirements.txt", "Evil_Pkg==1.0\n")
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    result = _attest("--manifest", head, "--policy", policy)
    assert result.exit_code == 1 and "PROHIBITED blocklisted" in result.output


def test_an_agent_ignoring_the_mcp_warning_is_stopped_in_ci(tmp_path, monkeypatch):
    """The agent is told; it adds the package anyway; CI fails without any model."""
    osv = _osv_flags("evil-pkg")
    told = dependency_status(
        "evil-pkg",
        "1.0",
        "PyPI",
        lookups=Lookups(
            fetch=lambda _s: {"endoflife": [], "osv": [], "github_meta": []}, osv_query=osv
        ),
    )
    assert told["trust"]["attention"][0]["status"] == "CONFIRMED_MALICIOUS"
    monkeypatch.setattr("core.malicious.default_query", osv)
    head = _write(tmp_path / "requirements.txt", "django==4.2\nevil-pkg==1.0\n")
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["confirmed_malicious"]})
    assert _attest("--manifest", head, "--policy", policy).exit_code == 1


def test_the_action_reads_the_gate_settings_from_the_base_branch():
    """A pull request must not weaken its own gate by editing the policy."""
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    run = next(s for s in action["runs"]["steps"] if s.get("id") == "run")["run"]
    assert "roles+=(policy private)" in run
    assert run.index('policy=(--policy "$base_policy")') < run.index(
        'policy=(--policy "$IN_POLICY")'
    )
    assert 'trust+=(--private-names "$base_private")' in run


# ---------------------------------------------------------------------------
# Routes the gate cannot cover (documented limits, pinned here)
# ---------------------------------------------------------------------------


def test_limit_unpinned_entries_are_skipped_not_checked(tmp_path, monkeypatch):
    osv = _osv_flags("evil-pkg")
    monkeypatch.setattr("core.malicious.default_query", osv)
    head = _write(tmp_path / "requirements.txt", "django==4.2\nevil-pkg>=1.0\n")
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["confirmed_malicious"]})
    result = _attest("--manifest", head, "--policy", policy, "--trust")
    assert result.exit_code == 0
    assert "evil-pkg" not in osv.asked  # unpinned: nothing to check; pin or use a lockfile


def test_limit_a_pinned_blocklist_entry_misses_other_versions(tmp_path):
    head = _write(tmp_path / "requirements.txt", "flask==3.0.1\n")
    pinned = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:flask==3.0.0"]})
    assert _attest("--manifest", head, "--policy", pinned).exit_code == 0
    every = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:flask"]})
    assert _attest("--manifest", head, "--policy", every).exit_code == 1


def test_limit_unreachable_sources_never_block(tmp_path, monkeypatch):
    """Silence is NOT_PERFORMED, never a prohibited status (by design)."""
    monkeypatch.setattr("core.malicious.default_query", lambda _body: (0, None))
    head = _write(tmp_path / "requirements.txt", "evil-pkg==1.0\n")
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["confirmed_malicious"]})
    assert _attest("--manifest", head, "--policy", policy).exit_code == 0


def test_limit_a_dependency_outside_the_files_is_invisible(tmp_path):
    """`pip install evil-pkg` in a build script never reaches the gate's inputs."""
    head = _write(tmp_path / "requirements.txt", "django==4.2\n")
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    assert _attest("--manifest", head, "--policy", policy).exit_code == 0


# ---------------------------------------------------------------------------
# Pre-install routes (v0.15.0 item Z4): around the pre-commit hook and the
# CI gate before install
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _hook_files() -> str:
    hooks = yaml.safe_load((ROOT / ".pre-commit-hooks.yaml").read_text(encoding="utf-8"))
    return next(h for h in hooks if h["id"] == "openpulse-gate")["files"]


def _gate(*args):
    return CliRunner().invoke(cli, ["gate", *args])


def _pypi_digests(**published):
    """Stub PyPI's release JSON: the wheel digest per package, 404 for the rest."""

    def fetch(url):
        name = url.split("/pypi/", 1)[1].split("/", 1)[0]
        if name not in published:
            return 404, None
        files = [
            {"filename": f"{name}-4.2-py3-none-any.whl", "digests": {"sha256": published[name]}}
        ]
        return 200, {"urls": files}

    return fetch


def test_the_gate_checks_a_hash_edited_in_place_whatever_the_policy_says(tmp_path, monkeypatch):
    """G3 (decision 14): a policy that forgot digest_mismatch still fails the edit."""
    monkeypatch.setattr("core.digest_integrity.default_fetch", _pypi_digests(django=SHA_GOOD))
    base = _write(tmp_path / "base/poetry.lock", _poetry(("django", "4.2", SHA_GOOD)))
    head = _write(tmp_path / "poetry.lock", _poetry(("django", "4.2", SHA_EVIL)))
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    result = _gate(head, "--base", base, "--policy", policy)
    assert result.exit_code == 1, result.output
    assert "PROHIBITED digest_mismatch: PyPI:django==4.2" in result.output
    assert "digest_mismatch is implied by the gate" in result.output


def test_the_gate_fails_closed_when_an_implied_digest_check_cannot_run(tmp_path, monkeypatch):
    monkeypatch.setattr("core.digest_integrity.default_fetch", lambda _url: (0, None))
    base = _write(tmp_path / "base/poetry.lock", _poetry(("django", "4.2", SHA_GOOD)))
    head = _write(tmp_path / "poetry.lock", _poetry(("django", "4.2", SHA_EVIL)))
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    assert _gate(head, "--base", base, "--policy", policy).exit_code == 1
    relaxed = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"], "unchecked": "pass"})
    assert _gate(head, "--base", base, "--policy", relaxed).exit_code == 0


def test_check_and_attest_keep_digest_mismatch_as_written(tmp_path, monkeypatch):
    """Only the gate implies the rule; attest enforces the policy it is given."""
    asked = []
    monkeypatch.setattr(
        "core.digest_integrity.default_fetch", lambda url: asked.append(url) or (404, None)
    )
    base = _write(tmp_path / "base/poetry.lock", _poetry(("django", "4.2", SHA_GOOD)))
    head = _write(tmp_path / "poetry.lock", _poetry(("django", "4.2", SHA_EVIL)))
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    result = _attest("--lockfile", head, "--base-lockfile", base, "--policy", policy)
    assert result.exit_code == 0, result.output
    assert asked == []


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_a_commit_made_with_no_verify_is_caught_by_the_ci_gate(tmp_path, monkeypatch):
    """`git commit --no-verify` skips the hook; the CI gate compares with the base."""
    monkeypatch.setattr("core.malicious.default_query", _osv_flags("evil-pkg"))
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "bypass@example.invalid")
    _git(tmp_path, "config", "user.name", "bypass test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    _write(tmp_path / "requirements.txt", "django==4.2\n")
    _git(tmp_path, "add", "requirements.txt")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "branch", "base")
    _write(tmp_path / "requirements.txt", "django==4.2\nevil-pkg==1.0\n")
    _git(tmp_path, "commit", "-q", "--no-verify", "-am", "skip the hook")
    policy = _policy(tmp_path, {"version": 1, "prohibit": ["confirmed_malicious"]})
    monkeypatch.chdir(tmp_path)
    # The hook's comparison (HEAD) now sees nothing new; the CI gate's (the base) does.
    assert _gate("requirements.txt", "--base-ref", "HEAD", "--policy", policy).exit_code == 0
    result = _gate("requirements.txt", "--base-ref", "base", "--policy", policy)
    assert result.exit_code == 1
    assert "PROHIBITED confirmed_malicious: PyPI:evil-pkg==1.0" in result.output


def test_the_hook_selects_every_requirements_variant_at_the_top_of_a_directory():
    for name in ("requirements.txt", "requirements-dev.txt", "api/requirements_test.txt"):
        assert re.search(_hook_files(), name), name


def test_limit_the_hook_misses_dependency_files_with_other_names():
    """Names outside the hook's pattern are not gated at commit: widen `files:`."""
    for name in ("requirements/base.txt", "constraints.txt", "deps/prod.txt"):
        assert not re.search(_hook_files(), name), name


def test_limit_a_lockfile_regenerated_after_the_gate_is_not_the_gated_one(tmp_path, monkeypatch):
    """The gate judges the file as it is when the gate runs, nothing later."""
    monkeypatch.setattr("core.digest_integrity.default_fetch", _pypi_digests(django=SHA_GOOD))
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    lock = tmp_path / "poetry.lock"
    _write(lock, _poetry(("django", "4.2", SHA_GOOD)))
    assert _gate(str(lock), "--policy", policy).exit_code == 0
    # A later `poetry lock` / `npm install` rewrites the file the install reads.
    _write(lock, _poetry(("django", "4.2", SHA_GOOD), ("evil-pkg", "1.0", SHA_EVIL)))
    assert _gate(str(lock), "--policy", policy).exit_code == 1  # only a re-run sees it


def test_limit_an_install_from_an_ungated_file_is_invisible(tmp_path):
    """Gating requirements.txt says nothing about `pip install -r requirements-dev.txt`."""
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    gated = _write(tmp_path / "requirements.txt", "django==4.2\n")
    ungated = _write(tmp_path / "requirements-dev.txt", "evil-pkg==1.0\n")
    assert _gate(gated, "--policy", policy).exit_code == 0
    assert _gate(gated, ungated, "--policy", policy).exit_code == 1  # gate every file


def test_a_lockfile_regenerated_after_the_gate_is_refused_before_install(tmp_path, monkeypatch):
    """v0.17.0 G2/G4: the receipt names the gated bytes; the regenerated file differs."""
    monkeypatch.setattr("core.digest_integrity.default_fetch", _pypi_digests(django=SHA_GOOD))
    monkeypatch.chdir(tmp_path)
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    _write(tmp_path / "poetry.lock", _poetry(("django", "4.2", SHA_GOOD)))
    assert _gate("poetry.lock", "--policy", policy, "--receipt", "r.json").exit_code == 0
    _write(tmp_path / "poetry.lock", _poetry(("django", "4.2", SHA_GOOD), ("evil", "1", SHA_EVIL)))
    result = _gate("--verify-receipt", "r.json", "--require-receipt-for", "poetry.lock")
    assert result.exit_code == 1 and "changed since the gate" in result.output


def test_a_dependency_file_generated_after_the_gate_is_refused_before_install(
    tmp_path, monkeypatch
):
    """v0.17.0 G4: nobody named it to the install step; the pattern finds it."""
    monkeypatch.chdir(tmp_path)
    policy = _policy(tmp_path, {"version": 1, "blocklist": ["PyPI:evil-pkg"]})
    _write(tmp_path / "requirements.txt", "django==4.2\n")
    assert _gate("requirements.txt", "--policy", policy, "--receipt", "r.json").exit_code == 0
    _write(tmp_path / "web" / "package-lock.json", '{"lockfileVersion": 3, "packages": {}}')
    result = _gate(
        "--verify-receipt",
        "r.json",
        "--require-receipt-for",
        "**/package-lock.json",
        "requirements.txt",
    )
    assert result.exit_code == 1 and "web/package-lock.json: not in the receipt" in result.output
