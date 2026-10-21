"""Bounded input reads (core/bounded_io.py) - review findings L1, L2, L4."""

import json

import pytest

from core import bounded_io


def test_read_stops_at_the_cap_even_when_getsize_lies(tmp_path, monkeypatch):
    """Regression: getsize() then an unbounded read() let a FIFO, /dev/zero
    or a growing file through. The read itself must be bounded."""
    path = tmp_path / "grows.json"
    path.write_bytes(b"x" * 64)
    monkeypatch.setattr(bounded_io.os.path, "getsize", lambda _p: 0)
    with pytest.raises(ValueError, match="exceeds 16 bytes"):
        bounded_io.read_bytes(str(path), 16, "input")


def test_read_under_the_cap_is_returned_whole(tmp_path):
    path = tmp_path / "ok.txt"
    path.write_bytes(b"0123456789")
    assert bounded_io.read_bytes(str(path), 10, "input") == b"0123456789"


def test_deep_json_is_a_value_error_not_a_crash():
    deep = "[" * 100_000 + "]" * 100_000
    with pytest.raises(ValueError, match="nests too deeply"):
        bounded_io.loads_json(deep, "lockfile")


def _deep_v1_lock(depth):
    node = {}
    root = node
    for i in range(depth):
        child = {}
        node[f"pkg{i}"] = {"version": "1.0.0", "dependencies": child}
        node = child
    return {"name": "app", "lockfileVersion": 1, "dependencies": root}


def test_package_lock_v1_walk_is_iterative():
    """Regression: the recursive v1 walk hit RecursionError on deep trees."""
    from core.lockfile_reader import load_package_lock_doc

    deps, _ = load_package_lock_doc(_deep_v1_lock(5_000))
    assert len(deps) == 5_000
    assert deps[0]["package"] == "pkg0" and deps[-1]["package"] == "pkg4999"


def test_package_lock_v1_walk_keeps_depth_first_order():
    from core.lockfile_reader import load_package_lock_doc

    doc = {
        "lockfileVersion": 1,
        "dependencies": {
            "a": {"version": "1", "dependencies": {"a1": {"version": "1"}}},
            "b": {"version": "1"},
        },
    }
    deps, _ = load_package_lock_doc(doc)
    assert [d["package"] for d in deps] == ["a", "a1", "b"]


def test_cli_reports_deep_json_cleanly(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    event = tmp_path / "deep.json"
    event.write_text("[" * 100_000 + "]" * 100_000, encoding="utf-8")
    out = CliRunner().invoke(cli, ["validate", "--event", str(event)])
    assert out.exit_code != 0
    assert "nests too deeply" in out.output
    assert "Traceback" not in out.output


def test_readers_use_bounded_reads(tmp_path, monkeypatch):
    """Every file reader goes through the bounded read path."""
    from core.image_inventory import read_image_inventory
    from core.lockfile_reader import read_lockfile
    from core.manifest_reader import read_manifest
    from core.sbom_reader import read_sbom

    path = tmp_path / "input"
    path.write_text(json.dumps({"x": "y" * 2_000_000}), encoding="utf-8")
    monkeypatch.setattr(bounded_io.os.path, "getsize", lambda _p: 0)
    for reader in (read_sbom, read_lockfile, read_manifest, read_image_inventory):
        monkeypatch.setattr("core.sbom_reader.MAX_SBOM_BYTES", 1024)
        monkeypatch.setattr("core.lockfile_reader.MAX_LOCKFILE_BYTES", 1024)
        monkeypatch.setattr("core.manifest_reader.MAX_MANIFEST_BYTES", 1024)
        with pytest.raises(ValueError, match="limit"):
            reader(str(path))


def test_blob_cap_matches_the_parser_cap():
    from core.github_reader import MAX_BLOB_BYTES
    from core.sbom_reader import MAX_SBOM_BYTES

    assert MAX_BLOB_BYTES == MAX_SBOM_BYTES
