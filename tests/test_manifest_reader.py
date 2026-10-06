"""Manifest reader tests: pinned-entry discipline, parity, CLI wiring (5 formats)."""

import json

import pytest

from core.manifest_reader import (
    MAX_MANIFEST_BYTES,
    _cargo_spec_to_dep,
    _exact_go_version,
    _poetry_exact,
    load_cargo_toml_doc,
    load_go_mod_doc,
    load_pom_xml_doc,
    load_pyproject_doc,
    load_requirements_txt_doc,
    read_manifest,
)
from core.risk.check import check_dependency
from core.schema.models import OSSEvent

REQUIREMENTS_FIXTURE = "data/fixtures/manifests/requirements.txt"
PEP621_FIXTURE = "data/fixtures/manifests/pyproject_pep621.toml"
POETRY_FIXTURE = "data/fixtures/manifests/pyproject_poetry.toml"
POM_FIXTURE = "data/fixtures/manifests/pom.xml"
GO_FIXTURE = "data/fixtures/manifests/go.mod"
CARGO_FIXTURE = "data/fixtures/manifests/Cargo.toml"
MALFORMED_FIXTURE = "data/fixtures/manifests/malformed.txt"


class TestRequirementsReader:
    def test_fixture_pins_three_and_records_four_skips(self):
        deps, skipped, fmt = read_manifest(REQUIREMENTS_FIXTURE)
        assert fmt == "requirements"
        assert deps == [
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"},
            {"kind": "package", "package": "celery", "ecosystem": "PyPI", "version": "5.4.0"},
            {"kind": "package", "package": "boto3", "ecosystem": "PyPI", "version": "1.34.90"},
        ]
        assert len(skipped) == 4
        assert any("`requests>=2.31.0`" in s and "never range-guessed" in s for s in skipped)
        assert any("`flask`" in s for s in skipped)
        assert any("pip option `--index-url" in s for s in skipped)
        assert any("pip option `-r requirements-dev.txt`" in s for s in skipped)

    def test_extras_and_markers_still_pin(self):
        text = "celery[redis]==5.4.0 ; python_version >= 3.8\n"
        deps, skipped = load_requirements_txt_doc(text)
        assert deps == [
            {"kind": "package", "package": "celery", "ecosystem": "PyPI", "version": "5.4.0"}
        ]
        assert skipped == []

    def test_hash_comment_annotation_keeps_the_pin(self):
        text = "boto3==1.34.90 # via deployment lock\n"
        deps, skipped = load_requirements_txt_doc(text)
        assert len(deps) == 1 and deps[0]["version"] == "1.34.90"
        assert skipped == []

    def test_url_and_editable_refs_are_skipped_not_guessed(self):
        text = "django @ https://example.com/django.whl\n-e .\nsomepkg==1.0.0\n"
        deps, skipped = load_requirements_txt_doc(text)
        assert [d["package"] for d in deps] == ["somepkg"]
        assert len(skipped) == 2
        assert any("never range-guessed" in s for s in skipped)
        assert any("pip option" in s for s in skipped)


class TestPyprojectReader:
    def test_pep621_fixture_pins_four_and_skips_two(self):
        deps, skipped, fmt = read_manifest(PEP621_FIXTURE)
        assert fmt == "pyproject"
        assert deps == [
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"},
            {"kind": "package", "package": "celery", "ecosystem": "PyPI", "version": "5.4.0"},
            {"kind": "package", "package": "boto3", "ecosystem": "PyPI", "version": "1.34.90"},
            {"kind": "package", "package": "sphinx", "ecosystem": "PyPI", "version": "7.2.6"},
        ]
        assert len(skipped) == 2
        assert any("`requests>=2.31.0`" in s for s in skipped)
        assert any("`pytest>=8.0`" in s for s in skipped)

    def test_pep621_without_dependencies_key_is_valid_empty(self):
        deps, skipped = load_pyproject_doc({"project": {"name": "x"}})
        assert deps == [] and skipped == []

    def test_pep621_malformed_dependencies_is_a_skip_line(self):
        deps, skipped = load_pyproject_doc({"project": {"dependencies": "not-a-list"}})
        assert deps == []
        assert "must be a list" in skipped[0]

    def test_poetry_fixture_pins_three_and_skips_five(self):
        deps, skipped, fmt = read_manifest(POETRY_FIXTURE)
        assert fmt == "pyproject"
        assert deps == [
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"},
            {"kind": "package", "package": "boto3", "ecosystem": "PyPI", "version": "1.34.90"},
            {"kind": "package", "package": "mypy", "ecosystem": "PyPI", "version": "1.11.0"},
        ]
        assert len(skipped) == 5
        assert any("interpreter constraint" in s for s in skipped)
        assert any("`tool.poetry.dependencies.celery`" in s and "constraint" in s for s in skipped)
        assert any("`tool.poetry.dependencies.local-tool`" in s and "guess" in s for s in skipped)
        assert any("`tool.poetry.dependencies.git-dep`" in s and "guess" in s for s in skipped)
        assert any("`tool.poetry.group.dev.dependencies.pytest`" in s for s in skipped)

    def test_poetry_equality_operator_pins(self):
        assert _poetry_exact("=1.2.3") == "1.2.3"
        assert _poetry_exact("==1.2.3") == "1.2.3"
        assert _poetry_exact("1.2.3") == "1.2.3"
        assert _poetry_exact("^1.0") is None
        assert _poetry_exact(">=1.2") is None
        assert _poetry_exact("~2.0") is None

    def test_pyproject_with_neither_table_is_refused(self):
        with pytest.raises(ValueError, match="PEP 621"):
            load_pyproject_doc({"build-system": {}})


class TestPomReader:
    def test_fixture_pins_three_and_skips_test_scope(self):
        deps, skipped, fmt = read_manifest(POM_FIXTURE)
        assert fmt == "pom"
        assert deps == [
            {
                "kind": "package",
                "package": "com.itextpdf:itext-core",
                "ecosystem": "Maven",
                "version": "8.0.2",
            },
            {
                "kind": "package",
                "package": "org.slf4j:slf4j-api",
                "ecosystem": "Maven",
                "version": "2.0.9",
            },
            {
                "kind": "package",
                "package": "org.managed:no-version",
                "ecosystem": "Maven",
                "version": "1.2.3",
            },
        ]
        assert skipped == ["`junit:junit`: test scope - not a runtime dependency"]

    def test_property_version_resolves_from_pom_properties(self):
        deps, _, _ = read_manifest(POM_FIXTURE)
        slf4j = next(d for d in deps if d["package"] == "org.slf4j:slf4j-api")
        assert slf4j["version"] == "2.0.9"

    def test_managed_table_fills_a_versionless_direct_dep(self):
        deps, _, _ = read_manifest(POM_FIXTURE)
        managed_dep = next(d for d in deps if d["package"] == "org.managed:no-version")
        assert managed_dep["version"] == "1.2.3"

    def test_plugin_dependencies_are_not_runtime_deps(self):
        deps, _, _ = read_manifest(POM_FIXTURE)
        assert all("maven-compiler-plugin" not in d["package"] for d in deps)

    def test_missing_group_or_artifact_is_skipped(self):
        pom = """<project><dependencies>
        <dependency><artifactId>only-aid</artifactId><version>1.0</version></dependency>
        </dependencies></project>"""
        deps, skipped = load_pom_xml_doc(pom)
        assert deps == []
        assert "missing groupId or artifactId" in skipped[0]

    def test_no_dependencies_block_is_refused(self):
        with pytest.raises(ValueError, match="declares no"):
            load_pom_xml_doc("<project></project>")

    def test_non_project_root_is_refused(self):
        with pytest.raises(ValueError, match="root element"):
            load_pom_xml_doc("<notproject><dependencies/></notproject>")

    def test_unparseable_xml_is_refused_with_clean_error(self):
        with pytest.raises(ValueError, match="not parseable XML"):
            load_pom_xml_doc("<project><dependencies></project>")


class TestGoReader:
    def test_fixture_pins_four_and_records_directives(self):
        deps, skipped, fmt = read_manifest(GO_FIXTURE)
        assert fmt == "go"
        assert [d["package"] for d in deps] == [
            "github.com/redis/go-redis/v9",
            "golang.org/x/text",
            "github.com/bad/entry",
            "github.com/stretchr/testify",
        ]
        assert [d["version"] for d in deps] == [
            "v9.0.0",
            "v0.14.0",
            "v1.2.3-rc1",
            "v1.9.0",
        ]
        assert len(skipped) == 2
        assert any("`replace` directive" in s for s in skipped)
        assert any("`retract` directive" in s for s in skipped)

    def test_version_gate_accepts_exact_spellings_only(self):
        assert _exact_go_version("v1.2.3")
        assert _exact_go_version("v1.2.3-rc1")
        assert _exact_go_version("v0.0.0-20240101120000-abcdef123456")
        assert _exact_go_version("v2.0.0+incompatible")
        assert not _exact_go_version("v1")
        assert not _exact_go_version("v1.2")
        assert not _exact_go_version("latest")
        assert not _exact_go_version("1.2.3")

    def test_single_line_require_outside_block(self):
        go = "module example.com/app\n\nrequire github.com/x/y v1.2.3\n"
        deps, skipped = load_go_mod_doc(go)
        assert deps == [
            {"kind": "package", "package": "github.com/x/y", "ecosystem": "Go", "version": "v1.2.3"}
        ]
        assert skipped == []

    def test_require_line_without_version_is_skipped(self):
        go = "module example.com/app\n\nrequire github.com/x/y\n"
        deps, skipped = load_go_mod_doc(go)
        assert deps == []
        assert "no version on the require line" in skipped[0]

    def test_go_mod_without_require_directive_is_refused(self):
        with pytest.raises(ValueError, match="no .require. directive"):
            load_go_mod_doc("module example.com/app\n\ngo 1.22\n")


class TestCargoReader:
    def test_fixture_pins_three_and_skips_five(self):
        deps, skipped, fmt = read_manifest(CARGO_FIXTURE)
        assert fmt == "cargo"
        assert deps == [
            {"kind": "package", "package": "serde", "ecosystem": "crates.io", "version": "1.0.210"},
            {"kind": "package", "package": "tokio", "ecosystem": "crates.io", "version": "1.40.0"},
            {"kind": "package", "package": "cc", "ecosystem": "crates.io", "version": "1.1.0"},
        ]
        assert len(skipped) == 5
        assert any("`[dependencies].rand`" in s and "caret" in s for s in skipped)
        assert any("`[dependencies].local-crate`" in s and "guess" in s for s in skipped)
        assert any("`[dependencies].git-sourced`" in s and "guess" in s for s in skipped)
        assert any("workspace inheritance" in s for s in skipped)
        assert any("`[dev-dependencies].criterion`" in s for s in skipped)

    def test_bare_req_is_caret_semantics_not_a_pin(self):
        dep, reason = _cargo_spec_to_dep("serde", "1.0.210")
        assert dep is None
        assert "bare means caret" in reason

    def test_exact_req_and_table_version_pin(self):
        dep, _ = _cargo_spec_to_dep("serde", "=1.0.210")
        assert dep == {
            "kind": "package",
            "package": "serde",
            "ecosystem": "crates.io",
            "version": "1.0.210",
        }
        # The table `version` key follows the same rule as the string
        # form: bare is caret semantics per the Cargo Book, so only
        # the explicit `=` req pins.
        dep, reason = _cargo_spec_to_dep("tokio", {"version": "1.40.0"})
        assert dep is None and "bare means caret" in reason
        dep, _ = _cargo_spec_to_dep("tokio", {"version": "=1.40.0"})
        assert dep["version"] == "1.40.0"

    def test_cargo_without_dependency_tables_is_refused(self):
        with pytest.raises(ValueError, match="declares no"):
            load_cargo_toml_doc({"package": {"name": "x"}})

    def test_cargo_without_package_or_workspace_is_refused(self):
        with pytest.raises(ValueError, match="needs a"):
            load_cargo_toml_doc({"dependencies": {"serde": "=1.0"}})


class TestFormatDetection:
    def test_pom_detected_from_structure_even_with_wrong_name(self, tmp_path):
        p = tmp_path / "go.mod"  # wrong name on purpose
        p.write_text(open(POM_FIXTURE, encoding="utf-8").read())
        deps, _, fmt = read_manifest(str(p))
        assert fmt == "pom"

    def test_go_mod_detected_from_module_directive_with_toml_name(self, tmp_path):
        p = tmp_path / "Cargo.toml"  # wrong name on purpose
        p.write_text(open(GO_FIXTURE, encoding="utf-8").read())
        deps, _, fmt = read_manifest(str(p))
        assert fmt == "go"

    def test_cargo_detected_by_tables_even_with_requirements_name(self, tmp_path):
        p = tmp_path / "requirements.txt"  # wrong name on purpose
        p.write_text(open(CARGO_FIXTURE, encoding="utf-8").read())
        deps, _, fmt = read_manifest(str(p))
        assert fmt == "cargo"

    def test_poetry_pyproject_detected_by_tool_table(self, tmp_path):
        p = tmp_path / "manifest.txt"
        p.write_text(open(POETRY_FIXTURE, encoding="utf-8").read())
        _, _, fmt = read_manifest(str(p))
        assert fmt == "pyproject"

    def test_malformed_fixture_refused_with_clean_error(self):
        with pytest.raises(ValueError, match="refusing to guess the format"):
            read_manifest(MALFORMED_FIXTURE)

    def test_size_cap_rejects_huge_files(self, tmp_path, monkeypatch):
        from core import manifest_reader

        p = tmp_path / "requirements.txt"
        p.write_text("django==4.2\n")
        monkeypatch.setattr(manifest_reader, "MAX_MANIFEST_BYTES", 10)
        with pytest.raises(ValueError) as excinfo:
            read_manifest(str(p))
        assert "limit 10" in str(excinfo.value)

    def test_cap_matches_sbom_policy_not_event_limit(self):
        """One bounded-read policy: the manifest cap reuses the SBOM cap
        (multi-MB manifests are legitimate), not the 1MB event cap."""
        from cli.main import MAX_INPUT_BYTES
        from core import sbom_reader

        assert MAX_MANIFEST_BYTES == sbom_reader.MAX_SBOM_BYTES
        assert MAX_MANIFEST_BYTES > MAX_INPUT_BYTES

    def test_non_utf8_input_is_refused_with_clean_error(self, tmp_path):
        p = tmp_path / "requirements.txt"
        p.write_bytes(b"django==4.2\n\xff\xfe garbage")
        with pytest.raises(ValueError, match="not UTF-8"):
            read_manifest(str(p))


class TestParityWithWatchlist:
    """Acceptance: pinned manifest entries produce identical verdicts to
    equivalent watchlist/lockfile entries - one identity engine, not a
    second matcher."""

    def _event(self, path):
        return OSSEvent(**json.load(open(path)))

    def test_requirements_django_matches_watchlist_verdict_for_verdict(self):
        event = self._event("data/fixtures/django-eol/event.json")
        man_deps, _, _ = read_manifest(REQUIREMENTS_FIXTURE)
        man_django = next(d for d in man_deps if d["package"] == "django")
        watchlist_shape = {
            "kind": "package",
            "package": "django",
            "ecosystem": "PyPI",
            "version": "4.2",
        }
        assert man_django == watchlist_shape
        from_watchlist = check_dependency(watchlist_shape, [event])
        from_manifest = check_dependency(man_django, [event])
        assert from_watchlist.affected is True
        assert from_manifest.affected is True
        assert from_watchlist.relationship == from_manifest.relationship == "AFFECTS_VERSION"
        assert from_watchlist.model_dump() == from_manifest.model_dump()

    def test_pyproject_django_is_the_same_shape_and_verdict(self):
        event = self._event("data/fixtures/django-eol/event.json")
        man_deps, _, _ = read_manifest(PEP621_FIXTURE)
        man_django = next(d for d in man_deps if d["package"] == "django")
        assert man_django == {
            "kind": "package",
            "package": "django",
            "ecosystem": "PyPI",
            "version": "4.2",
        }
        from_manifest = check_dependency(man_django, [event])
        assert from_manifest.affected is True
        assert from_manifest.relationship == "AFFECTS_VERSION"

    def test_pom_itext_correlates_like_the_sbom_purl(self):
        """The pom colon form (`com.itextpdf:itext-core`) is the same
        identity the sbom reader's maven purl mapping produces - the
        manifest path converges on the catalog hit without a second
        matching engine."""
        from core.entities.resolve import resolve_project
        from core.sbom_reader import _dep_from_purl

        deps, _, _ = read_manifest(POM_FIXTURE)
        itext = next(d for d in deps if d["package"] == "com.itextpdf:itext-core")
        purl_dep, _ = _dep_from_purl("pkg:maven/com.itextpdf/itext-core@8.0.2")
        assert itext == purl_dep
        assert resolve_project(itext["package"]) == "itext"

    def test_go_identity_keeps_the_full_module_path(self):
        """The go module path is the identity the golang purl mapping
        keeps (`github.com/redis/go-redis/v9`), matching the sbom
        reader's namespace/name join."""
        from core.sbom_reader import _dep_from_purl

        deps, _, _ = read_manifest(GO_FIXTURE)
        redis_go = next(d for d in deps if "go-redis" in d["package"])
        purl_dep, _ = _dep_from_purl("pkg:golang/github.com/redis/go-redis/v9@v9.0.0")
        assert redis_go == purl_dep

    def test_cargo_manifest_and_lockfile_agree_on_serde(self):
        from core.lockfile_reader import read_lockfile

        man_deps, _, _ = read_manifest(CARGO_FIXTURE)
        lock_deps, _, _ = read_lockfile("data/fixtures/lockfiles/Cargo.lock")
        man_serde = next(d for d in man_deps if d["package"] == "serde")
        lock_serde = next(d for d in lock_deps if d["package"] == "serde")
        assert man_serde == lock_serde


class TestCheckCliManifest:
    def _run(self, *args):
        from click.testing import CliRunner

        from cli.main import cli

        return CliRunner().invoke(cli, ["check", *args])

    def test_requirements_only_run_produces_watchlist_verdicts(self):
        out = self._run(
            "--manifest", REQUIREMENTS_FIXTURE, "--event", "data/fixtures/django-eol/event.json"
        )
        assert out.exit_code == 0, out.output
        assert "manifest (requirements.txt): 3 pinned package(s), 4 skipped" in out.output
        assert "! skipped: line 5: `requests>=2.31.0`" in out.output
        assert "django==4.2: AFFECTED (AFFECTS_VERSION)" in out.output
        assert "celery==5.4.0: UNKNOWN" in out.output
        assert "1/3 dependencies affected" in out.output

    def test_pom_only_run_reports_the_itext_license_event(self):
        out = self._run(
            "--manifest", POM_FIXTURE, "--event", "data/fixtures/itext-license/event.json"
        )
        assert out.exit_code == 0, out.output
        assert "manifest (pom.xml): 3 pinned package(s), 1 skipped" in out.output
        assert "com.itextpdf:itext-core==8.0.2: AFFECTED" in out.output
        assert "1/3 dependencies affected" in out.output

    def test_manifest_composes_with_watchlist(self):
        out = self._run(
            "--manifest",
            REQUIREMENTS_FIXTURE,
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
        )
        assert out.exit_code == 0, out.output
        assert "manifest (requirements.txt): 3 pinned package(s), 4 skipped" in out.output
        assert "1/6 dependencies affected" in out.output

    def test_manifest_composes_with_lockfile(self):
        out = self._run(
            "--manifest",
            REQUIREMENTS_FIXTURE,
            "--lockfile",
            "data/fixtures/lockfiles/poetry.lock",
            "--event",
            "data/fixtures/django-eol/event.json",
        )
        assert out.exit_code == 0, out.output
        assert "lockfile (poetry.lock): 2 pinned package(s), 1 skipped" in out.output
        assert "manifest (requirements.txt): 3 pinned package(s), 4 skipped" in out.output
        assert "2/5 dependencies affected" in out.output

    def test_malformed_manifest_exits_with_named_error(self):
        out = self._run(
            "--manifest", MALFORMED_FIXTURE, "--event", "data/fixtures/django-eol/event.json"
        )
        assert out.exit_code != 0
        assert "refusing to guess the format" in out.output

    def test_strict_fires_when_manifest_dep_is_affected(self):
        out = self._run(
            "--manifest",
            REQUIREMENTS_FIXTURE,
            "--event",
            "data/fixtures/django-eol/event.json",
            "--strict",
        )
        assert out.exit_code == 1

    def test_all_skip_manifest_echoes_reasons_then_reports_nothing_checkable(self, tmp_path):
        text = "[project]" + chr(10) + 'dependencies = ["requests>=2.0", "flask"]' + chr(10)
        p = tmp_path / "pyproject.toml"
        p.write_text(text)
        out = self._run("--manifest", str(p), "--event", "data/fixtures/django-eol/event.json")
        assert out.exit_code != 0
        output = out.output
        reasons_pos = output.find("! skipped:")
        guard_pos = output.find("no checkable dependencies")
        assert reasons_pos != -1 and guard_pos != -1
        assert reasons_pos < guard_pos, output
        assert "never range-guessed" in output

    def test_digest_output_includes_manifest_summary(self):
        out = self._run("--manifest", REQUIREMENTS_FIXTURE, "--digest")
        assert out.exit_code == 0, out.output
        assert "manifest (requirements.txt): 3 pinned package(s), 4 skipped" in out.output
