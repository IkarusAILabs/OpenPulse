import pytest


def test_legacy_aliases_preserved():
    from core.entities.resolve import resolve_project

    assert resolve_project("bitnami/redis:7.2") == "bitnami-redis-stack"
    assert resolve_project("docker.io/redis:7") == "redis"


def test_bitnami_namespace_rule():
    from core.entities.resolve import resolve_project

    assert resolve_project("docker.io/bitnami/postgresql:16") == "bitnami-postgresql"
    assert resolve_project("docker.io/bitnamilegacy/kafka:3.7") == "bitnami-kafka"
    assert resolve_project("bitnamisecure/redis:latest") == "bitnami-redis-stack"


def test_catalog_aliases():
    from core.entities.resolve import resolve_project

    assert resolve_project("postgres:16") == "postgresql"
    assert resolve_project("docker.io/library/postgres:16") == "postgresql"
    assert resolve_project("apache/kafka") == "kafka"


def test_catalog_alias_collision_names_both_slugs():
    from core.entities.catalog import CatalogCollisionError, catalog_alias_map

    with pytest.raises(
        CatalogCollisionError, match=r"'shared' claimed by both 'slug-alpha' and 'slug-beta'"
    ):
        catalog_alias_map(
            [
                {"slug": "slug-alpha", "aliases": ["shared"]},
                {"slug": "slug-beta", "aliases": ["shared"]},
            ]
        )


def test_catalog_docker_image_collision_raises():
    from core.entities.catalog import CatalogCollisionError, catalog_alias_map

    with pytest.raises(CatalogCollisionError, match=r"'docker.io/acme/app'"):
        catalog_alias_map(
            [
                {"slug": "slug-alpha", "docker_images": ["docker.io/acme/app"]},
                {"slug": "slug-beta", "aliases": ["docker.io/acme/app"]},
            ]
        )


def test_catalog_repeated_alias_within_one_slug_is_not_a_collision():
    from core.entities.catalog import catalog_alias_map

    alias_map = catalog_alias_map([{"slug": "solo", "aliases": ["x"], "docker_images": ["x"]}])
    assert alias_map["x"] == "solo"


def test_shipped_catalog_has_no_collisions():
    from core.entities.catalog import catalog_alias_map, load_catalog

    assert catalog_alias_map(load_catalog())


def test_catalog_yaml_file_collision_raises(tmp_path):
    import yaml

    from core.entities.catalog import CatalogCollisionError, catalog_alias_map, load_catalog

    path = tmp_path / "catalog.yaml"
    path.write_text(
        yaml.safe_dump([{"slug": "x", "aliases": ["dup"]}, {"slug": "y", "aliases": ["dup"]}]),
        encoding="utf-8",
    )
    with pytest.raises(CatalogCollisionError, match=r"'dup' claimed by both 'x' and 'y'"):
        catalog_alias_map(load_catalog(str(path)))


@pytest.fixture
def colliding_catalog(monkeypatch):
    """The default catalog replaced by one with a collision, caches cleared."""
    import core.entities.catalog as catalog_module
    from core.entities import resolve

    colliding = [
        {"slug": "postgresql", "aliases": ["postgres"]},
        {"slug": "impostor", "aliases": ["postgres"]},
    ]
    monkeypatch.setattr(catalog_module, "load_catalog", lambda path=None: colliding)
    resolve._catalog_map.cache_clear()
    yield
    resolve._catalog_map.cache_clear()


def test_collision_surfaces_in_resolution_not_as_an_empty_catalog(colliding_catalog):
    from core.entities.catalog import CatalogCollisionError
    from core.entities.resolve import resolve_project

    # Before #144 the resolver swallowed this into {}, so every reference
    # silently resolved to itself.
    with pytest.raises(CatalogCollisionError):
        resolve_project("postgres:16")


def test_collision_surfaces_in_trust_resolution(colliding_catalog):
    from core.entities.catalog import CatalogCollisionError
    from core.entities.identity import resolution_trust

    with pytest.raises(CatalogCollisionError):
        resolution_trust("postgres:16")


def test_cli_reports_a_collision_cleanly(colliding_catalog):
    from click.testing import CliRunner

    from cli.main import cli

    watchlist = "data/fixtures/watchlist_sample.yaml"
    result = CliRunner().invoke(cli, ["check", "--watchlist", watchlist])
    assert result.exit_code == 1
    assert "catalog alias collision: 'postgres' claimed by both" in result.output
    assert "Traceback" not in result.output
    assert not isinstance(result.exception, ValueError)  # a clean ClickException exit


def test_catalog_hygiene():
    from core.entities.catalog import catalog_alias_map, load_catalog

    catalog = load_catalog()
    assert len(catalog) >= 10
    for entry in catalog:
        assert entry.get("slug")
    for alias in catalog_alias_map(catalog):
        assert alias == alias.strip().lower()
        assert ":" not in alias and "@" not in alias


def test_catalog_identity_metadata_optional():
    from core.entities.catalog import load_catalog
    from core.entities.identity import (
        REVIEW_REQUIRED,
        VERIFIED,
        identity_block_for_slug,
    )

    catalog = load_catalog()
    by_slug = {e.get("slug"): e for e in catalog}
    for slug in ("redis", "kafka", "spring-boot", "bitnami-redis-stack"):
        block = identity_block_for_slug(slug, catalog)
        assert block.get("status") in (VERIFIED, REVIEW_REQUIRED), slug
        assert block.get("reviewed_at"), slug
    assert identity_block_for_slug("redis", catalog)["status"] == "VERIFIED"
    assert identity_block_for_slug("spring-boot", catalog)["status"] == "REVIEW_REQUIRED"
    # Entries reviewed on 2026-10-02 (issue #15): forks, renames,
    # ecosystem mappings, and namespace collisions.
    verified = (
        "jaeger",
        "clickhouse",
        "itext",
        "mariadb",
        "redpanda",
        "valkey",
        "nodejs",
        "cpython",
        "pytorch",
        "transformers",
    )
    review_required = ("vue", "angular", "junit", "flux", "linkerd", "go", "nats")
    for slug in verified + review_required:
        block = identity_block_for_slug(slug, catalog)
        assert block.get("source"), slug
        assert block.get("reviewed_at"), slug
        assert block.get("maintainer"), slug
        assert block.get("confidence") in ("high", "medium", "low"), slug
    for slug in verified:
        assert identity_block_for_slug(slug, catalog)["status"] == VERIFIED, slug
    for slug in review_required:
        assert identity_block_for_slug(slug, catalog)["status"] == REVIEW_REQUIRED, slug
    # Unreviewed entries simply lack identity metadata — never assumed reviewed.
    assert identity_block_for_slug("django", catalog) == {}
    assert "identity" not in by_slug["django"]


def test_identity_status_values_valid():
    from core.entities.catalog import load_catalog
    from core.entities.identity import VALID_STATUSES

    for entry in load_catalog():
        block = entry.get("identity")
        if isinstance(block, dict) and "status" in block:
            assert str(block["status"]).upper() in VALID_STATUSES, entry.get("slug")


def test_purl_builder():
    from core.entities.catalog import purl_for

    assert purl_for("docker", "bitnami", "redis", "7.2") == "pkg:docker/bitnami/redis@7.2"
    assert purl_for("github", "redis", "redis") == "pkg:github/redis/redis"


def test_endoflife_map_verified_overrides():
    from core.entities.catalog import endoflife_map, load_catalog

    mapping = endoflife_map(load_catalog())
    assert mapping["kafka"] == "apache-kafka"
    assert mapping["spark"] == "apache-spark"
    assert mapping["maven"] == "apache-maven"
    assert mapping["pulsar"] == "apache-pulsar"
    assert mapping["cpython"] == "python"
    assert "redis" not in mapping  # slug == product needs no override
    for product in mapping.values():
        assert product == product.strip().lower()
        assert " " not in product


def test_catalog_new_entries_resolve():
    from core.entities.resolve import resolve_project

    assert resolve_project("airflow") == "airflow"
    assert resolve_project("apache/airflow") == "airflow"
    assert resolve_project("spark") == "spark"
    assert resolve_project("apache/spark") == "spark"
    assert resolve_project("minio") == "minio"
    assert resolve_project("minio/minio") == "minio"
    assert resolve_project("docker.io/minio/minio") == "minio"
    assert resolve_project("celery") == "celery"
    assert resolve_project("zookeeper") == "zookeeper"
    assert resolve_project("apache/zookeeper") == "zookeeper"


def test_registry_port_is_not_a_tag():
    """Regression: normalize_ref cut at the first colon, so every image on
    `host:port` collapsed to one VERIFIED `host` identity."""
    from core.entities.identity import resolution_trust
    from core.entities.resolve import normalize_ref, resolve_project

    assert normalize_ref("localhost:5000/team/redis:7") == "localhost:5000/team/redis"
    assert normalize_ref("Registry.Example.com:5000/a/postgres") == (
        "registry.example.com:5000/a/postgres"
    )
    assert normalize_ref("registry.example.com:5000/ns/repo@sha256:abc") == (
        "registry.example.com:5000/ns/repo"
    )
    assert normalize_ref("ghcr.io/org/app:1.2@sha256:abc") == "ghcr.io/org/app"
    # two images on one private registry keep distinct identities
    assert resolve_project("localhost:5000/team/redis:7") != resolve_project(
        "localhost:5000/team/nginx:1"
    )
    assert resolution_trust("localhost:5000/team/redis:7")["slug"] != "localhost"


def test_single_segment_refs_keep_first_colon_cut():
    from core.entities.resolve import normalize_ref, resolve_project

    assert normalize_ref("redis:7") == "redis"
    assert normalize_ref("redis@sha256:abc") == "redis"
    assert normalize_ref("com.itextpdf:itext-core") == "com.itextpdf"
    # the maven fallback still resolves from the raw ref
    assert resolve_project("com.itextpdf:itext-core") == "itext"


def test_private_registry_images_do_not_cross_match():
    from core.risk.match import match_artifact

    assert match_artifact("localhost:5000/team/redis:7", "localhost:5000/team/redis:6")
    assert not match_artifact("localhost:5000/team/redis:7", "localhost:5000/team/nginx:1")


def test_package_identity_is_per_ecosystem():
    """F1: a package name identifies a project only inside its ecosystem."""
    from core.entities.identity import package_trust

    assert package_trust("redis", "PyPI")["slug"] == "redis-py"
    assert package_trust("redis", "npm")["slug"] == "node-redis"
    assert package_trust("Django", "PyPI")["slug"] == "django"
    # PEP 503 folding for PyPI names.
    assert package_trust("django", "pypi")["slug"] == "django"


def test_alias_of_a_package_curated_project_is_not_identity():
    """Redis declares no packages, so a Maven `redis` that only shares the
    alias is unresolved (qualified by ecosystem), never the server."""
    from core.entities.identity import package_trust

    trust = package_trust("redis", "Maven")
    assert trust["via"] == "self"
    assert trust["slug"] == "maven:redis"


def test_package_without_ecosystem_keeps_name_resolution():
    from core.entities.identity import package_trust

    for ecosystem in (None, "", "generic"):
        assert package_trust("redis", ecosystem)["slug"] == "redis"


def test_redis_py_end_of_life_is_not_the_servers():
    """End to end: Redis server 6.2 EOL says nothing about redis-py 6.2.0."""
    import json
    from datetime import date

    from analyzers.change_analyst import analyze
    from analyzers.lifecycle_events import finding_to_event
    from core.risk.check import check_dependency

    raw = json.load(open("data/fixtures/redis/raw_bundle.json", encoding="utf-8"))
    (finding,) = [f for f in analyze(raw, today=date(2026, 9, 26)) if f["event_type"] == "EOL"]
    event = finding_to_event(finding, "redis", today=date(2026, 9, 26))
    client = {"kind": "package", "package": "redis", "ecosystem": "PyPI", "version": "6.2.0"}
    unknown_eco = {"kind": "package", "package": "redis", "ecosystem": "Maven", "version": "6.2.0"}
    assert check_dependency(client, [event]).relationship == "UNKNOWN"
    assert check_dependency(unknown_eco, [event]).relationship == "RELATED"


#: Ecosystem names as the readers emit them (manifest, lockfile, SBOM).
_ECOSYSTEMS = {"PyPI", "npm", "Maven", "Go", "crates.io"}


def test_every_catalog_entry_curates_its_packages():
    """Package curation (2026-10-30): every entry states which packages ARE
    the project, possibly none. A new entry without the list would let a
    same-named package of another ecosystem resolve to it by name (F1)."""
    from core.entities.catalog import load_catalog, package_name_key

    claimed = {}
    for entry in load_catalog():
        assert "packages" in entry, entry["slug"]
        for package in entry["packages"]:
            assert package["ecosystem"] in _ECOSYSTEMS, (entry["slug"], package)
            name = str(package["name"])
            assert name == name.strip() and "@" not in name.lstrip("@"), (entry["slug"], name)
            if package["ecosystem"] == "Maven":
                assert name.count("/") == 1 and ":" not in name, (entry["slug"], name)
            key = package_name_key(package["ecosystem"], name)
            assert claimed.setdefault(key, entry["slug"]) == entry["slug"], key


def test_registry_name_collisions_resolve_per_ecosystem():
    from core.entities.identity import package_trust

    resolved = {
        ("npm", "@angular/core"): "angular",
        ("PyPI", "torch"): "pytorch",
        ("Maven", "org.apache.kafka:kafka-clients"): "kafka",
        ("Maven", "com.itextpdf:sign"): "itext",
        ("PyPI", "apache-airflow"): "airflow",
        ("crates.io", "serde"): "serde",
    }
    for (ecosystem, name), slug in resolved.items():
        assert package_trust(name, ecosystem)["slug"] == slug, (ecosystem, name)
    # Same names, different projects: unresolved, never the server or framework.
    for ecosystem, name in [
        ("npm", "angular"),  # AngularJS 1.x
        ("PyPI", "kubernetes"),  # the Python client
        ("PyPI", "kafka"),  # an old kafka-python name
        ("npm", "mongodb"),  # the Node.js driver
        ("PyPI", "pytorch"),  # a placeholder
        ("PyPI", "elasticsearch"),  # the Python client
    ]:
        assert package_trust(name, ecosystem)["via"] == "self", (ecosystem, name)



def test_normalize_ref_keeps_a_leading_npm_scope():
    from core.entities.resolve import normalize_ref

    assert normalize_ref("@types/node") == "@types/node"
    assert normalize_ref("@Colors/Colors") == "@colors/colors"
    assert normalize_ref("@babel/core@7.0.0") == "@babel/core"  # a version suffix is still cut
    assert normalize_ref("redis@sha256:abc") == "redis"  # digests are unchanged
    assert normalize_ref("ghcr.io/org/app:1.2@sha256:abc") == "ghcr.io/org/app"


def test_scoped_npm_packages_have_distinct_identities():
    """Every uncatalogued scoped package used to share the empty identity."""
    from core.entities.identity import package_trust

    slugs = {p: package_trust(p, "npm")["slug"] for p in ("@types/node", "@babel/core")}
    assert slugs == {"@types/node": "@types/node", "@babel/core": "@babel/core"}
    # A scoped fork is not the unscoped package it forked.
    assert package_trust("@colors/colors", "npm")["slug"] != package_trust("colors", "npm")["slug"]
    # A curated scoped package still resolves through the catalog.
    assert package_trust("@angular/core", "npm")["via"] == "catalog"


def test_derived_catalog_maps_are_memoised_per_catalog_object():
    """Identity resolution rebuilt these maps on every dependency check."""
    from core.entities.catalog import (
        catalog_alias_map,
        load_catalog,
        package_curated_slugs,
        package_map,
    )

    catalog = load_catalog()
    for build in (package_map, package_curated_slugs, catalog_alias_map):
        assert build(catalog) is build(catalog)
    assert package_map() is package_map(catalog)  # the default is the same object


def test_derived_catalog_maps_follow_a_different_or_grown_catalog():
    from core.entities.catalog import load_catalog, package_map

    base = list(load_catalog())
    extra = {"slug": "zz-new", "packages": [{"ecosystem": "npm", "name": "zz-new-pkg"}]}
    other = [*base, extra]
    assert ("npm", "zz-new-pkg") not in package_map(base)
    assert package_map(other)[("npm", "zz-new-pkg")] == "zz-new"
    base.append(extra)  # grown in place: the length guard rebuilds
    assert package_map(base)[("npm", "zz-new-pkg")] == "zz-new"


def test_derived_catalog_maps_are_read_only():
    from core.entities.catalog import catalog_alias_map, load_catalog, package_map

    with pytest.raises(TypeError):
        package_map()[("npm", "x")] = "y"
    with pytest.raises(TypeError):
        catalog_alias_map(load_catalog())["x"] = "y"
