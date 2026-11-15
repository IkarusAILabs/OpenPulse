"""Hash-pinned lock files (#110, plan H12): invariants CI relies on."""

import importlib.metadata
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LOCKS = {
    "core": REPO / "requirements.lock",
    "runtime": REPO / "requirements-runtime.lock",
    "mcp": REPO / "requirements-mcp.lock",
    "provenance": REPO / "requirements-provenance.lock",
    "ci-tools": REPO / ".github" / "ci-tools.lock",
    "audit-tools": REPO / ".github" / "audit-tools.lock",
}
_ENTRY = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;\\]+)")

sys.path.insert(0, str(REPO / "scripts"))
import check_lock  # noqa: E402


def _entries(path):
    """name -> (version, [hashes]) for one lock file."""
    out, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _ENTRY.match(line)
        if match:
            current = check_lock._normalize(match.group(1))
            out[current] = (match.group(2), [])
        elif current and "--hash=sha256:" in line:
            out[current][1].append(line.split("--hash=sha256:")[1].split()[0])
    return out


@pytest.mark.parametrize("name", sorted(LOCKS))
def test_every_pin_carries_hashes(name):
    entries = _entries(LOCKS[name])
    assert entries, f"{name} lock is empty"
    for pkg, (_version, hashes) in entries.items():
        assert hashes, f"{name}: {pkg} has no --hash"
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes), pkg


def test_runtime_lock_is_the_core_subset_at_the_same_versions():
    core, runtime = _entries(LOCKS["core"]), _entries(LOCKS["runtime"])
    assert set(runtime) <= set(core)
    assert {k: v[0] for k, v in runtime.items()} == {k: core[k][0] for k in runtime}
    assert not {"pytest", "ruff"} & set(runtime)  # dev tools stay out of the Action


def test_extra_and_tool_locks_never_move_a_project_pin():
    core = {k: v[0] for k, v in _entries(LOCKS["core"]).items()}
    tools = {k: v[0] for k, v in _entries(LOCKS["ci-tools"]).items()}
    for name in ("mcp", "audit-tools", "provenance"):
        for pkg, (version, _hashes) in _entries(LOCKS[name]).items():
            if pkg in core:
                assert version == core[pkg], f"{name} moves {pkg}"
            if pkg in tools:
                assert version == tools[pkg], f"{name} moves tool {pkg}"


def test_core_lock_is_complete_for_typing_inspection():
    """Regression: pydantic's typing-inspection was missing and floated."""
    assert "typing-inspection" in _entries(LOCKS["core"])


def test_markers_are_evaluated_not_just_sys_platform(tmp_path):
    lock = tmp_path / "x.lock"
    lock.write_text(
        "alpha==1.0 \\\n    --hash=sha256:" + "a" * 64 + "\n"
        "beta==2.0 ; python_full_version < '3.0' \\\n    --hash=sha256:" + "b" * 64 + "\n"
        "gamma==3.0 ; sys_platform == 'no-such-os' \\\n    --hash=sha256:" + "c" * 64 + "\n",
        encoding="utf-8",
    )
    assert check_lock._read_pins(str(lock), this_platform_only=True) == {"alpha": "1.0"}
    assert set(check_lock._read_pins(str(lock))) == {"alpha", "beta", "gamma"}


def test_exact_mode_flags_installed_but_unlocked(monkeypatch, tmp_path):
    lock = tmp_path / "x.lock"
    lock.write_text("alpha==1.0 \\\n    --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8")

    class Dist:
        def __init__(self, name, version):
            self.metadata = {"Name": name}
            self.version = version

    monkeypatch.setattr(
        importlib.metadata, "distributions", lambda: [Dist("alpha", "1.0"), Dist("six", "1.17.0"),
                                                      Dist("pip", "26.2.1")]
    )
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "1.0")
    monkeypatch.chdir(REPO)  # floors are read from pyproject.toml
    problems = check_lock.check(str(lock), exact=True)
    assert "six==1.17.0 is installed but not locked" in problems
    assert not any("pip==" in p for p in problems)  # bootstrap tooling is allowed
    assert not any("alpha" in p for p in problems)


def test_the_provenance_extra_agrees_with_every_lock_it_installs_beside():
    """[provenance] installs beside core, mcp and the audit tools (T-B1)."""
    provenance = {k: v[0] for k, v in _entries(LOCKS["provenance"]).items()}
    assert "pypi-attestations" in provenance and "sigstore" in provenance
    for other in ("mcp", "audit-tools"):
        for pkg, (version, _hashes) in _entries(LOCKS[other]).items():
            if pkg in provenance:
                assert provenance[pkg] == version, f"provenance and {other} disagree on {pkg}"
