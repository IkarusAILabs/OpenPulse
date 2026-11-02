"""Gate bypass routes (track T evaluation category 8, v0.14.0 item Y5).

Each test is one route an attacker or a careless agent could take past the
trust gate. A route the gate covers asserts that it fails the run; a route
it cannot cover asserts the documented limit, so the limit cannot change
silently. The routes and their status are listed in docs/TRUST_POLICY.md,
"Bypass routes".
"""

from __future__ import annotations

from pathlib import Path

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
