"""Watchlist check tests: verdicts, streams, versions, CLI."""

import json

import pytest

from core.risk.check import check_dependency, check_watchlist, load_watchlist_doc
from core.schema.models import OSSEvent


@pytest.fixture(scope="module")
def event():
    return OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))


@pytest.fixture(scope="module")
def django_eol():
    return OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))


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


def test_load_watchlist_optional_fields():
    deps = load_watchlist_doc(
        {"dependencies": [{"ref": "x:1", "environment": "production", "owner": "platform"}]}
    )
    assert deps[0]["environment"] == "production"
    with pytest.raises(ValueError):
        load_watchlist_doc({"dependencies": [{"ref": "x:1", "owner": 5}]})


def test_image_dep_matches_event(event):
    result = check_dependency({"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}, [event])
    assert result.affected is True
    assert result.relationship == "AFFECTS_ARTIFACT"
    assert result.confidence == "CONFIRMED"
    assert result.events == [event.id]


def test_image_dep_excluded_by_scope(event):
    """Upstream redis is NOT_AFFECTED (not UNKNOWN): scope excludes it."""
    result = check_dependency({"kind": "image", "ref": "docker.io/redis:7.2"}, [event])
    assert result.affected is False
    assert result.relationship == "NOT_AFFECTED"


def test_package_dep_affected_version(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.0"}
    result = check_dependency(dep, [event], {"django": _django_osv("5.0")})
    assert result.affected is True
    assert result.relationship == "AFFECTS_VERSION"
    assert result.match_method == "osv_package+version_range"
    assert result.confidence == "CORROBORATED"


def test_package_dep_fixed_version_cleared(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.2"}
    result = check_dependency(dep, [event], {"django": _django_osv("5.2")})
    assert result.affected is False
    assert result.relationship == "NOT_AFFECTED"


def test_package_dep_unknown_version_no_version_claim(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": None}
    result = check_dependency(dep, [event], {"django": _django_osv(None)})
    assert result.relationship in ("AFFECTS_PACKAGE", "UNKNOWN")
    for verdict in result.verdicts:
        assert verdict.get("relationship") != "AFFECTS_VERSION"


def test_project_tie_is_not_impact(django_eol):
    """Same project, no scope bite: RELATED context, affected False."""
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.0"}
    event = django_eol.model_copy(update={"scope": None})
    result = check_dependency(dep, [event])
    assert result.affected is False
    assert result.relationship in ("RELATED", "AFFECTS_PROJECT")


def test_django_eol_scope_matrix(django_eol):
    """4.2 → AFFECTS_VERSION; 5.0/5.2 → NOT_AFFECTED; unknown → RELATED."""
    by_version = {}
    for version in ("4.2", "5.0", "5.2", None):
        dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": version}
        by_version[version] = check_dependency(dep, [django_eol])
    assert by_version["4.2"].affected is True
    assert by_version["4.2"].relationship == "AFFECTS_VERSION"
    assert by_version["5.0"].relationship == "NOT_AFFECTED"
    assert by_version["5.2"].affected is False
    assert by_version[None].relationship == "RELATED"


def test_streams_stay_separate(event):
    """Bitnami event + Django CVE must not merge into one generic cause."""
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.0"}
    result = check_dependency(dep, [event], {"django": _django_osv("5.0")})
    causes = {c["cause"] for c in result.verdicts}
    assert causes == {"security_vulnerability"}
    assert result.affected is True
    assert result.relationship == "AFFECTS_VERSION"


def test_check_watchlist_batch(event):
    results = check_watchlist(
        [
            {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"},
            {"kind": "image", "ref": "docker.io/redis:7.2"},
        ],
        [event],
    )
    assert [r.relationship for r in results] == ["AFFECTS_ARTIFACT", "NOT_AFFECTED"]


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
    assert "NOT_AFFECTED" in out.output


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


def test_check_digest_groups_all_states():
    from analyzers.report_analyst import render_check_digest

    verdicts = [
        {
            "dependency": "a:1",
            "affected": True,
            "relationship": "AFFECTS_VERSION",
            "reason": "in range",
        },
        {
            "dependency": "b:2",
            "affected": False,
            "relationship": "NOT_AFFECTED",
            "reason": "cleared",
        },
        {"dependency": "c", "affected": False, "relationship": "RELATED", "reason": "context only"},
        {"dependency": "d", "affected": False, "relationship": "UNKNOWN", "reason": ""},
    ]
    md = render_check_digest(verdicts)
    assert "1/4 dependencies affected" in md
    assert "## 🚨 AFFECTED (1)" in md
    assert "## ✅ NOT_AFFECTED (1)" in md
    assert "## ℹ️ RELATED (1)" in md
    assert "## ❓ UNKNOWN (1)" in md
    assert md.index("AFFECTED") < md.index("NOT_AFFECTED") < md.index("RELATED")


def test_check_cli_digest_flag():
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
            "--digest",
        ],
    )
    assert out.exit_code == 0, out.output
    assert "1/3 dependencies affected" in out.output
    assert "## 🚨 AFFECTED (1)" in out.output
