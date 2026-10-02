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


def test_bitnami_digest_mainline_gap_locked():
    """The latest-only heuristic does NOT fire on digest-tagged
    mainlines: bitnami/redis serves `latest` + hundreds of `sha256-*`
    digest tags (recorded full-set observation, 2026-10-02), so
    `latest_only` is False and no model-change finding fires — even
    though zero version-like tags live there vs 919+ in
    bitnamilegacy/redis. This test locks the blind spot (see
    docs/DISCOVERIES.md case 2): the structural split is
    analyst-confirmed, but no producer derives it yet. A future
    version-aware rule must flip this test, not sneak past it.
    """
    from analyzers.change_analyst import analyze_registries

    bitnami_probe = {
        "collector": "registries",
        "repo": "redis",
        "namespace": "bitnami",
        "latest_only": False,
        "has_versioned_tags": True,  # sha256-* digest tags pollute the flag
    }
    legacy_probe = {
        "collector": "registries",
        "repo": "redis",
        "namespace": "bitnamilegacy",
        "latest_only": False,
        "has_versioned_tags": True,
    }
    findings = analyze_registries([bitnami_probe, legacy_probe])
    assert all(not f.get("distribution_model_change") for f in findings)
