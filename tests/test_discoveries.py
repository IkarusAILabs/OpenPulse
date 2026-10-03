"""M2 discovery replays — accepted cases re-fire from recorded evidence.

Each test replays one formalized discovery (see docs/DISCOVERIES.md)
from its recorded inputs and asserts the full acceptance shape:
finding type, impact, scope, evidence identity, and dates. If a case
cannot replay, it does not count — remove it from the ledger, do not
weaken the test.
"""

from analyzers.change_analyst import analyze_github_meta

# Recorded live 2026-10-02: minio/minio repo_meta (archived, owner unchanged).
MINIO_META = {
    "collector": "github",
    "kind": "repo_meta",
    "repo": "minio/minio",
    "full_name": "minio/minio",
    "archived": True,
    "pushed_at": "2026-04-24T17:54:39Z",
    "default_branch": "master",
    "license": "AGPL-3.0",
    "stargazers": 54000,
    "url": "https://github.com/minio/minio",
}


def test_minio_archived_replays():
    findings = analyze_github_meta([MINIO_META])
    assert len(findings) == 1
    finding = findings[0]
    assert finding["event_type"] == "PROJECT_ARCHIVED"
    assert finding["impact"] == "ACTION"
    assert finding["lifecycle_state"] == "EFFECTIVE"
    assert finding["scope"] == {"kind": "project", "versions": []}
    assert finding["supporting"] == [MINIO_META]


def test_minio_shows_no_ownership_drift():
    """The detector must not hallucinate on the verified case: same
    owner in, no OWNERSHIP_CHANGE out."""
    findings = analyze_github_meta([MINIO_META])
    assert all(f["event_type"] != "OWNERSHIP_CHANGE" for f in findings)


def test_bitnami_digest_mainline_gap_closed():
    """The version-aware latest-only rule derives the Bitnami split
    from the recorded probe shapes: bitnami/redis serves `latest` +
    hundreds of `sha256-*` digest tags (recorded full-set observation,
    2026-10-02), which is distribution machinery, not a versioned
    distribution — so the mainline counts as latest-only and the
    model-change finding fires against bitnamilegacy/redis holding
    the 919+ version-like tags (see docs/DISCOVERIES.md case 2).
    The flags below are exactly what `parse_tags` produces for those
    two recorded tag sets (see `test_parse_tags_version_aware_flags`),
    not hand-tuned to force the firing.
    """
    from analyzers.change_analyst import analyze_registries
    from collectors.registries.docker import parse_tags

    bitnami_tags = ["latest"] + [f"sha256-{i}" for i in range(5)]
    legacy_tags = ["latest", "7.2.0", "5.0.4", "5.0.3-r75"]
    bitnami_probe = parse_tags(
        "bitnami",
        "redis",
        {"count": len(bitnami_tags), "results": [{"name": t} for t in bitnami_tags]},
    )
    legacy_probe = parse_tags(
        "bitnamilegacy",
        "redis",
        {"count": len(legacy_tags), "results": [{"name": t} for t in legacy_tags]},
    )
    assert bitnami_probe["latest_only"] is True
    assert bitnami_probe["has_versioned_tags"] is False
    assert legacy_probe["latest_only"] is False
    assert legacy_probe["has_versioned_tags"] is True

    findings = analyze_registries([bitnami_probe, legacy_probe])
    fired = [f for f in findings if f.get("distribution_model_change")]
    assert len(fired) == 1
    assert fired[0]["event_type"] == "DISTRIBUTION_CHANGE"
    assert "bitnami" in fired[0]["title"]
    assert "bitnamilegacy" in fired[0]["title"]


def test_versioned_mainlines_do_not_trigger_the_split():
    """No false positives on versioned mainlines: a namespace serving
    real version tags (the `library/nginx` full-set shape) is not
    latest-only, so no model-change finding fires — even when a
    legacy-marked namespace exists for the same repo.
    """
    from analyzers.change_analyst import analyze_registries
    from collectors.registries.docker import parse_tags

    mainline_tags = ["latest", "1.30-alpine3.24", "1.30.5-alpine", "stable"]
    mainline_probe = parse_tags(
        "library",
        "nginx",
        {"count": len(mainline_tags), "results": [{"name": t} for t in mainline_tags]},
    )
    legacy_probe = parse_tags(
        "librarylegacy", "nginx", {"count": 2, "results": [{"name": "1.30"}, {"name": "1.29"}]}
    )
    assert mainline_probe["latest_only"] is False
    assert mainline_probe["has_versioned_tags"] is True

    findings = analyze_registries([mainline_probe, legacy_probe])
    assert all(not f.get("distribution_model_change") for f in findings)
