"""Issue #36 - Hub anonymous pagination wall vs the v2 protocol full set.

The Hub walk stops short of the complete name set for large repos
(403 "pagination offset too large", positional, not a quota). The
rescue path asks the registry v2 protocol for the complete tag-name
list and unions it in. These tests pin the honest-state contract:

- v2 rescue succeeds -> names complete, digests window-partial,
  digests_partial carries that fact, truncated cleared;
- v2 unavailable -> the probe stays truncated and diffs are
  withheld (a window is never mistaken for a removal);
- digest diffs on window-partial observations are withheld so
  acquisition churn cannot manufacture findings.
"""

import httpx


def _hub_page(results, next_url=None, count=None, url="https://hub.docker.com/v2/x"):
    payload = {"results": results, "count": count if count is not None else len(results)}
    if next_url:
        payload["next"] = next_url
    return httpx.Response(200, json=payload, request=httpx.Request("GET", url))


def _hub_wall(url="https://hub.docker.com/v2/x?page=11"):
    return httpx.Response(
        403,
        json={
            "message": "pagination offset too large for anonymous requests; sign in to page further"
        },
        request=httpx.Request("GET", url),
    )


def _tag(name):
    return {"name": name, "images": [{"digest": "sha256:" + name}]}


def _v2_calls(monkeypatch, full_names, hub_pages, v2_status=200):
    """Wire the Hub walk to hub_pages, the v2 path to full_names."""
    calls = {"hub": [], "v2": []}

    def fake_get(url, params=None, headers=None, timeout=None):
        if url.startswith("https://auth.docker.io"):
            calls["v2"].append("auth")
            return httpx.Response(200, json={"token": "tok"}, request=httpx.Request("GET", url))
        if "registry-1.docker.io" in url:
            calls["v2"].append(url)
            if v2_status == 404:
                return httpx.Response(404, request=httpx.Request("GET", url))
            return httpx.Response(
                200,
                json={"name": "library/demo", "tags": list(full_names)},
                request=httpx.Request("GET", url),
            )
        calls["hub"].append(url)
        return hub_pages.pop(0)

    monkeypatch.setattr(httpx, "get", fake_get)
    return calls


def test_offset_wall_triggers_v2_rescue(monkeypatch):
    from collectors.registries.docker import RegistryCollector

    hub_pages = [
        _hub_page([_tag("latest"), _tag("1.0")], next_url="https://hub.docker.com/v2/x?page=2"),
        _hub_wall(),
    ]
    calls = _v2_calls(monkeypatch, ["latest", "1.0", "old-a", "old-b"], hub_pages)
    out = RegistryCollector().check_image("demo", "app")
    assert out.get("error") is None
    assert len(calls["v2"]) == 2  # auth + tags/list
    assert set(out["digests"]) == {"latest", "1.0", "old-a", "old-b"}
    assert out["digests"]["latest"] == ["sha256:latest"]
    assert out["digests"]["old-a"] == []
    assert out["tags_sample"] == ["latest", "1.0", "old-a", "old-b"]
    assert out["count"] == 4
    assert out["truncated"] is False
    assert out["digests_partial"] is True
    assert out["has_versioned_tags"] is True
    assert out["latest_only"] is False


def test_offset_wall_with_v2_down_stays_truncated(monkeypatch):
    from collectors.registries.docker import RegistryCollector

    hub_pages = [
        _hub_page([_tag("latest"), _tag("1.0")], next_url="https://hub.docker.com/v2/x?page=2"),
        _hub_wall(),
    ]
    _v2_calls(monkeypatch, [], hub_pages, v2_status=404)
    out = RegistryCollector().check_image("demo", "app")
    assert out.get("error") is None
    assert out["truncated"] is True
    assert "digests_partial" not in out
    assert set(out["digests"]) == {"latest", "1.0"}


def test_page_cap_triggers_v2_rescue_too(monkeypatch):
    from collectors.registries.docker import _MAX_TAG_PAGES, RegistryCollector

    hub_pages = [_hub_page([_tag("w" + str(i))], next_url="more") for i in range(_MAX_TAG_PAGES)]
    calls = _v2_calls(monkeypatch, ["w0", "rescued"], hub_pages)
    out = RegistryCollector().check_image("demo", "app")
    assert out.get("error") is None
    assert len(calls["hub"]) == _MAX_TAG_PAGES
    assert out["digests_partial"] is True
    assert "rescued" in out["digests"]
    assert out["truncated"] is False


def test_small_repo_never_consults_v2(monkeypatch):
    from collectors.registries.docker import RegistryCollector

    hub_pages = [
        _hub_page([_tag("latest"), _tag("1.0")], count=2),
    ]
    calls = _v2_calls(monkeypatch, ["should-not-appear"], hub_pages)
    out = RegistryCollector().check_image("demo", "app")
    assert out.get("error") is None
    assert calls["v2"] == []
    assert out["truncated"] is False
    assert "digests_partial" not in out
    assert set(out["digests"]) == {"latest", "1.0"}
    assert out["count"] == 2


def test_rescued_probe_seals_with_partial_flag(monkeypatch):
    from collectors.registries.docker import RegistryCollector
    from core.observations.registry import to_observation

    hub_pages = [
        _hub_page([_tag("latest")], next_url="https://hub.docker.com/v2/x?page=2"),
        _hub_wall(),
    ]
    _v2_calls(monkeypatch, ["latest", "3.11", "3.12"], hub_pages)
    out = RegistryCollector().check_image("demo", "app")
    obs = to_observation(out)
    assert obs.digests_partial is True
    assert set(obs.tags) == {"latest", "3.11", "3.12"}
    from core.evidence.provenance import hash_content

    body = obs.integrity_body()
    flipped = dict(body)
    flipped["digests_partial"] = False
    assert hash_content(body) != hash_content(flipped)


def test_digest_diff_withheld_on_partial_acquisition():
    from datetime import datetime, timezone

    from core.observations.registry import RegistryObservation, diff_observations

    def obs(**kw):
        base = {
            "namespace": "library",
            "repository": "demo",
            "observed_at": datetime(2026, 9, 1, tzinfo=timezone.utc),
        }
        base.update(kw)
        return RegistryObservation(**base).seal()

    prev = obs(tags={"latest": ["sha256:A"], "7.2": ["sha256:1"]})
    curr = obs(
        observed_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
        tags={"latest": ["sha256:A"], "7.2": []},
        digests_partial=True,
    )
    assert diff_observations(prev, curr) == []

    prev2 = obs(tags={"latest": [], "7.2": ["sha256:1"]}, digests_partial=True)
    curr2 = obs(
        observed_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
        tags={"latest": ["sha256:A"], "7.2": ["sha256:1"]},
    )
    assert diff_observations(prev2, curr2) == []

    curr3 = obs(
        observed_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
        tags={"latest": ["sha256:A"], "7.2": [], "7.4": []},
        digests_partial=True,
    )
    types = [c.type for c in diff_observations(prev, curr3)]
    assert "tag_appeared" in types
    assert "tag_digest_changed" not in types


def test_digest_diff_still_fires_on_real_changes():
    from datetime import datetime, timezone

    from core.observations.registry import RegistryObservation, diff_observations

    def obs(**kw):
        base = {
            "namespace": "library",
            "repository": "demo",
            "observed_at": datetime(2026, 9, 1, tzinfo=timezone.utc),
        }
        base.update(kw)
        return RegistryObservation(**base).seal()

    prev = obs(tags={"latest": ["sha256:A"], "7.2": ["sha256:1"]})
    curr = obs(
        observed_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
        tags={"latest": ["sha256:A"], "7.2": ["sha256:2"]},
        digests_partial=True,
    )
    changes = diff_observations(prev, curr)
    assert [c.type for c in changes] == ["tag_digest_changed"]


def test_rebaselined_across_parser_bump_with_partial_digests(tmp_path):
    from core.observations.registry import RegistryObservation
    from core.observations.store import save_observation
    from core.observations.sweep import observe_repository

    legacy = (
        RegistryObservation(
            namespace="demo",
            repository="app",
            tags={"latest": ["sha256:latest"]},
            parser_version="openpulse-parsers/0.4.2",
        )
        .seal()
        .link(None)
    )
    save_observation(legacy.model_dump(mode="json"), root=tmp_path)
    probe = {
        "collector": "registries",
        "registry": "docker.io",
        "namespace": "demo",
        "repo": "app",
        "digests": {"latest": ["sha256:latest"], "3.11": [], "3.12": []},
        "count": 3,
        "digests_partial": True,
    }
    result = observe_repository("docker.io", "demo", "app", probe, store_root=tmp_path)
    assert result["error"] is None
    assert result["history_status"] == "REBASELINED"
    assert result["changes"] == []
