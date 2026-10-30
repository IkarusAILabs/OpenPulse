"""Packaging: an installed wheel must carry the data it needs at runtime."""

from pathlib import Path

import pytest
from setuptools import find_packages

from core import resources

tomllib = pytest.importorskip("tomllib")  # stdlib on 3.11+ (CI); 3.10 skips
_PYPROJECT = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
_SETUPTOOLS = _PYPROJECT["tool"]["setuptools"]
_DATA_PACKAGES = {"openpulse_data", "openpulse_schemas"}


def test_explicit_package_list_matches_the_code_tree():
    """The explicit list exists only so data dirs can ship; it must never
    drop a code package a future PR adds."""
    code = set(
        find_packages(include=["core*", "collectors*", "analyzers*", "cli*", "reports*"])
    )
    listed = set(_SETUPTOOLS["packages"]) - _DATA_PACKAGES
    assert listed == code, {"missing": code - listed, "stale": listed - code}


def test_runtime_data_is_declared_as_package_data():
    """Regression: wheels shipped no catalog, events or contract schemas."""
    assert _SETUPTOOLS["package-dir"] == {"openpulse_data": "data", "openpulse_schemas": "schemas"}
    data_globs = _SETUPTOOLS["package-data"]
    for pkg, glob in (
        ("openpulse_data", "canonical_projects.yaml"),
        ("openpulse_data", "fixtures/django-eol/event.json"),
        ("openpulse_schemas", "evidence-contract/v1.1/schema.json"),
        ("openpulse_schemas", "evidence-contract/v1.2/schema.json"),
    ):
        root = Path(_SETUPTOOLS["package-dir"][pkg])
        assert any(path == root / glob for g in data_globs[pkg] for path in root.glob(g)), glob


def test_resources_fall_back_to_the_installed_package(tmp_path, monkeypatch):
    """Outside a checkout, data resolves through the installed package."""
    monkeypatch.setattr(resources, "_REPO_ROOT", tmp_path / "no-checkout")
    path = resources.data_path("canonical_projects.yaml")
    assert path.name == "canonical_projects.yaml"
    assert "no-checkout" not in str(path)


def test_checkout_layout_is_preferred():
    assert resources.data_path("canonical_projects.yaml") == (
        Path(resources.__file__).resolve().parents[1] / "data" / "canonical_projects.yaml"
    )
    assert resources.schema_path("evidence-contract", "v1.1", "schema.json").exists()
