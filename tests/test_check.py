"""Watchlist check tests: image matching, version-aware correlation, CLI."""

import json

import pytest

from core.risk.check import check_dependency, load_watchlist_doc
from core.schema.models import OSSEvent


@pytest.fixture(scope="module")
def event():
    return OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))


def _django_osv(version):
    return {
        "osv": [
            {
                "collector": "osv",
                "package": "django",
                "ecosystem": "PyPI",
                "id": "CVE-2026-0100",
                "severity": [{"score": 8.0}],
                "affected": [
                    {
                        "package": "django",
                        "ecosystem": "PyPI",
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [{"introduced": "0"}, {"fixed": "5.1.1"}],
                            }
                        ],
                        "fixed": ["5.1.1"],
                        "versions": [],
                    }
                ],
                "references": [],
            }
        ]
    }


def test_load_watchlist_doc():
    import yaml

    doc = yaml.safe_load(open("data/fixtures/watchlist_sample.yaml", encoding="utf-8"))
    deps = load_watchlist_doc(doc)
    assert deps[0] == {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}
    assert deps[2]["version"] == "5.0"
    with pytest.raises(ValueError):
        load_watchlist_doc({})
    with pytest.raises(ValueError):
        load_watchlist_doc({"dependencies": [{"foo": 1}]})


def test_image_dep_matches_event(event):
    result = check_dependency({"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}, [event])
    assert result["affected"] is True
    assert result["relationship"] == "AFFECTS_ARTIFACT"


def test_image_dep_no_match(event):
    result = check_dependency({"kind": "image", "ref": "docker.io/redis:7.2"}, [event])
    assert result["affected"] is False


def test_package_dep_affected_version(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.0"}
    result = check_dependency(dep, [event], {"django": _django_osv("5.0")})
    assert result["affected"] is True
    assert result["relationship"] == "AFFECTS_VERSION"


def test_package_dep_fixed_version_unaffected(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.2"}
    result = check_dependency(dep, [event], {"django": _django_osv("5.2")})
    assert result["affected"] is False


def test_package_dep_unknown_version_no_version_claim(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": None}
    result = check_dependency(dep, [event], {"django": _django_osv(None)})
    assert result["relationship"] in ("AFFECTS_PACKAGE", "UNKNOWN")
    for verdict in result["verdicts"]:
        assert verdict.get("relationship") != "AFFECTS_VERSION"


def test_check_cli_offline(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    out = CliRunner().invoke(
        cli,
        [
            "check",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
            "--raw-bundle-dir",
            str(bundle_dir),
        ],
    )
    assert out.exit_code == 0, out.output
    assert "1/3 dependencies affected" in out.output
    assert "docker.io/bitnami/redis:7.2" in out.output


def test_check_cli_strict_fails_when_affected():
    from click.testing import CliRunner

    from cli.main import cli

    out = CliRunner().invoke(
        cli,
        [
            "check",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
            "--strict",
        ],
    )
    assert out.exit_code == 1
