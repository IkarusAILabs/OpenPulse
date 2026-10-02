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
