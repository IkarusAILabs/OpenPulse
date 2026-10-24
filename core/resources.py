"""Locate OpenPulse's shipped data files in a checkout or an installed wheel.

A source checkout keeps them at the repository root (`data/`, `schemas/`).
An installed wheel ships the same trees as the `openpulse_data` and
`openpulse_schemas` packages (see `[tool.setuptools]` in pyproject.toml).
Resolving only the checkout layout made a plain `pip install` silently run
with an empty catalog - every identity falling back to self - and without
the evidence-contract schemas.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve(tree: str, package: str, parts: tuple[str, ...]) -> Path:
    checkout = _REPO_ROOT.joinpath(tree, *parts)
    if checkout.exists():
        return checkout
    try:
        from importlib.resources import files

        return Path(str(files(package).joinpath(*parts)))
    except ModuleNotFoundError:
        return checkout  # neither layout present: callers report the missing path


def data_path(*parts: str) -> Path:
    """A file under `data/` (catalog, seed, curated events)."""
    return _resolve("data", "openpulse_data", parts)


def schema_path(*parts: str) -> Path:
    """A file under `schemas/` (evidence-contract JSON Schemas)."""
    return _resolve("schemas", "openpulse_schemas", parts)
