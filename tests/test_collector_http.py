"""collectors/http.py: size-bounded collector HTTP (plan A6b / H11)."""

import gzip
import json

import httpx
import pytest

from collectors import http
from collectors.http import ResponseTooLarge


@pytest.fixture
def serve(monkeypatch):
    """Route collectors.http through a MockTransport handler."""

    def install(handler):
        client = httpx.Client(transport=httpx.MockTransport(handler))

        def stream(method, url, **kwargs):
            return client.stream(method, url, **kwargs)

        monkeypatch.setattr(http.httpx, "stream", stream)

    return install


def test_small_json_comes_back_as_a_normal_response(serve):
    serve(lambda request: httpx.Response(200, json={"ok": [1, 2]}))
    r = http.get("https://api.example/x", timeout=5)
    assert r.status_code == 200
    assert r.json() == {"ok": [1, 2]}
    r.raise_for_status()


def test_declared_length_over_the_cap_is_refused(serve):
    serve(lambda request: httpx.Response(200, content=b"x" * 100))
    with pytest.raises(ResponseTooLarge, match="api.example exceeds 10 bytes"):
        http.get("https://api.example/x", max_bytes=10)


def test_undeclared_body_is_cut_off_while_streaming(serve):
    def chunked(request):
        return httpx.Response(200, content=iter([b"a" * 8, b"b" * 8, b"c" * 8]))

    serve(chunked)
    with pytest.raises(ResponseTooLarge):
        http.get("https://api.example/x", max_bytes=12)


def test_gzip_bomb_is_measured_after_decoding(serve):
    bomb = gzip.compress(b"0" * 1_000_000)  # ~1 KB on the wire, 1 MB decoded
    serve(
        lambda request: httpx.Response(
            200, content=bomb, headers={"content-encoding": "gzip"}
        )
    )
    assert len(bomb) < 64 * 1024
    with pytest.raises(ResponseTooLarge):
        http.get("https://api.example/x", max_bytes=64 * 1024)


def test_gzip_body_is_decoded_once(serve):
    payload = json.dumps({"vulns": ["GHSA-1"]}).encode()
    serve(
        lambda request: httpx.Response(
            200, content=gzip.compress(payload), headers={"content-encoding": "gzip"}
        )
    )
    r = http.post("https://api.example/q", json={})
    assert r.json() == {"vulns": ["GHSA-1"]}
    assert "content-encoding" not in r.headers


def test_redirects_are_not_followed(serve):
    serve(lambda request: httpx.Response(302, headers={"location": "http://169.254.169.254/"}))
    r = http.get("https://api.example/x")
    assert r.status_code == 302


def test_oversized_collector_response_becomes_an_error_record(serve, monkeypatch):
    """End to end: a collector never raises; it reports a non-retryable error."""
    from collectors.osv.collector import OSVCollector

    monkeypatch.setattr(http, "DEFAULT_MAX_BYTES", 1024)
    serve(lambda request: httpx.Response(200, json={"vulns": [{"id": "x" * 4096}]}))
    out = OSVCollector({"django": ("django", "PyPI")}).collect("django")
    assert out[0]["error"] is True
    assert out[0]["category"] == "parse"
    assert out[0]["retryable"] is False
    assert "exceeds" in out[0]["safe_message"]
