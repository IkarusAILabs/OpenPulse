"""Tests for scripts/gen_sbom.py CycloneDX serialNumber determinism and RFC 4122 compliance."""

import re
from pathlib import Path

from scripts.gen_sbom import build

_CYCLONEDX_UUID_URN_REGEX = re.compile(
    r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_sbom_serial_number_is_valid_rfc4122_urn_uuid():
    """CycloneDX requires serialNumber to follow RFC 4122 UUID URN format."""
    sbom = build("requirements.lock")
    serial = sbom["serialNumber"]
    assert _CYCLONEDX_UUID_URN_REGEX.match(serial), f"serialNumber {serial!r} does not match RFC 4122 pattern"


def test_sbom_serial_number_is_deterministic_and_lock_sensitive(tmp_path):
    """Identical lock files produce identical serial numbers; distinct locks produce different serial numbers."""
    lock_a = tmp_path / "lock_a.txt"
    lock_b = tmp_path / "lock_b.txt"

    lock_a.write_text("click==8.1.7\npytest==8.0.0\n", encoding="utf-8")
    lock_b.write_text("click==8.1.8\npytest==8.0.0\n", encoding="utf-8")

    sbom1 = build(str(lock_a))
    sbom2 = build(str(lock_a))
    sbom3 = build(str(lock_b))

    assert sbom1["serialNumber"] == sbom2["serialNumber"]
    assert sbom1 == sbom2
    assert sbom1["serialNumber"] != sbom3["serialNumber"]
