"""scripts/gen_sbom.py: RFC 4122 serialNumber, determinism, lock argument."""

import re
import uuid

from scripts.gen_sbom import _SERIAL_NAMESPACE, build, main, serial_number

#: CycloneDX 1.5 `serialNumber` pattern (RFC 4122 UUID URN).
_CYCLONEDX_SERIAL = re.compile(
    r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _lock(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_serial_number_is_a_valid_cyclonedx_uuid_urn(tmp_path):
    """Regression: `urn:uuid:openpulse-lock-<hex>` is not a UUID."""
    serial = build(_lock(tmp_path, "a.lock", "click==8.5.0\n"))["serialNumber"]
    assert _CYCLONEDX_SERIAL.match(serial), serial
    assert uuid.UUID(serial.removeprefix("urn:uuid:")).version == 5


def test_serial_uses_openpulse_namespace():
    expected = uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_DNS, "openpulse.ikaruslabs.net"), "d")
    assert serial_number("d") == f"urn:uuid:{expected}"
    assert _SERIAL_NAMESPACE != uuid.NAMESPACE_URL


def test_serial_is_deterministic_and_lock_sensitive(tmp_path):
    a = _lock(tmp_path, "a.lock", "click==8.1.7\npytest==8.0.0\n")
    b = _lock(tmp_path, "b.lock", "click==8.1.8\npytest==8.0.0\n")
    assert build(a) == build(a)
    assert build(a)["serialNumber"] != build(b)["serialNumber"]


def test_written_file_is_byte_identical_across_runs(tmp_path):
    """The guarantee CI's `cmp` step relies on: same lock -> same bytes."""
    lock = _lock(tmp_path, "a.lock", "click==8.5.0\nhttpx==0.28.1\n")
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    assert main([lock, str(first)]) == 0
    assert main([lock, str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()


def test_lock_argument_is_honoured(tmp_path):
    """Regression: argv[1] was ignored and requirements.lock was always read."""
    lock = _lock(tmp_path, "only-click.lock", "click==8.5.0\n")
    out = tmp_path / "sbom.json"
    assert main([lock, str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert '"name": "click"' in text
    assert '"name": "pydantic"' not in text
