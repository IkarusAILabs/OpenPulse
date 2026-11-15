"""NVD: API key, pacing within the published limits, retry on rate limits.

A whole-catalog report makes one NVD request per project. Without a key
NVD allows 5 requests per 30 s and answers the excess with 403, so the
November 2026 run silently lost a different set of projects each time.
"""

from __future__ import annotations

import httpx
import pytest

from collectors.nvd import collector as nvd

EMPTY = {"vulnerabilities": []}


class FakeTime:
    def __init__(self):
        self.now = 1000.0
        self.slept: list[float] = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(round(seconds, 3))
        self.now += seconds


@pytest.fixture
def fake(monkeypatch):
    t = FakeTime()
    monkeypatch.setattr(nvd, "_clock", t.clock)
    monkeypatch.setattr(nvd, "_sleep", t.sleep)
    monkeypatch.setattr(nvd, "_last_request", [float("-inf")])
    monkeypatch.delenv(nvd.KEY_ENV, raising=False)
    return t


def _answers(monkeypatch, *responses):
    """Patch http.get to return the given (status, headers) in order; record calls."""
    calls = []
    queue = list(responses)

    def get(url, params=None, headers=None, timeout=None):
        calls.append(dict(headers or {}))
        status, extra = queue.pop(0) if len(queue) > 1 else queue[0]
        request = httpx.Request("GET", url)
        return httpx.Response(status, json=EMPTY, headers=extra, request=request)

    monkeypatch.setattr(nvd.http, "get", get)
    return calls


def test_keyless_requests_are_paced_within_five_per_thirty_seconds(fake, monkeypatch):
    _answers(monkeypatch, (200, {}))
    collector = nvd.NVDCollector()
    for slug in ("a", "b", "c"):
        collector.collect(slug)
    assert fake.slept == [nvd.INTERVAL_KEYLESS, nvd.INTERVAL_KEYLESS]
    assert nvd.INTERVAL_KEYLESS * 5 >= 30


def test_a_key_paces_within_fifty_per_thirty_seconds(fake, monkeypatch):
    calls = _answers(monkeypatch, (200, {}))
    monkeypatch.setenv(nvd.KEY_ENV, "test-nvd-key")
    collector = nvd.NVDCollector()
    collector.collect("a")
    collector.collect("b")
    assert fake.slept == [nvd.INTERVAL_KEYED] and nvd.INTERVAL_KEYED * 50 >= 30
    assert calls[0] == {"apiKey": "test-nvd-key"}


def test_an_explicit_key_wins_over_the_environment(fake, monkeypatch):
    calls = _answers(monkeypatch, (200, {}))
    monkeypatch.setenv(nvd.KEY_ENV, "from-env")
    nvd.NVDCollector(api_key="explicit").collect("a")
    assert calls[0] == {"apiKey": "explicit"}


def test_a_rate_limit_answer_is_retried_then_succeeds(fake, monkeypatch):
    calls = _answers(monkeypatch, (403, {}), (200, {}))
    out = nvd.NVDCollector().collect("vitess")
    assert len(calls) == 2
    assert nvd.RETRY_WAIT_KEYLESS in fake.slept
    assert out == [{"collector": "nvd", "keyword": "vitess", "vulns": 0}]


def test_retry_after_is_honoured(fake, monkeypatch):
    _answers(monkeypatch, (429, {"Retry-After": "12"}), (200, {}))
    nvd.NVDCollector().collect("vitess")
    assert 12.0 in fake.slept


def test_persistent_rate_limiting_is_an_error_record_after_max_attempts(fake, monkeypatch):
    calls = _answers(monkeypatch, (403, {}))
    monkeypatch.setenv(nvd.KEY_ENV, "secret-nvd-key-value")
    out = nvd.NVDCollector().collect("vitess")
    assert len(calls) == nvd.MAX_ATTEMPTS
    assert out[0]["error"] is True and out[0]["status_code"] == 403
    assert "secret-nvd-key-value" not in str(out)


def test_other_errors_are_not_retried(fake, monkeypatch):
    calls = _answers(monkeypatch, (404, {}))
    out = nvd.NVDCollector().collect("vitess")
    assert len(calls) == 1 and out[0]["error"] is True
