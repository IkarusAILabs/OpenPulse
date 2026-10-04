"""CycloneDX SBOM reader tests: purl mapping, skip-and-record, CLI wiring."""

import json

import pytest

from core.entities.resolve import resolve_project
from core.sbom_reader import (
    MAX_SBOM_BYTES,
    _dep_from_purl,
    _split_purl,
    load_sbom_doc,
    read_sbom,
)

FIXTURE = "data/fixtures/sbom/cyclonedx.json"


class TestPurlParsing:
    def test_split_basic(self):
        assert _split_purl("pkg:pypi/django@5.0") == {
            "type": "pypi",
            "namespace": "",
            "name": "django",
            "version": "5.0",
        }

    def test_split_nested_namespace(self):
        assert _split_purl("pkg:maven/com.itextpdf/itext-core@8.0.2") == {
            "type": "maven",
            "namespace": "com.itextpdf",
            "name": "itext-core",
            "version": "8.0.2",
        }

    def test_split_strips_qualifiers_and_subpath(self):
        assert _split_purl("pkg:npm/lodash@4.17.21?arch=amd64#dist/npm") == {
            "type": "npm",
            "namespace": "",
            "name": "lodash",
            "version": "4.17.21",
        }

    def test_split_without_version(self):
        assert _split_purl("pkg:docker/redis")["version"] == ""

    def test_split_rejects_non_purl(self):
        assert _split_purl("docker.io/bitnami/redis:7.2") is None
        assert _split_purl("pkg:") is None
        assert _split_purl("pkg:/only-namespace") is None

    def test_split_empty_version_is_rejected(self):
        # a trailing @ with no version cannot carry identity
        assert _split_purl("pkg:pypi/django@") is None


class TestDepMapping:
    def test_docker_purl_maps_to_image_ref(self):
        dep, reason = _dep_from_purl("pkg:docker/bitnami/redis@7.2")
        assert dep == {"kind": "image", "ref": "bitnami/redis:7.2"}
        assert reason is None

    def test_docker_purl_bare_name_is_hub_library(self):
        dep, _ = _dep_from_purl("pkg:docker/redis@7")
        assert dep == {"kind": "image", "ref": "redis:7"}

    def test_docker_digest_purl_attaches_with_at(self):
        dep, _ = _dep_from_purl("pkg:docker/bitnami/redis@sha256:abc123")
        assert dep == {"kind": "image", "ref": "bitnami/redis@sha256:abc123"}

    def test_pypi_maps_to_package_with_version(self):
        dep, _ = _dep_from_purl("pkg:pypi/django@5.0")
        assert dep == {
            "kind": "package",
            "package": "django",
            "ecosystem": "PyPI",
            "version": "5.0",
        }

    def test_maven_coordinates_use_colon_form(self):
        dep, _ = _dep_from_purl("pkg:maven/com.itextpdf/itext-core@8.0.2")
        assert dep == {
            "kind": "package",
            "package": "com.itextpdf:itext-core",
            "ecosystem": "Maven",
            "version": "8.0.2",
        }

    def test_npm_scope_decoded(self):
        dep, _ = _dep_from_purl("pkg:npm/%40angular/core@16.0.0")
        assert dep == {
            "kind": "package",
            "package": "@angular/core",
            "ecosystem": "npm",
            "version": "16.0.0",
        }

    def test_golang_full_path_kept(self):
        dep, _ = _dep_from_purl("pkg:golang/github.com/redis/go-redis@v9.0.0")
        assert dep == {
            "kind": "package",
            "package": "github.com/redis/go-redis",
            "ecosystem": "Go",
            "version": "v9.0.0",
        }

    def test_unmapped_purl_type_skip_and_record(self):
        dep, reason = _dep_from_purl("pkg:composer/symfony/http-foundation@7.0")
        assert dep is None
        assert "composer" in reason and "no unambiguous ecosystem mapping" in reason

    def test_unparseable_purl_skip_and_record(self):
        dep, reason = _dep_from_purl("not-a-purl")
        assert dep is None
        assert "not a parseable package URL" in reason

    def test_maven_without_groupid_is_skipped(self):
        dep, reason = _dep_from_purl("pkg:maven/itext-core@8.0.2")
        assert dep is None
        assert "no maven groupId namespace" in reason


class TestLoadSbomDoc:
    def test_fixture_maps_docker_and_pypi_records_composer(self):
        deps, skipped = read_sbom(FIXTURE)
        assert {"kind": "image", "ref": "bitnami/redis:7.2"} in deps
        assert {
            "kind": "package",
            "package": "django",
            "ecosystem": "PyPI",
            "version": "5.0",
        } in deps
        assert {
            "kind": "package",
            "package": "com.itextpdf:itext-core",
            "ecosystem": "Maven",
            "version": "8.0.2",
        } in deps
        assert len(deps) == 3
        assert len(skipped) == 1
        assert "composer" in skipped[0]

    def test_maven_colon_form_correlates_against_osv(self):
        """The colon form is what OSV/NVD records spell - prove the
        dep string survives to identity comparison and matches an OSV
        entry whose package field carries the same coordinates."""
        from analyzers.security_analyst import correlate

        deps, _ = read_sbom(FIXTURE)
        maven = next(d for d in deps if d.get("ecosystem") == "Maven")
        assert maven["package"] == "com.itextpdf:itext-core"
        slug = resolve_project(maven["package"])
        assert slug == "itext", slug
        raw = {
            "osv": [
                {
                    "collector": "osv",
                    "package": "com.itextpdf:itext-core",
                    "ecosystem": "Maven",
                    "id": "CVE-2026-0200",
                    "severity": [{"score": 7.5}],
                    "affected": [
                        {
                            "package": "com.itextpdf:itext-core",
                            "ecosystem": "Maven",
                            "ranges": [
                                {
                                    "type": "ECOSYSTEM",
                                    "events": [
                                        {"introduced": "0"},
                                        {"fixed": "8.0.3"},
                                    ],
                                }
                            ],
                            "fixed": ["8.0.3"],
                            "versions": [],
                        }
                    ],
                    "references": [],
                }
            ]
        }
        context = {
            "slug": slug,
            "package": maven["package"],
            "ecosystem": maven["ecosystem"],
            "version": maven["version"],
        }
        findings = correlate(raw, context)
        assert findings, "colon-form package must correlate against OSV records"
        assert findings[0]["relationship"] == "AFFECTS_VERSION"
        assert findings[0]["cve_id"] == "CVE-2026-0200"

    def test_maven_colon_form_resolves_to_catalog_slug(self):
        """The colon form must resolve identity like the purl spelling:
        slug via the catalog, trust VERIFIED via catalog mapping."""
        from core.entities.identity import resolution_trust

        trust = resolution_trust("com.itextpdf:itext-core")
        assert trust["slug"] == "itext"
        assert trust["via"] == "catalog"
        assert trust["identity_status"] == "VERIFIED"
        # the purl spelling resolves identically - one identity
        assert (
            resolve_project("com.itextpdf:itext-core")
            == resolve_project("com.itextpdf/itext-core")
            == "itext"
        )

    def test_maven_colon_form_event_scope_still_matches(self):
        """Regression guard: switching the reader to colon form must not
        break package-scope events that list the purl spelling - the
        slug (not the raw string) carries the identity."""
        from core.risk.check import check_dependency
        from core.schema.models import OSSEvent

        event = OSSEvent(**json.load(open("data/fixtures/itext-license/event.json")))
        deps, _ = read_sbom(FIXTURE)
        maven = next(d for d in deps if d.get("ecosystem") == "Maven")
        verdict = check_dependency(maven, [event])
        assert verdict.affected is True
        assert verdict.relationship == "AFFECTS_PACKAGE"

    def test_sbom_deps_feed_check_dependency_unchanged(self):
        # the whole point: SBOM entries produce watchlist-shaped verdicts
        from core.risk.check import check_dependency
        from core.schema.models import OSSEvent

        event = OSSEvent(**json.load(open("data/fixtures/bitnami/event.json")))
        deps, _ = read_sbom(FIXTURE)
        image = next(d for d in deps if d["kind"] == "image")
        verdict = check_dependency(image, [event])
        assert verdict.affected is True
        assert verdict.relationship == "AFFECTS_ARTIFACT"

        package = next(d for d in deps if d["kind"] == "package")
        package_verdict = check_dependency(package, [event])
        assert package_verdict.affected is False

    def test_docker_purl_version_reaches_version_scopes_as_tag(self):
        # a docker purl version must reach tag_of() as a real tag
        from core.risk.match import tag_of

        dep, _ = _dep_from_purl("pkg:docker/library/redis@7.2")
        assert tag_of(dep["ref"]) == "7.2"

    def test_component_without_purl_is_skipped(self):
        doc = {
            "specVersion": "1.5",
            "components": [{"type": "library", "name": "mystery", "version": "1"}],
        }
        deps, skipped = load_sbom_doc(doc)
        assert deps == []
        assert len(skipped) == 1
        assert "no purl" in skipped[0]

    def test_non_mapping_component_is_skipped(self):
        doc = {"specVersion": "1.5", "components": ["not-a-mapping"]}
        deps, skipped = load_sbom_doc(doc)
        assert deps == []
        assert skipped == ["component #0: not a mapping"]

    def test_invalid_documents_raise_value_error(self):
        with pytest.raises(ValueError, match="components"):
            load_sbom_doc({})
        with pytest.raises(ValueError, match="specVersion"):
            load_sbom_doc({"components": [{"purl": "pkg:pypi/django@5.0"}]})
        with pytest.raises(ValueError, match="mapping"):
            load_sbom_doc(["not-a-mapping-doc"])

    def test_empty_components_list_is_rejected(self):
        with pytest.raises(ValueError, match="non-empty"):
            load_sbom_doc({"specVersion": "1.5", "components": []})


class TestCheckCliSbom:
    def _run(self, *args):
        from click.testing import CliRunner

        from cli.main import cli

        return CliRunner().invoke(cli, ["check", *args])

    def test_sbom_only_run_produces_watchlist_verdicts(self):
        out = self._run("--sbom", FIXTURE, "--event", "data/fixtures/bitnami/event.json")
        assert out.exit_code == 0, out.output
        assert "sbom: 3 mapped component(s), 1 skipped" in out.output
        assert "! skipped: component" in out.output
        assert "pkg:composer/symfony/http-foundation@7.0" in out.output
        assert "bitnami/redis:7.2: AFFECTED" in out.output
        assert "django" in out.output
        # maven colon form flows through the whole check path: the
        # bitnami event says nothing about itext, so the honest verdict
        # is UNKNOWN - evaluated, no applicable evidence (not a crash,
        # not a false AFFECTED from a broken identity chain).
        assert "com.itextpdf:itext-core==8.0.2: UNKNOWN" in out.output
        assert "1/3 dependencies affected" in out.output

    def test_sbom_composes_with_watchlist(self):
        out = self._run(
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--sbom",
            FIXTURE,
            "--event",
            "data/fixtures/bitnami/event.json",
        )
        assert out.exit_code == 0, out.output
        # 3 watchlist deps + 3 mapped SBOM deps = 6 checkable entries;
        # bitnami/redis:7.2 appears in both inputs and matches the event
        # artifact scope both times, so exactly 2 of 6 are affected.
        assert "sbom: 3 mapped component(s), 1 skipped" in out.output
        assert "2/6 dependencies affected" in out.output

    def test_sbom_strict_fires_when_affected(self):
        out = self._run(
            "--sbom", FIXTURE, "--event", "data/fixtures/bitnami/event.json", "--strict"
        )
        assert out.exit_code == 1

    def test_sbom_all_skipped_reports_nothing_checkable(self, tmp_path):
        doc = {
            "specVersion": "1.5",
            "components": [
                {
                    "type": "library",
                    "name": "s",
                    "purl": "pkg:composer/symfony/http-foundation@7.0",
                }
            ],
        }
        path = tmp_path / "sbom.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        out = self._run("--sbom", str(path), "--event", "data/fixtures/bitnami/event.json")
        assert out.exit_code != 0
        assert "0 mapped" in out.output
        assert "no checkable dependencies" in out.output

    def test_sbom_size_cap_rejects_huge_files(self, tmp_path, monkeypatch):
        """Bounded read: over the cap -> clean ValueError naming it."""
        from core import sbom_reader

        doc = {
            "specVersion": "1.5",
            "components": [{"type": "library", "name": "django", "purl": "pkg:pypi/django@5.0"}],
        }
        path = tmp_path / "sbom.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        # monkeypatch the cap down so the test does not write 50MB
        monkeypatch.setattr(sbom_reader, "MAX_SBOM_BYTES", 10)
        with pytest.raises(ValueError) as excinfo:
            read_sbom(str(path))
        assert "limit 10" in str(excinfo.value)

    def test_sbom_under_cap_still_loads(self, tmp_path):
        """The cap bounds, it does not break normal loads."""
        doc = {
            "specVersion": "1.5",
            "components": [{"type": "library", "name": "django", "purl": "pkg:pypi/django@5.0"}],
        }
        path = tmp_path / "sbom.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        deps, skipped = read_sbom(str(path))
        assert len(deps) == 1 and not skipped

    def test_cap_is_documented_larger_than_event_limit(self):
        """Policy check: SBOM cap must exceed the 1MB event-input cap
        (multi-MB SBOMs are legitimate) but stay bounded."""
        from cli.main import MAX_INPUT_BYTES

        assert MAX_SBOM_BYTES > MAX_INPUT_BYTES

    def test_all_skip_sbom_echoes_reasons_before_dying(self, tmp_path):
        """Suggestion from review: an SBOM yielding only skips must
        explain itself before the nothing-checkable error kills the
        run - reasons echo ahead of the guard, not only with a
        partial mapping."""
        doc = {
            "specVersion": "1.5",
            "components": [
                {
                    "type": "library",
                    "name": "s",
                    "purl": "pkg:composer/symfony/http-foundation@7.0",
                },
                {"type": "library", "name": "bare", "purl": "pkg:maven/itext-core@8.0.2"},
            ],
        }
        path = tmp_path / "sbom.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        out = self._run("--sbom", str(path), "--event", "data/fixtures/bitnami/event.json")
        assert out.exit_code != 0
        output = out.output
        # skip reasons precede the nothing-checkable error
        reasons_pos = output.find("! skipped: component `pkg:composer")
        guard_pos = output.find("no checkable dependencies")
        assert reasons_pos != -1 and guard_pos != -1
        assert reasons_pos < guard_pos, output
        assert "no maven groupId namespace" in output

    def test_check_requires_at_least_one_input(self):
        out = self._run("--event", "data/fixtures/bitnami/event.json")
        assert out.exit_code != 0
        assert "needs --watchlist and/or --sbom" in out.output

    def test_sbom_digest_output(self):
        out = self._run("--sbom", FIXTURE, "--digest")
        assert out.exit_code == 0, out.output
        assert "sbom: 3 mapped component(s), 1 skipped" in out.output
        assert "! skipped: component" in out.output
