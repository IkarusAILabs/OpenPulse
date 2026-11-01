"""High-precision secret tripwire over tracked-looking text files.

Threat: accidental credential commits (tokens, private keys, cloud
keys). This is a tripwire, not a scanner: a handful of low-false-
positive patterns, no entropy heuristics. It does NOT replace GitHub
push protection — enable that on the repo. stdlib only.

What it walks (#142): every file under the root except
- tool and cache directories (``_SKIP_DIRS``), matched on the path
  relative to the root, so a checkout that happens to live under a
  directory called ``env`` is still scanned;
- virtualenvs: ``.venv``, ``venv``, ``env``, ``site-packages`` and any
  directory holding a ``pyvenv.cfg``. Installed libraries ship sample
  keys in their test fixtures; they are not this repository's secrets;
- nested git checkouts (a ``.git`` file or directory below the root,
  such as a worktree), which are other checkouts with their own tripwire;
- this scanner itself, at its canonical path ``scripts/scan_secrets.py``
  only, because it contains the patterns. A copy anywhere else is scanned.

``*.lock`` files are scanned. They hold pins and lowercase hex hashes,
which none of the patterns match, so scanning them is cheap and closes a
place a token could hide (a lock edited by hand, a registry URL with
credentials in it).

Exits 1 on any hit, listing file:line (patterns only, never values).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "aws-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github-token": re.compile(
        r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
    ),
    "slack-token": re.compile(r"xox[bpas]-[A-Za-z0-9\-]{10,}"),
    "google-key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "live-secret-key": re.compile(r"sk-live-[A-Za-z0-9]{8,}"),
}

_SKIP_DIRS = {
    ".git",
    ".openpulse",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    # virtualenvs (plus any directory holding a pyvenv.cfg, below)
    ".venv",
    "venv",
    "env",
    "site-packages",
}
_SKIP_SUFFIXES = (".png", ".ico", ".woff", ".woff2")
#: Relative to the scanned root: this file contains the patterns themselves.
_SELF = Path("scripts") / "scan_secrets.py"


def _skip_dir(directory: Path, name: str) -> bool:
    child = directory / name
    return (
        name in _SKIP_DIRS
        or (child / "pyvenv.cfg").is_file()
        or (child / ".git").exists()  # a nested checkout or worktree
    )


def scan(root: str | Path = ".") -> list[str]:
    root = Path(root)
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        directory = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if not _skip_dir(directory, d))
        for filename in sorted(filenames):
            path = directory / filename
            if path.relative_to(root) == _SELF or path.suffix in _SKIP_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, ValueError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for name, pattern in _PATTERNS.items():
                    if pattern.search(line):
                        hits.append(f"{path}:{lineno} [{name}]")
    return hits


def main() -> int:
    hits = scan(sys.argv[1] if len(sys.argv) > 1 else ".")
    for hit in hits:
        print(f"possible secret: {hit}")
    if hits:
        print(f"{len(hits)} possible secret(s) — remove before committing")
        return 1
    print("secret tripwire: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
