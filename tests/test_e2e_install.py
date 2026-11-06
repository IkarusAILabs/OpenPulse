"""Gate to install, end to end and offline (track T, T-E2; v0.17.0 item G5).

Each test runs a pipeline the way CI would: gate the dependency files with a
receipt, verify the receipt immediately before install, then
``pip install --require-hashes`` from a local wheel index. Nothing reaches
the network: the wheels are built here, ``--no-index --find-links`` serves
them, and PyPI's digest answers are stubbed with the digest of the wheel the
project really published. Both outcomes are asserted: what installs, and
that a refused change installs nothing.

The routes are the ones ``docs/TRUST_POLICY.md`` ("Bypass routes") claims
v0.17.0 covers: a file swapped after the gate (G2), a lockfile hash edited
in place under a policy that forgot ``digest_mismatch`` (G3), and a lockfile
regenerated after the gate (G4).
"""

from __future__ import annotations

import base64
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli

NAME, MODULE, VERSION = "openpulse-e2e-demo", "openpulse_e2e_demo", "1.0"
WHEEL = f"{MODULE}-{VERSION}-py3-none-any.whl"


def _pip_works() -> bool:
    try:
        done = subprocess.run(
            [sys.executable, "-m", "pip", "--version"], capture_output=True, timeout=60
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


pytestmark = pytest.mark.skipif(not _pip_works(), reason="pip is not available")


def _record_hash(data: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return "sha256=" + digest.decode("ascii")


def build_wheel(directory: Path, marker: str) -> str:
    """A minimal pure-Python wheel whose module says ``marker``; its SHA-256."""
    files = {
        f"{MODULE}/__init__.py": f"WHO = {marker!r}\n".encode(),
        f"{MODULE}-{VERSION}.dist-info/METADATA": (
            f"Metadata-Version: 2.1\nName: {NAME}\nVersion: {VERSION}\n"
        ).encode(),
        f"{MODULE}-{VERSION}.dist-info/WHEEL": (
            b"Wheel-Version: 1.0\nGenerator: openpulse-tests\n"
            b"Root-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }
    record = "".join(f"{p},{_record_hash(d)},{len(d)}\n" for p, d in files.items())
    record += f"{MODULE}-{VERSION}.dist-info/RECORD,,\n"
    files[f"{MODULE}-{VERSION}.dist-info/RECORD"] = record.encode()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / WHEEL
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lockfiles(project: Path, sha: str, extra: str = "") -> None:
    """poetry.lock (what the gate checks) and the requirements export pip installs."""
    (project / "poetry.lock").write_text(
        'lock-version = "2.1"\n\n'
        f'[[package]]\nname = "{NAME}"\nversion = "{VERSION}"\n'
        f'files = [{{file = "{WHEEL}", hash = "sha256:{sha}"}}]\n' + extra,
        encoding="utf-8",
    )
    (project / "requirements.txt").write_text(
        f"{NAME}=={VERSION} --hash=sha256:{sha}\n", encoding="utf-8"
    )


class Pipeline:
    """One CI job: gate, verify, install. Every step is the shipped CLI or pip."""

    FILES = ("poetry.lock", "requirements.txt")

    def __init__(self, project: Path, index: Path) -> None:
        self.project, self.index = project, index
        self.target = project / "site"

    def gate(self) -> int:
        args = ["gate", *self.FILES, "--policy", "policy.yml", "--receipt", "receipt.json"]
        return CliRunner().invoke(cli, args).exit_code

    def verify(self) -> int:
        args = ["gate", "--verify-receipt", "receipt.json"]
        for name in self.FILES:
            args += ["--require-receipt-for", name]
        return CliRunner().invoke(cli, args).exit_code

    def pip_install(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(self.index),
                "--require-hashes",
                "--no-deps",
                "--disable-pip-version-check",
                "--no-cache-dir",
                "--target",
                str(self.target),
                "-r",
                str(self.project / "requirements.txt"),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

    def install(self) -> bool:
        """The install step: verify first, then pip. True when something installed."""
        if self.verify() != 0:
            return False
        return self.pip_install().returncode == 0

    def installed(self) -> str | None:
        module = self.target / MODULE / "__init__.py"
        if not module.is_file():
            return None
        return module.read_text(encoding="utf-8").split("'")[1]


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """A project locking the published wheel, a local index serving it, and a
    PyPI stub that publishes that wheel's digest. The policy forgot
    ``digest_mismatch``: only a blocklist, as many real policies are."""
    project, index = tmp_path / "project", tmp_path / "index"
    project.mkdir()
    published = build_wheel(index, "published")
    lockfiles(project, published)
    (project / "policy.yml").write_text(
        yaml.safe_dump({"version": 1, "blocklist": ["PyPI:evil-pkg"]}), encoding="utf-8"
    )

    def pypi(url):
        if f"/pypi/{NAME}/{VERSION}/json" not in url:
            return 404, None
        return 200, {"urls": [{"filename": WHEEL, "digests": {"sha256": published}}]}

    monkeypatch.setattr("core.digest_integrity.default_fetch", pypi)
    monkeypatch.setenv("OPENPULSE_CACHE_DIR", "")
    monkeypatch.chdir(project)
    return Pipeline(project, index), published


def test_a_clean_change_is_gated_verified_and_installs(setup):
    pipeline, _published = setup
    assert pipeline.gate() == 0
    assert pipeline.install()
    assert pipeline.installed() == "published"


def test_a_lockfile_swapped_after_the_gate_installs_nothing(setup, tmp_path):
    """G2: a later step points the files at another artifact after the gate."""
    pipeline, _published = setup
    assert pipeline.gate() == 0
    swapped = build_wheel(tmp_path / "attacker", "swapped")
    build_wheel(pipeline.index, "swapped")  # the index now serves the swapped wheel
    lockfiles(pipeline.project, swapped)
    assert pipeline.verify() == 1
    assert not pipeline.install() and pipeline.installed() is None
    # Without the verify step, pip would have installed it: the hashes agree.
    assert pipeline.pip_install().returncode == 0 and pipeline.installed() == "swapped"


def test_an_in_place_hash_edit_fails_the_gate_and_installs_nothing(setup):
    """G3: same name and version, another artifact, under a policy that never
    mentions digest_mismatch."""
    pipeline, _published = setup
    edited = build_wheel(pipeline.index, "edited")  # a mirror serving another artifact
    lockfiles(pipeline.project, edited)
    assert pipeline.gate() == 1
    assert not pipeline.install() and pipeline.installed() is None


def test_a_regenerated_lockfile_is_refused_until_gated_again(setup):
    """G4: `poetry lock` after the gate rewrites poetry.lock."""
    pipeline, published = setup
    assert pipeline.gate() == 0
    lockfiles(pipeline.project, published, extra="\n# regenerated by a later step\n")
    assert pipeline.verify() == 1
    assert not pipeline.install() and pipeline.installed() is None
    assert pipeline.gate() == 0  # gate again: now the regenerated file is the gated one
    assert pipeline.install() and pipeline.installed() == "published"


def test_require_hashes_installs_exactly_the_gated_digests(setup, tmp_path):
    """The files are untouched, but the index serves another artifact: the
    receipt verifies, and pip refuses what the gated hashes do not name."""
    pipeline, _published = setup
    assert pipeline.gate() == 0
    build_wheel(pipeline.index, "substituted")
    assert pipeline.verify() == 0
    result = pipeline.pip_install()
    assert result.returncode != 0 and "hash" in (result.stdout + result.stderr).lower()
    assert pipeline.installed() is None
