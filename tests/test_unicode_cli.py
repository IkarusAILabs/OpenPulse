"""Regression tests: every CLI command must survive non-UTF-8 output streams.

``openpulse check`` gained an ASCII fallback for non-UTF-8 consoles (#17),
but the remaining commands still printed emoji/symbols through bare
``click.echo`` and crashed with ``UnicodeEncodeError``. These tests mirror
``test_check_cli_non_utf8_stdout`` for each command: cp1252 runner, exit 0,
ASCII markers in place of glyphs.
"""

import pytest
from click.testing import CliRunner

from cli.main import cli

GLYPHS = "🚨✅ℹ️❓🟢🟡🟠🔴⚪⚠️"


def _assert_no_glyphs(output: str) -> None:
    for glyph in GLYPHS:
        assert glyph not in output, f"raw glyph {glyph!r} leaked to a cp1252 stream"


def test_demo_bitnami_cli_non_utf8_stdout():
    out = CliRunner(charset="cp1252").invoke(cli, ["demo-bitnami"])
    assert out.exit_code == 0, out.output
    _assert_no_glyphs(out.output)
    assert "event: evt-bitnami-2025-distribution-001" in out.output
    assert "gate: PASS" in out.output
    assert "[affected] docker.io/bitnami/redis:7.2: [AFFECTS_ARTIFACT]" in out.output
    assert "[ok] docker.io/redis:7.2: [NOT_AFFECTED]" in out.output
    # event report header keeps its badge meaning without the emoji
    assert "[action] Bitnami public catalog distribution/support change" in out.output


def test_pulse_cli_non_utf8_stdout():
    out = CliRunner(charset="cp1252").invoke(
        cli,
        ["pulse", "--project", "redis", "--raw-bundle", "data/fixtures/redis/raw_bundle.json"],
    )
    assert out.exit_code == 0, out.output
    _assert_no_glyphs(out.output)
    assert "Lifecycle [action] action — redis 6.2 is end-of-life" in out.output
    assert "Activity [ok] ok — latest release" in out.output


def test_analyze_cli_non_utf8_stdout():
    out = CliRunner(charset="cp1252").invoke(
        cli,
        ["analyze", "--project", "redis", "--raw-bundle", "data/fixtures/redis/raw_bundle.json"],
    )
    assert out.exit_code == 0, out.output
    _assert_no_glyphs(out.output)
    assert "## Change findings (1)" in out.output
    assert "[action] **[EOL]** redis 6.2 is end-of-life" in out.output
    assert "note: findings are proposals — Evidence Analyst + gate decide events." in out.output


def test_report_cli_non_utf8_stdout(tmp_path):
    import shutil

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    shutil.copy("data/fixtures/redis/raw_bundle.json", bundle_dir / "redis.json")
    out_path = tmp_path / "report.md"
    out = CliRunner(charset="cp1252").invoke(
        cli,
        [
            "report",
            "--month",
            "2026-09",
            "--raw-bundle-dir",
            str(bundle_dir),
            "--out",
            str(out_path),
        ],
    )
    assert out.exit_code == 0, out.output
    _assert_no_glyphs(out.output)
    assert f"wrote {out_path} (1 projects)" in out.output
    # the report file itself stays UTF-8 and keeps the badge glyph
    text = out_path.read_text(encoding="utf-8")
    assert "#### redis" in text


@pytest.fixture()
def registry_store(tmp_path, monkeypatch):
    """Offline Docker Hub probes: two observations with a tag change between them."""
    import collectors.registries.docker as docker_module

    store = tmp_path / "store"
    probes = [
        {
            "collector": "registries",
            "registry": "docker.io",
            "tags_sample": ["latest", "7.2.0"],
            "digests": {"latest": ["sha256:AAA"], "7.2.0": ["sha256:111"]},
            "count": 2,
            "has_versioned_tags": True,
            "latest_only": False,
        },
        {
            "collector": "registries",
            "registry": "docker.io",
            "tags_sample": ["latest", "7.4.0"],
            "digests": {"latest": ["sha256:AAA"], "7.4.0": ["sha256:222"]},
            "count": 2,
            "has_versioned_tags": True,
            "latest_only": False,
        },
    ]

    def fake_check_image(self, namespace, repo):
        probe = probes[0] if not (store / "docker.io").exists() else probes[1]
        probe = probes[1] if (store / "docker.io").exists() else probes[0]
        return {**probe, "namespace": namespace, "repo": repo}

    monkeypatch.setattr(docker_module.RegistryCollector, "check_image", fake_check_image)
    return str(store)


def test_observe_cli_non_utf8_stdout(registry_store):
    args = ["observe", "--namespace", "bitnami", "--repo", "redis", "--store", registry_store]
    genesis = CliRunner(charset="cp1252").invoke(cli, args)
    assert genesis.exit_code == 0, genesis.output
    _assert_no_glyphs(genesis.output)
    assert "baseline recorded — no previous observation, no change claims." in genesis.output

    changed = CliRunner(charset="cp1252").invoke(cli, args)
    assert changed.exit_code == 0, changed.output
    _assert_no_glyphs(changed.output)
    assert "- tag_appeared: 7.4.0 None -> ['sha256:222']" in changed.output
    assert "- tag_disappeared: 7.2.0 ['sha256:111'] -> None" in changed.output
    # findings render their impact badges as ASCII markers
    assert "[watch] **[DISTRIBUTION_CHANGE]**" in changed.output
    assert "[review] **[DISTRIBUTION_CHANGE]**" in changed.output


def test_echo_err_stream_uses_stderr_encoding(monkeypatch):
    """_echo(err=True) must fall back against the stderr encoding, not stdout's."""
    import io
    import sys as sys_module

    from cli.main import _echo

    class StrictCp1252(io.StringIO):
        encoding = "cp1252"

        def write(self, s):
            s.encode(self.encoding)
            return super().write(s)

    class Utf8(io.StringIO):
        encoding = "utf-8"

    fake_err = StrictCp1252()
    fake_out = Utf8()
    monkeypatch.setattr(sys_module, "stdout", fake_out)
    monkeypatch.setattr(sys_module, "stderr", fake_err)

    _echo("🚨 pkg1: AFFECTED (DIRECT)", err=True)

    assert "[affected] pkg1: AFFECTED (DIRECT)" in fake_err.getvalue()
    assert fake_out.getvalue() == ""
