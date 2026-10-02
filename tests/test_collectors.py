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
        return _paged_response([_tag("latest"), _tag("1.0")], next_url="https://x?page=2")

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
        return _paged_response([_tag(f"t{len(calls)}")], next_url="https://x?page=more")

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
