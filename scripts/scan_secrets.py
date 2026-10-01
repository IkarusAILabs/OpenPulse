"""High-precision secret tripwire over tracked-looking text files.

Threat: accidental credential commits (tokens, private keys, cloud
keys). This is a tripwire, not a scanner: a handful of low-false-
positive patterns, no entropy heuristics. It does NOT replace GitHub
push protection — enable that on the repo. stdlib only.

Exits 1 on any hit, listing file:line (patterns only, never values).
"""

from __future__ import annotations

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

_SKIP_DIRS = {".git", ".openpulse", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
_SKIP_SUFFIXES = (".lock", ".png", ".ico", ".woff", ".woff2")
_SKIP_FILES = {"scan_secrets.py"}  # this file contains the patterns themselves


def scan(root: str | Path = ".") -> list[str]:
    hits = []
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.name in _SKIP_FILES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in _SKIP_SUFFIXES:
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
