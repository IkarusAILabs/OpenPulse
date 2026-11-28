"""Regenerate every research result, table and figure; or check them.

    python research/scripts/reproduce.py            # regenerate into research/
    python research/scripts/reproduce.py --check    # regenerate elsewhere, compare
    python research/scripts/reproduce.py --full     # also the 100,000-case run

Steps (REPRODUCIBILITY.md §3): validate the case sets; run the oracle
matrix, the randomised differential and the decision invariants and
compare them with conformance/results/; evaluate every policy; compute
intervals; compare implementation versions; build tables and figures;
write research/results/MANIFEST.json.

The manifest ties the outputs to their source: a SHA-256 over every
source file that can change a number (line endings normalised, so a
Windows and a Linux checkout agree), the commit, and whether the tree
was clean. ``--check`` fails when any regenerated output differs from
the committed one, or when the committed outputs were produced from
other source than the tree being checked. Offline and deterministic.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.metadata
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import _common  # noqa: F401

ROOT = _common.ROOT
SCRIPTS = Path(__file__).resolve().parent

#: Every source that can change a reported number.
SOURCE_GLOBS = (
    "core/**/*.py",
    "analyzers/**/*.py",
    "evaluation/*.py",
    "conformance/*.py",
    "research/scripts/*.py",
    "research/dataset/schema.json",
    "research/labelling/**/*.json",
    "research/labelling/**/*.jsonl",
    "evaluation/retrospective/labelling/**/*.jsonl",
    "data/canonical_projects.yaml",
    "data/fixtures/**/*.json",
    "evaluation/cases/*.json",
    "evaluation/retrospective/cases/*.json",
    "evaluation/retrospective/events/**/*",
    "evaluation/representations/**/*.json",
    "evaluation/retrospective/results/**/*.json",
    "evaluation/results/*.json",
)
PACKAGES = ("pydantic", "pyyaml", "packaging", "jsonschema", "httpx", "click")
OUTPUT_DIRS = ("results", "tables", "figures")


def _normalised(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def source_files() -> list[Path]:
    seen = set()
    for pattern in SOURCE_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file() and "__pycache__" not in path.parts:
                seen.add(path)
    # Sort by the relative POSIX path string: Path ordering differs between
    # Windows and POSIX (e.g. "terraform/" vs "terraform-support-change/"),
    # which made the source hash depend on the platform.
    return sorted(seen, key=lambda p: p.relative_to(ROOT).as_posix())


def source_sha256() -> str:
    digest = hashlib.sha256()
    for path in source_files():
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(_normalised(path)).digest())
    return digest.hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(  # noqa: S603 - fixed git argv; git from PATH, as the user runs it
            ["git", *args],  # noqa: S607 - fixed git argv; git from PATH, as the user runs it
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _step(title: str, argv: list[str], env: dict[str, str]) -> None:
    print(f"== {title}", flush=True)
    done = subprocess.run([sys.executable, *argv], cwd=ROOT, env=env)  # noqa: S603 - this interpreter, fixed script paths
    if done.returncode:
        raise SystemExit(f"step failed ({done.returncode}): {title}")


def conformance(full: bool) -> dict[str, Any]:
    """Re-run the conformance checks; fail on any deviation from conformance/results."""
    import invariants
    import matrix
    import randomized

    committed = ROOT / "conformance" / "results"
    out: dict[str, Any] = {}
    result = matrix.run()
    recorded = _common.load_json(committed / "matrix.json")
    if (result["cases"], result["by_severity"]) != (recorded["cases"], recorded["by_severity"]):
        raise SystemExit(
            f"oracle matrix differs from conformance/results/matrix.json: "
            f"{result['by_severity']} vs {recorded['by_severity']}"
        )
    out["matrix"] = {"cases": result["cases"], "by_severity": result["by_severity"]}
    recorded = _common.load_json(committed / "randomized.json")
    cases, seed = (recorded["cases"], recorded["seed"]) if full else (5000, 2026)
    result = randomized.run(cases, seed)
    unsafe = {k: v for k, v in result["summary_severity"].items() if k not in ("conform", "label")}
    if unsafe or (full and result["summary_severity"] != recorded["summary_severity"]):
        raise SystemExit(f"randomised differential: {result['summary_severity']}")
    out["randomized"] = {"cases": cases, "seed": seed, "summary": result["summary_severity"]}
    recorded = _common.load_json(committed / "invariants.json")
    result = invariants.run(recorded["cases_per_seed"], tuple(recorded["seeds"]))
    if result["violations"] != recorded["violations"] or any(result["violations"].values()):
        raise SystemExit(f"decision invariants violated: {result['violations']}")
    if result["exercised"] != recorded["exercised"]:
        raise SystemExit("decision invariants: generated cases differ from the committed run")
    out["invariants"] = {k: result[k] for k in ("seeds", "cases", "exercised", "violations")}
    return out


def generate(out_dir: Path, full: bool) -> None:
    env = {**os.environ, "OPENPULSE_RESEARCH_OUT": str(out_dir), "PYTHONHASHSEED": "0"}
    _step("validate case sets", [str(SCRIPTS / "validate_dataset.py")], env)
    print("== conformance: oracle matrix, randomised differential, invariants", flush=True)
    summary = conformance(full)
    for dataset in ("retro", "dev"):
        _step(
            f"evaluate {dataset}",
            [str(SCRIPTS / "evaluate.py"), dataset, "--out", str(out_dir / "results")],
            env,
        )
        _step(
            f"intervals {dataset}",
            [str(SCRIPTS / "inference.py"), dataset, "--results", str(out_dir / "results")],
            env,
        )
        _step(
            f"versions {dataset}",
            [str(SCRIPTS / "compare.py"), dataset, "--results", str(out_dir / "results")],
            env,
        )
        _step(
            f"identity faults {dataset}",
            [str(SCRIPTS / "identity_faults.py"), dataset, "--results", str(out_dir / "results")],
            env,
        )
    _step(
        "label sensitivity retro",
        [str(SCRIPTS / "label_sensitivity.py"), "--results", str(out_dir / "results")],
        env,
    )
    _step("tables and figures", [str(SCRIPTS / "tables.py")], env)
    _common.write_json(out_dir / "results" / "conformance.json", summary)


def outputs(out_dir: Path) -> list[Path]:
    return sorted(
        p
        for d in OUTPUT_DIRS
        for p in (out_dir / d).rglob("*")
        if p.is_file() and p.name != "MANIFEST.json"
    )


def manifest(out_dir: Path) -> dict[str, Any]:
    status = _git("status", "--porcelain", "--untracked-files=no")
    return {
        "source_sha256": source_sha256(),
        "source_files": len(source_files()),
        "commit": _git("rev-parse", "HEAD"),
        "tracked_tree_clean": status == "" if status is not None else None,
        "python": platform.python_version(),
        "packages": {name: _version(name) for name in PACKAGES},
        "datasets": {
            name: {"file": _common.relative(path), "sha256": _common.sha256(path)}
            for name, path in _common.DATASETS.items()
        },
        "seeds": {"bootstrap": _common.BOOTSTRAP_SEED, "registered_bootstrap": 20261030},
        "nondeterminism": "none known: no clock, network or unseeded randomness is read",
        "outputs": {
            p.relative_to(out_dir).as_posix(): hashlib.sha256(_normalised(p)).hexdigest()
            for p in outputs(out_dir)
        },
    }


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def check(full: bool) -> int:
    committed = _common.RESEARCH
    recorded = _common.load_json(committed / "results" / "MANIFEST.json")
    problems = []
    if recorded["source_sha256"] != source_sha256():
        problems.append(
            "the committed results were produced from other source than this tree "
            "(source_sha256 differs): regenerate them with reproduce.py"
        )
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp)
        generate(fresh, full)
        mine = {p.relative_to(fresh).as_posix(): p for p in outputs(fresh)}
        theirs = {p.relative_to(committed).as_posix(): p for p in outputs(committed)}
        for name in sorted(set(mine) | set(theirs)):
            if name not in theirs:
                problems.append(f"{name}: generated but not committed")
            elif name not in mine:
                problems.append(f"{name}: committed but no longer generated")
            elif _normalised(mine[name]) != _normalised(theirs[name]):
                diff = difflib.unified_diff(
                    _normalised(theirs[name]).decode().splitlines(),
                    _normalised(mine[name]).decode().splitlines(),
                    "committed",
                    "regenerated",
                    lineterm="",
                    n=0,
                )
                problems.append(f"{name}: differs\n    " + "\n    ".join(list(diff)[:12]))
    if problems:
        print("REPRODUCTION CHECK FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"reproduced: {len(mine)} outputs identical; source {recorded['source_sha256'][:12]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="regenerate elsewhere and compare")
    parser.add_argument("--full", action="store_true", help="100,000 randomised cases")
    args = parser.parse_args()
    if args.check:
        return check(args.full)
    generate(_common.OUT, args.full)
    _common.write_json(_common.RESULTS / "MANIFEST.json", manifest(_common.OUT))
    print(f"wrote {len(outputs(_common.OUT))} outputs and results/MANIFEST.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
