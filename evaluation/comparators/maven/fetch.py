"""Fetch the pinned maven-artifact jar from Maven Central and verify it.

Run from the repository root:

    python evaluation/comparators/maven/fetch.py

The jar goes to ``evaluation/comparators/maven/lib/`` (git-ignored). Its
SHA-256 was computed on 2026-10-30 from the Central artefact, whose
published SHA-1 matched. A mismatch removes the download and fails:
nothing unverified is ever left in place to run.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

GROUP, ARTIFACT, VERSION = "org/apache/maven", "maven-artifact", "3.9.16"
SHA256 = "54cc1c1ef932e3d4a903352111b42b4d3c3ed8e7a1d0de73b625309d9c3ad3e8"
URL = f"https://repo1.maven.org/maven2/{GROUP}/{ARTIFACT}/{VERSION}/{ARTIFACT}-{VERSION}.jar"
JAR = Path(__file__).resolve().parent / "lib" / f"{ARTIFACT}-{VERSION}.jar"


def verified(path: Path) -> bool:
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == SHA256


def main() -> int:
    if verified(JAR):
        print(f"{JAR.name}: present and verified")
        return 0
    JAR.parent.mkdir(exist_ok=True)
    partial = JAR.with_suffix(".part")
    with urllib.request.urlopen(URL, timeout=60) as response:  # noqa: S310 (pinned https URL)
        partial.write_bytes(response.read())
    if not verified(partial):
        partial.unlink()
        print(f"{JAR.name}: SHA-256 mismatch, download removed", file=sys.stderr)
        return 1
    partial.replace(JAR)
    print(f"{JAR.name}: downloaded and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
