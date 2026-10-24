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
    # The data packages have no __init__.py (they are plain directories), so
    # resolve their search locations directly. importlib.resources.files()
    # returns a MultiplexedPath for them, whose joinpath() rejects file
    # names before Python 3.12 (NotADirectoryError).
    import importlib.util

    try:
        spec = importlib.util.find_spec(package)
    except (ImportError, ValueError):
        spec = None
    locations = list(spec.submodule_search_locations or []) if spec else []
    for location in locations:
        candidate = Path(location).joinpath(*parts)
        if candidate.exists():
            return candidate
    if locations:
        return Path(locations[0]).joinpath(*parts)
    return checkout  # neither layout present: callers report the missing path


def data_path(*parts: str) -> Path:
    """A file under `data/` (catalog, seed, curated events)."""
    return _resolve("data", "openpulse_data", parts)


def schema_path(*parts: str) -> Path:
    """A file under `schemas/` (evidence-contract JSON Schemas)."""
    return _resolve("schemas", "openpulse_schemas", parts)
