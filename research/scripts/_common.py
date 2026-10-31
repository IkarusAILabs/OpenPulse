"""Paths, imports and output conventions shared by the research scripts.

The scripts reuse the evaluation harness (``evaluation/``) and the
conformance tooling (``conformance/``) rather than re-implementing them:
this module puts both on ``sys.path`` the way their own scripts do.
Every output is deterministic: no timestamps, no absolute paths, sorted
where order is not meaningful, one trailing newline.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
#: Generated outputs. ``OPENPULSE_RESEARCH_OUT`` redirects all three, which is
#: how ``reproduce.py --check`` regenerates them beside the committed ones.
OUT = Path(os.environ.get("OPENPULSE_RESEARCH_OUT") or RESEARCH)
RESULTS = OUT / "results"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"

for path in (ROOT, ROOT / "evaluation", ROOT / "conformance"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

#: The case sets the research package evaluates, by short name.
DATASETS = {
    "retro": ROOT / "evaluation" / "retrospective" / "cases" / "retro-2026-11.json",
    "dev": ROOT / "evaluation" / "cases" / "dev-2026-10.json",
}

#: Result files of earlier implementation versions, for cross-version comparison.
VERSIONED_RESULTS = {
    "retro": {
        "freeze (3639a0f)": ROOT
        / "evaluation"
        / "retrospective"
        / "results"
        / "openpulse-retro-2026-11.json",
        "after fixes (abcb685)": ROOT
        / "evaluation"
        / "retrospective"
        / "results"
        / "after-fixes"
        / "openpulse-retro-2026-11.json",
    },
    "dev": {"47fd707": ROOT / "evaluation" / "results" / "openpulse-dev-2026-10.json"},
}

#: Fixed seed for every bootstrap in research/ (METRICS.md §4).
BOOTSTRAP_SEED = 20261031
BOOTSTRAP_RESAMPLES = 10000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    """Repository-relative POSIX path; outside the repository, the path as given."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
