def test_github_parse():
    from collectors.github.collector import parse_releases

    out = parse_releases(
        "redis/redis",
        [
            {
                "tag_name": "7.2.0",
                "name": "7.2",
                "published_at": "2024-01-01T00:00:00Z",
                "prerelease": False,
                "html_url": "https://github.com/redis/redis/releases/tag/7.2.0",
            }
        ],
    )
    assert out[0]["tag"] == "7.2.0"


def test_endoflife_parse():
    from collectors.endoflife.collector import parse_product

    out = parse_product(
        "nodejs",
        [{"cycle": "20", "eol": "2026-04-30", "support": "2025-10-21", "latest": "20.11.0"}],
    )
    assert out[0]["cycle"] == "20"


def test_osv_parse():
    from collectors.osv.collector import parse_vulns

    out = parse_vulns(
        "redis",
        "PyPI",
        {
            "vulns": [
                {
                    "id": "CVE-2024-0001",
                    "summary": "x",
                    "severity": [],
                    "references": [{"url": "https://example.com"}],
                }
            ]
        },
    )
    assert out[0]["id"] == "CVE-2024-0001"


def test_registry_parse_latest_only():
    from collectors.registries.docker import parse_tags

    out = parse_tags("bitnami", "redis", {"count": 1, "results": [{"name": "latest"}]})
    assert out["latest_only"] is True
    out2 = parse_tags(
        "bitnamilegacy", "redis", {"count": 2, "results": [{"name": "7.2.0"}, {"name": "latest"}]}
    )
    assert out2["has_versioned_tags"] is True


def test_parse_tags_version_aware_flags():
    """The latest-only flags come from a version-aware predicate, not
    from "any tag that isn't latest" (docs/DISCOVERIES.md case 2):
    `_is_version_like` counts a numeric version component anywhere in
    the tag, and excludes distribution machinery first. The split test
    in test_discoveries.py references this one for the flag shapes.
    """
    from collectors.registries.docker import _is_version_like, parse_tags

    # Versioned: any digit run qualifies, wherever it sits.
    assert _is_version_like("7.2.0") is True
    assert _is_version_like("3.12-slim") is True
    assert _is_version_like("1.30-alpine3.24") is True
    assert _is_version_like("19beta4-bookworm") is True

    # Machinery is never version-like, digits or not.
    assert _is_version_like("latest") is False
    assert _is_version_like("sha256-29f3b4b8b7c4") is False
    assert _is_version_like("SHA256-29f3b4b8b7c4") is False  # case-folded guard
    assert _is_version_like("latest.sig") is False
    assert _is_version_like("latest.att") is False
    assert _is_version_like("latest-metadata") is False

    # parse_tags derives its flags from that predicate: a machinery-only
    # mainline stays latest-only, a single version tag breaks it.
    machinery_only = parse_tags(
        "bitnami",
        "redis",
        {"count": 3, "results": [{"name": "latest"}, {"name": "sha256-1234"}, {"name": "v2.sig"}]},
    )
    assert machinery_only["has_versioned_tags"] is False
    assert machinery_only["latest_only"] is True

    versioned = parse_tags(
        "bitnami",
        "redis",
        {"count": 2, "results": [{"name": "latest"}, {"name": "3.12-slim"}]},
    )
    assert versioned["has_versioned_tags"] is True
    assert versioned["latest_only"] is False


def test_github_token_header():
    from collectors.github.collector import GitHubCollector

    authed = GitHubCollector({"x": "y/z"}, token="secret")
    assert authed._headers()["Authorization"] == "Bearer secret"
    assert "Authorization" not in GitHubCollector()._headers()


def _paged_response(results, next_url=None, count=None, url="https://hub.docker.com/v2/x"):
    import httpx

    payload = {"results": results, "count": count if count is not None else len(results)}
    if next_url:
        payload["next"] = next_url
    return httpx.Response(200, json=payload, request=httpx.Request("GET", url))


def _tag(name):
    return {"name": name, "images": [{"digest": f"sha256:{name}"}]}


def test_check_image_paginates_full_tag_set(monkeypatch):
    import httpx

    from collectors.registries import docker as docker_module

    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        if "page=2" in url:
            return _paged_response([_tag("old")])
        return _paged_response([_tag("latest"), _tag("1.0")], next_url="https://hub.docker.com/v2/x?page=2")

    monkeypatch.setattr(httpx, "get", fake_get)
    out = docker_module.RegistryCollector().check_image("demo", "app")
    assert out.get("error") is None
    assert set(out["digests"]) == {"latest", "1.0", "old"}
    assert len(calls) == 2
    assert "page_size=100" in calls[0]


def test_check_image_stops_at_page_cap(monkeypatch):
    import httpx

    from collectors.registries import docker as docker_module
    from collectors.registries.docker import _MAX_TAG_PAGES

    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        return _paged_response([_tag(f"t{len(calls)}")], next_url="https://hub.docker.com/v2/x?page=more")

    monkeypatch.setattr(httpx, "get", fake_get)
    out = docker_module.RegistryCollector().check_image("demo", "app")
    assert out.get("error") is None
    assert len(calls) == _MAX_TAG_PAGES
    assert len(out["digests"]) == _MAX_TAG_PAGES


def test_check_image_malformed_pages_are_errors(monkeypatch):
    import httpx

    from collectors.registries import docker as docker_module

    def fake_get(url, timeout=None):
        return httpx.Response(200, json=["not", "a", "mapping"], request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    out = docker_module.RegistryCollector().check_image("demo", "app")
    assert out.get("error") is True
    assert out.get("category") == "parse"
