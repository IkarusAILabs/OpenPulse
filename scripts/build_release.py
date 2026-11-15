"""Build the release sdist and wheel for one tag (v0.10.0 item V1, #111).

Threat: a release artifact that cannot be tied to the reviewed tree, or
whose version disagrees with its tag. The tag must equal the version in
pyproject.toml and core.version (``v`` + version), and the build runs
setuptools' own PEP 517 hooks in this interpreter - no build isolation,
so the setuptools that builds is the hash-locked one in
.github/ci-tools.lock, never one fetched at build time. The locked
setuptools must satisfy ``[build-system].requires``. stdlib + setuptools.

Usage: python scripts/build_release.py TAG [OUTDIR]   (OUTDIR default: dist)
Run with SOURCE_DATE_EPOCH set to the tagged commit's time so archive
timestamps come from the commit, not the build clock.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_FLOOR = re.compile(r"^setuptools\s*>=\s*([0-9][^,;\s]*)$")
_LOCKED = re.compile(r"^setuptools==([^\s;\\]+)", re.MULTILINE)


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def project_version(root: Path = ROOT) -> str:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("build_release: pyproject.toml has no project version")
    return match.group(1)


def build_floor(root: Path = ROOT) -> str:
    """The ``setuptools>=X`` floor in ``[build-system].requires``."""
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    block = text.split("[build-system]", 1)[1].split("\n[", 1)[0]
    for requirement in re.findall(r'"([^"]+)"', block):
        match = _FLOOR.match(requirement.strip())
        if match:
            return match.group(1)
    raise SystemExit("build_release: [build-system].requires has no setuptools>= floor")


def locked_setuptools(root: Path = ROOT) -> str:
    text = (root / ".github" / "ci-tools.lock").read_text(encoding="utf-8")
    match = _LOCKED.search(text)
    if not match:
        raise SystemExit("build_release: .github/ci-tools.lock pins no setuptools")
    return match.group(1)


def check(tag: str, root: Path = ROOT) -> str:
    """Return the version, or exit with every reason the tag can't be built."""
    sys.path.insert(0, str(root))
    from core.version import FALLBACK_VERSION

    version = project_version(root)
    problems = []
    if tag != f"v{version}":
        problems.append(f"tag {tag!r} does not match pyproject.toml version {version!r}")
    if FALLBACK_VERSION != version:
        problems.append(f"core.version FALLBACK_VERSION {FALLBACK_VERSION!r} != {version!r}")
    floor, locked = build_floor(root), locked_setuptools(root)
    if _version_tuple(locked) < _version_tuple(floor):
        problems.append(
            f"locked setuptools {locked} is below the build floor {floor}; "
            "bump CI_TOOLS in scripts/compile_locks.py and regenerate the locks"
        )
    if problems:
        raise SystemExit("build_release: " + "; ".join(problems))
    return version


def build(outdir: Path, root: Path = ROOT) -> list[str]:
    import setuptools
    from setuptools import build_meta

    if _version_tuple(setuptools.__version__) < _version_tuple(build_floor(root)):
        raise SystemExit(
            f"build_release: running setuptools {setuptools.__version__} is below the "
            f"build floor {build_floor(root)}; install .github/ci-tools.lock first"
        )
    outdir = outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(root)
    try:
        return [build_meta.build_sdist(str(outdir)), build_meta.build_wheel(str(outdir))]
    finally:
        os.chdir(cwd)


def main(argv: list[str]) -> int:
    if not argv or len(argv) > 2:
        print("usage: python scripts/build_release.py TAG [OUTDIR]", file=sys.stderr)
        return 2
    version = check(argv[0])
    built = build(Path(argv[1] if len(argv) > 1 else "dist"))
    print(f"built {version}: {', '.join(built)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
