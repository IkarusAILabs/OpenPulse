"""Single source for the OpenPulse release identity (F9).

The installed distribution metadata (``pyproject.toml`` version) is the
one source of truth. Every surface that stamps a version - the CLI
``--version``, the evidence-contract provenance block and report
sidecars - calls :func:`openpulse_version`, so they cannot drift.

The fallback only applies when running from a source tree that was never
installed; it must be updated in lockstep with ``pyproject.toml`` at
release time and is asserted against it by the test suite.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

#: Used only when distribution metadata is unavailable (uninstalled source tree).
FALLBACK_VERSION = "0.6.2"


def openpulse_version() -> str:
    """Installed OpenPulse version, or :data:`FALLBACK_VERSION` if unknown."""
    try:
        return str(_pkg_version("openpulse"))
    except PackageNotFoundError:
        return FALLBACK_VERSION
