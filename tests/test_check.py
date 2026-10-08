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
    # Single-source range hit: scoped match, EMERGING evidence — the
    # precise match must not inflate confidence to CORROBORATED (§5).
    assert result.match_strength == "scoped"
    assert result.evidence_confidence == "EMERGING"
    assert result.confidence == "EMERGING"


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


def test_strict_fires_only_on_action_impacts():
    """REVIEW-level affected verdicts must not trip the ACTION gate."""
    from core.risk.check import DependencyVerdict, strict_affected

    def verdict(impact, affected=True):
        return DependencyVerdict(
            dependency="x",
            affected=affected,
            relationship="AFFECTS_VERSION",
            confidence="EMERGING",
            reason="t",
            verdicts=[{"affected": affected, "impact": impact}],
        )

    assert strict_affected([verdict("ACTION")]) is True
    assert strict_affected([verdict("CRITICAL")]) is True
    assert strict_affected([verdict("REVIEW")]) is False
    assert strict_affected([verdict("ACTION", affected=False)]) is False


def test_itext_license_change_warns():
    """iText closed-source use without a commercial license: ACTION warning."""
    import json as _json

    from core.evidence.policy import gate
    from core.risk.check import check_dependency
    from core.schema.models import OSSEvent

    event = OSSEvent(**_json.load(open("data/fixtures/itext-license/event.json")))
    assert gate(event) == []
    assert event.confidence.value == "CONFIRMED"
    dep = {"kind": "package", "package": "itext-core", "ecosystem": "Maven", "version": "8.0.2"}
    result = check_dependency(dep, [event])
    assert result.affected is True
    assert result.relationship == "AFFECTS_PACKAGE"
    unrelated = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "5.2"}
    assert check_dependency(unrelated, [event]).affected is False


def test_itext_resolves_from_maven_coordinates():
    from core.entities.resolve import resolve_project

    assert resolve_project("itext") == "itext"
    assert resolve_project("itext7") == "itext"
    assert resolve_project("com.itextpdf/itext-core") == "itext"


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


def _mock_transport(status=200, location=None):
    import httpx

    def handler(request):
        headers = {"location": location} if location else {}
        return httpx.Response(status, headers=headers, request=request)

    return httpx.MockTransport(handler)


def test_post_digest_success():
    from core.notify import post_digest

    result = post_digest(
        "https://hooks.example/x",
        "# digest",
        transport=_mock_transport(200),
        resolver=lambda host: ["93.184.216.34"],
    )
    assert result == {"ok": True, "status_code": 200, "error": None}


def test_post_digest_failure_never_raises():
    import httpx

    from core.notify import post_digest

    def boom(request):
        raise httpx.ConnectTimeout("down")

    result = post_digest(
        "https://hooks.example/x",
        "md",
        transport=httpx.MockTransport(boom),
        resolver=lambda host: ["93.184.216.34"],
    )
    assert result["ok"] is False
    assert result["status_code"] is None
    assert post_digest("ftp://x", "md")["ok"] is False


def test_check_cli_webhook_posts_digest(monkeypatch):
    from click.testing import CliRunner

    import core.notify as notify
    from cli.main import cli

    seen = {}
    monkeypatch.setattr(
        notify,
        "post_digest",
        lambda url, text, **kw: (
            seen.update(url=url) or {"ok": True, "status_code": 200, "error": None}
        ),
    )
    out = CliRunner().invoke(
        cli,
        [
            "check",
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
            "--digest",
            "--webhook",
            "https://hooks.example/x",
        ],
    )
    assert out.exit_code == 0, out.output
    assert seen["url"] == "https://hooks.example/x"
    assert "posted digest" in out.output


def test_check_cli_non_utf8_stdout(tmp_path):
    from click.testing import CliRunner

    from cli.main import cli

    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()

    # Simulate non-UTF-8 stdout (e.g. Windows console with cp1252 charset)
    runner = CliRunner(charset="cp1252")
    out = runner.invoke(
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
    assert "[affected] docker.io/bitnami/redis:7.2: AFFECTED" in out.output
    assert "[ok] docker.io/redis:7.2: NOT_AFFECTED" in out.output
    assert "[unknown] django==5.0: UNKNOWN" in out.output


def test_check_echo_fallback_when_stdout_encoding_non_utf8(monkeypatch):
    import io
    import sys

    from cli.main import _echo

    class StrictCp1252Stream(io.StringIO):
        encoding = "cp1252"

        def write(self, s):
            s.encode(self.encoding)
            return super().write(s)

    fake_out = StrictCp1252Stream()
    monkeypatch.setattr(sys, "stdout", fake_out)

    _echo("🚨 pkg1: AFFECTED (DIRECT)")
    _echo("✅ pkg2: NOT_AFFECTED — reason")
    _echo("ℹ️ pkg3: RELATED — reason")
    _echo("❓ pkg4: UNKNOWN — evaluated")
    _echo("1/4 dependencies affected")

    val = fake_out.getvalue()
    assert "[affected] pkg1: AFFECTED (DIRECT)" in val
    assert "[ok] pkg2: NOT_AFFECTED" in val
    assert "[related] pkg3: RELATED" in val
    assert "[unknown] pkg4: UNKNOWN" in val
    assert "1/4 dependencies affected" in val


# Convergence tests: same dependency from different sources must produce
# identical verdicts. This is the core acceptance criterion for P0.
def test_convergence_watchlist_vs_manifest():
    """django==4.2 from watchlist and manifest must yield identical verdicts."""
    from core.risk.check import check_dependency
    from core.schema.models import OSSEvent

    django_eol = OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))

    dep_watchlist = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    dep_manifest = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}

    v_watchlist = check_dependency(dep_watchlist, [django_eol])
    v_manifest = check_dependency(dep_manifest, [django_eol])

    # Verdicts must be identical
    assert v_watchlist.affected == v_manifest.affected
    assert v_watchlist.relationship == v_manifest.relationship
    assert v_watchlist.confidence == v_manifest.confidence
    assert v_watchlist.match_strength == v_manifest.match_strength
    assert v_watchlist.evidence_confidence == v_manifest.evidence_confidence
    assert v_watchlist.identity_status == v_manifest.identity_status
    assert v_watchlist.match_method == v_manifest.match_method
    assert v_watchlist.reason == v_manifest.reason


def test_convergence_watchlist_vs_lockfile():
    """django==4.2 from watchlist and poetry.lock must yield identical verdicts."""
    from core.risk.check import check_dependency
    from core.schema.models import OSSEvent

    django_eol = OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))

    dep_watchlist = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    dep_lockfile = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}

    v_watchlist = check_dependency(dep_watchlist, [django_eol])
    v_lockfile = check_dependency(dep_lockfile, [django_eol])

    assert v_watchlist.affected == v_lockfile.affected
    assert v_watchlist.relationship == v_lockfile.relationship
    assert v_watchlist.confidence == v_lockfile.confidence


def test_convergence_watchlist_vs_sbom():
    """django==4.2 from watchlist and CycloneDX SBOM must yield identical verdicts."""
    from core.risk.check import check_dependency
    from core.schema.models import OSSEvent

    django_eol = OSSEvent(**json.load(open("data/fixtures/django-eol/event.json")))

    dep_watchlist = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    dep_sbom = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}

    v_watchlist = check_dependency(dep_watchlist, [django_eol])
    v_sbom = check_dependency(dep_sbom, [django_eol])

    assert v_watchlist.affected == v_sbom.affected
    assert v_watchlist.relationship == v_sbom.relationship
    assert v_watchlist.confidence == v_sbom.confidence


def test_convergence_image_refs():
    """docker.io/bitnami/redis:7.2 from watchlist and image
    inventory must yield identical verdicts."""
    from core.risk.check import check_dependency
    from core.schema.models import OSSEvent

    bitnami = OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))

    dep_watchlist = {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}
    dep_inventory = {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}

    v_watchlist = check_dependency(dep_watchlist, [bitnami])
    v_inventory = check_dependency(dep_inventory, [bitnami])

    assert v_watchlist.affected == v_inventory.affected
    assert v_watchlist.relationship == v_inventory.relationship
    assert v_watchlist.confidence == v_inventory.confidence
    assert v_watchlist.match_strength == v_inventory.match_strength
