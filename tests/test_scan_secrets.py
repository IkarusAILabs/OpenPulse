"""scripts/scan_secrets.py: what the CI secret tripwire walks and skips (#142)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.scan_secrets import scan

# Assembled at runtime so this file never trips the tripwire itself.
TOKEN = "gh" + "p_" + "A1b2C3d4" * 3
REPO = Path(__file__).resolve().parents[1]


def _plant(root: Path, rel: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"token = '{TOKEN}'\n", encoding="utf-8")


def _hits(root: Path) -> set[str]:
    return {Path(hit.rsplit(":", 1)[0]).relative_to(root).as_posix() for hit in scan(root)}


def test_only_the_canonical_scanner_is_skipped(tmp_path):
    _plant(tmp_path, "scripts/scan_secrets.py")
    _plant(tmp_path, "other/scan_secrets.py")
    assert _hits(tmp_path) == {"other/scan_secrets.py"}


@pytest.mark.parametrize(
    "rel",
    [
        ".venv/lib/python3.11/site-packages/cryptography/fixture.py",
        "venv/lib/x.py",
        "env/lib/x.py",
        "build-tools/lib/python3.11/site-packages/pkg/key.py",
    ],
)
def test_virtualenvs_are_not_scanned(tmp_path, rel):
    _plant(tmp_path, rel)
    assert _hits(tmp_path) == set()


def test_a_directory_with_pyvenv_cfg_is_a_virtualenv(tmp_path):
    (tmp_path / "py311").mkdir()
    (tmp_path / "py311" / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    _plant(tmp_path, "py311/lib/x.py")
    assert _hits(tmp_path) == set()


def test_nested_checkouts_are_left_to_their_own_tripwire(tmp_path):
    (tmp_path / ".claude" / "worktrees" / "wt").mkdir(parents=True)
    (tmp_path / ".claude" / "worktrees" / "wt" / ".git").write_text("gitdir: x\n", encoding="utf-8")
    _plant(tmp_path, ".claude/worktrees/wt/config.py")
    _plant(tmp_path, ".claude/notes.md")
    assert _hits(tmp_path) == {".claude/notes.md"}


def test_lock_files_are_scanned(tmp_path):
    _plant(tmp_path, "requirements.lock")
    assert _hits(tmp_path) == {"requirements.lock"}


def test_skips_match_paths_below_the_root_only(tmp_path):
    """A checkout under a directory called `env` is still scanned."""
    root = tmp_path / "env" / "checkout"
    _plant(root, "app/config.py")
    assert _hits(root) == {"app/config.py"}


def test_the_repository_is_clean():
    assert scan(REPO) == []
