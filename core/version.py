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

#: The PyPI distribution name. `openpulse` on PyPI is an unrelated project
#: (OpenQASM's pulse AST), so OpenPulse ships as `ikarus-openpulse`; the CLI
#: command stays `openpulse`.
DISTRIBUTION = "ikarus-openpulse"

#: Used only when distribution metadata is unavailable (uninstalled source tree).
FALLBACK_VERSION = "0.7.0"


def openpulse_version() -> str:
    """Installed OpenPulse version, or :data:`FALLBACK_VERSION` if unknown."""
    try:
        return str(_pkg_version(DISTRIBUTION))
    except PackageNotFoundError:
        return FALLBACK_VERSION


def install_hint(extra: str = "") -> str:
    """The pip command that installs this OpenPulse release (optionally an extra).

    Pinned to the release tag on GitHub until `ikarus-openpulse` is on PyPI
    (plan item D2); never the bare PyPI name `openpulse`, which installs an
    unrelated package.
    """
    spec = f"{DISTRIBUTION}[{extra}]" if extra else DISTRIBUTION
    return (
        f'pip install "{spec} @ '
        f'git+https://github.com/IkarusAILabs/OpenPulse@v{openpulse_version()}"'
    )
