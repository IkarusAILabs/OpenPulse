"""Lockfile reader tests: pinned-entry discipline, parity, CLI wiring (npm/poetry/cargo)."""

import json

import pytest

from core.lockfile_reader import (
    MAX_LOCKFILE_BYTES,
    load_cargo_lock_doc,
    load_package_lock_doc,
    load_poetry_lock_doc,
    read_lockfile,
)
from core.risk.check import check_dependency
from core.schema.models import OSSEvent

NPM_FIXTURE = "data/fixtures/lockfiles/package-lock.json"
POETRY_FIXTURE = "data/fixtures/lockfiles/poetry.lock"
CARGO_FIXTURE = "data/fixtures/lockfiles/Cargo.lock"
MALFORMED_FIXTURE = "data/fixtures/lockfiles/malformed.txt"


class TestNpmReader:
    def test_fixture_pins_three_packages_and_records_four_skips(self):
        deps, skipped, fmt = read_lockfile(NPM_FIXTURE)
        assert fmt == "npm"
        assert deps == [
            {"kind": "package", "package": "lodash", "ecosystem": "npm", "version": "4.17.21"},
            {"kind": "package", "package": "@scope/util", "ecosystem": "npm", "version": "2.0.0"},
            {"kind": "package", "package": "redis", "ecosystem": "npm", "version": "4.7.0"},
        ]
        assert len(skipped) == 4
        assert any("root project entry" in line for line in skipped)
        assert any("`worker`: workspace link" in line for line in skipped)
        assert any("workspace member" in line for line in skipped)
        assert any("`missing-resolved`: no resolved version" in line for line in skipped)

    def test_v3_lock_with_only_root_is_refused_not_empty(self):
        doc = {"lockfileVersion": 3, "packages": {"": {"name": "root"}}}
        deps, skipped = load_package_lock_doc(doc)
        assert deps == []
        assert skipped == ['root project entry (`packages[""]`): not a dependency']

    def test_v1_lockfile_walks_nested_dependencies(self):
        doc = {
            "lockfileVersion": 1,
            "dependencies": {
                "a": {"version": "1.0.0", "dependencies": {"b": {"version": "2.0.0"}}},
            },
        }
        deps, skipped = load_package_lock_doc(doc)
        assert [d["package"] for d in deps] == ["a", "b"]
        assert not skipped

    def test_v1_entry_without_version_is_skipped_not_guessed(self):
        doc = {"lockfileVersion": 1, "dependencies": {"bare": {"resolved": "https://example.com"}}}
        deps, skipped = load_package_lock_doc(doc)
        assert deps == []
        assert "no resolved version" in skipped[0]

    def test_v2_lock_reads_packages_not_the_v1_view(self):
        """v2 carries both views; the richer path-keyed `packages`
        is the single source, so no dep is counted twice."""
        doc = {
            "lockfileVersion": 2,
            "packages": {"node_modules/left": {"version": "1.0.0"}},
            "dependencies": {"left": {"version": "1.0.0"}},
        }
        deps, _ = load_package_lock_doc(doc)
        assert len(deps) == 1

    def test_scoped_and_nested_names_resolve_from_paths(self):
        doc = {
            "lockfileVersion": 3,
            "packages": {
                "node_modules/@scope/util": {"version": "2.0.0"},
                "node_modules/a/node_modules/b": {"version": "1.0.0"},
            },
        }
        deps, _ = load_package_lock_doc(doc)
        assert {d["package"] for d in deps} == {"@scope/util", "b"}

    def test_npm_internal_metadata_keys_are_not_packages(self):
        doc = {"lockfileVersion": 3, "packages": {"node_modules/.package-lock.json": {"a": 1}}}
        deps, skipped = load_package_lock_doc(doc)
        assert deps == []
        assert "npm-internal metadata key" in skipped[0]

    def test_non_integer_lockfile_version_is_refused(self):
        with pytest.raises(ValueError, match="integer `lockfileVersion`"):
            load_package_lock_doc({"lockfileVersion": "3", "packages": {}})

    def test_empty_packages_and_dependencies_is_refused(self):
        with pytest.raises(ValueError, match="`packages` mapping"):
            load_package_lock_doc({"lockfileVersion": 3})


class TestPoetryReader:
    def test_fixture_pins_two_and_skips_the_unpinned_entry(self):
        deps, skipped, fmt = read_lockfile(POETRY_FIXTURE)
        assert fmt == "poetry"
        assert deps == [
            {"kind": "package", "package": "celery", "ecosystem": "PyPI", "version": "5.4.0"},
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"},
        ]
        assert skipped == ["`requests`: no pinned version - skipped, never range-guessed"]

    def test_entry_without_version_is_skipped_not_guessed(self):
        doc = {"lock-version": "2.1", "package": [{"name": "bare"}]}
        deps, skipped = load_poetry_lock_doc(doc)
        assert deps == []
        assert "no pinned version" in skipped[0]

    def test_entry_without_name_is_skipped(self):
        doc = {"lock-version": "2.1", "package": [{"version": "1.0"}]}
        deps, skipped = load_poetry_lock_doc(doc)
        assert deps == []
        assert "no name" in skipped[0]

    def test_missing_lock_version_marker_is_refused(self):
        with pytest.raises(ValueError, match="`lock-version` marker"):
            load_poetry_lock_doc({"package": [{"name": "x", "version": "1"}]})

    def test_zero_package_lock_is_valid_not_an_error(self):
        deps, skipped = load_poetry_lock_doc({"lock-version": "2.1", "package": []})
        assert deps == [] and skipped == []


class TestCargoReader:
    def test_fixture_pins_two_registry_crates_and_skips_the_rest(self):
        deps, skipped, fmt = read_lockfile(CARGO_FIXTURE)
        assert fmt == "cargo"
        assert deps == [
            {
                "kind": "package",
                "package": "serde",
                "ecosystem": "crates.io",
                "version": "1.0.210",
            },
            {
                "kind": "package",
                "package": "serde_derive",
                "ecosystem": "crates.io",
                "version": "1.0.210",
            },
        ]
        assert len(skipped) == 2
        assert any(
            "`local-crate`" in line and "identity would be a guess" in line for line in skipped
        )
        assert any("`git-sourced-crate`" in line for line in skipped)

    def test_non_registry_source_is_a_guess_so_skipped(self):
        doc = {
            "version": 4,
            "package": [
                {"name": "local", "version": "0.1.0"},
                {"name": "gitdep", "version": "0.2.0", "source": "git+https://example.com/x"},
            ],
        }
        deps, skipped = load_cargo_lock_doc(doc)
        assert deps == []
        assert len(skipped) == 2
        assert all("identity would be a guess" in line for line in skipped)

    def test_missing_version_is_skipped_not_guessed(self):
        doc = {"version": 4, "package": [{"name": "bare", "source": "registry+https://x"}]}
        deps, skipped = load_cargo_lock_doc(doc)
        assert deps == []
        assert "no pinned version" in skipped[0]

    def test_non_integer_root_version_is_refused(self):
        with pytest.raises(ValueError, match="integer root `version`"):
            load_cargo_lock_doc({"version": "4", "package": []})

    def test_registry_prefix_is_required_not_substring(self):
        doc = {
            "version": 4,
            "package": [
                # "sparse+registry" style is real in Cargo.lock v4; only
                # the `registry+` source is a crates.io pin.
                {"name": "v4-sparse", "version": "1.0", "source": "sparse+https://x"},
                {"name": "real", "version": "1.0", "source": "registry+https://x"},
            ],
        }
        deps, skipped = load_cargo_lock_doc(doc)
        assert [d["package"] for d in deps] == ["real"]
        assert len(skipped) == 1


class TestFormatDetection:
    def test_npm_detected_from_structure_even_with_toml_name(self, tmp_path):
        p = tmp_path / "poetry.lock"  # wrong name on purpose
        p.write_text(
            json.dumps({"lockfileVersion": 3, "packages": {"node_modules/x": {"version": "1"}}})
        )
        deps, _, fmt = read_lockfile(str(p))
        assert fmt == "npm"
        assert deps[0]["package"] == "x"

    def test_json_without_lockfile_version_is_refused(self, tmp_path):
        p = tmp_path / "package-lock.json"
        p.write_text(json.dumps({"name": "not-a-lock"}))
        with pytest.raises(ValueError, match="lockfileVersion"):
            read_lockfile(str(p))

    def test_malformed_fixture_refused_with_clean_error(self):
        with pytest.raises(ValueError, match="neither npm JSON nor valid TOML"):
            read_lockfile(MALFORMED_FIXTURE)

    def test_unknown_toml_is_refused_not_guessed(self, tmp_path):
        p = tmp_path / "Cargo.lock"
        p.write_text('[section]\nkey = "value"\n')
        with pytest.raises(ValueError, match="refusing to guess"):
            read_lockfile(str(p))

    def test_size_cap_rejects_huge_files(self, tmp_path, monkeypatch):
        from core import lockfile_reader

        p = tmp_path / "package-lock.json"
        p.write_text(json.dumps({"lockfileVersion": 3, "packages": {}}))
        monkeypatch.setattr(lockfile_reader, "MAX_LOCKFILE_BYTES", 10)
        with pytest.raises(ValueError) as excinfo:
            read_lockfile(str(p))
        assert "limit 10" in str(excinfo.value)

    def test_cap_matches_sbom_policy_not_event_limit(self):
        """One bounded-read policy: the lockfile cap reuses the SBOM
        cap (multi-MB inputs are legitimate), not the 1MB event cap."""
        from cli.main import MAX_INPUT_BYTES
        from core import sbom_reader

        assert MAX_LOCKFILE_BYTES == sbom_reader.MAX_SBOM_BYTES
        assert MAX_LOCKFILE_BYTES > MAX_INPUT_BYTES


class TestParityWithWatchlist:
    """Acceptance: pinned entries produce identical verdict shapes to
    equivalent watchlist entries — one identity/applicability engine,
    not a second matcher."""

    def _event(self, path):
        return OSSEvent(**json.load(open(path)))

    def test_poetry_django_matches_watchlist_django_verdict_for_verdict(self):
        event = self._event("data/fixtures/django-eol/event.json")
        poetry_deps, _, _ = read_lockfile(POETRY_FIXTURE)
        poetry_django = next(d for d in poetry_deps if d["package"] == "django")
        watchlist_django = {
            "kind": "package",
            "package": "django",
            "ecosystem": "PyPI",
            "version": "4.2",
        }
        assert poetry_django == watchlist_django
        from_watchlist = check_dependency(watchlist_django, [event])
        from_lockfile = check_dependency(poetry_django, [event])
        assert from_watchlist.affected is True
        assert from_lockfile.affected is True
        assert from_watchlist.relationship == from_lockfile.relationship == "AFFECTS_VERSION"
        assert from_watchlist.model_dump() == from_lockfile.model_dump()

    def test_npm_redis_package_parities_the_watchlist_shape(self):
        """The npm `redis` package (a library, not the image) must
        evaluate as a package dep exactly like a watchlist entry."""
        event = self._event("data/fixtures/bitnami/event.json")
        npm_deps, _, _ = read_lockfile(NPM_FIXTURE)
        npm_redis = next(d for d in npm_deps if d["package"] == "redis")
        watchlist_shape = {
            "kind": "package",
            "package": "redis",
            "ecosystem": "npm",
            "version": "4.7.0",
        }
        assert npm_redis == watchlist_shape
        from_watchlist = check_dependency(watchlist_shape, [event])
        from_lockfile = check_dependency(npm_redis, [event])
        assert from_watchlist.model_dump() == from_lockfile.model_dump()
        # redis the npm library is not docker.io/bitnami/redis:7.2 —
        # the artifact scope cannot claim it.
        assert from_lockfile.affected is False

    def test_cargo_serde_evaluates_through_the_same_engine(self):
        event = self._event("data/fixtures/django-eol/event.json")
        cargo_deps, _, _ = read_lockfile(CARGO_FIXTURE)
        serde = next(d for d in cargo_deps if d["package"] == "serde")
        from_lockfile = check_dependency(serde, [event])
        from_watchlist = check_dependency(dict(serde), [event])
        assert from_lockfile.model_dump() == from_watchlist.model_dump()
        assert from_lockfile.relationship == "UNKNOWN"


class TestCheckCliLockfile:
    def _run(self, *args):
        from click.testing import CliRunner

        from cli.main import cli

        return CliRunner().invoke(cli, ["check", *args])

    def test_poetry_lock_only_run_produces_watchlist_verdicts(self):
        out = self._run(
            "--lockfile", POETRY_FIXTURE, "--event", "data/fixtures/django-eol/event.json"
        )
        assert out.exit_code == 0, out.output
        assert "lockfile (poetry.lock): 2 pinned package(s), 1 skipped" in out.output
        assert "! skipped: `requests`" in out.output
        assert "django==4.2: AFFECTED (AFFECTS_VERSION)" in out.output
        assert "celery==5.4.0: UNKNOWN" in out.output
        assert "1/2 dependencies affected" in out.output

    def test_npm_lock_only_run_reports_zero_affected(self):
        out = self._run("--lockfile", NPM_FIXTURE, "--event", "data/fixtures/django-eol/event.json")
        assert out.exit_code == 0, out.output
        assert "lockfile (package-lock): 3 pinned package(s), 4 skipped" in out.output
        assert "redis==4.7.0: UNKNOWN" in out.output
        assert "0/3 dependencies affected" in out.output

    def test_lockfile_composes_with_watchlist(self):
        out = self._run(
            "--lockfile",
            POETRY_FIXTURE,
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            "data/fixtures/bitnami/event.json",
        )
        assert out.exit_code == 0, out.output
        # 2 poetry pins + 3 watchlist deps = 5 checkable; the watchlist
        # bitnami/redis:7.2 image matches the event artifact scope.
        assert "lockfile (poetry.lock): 2 pinned package(s), 1 skipped" in out.output
        assert "1/5 dependencies affected" in out.output

    def test_lockfile_composes_with_sbom(self):
        out = self._run(
            "--lockfile",
            NPM_FIXTURE,
            "--sbom",
            "data/fixtures/sbom/cyclonedx.json",
            "--event",
            "data/fixtures/bitnami/event.json",
        )
        assert out.exit_code == 0, out.output
        assert "sbom: 3 mapped component(s), 1 skipped" in out.output
        assert "lockfile (package-lock): 3 pinned package(s), 4 skipped" in out.output
        # 3 npm pins + 3 sbom components = 6; the sbom bitnami/redis:7.2
        # image is the one affected entry.
        assert "1/6 dependencies affected" in out.output

    def test_malformed_lockfile_exits_with_named_error(self):
        out = self._run(
            "--lockfile", MALFORMED_FIXTURE, "--event", "data/fixtures/django-eol/event.json"
        )
        assert out.exit_code != 0
        assert "is neither npm JSON nor valid TOML" in out.output

    def test_strict_fires_when_lockfile_dep_is_affected(self):
        out = self._run(
            "--lockfile",
            POETRY_FIXTURE,
            "--event",
            "data/fixtures/django-eol/event.json",
            "--strict",
        )
        assert out.exit_code == 1

    def test_all_skip_lockfile_echoes_reasons_then_reports_nothing_checkable(self, tmp_path):
        doc = {"lockfileVersion": 3, "packages": {"": {"name": "only-root"}}}
        p = tmp_path / "package-lock.json"
        p.write_text(json.dumps(doc))
        out = self._run("--lockfile", str(p), "--event", "data/fixtures/django-eol/event.json")
        assert out.exit_code != 0
        output = out.output
        reasons_pos = output.find("! skipped:")
        guard_pos = output.find("no checkable dependencies")
        assert reasons_pos != -1 and guard_pos != -1
        assert reasons_pos < guard_pos, output
        assert "root project entry" in output

    def test_digest_output_includes_lockfile_summary(self):
        out = self._run("--lockfile", POETRY_FIXTURE, "--digest")
        assert out.exit_code == 0, out.output
        assert "lockfile (poetry.lock): 2 pinned package(s), 1 skipped" in out.output
