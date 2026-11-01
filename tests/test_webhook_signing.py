"""Signed webhook payloads (v0.11.0 W3, #78)."""

from __future__ import annotations

import json

import httpx
import pytest
from click.testing import CliRunner

from core import notify
from core.webhook_signing import (
    ENV_VAR,
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    TOLERANCE_SECONDS,
    WebhookSecretError,
    load_webhook_secret,
    sign,
    verify_webhook_signature,
)

SECRET = b"0123456789abcdef0123456789abcdef-test-secret"
BODY = b'{"text":"# OpenPulse new alerts"}'
T = 1_793_000_000


def test_a_signed_body_verifies():
    headers = sign(SECRET, BODY, timestamp=T)
    assert headers[SIGNATURE_HEADER].startswith("v1=")
    assert verify_webhook_signature(
        SECRET, BODY, headers[TIMESTAMP_HEADER], headers[SIGNATURE_HEADER], now=T + 10
    )


@pytest.mark.parametrize(
    "tamper",
    ["body", "secret", "timestamp", "stale", "future", "scheme", "missing", "garbage-ts"],
)
def test_anything_else_is_rejected(tamper):
    headers = sign(SECRET, BODY, timestamp=T)
    body, secret = BODY, SECRET
    ts, sig, now = headers[TIMESTAMP_HEADER], headers[SIGNATURE_HEADER], T + 10
    if tamper == "body":
        body = BODY.replace(b"alerts", b"alertz")
    elif tamper == "secret":
        secret = b"another-secret-that-is-also-long-enough!!"
    elif tamper == "timestamp":
        ts = str(T + 1)  # signature is bound to the timestamp
    elif tamper == "stale":
        now = T + TOLERANCE_SECONDS + 1  # a replay outside the window
    elif tamper == "future":
        now = T - TOLERANCE_SECONDS - 1
    elif tamper == "scheme":
        sig = sig.replace("v1=", "v0=")
    elif tamper == "missing":
        sig = None
    elif tamper == "garbage-ts":
        ts = "soon"
    assert not verify_webhook_signature(secret, body, ts, sig, now=now)


# ---------------------------------------------------------------------------
# post_digest sends the headers over the exact bytes
# ---------------------------------------------------------------------------


def _capture():
    seen = {}

    def handler(request):
        seen["request"] = request
        seen["body"] = request.read()
        return httpx.Response(200)

    return seen, httpx.MockTransport(handler)


def _post(markdown, **kwargs):
    seen, transport = _capture()
    result = notify.post_digest(
        "https://hooks.example/x",
        markdown,
        transport=transport,
        resolver=lambda _host: ["93.184.216.34"],
        **kwargs,
    )
    assert result["ok"], result
    return seen


def test_post_digest_signs_the_bytes_it_sends():
    seen = _post("# alerts — ünïcode", signing_secret=SECRET)
    request = seen["request"]
    assert verify_webhook_signature(
        SECRET, seen["body"], request.headers[TIMESTAMP_HEADER], request.headers[SIGNATURE_HEADER]
    )
    assert json.loads(seen["body"]) == {"text": "# alerts — ünïcode"}


def test_unsigned_posts_are_unchanged():
    """Same bytes and content type as httpx's json= produced before W3."""
    seen = _post("# alerts — ünïcode")
    request = seen["request"]
    assert TIMESTAMP_HEADER not in request.headers and SIGNATURE_HEADER not in request.headers
    expected = httpx.Request("POST", "https://x", json={"text": "# alerts — ünïcode"})
    assert seen["body"] == expected.read()
    assert request.headers["content-type"] == "application/json"


# ---------------------------------------------------------------------------
# Loading the secret
# ---------------------------------------------------------------------------


def test_secret_from_env_and_file(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert load_webhook_secret(None) is None
    monkeypatch.setenv(ENV_VAR, SECRET.decode())
    assert load_webhook_secret(None) == SECRET
    secret_file = tmp_path / "webhook-secret"
    other = "f" * 64
    secret_file.write_text(f"\n{other}\n", encoding="utf-8")
    assert load_webhook_secret(str(secret_file)) == other.encode()  # the file wins


@pytest.mark.parametrize("value", ["short-secret", "   "])
def test_short_secrets_are_refused_without_echoing_them(monkeypatch, tmp_path, value):
    secret_file = tmp_path / "webhook-secret"
    secret_file.write_text(value, encoding="utf-8")
    with pytest.raises(WebhookSecretError) as exc:
        load_webhook_secret(str(secret_file))
    assert "short-secret" not in str(exc.value)


# ---------------------------------------------------------------------------
# CLI: check --webhook, end to end through the real post_digest
# ---------------------------------------------------------------------------


def _check(monkeypatch, tmp_path, *extra, delivery_state=None):
    from cli.main import cli

    seen, transport = _capture()
    real = notify.post_digest

    def through_mock(url, text, **kwargs):
        return real(url, text, transport=transport, resolver=lambda _h: ["93.184.216.34"], **kwargs)

    monkeypatch.setattr(notify, "post_digest", through_mock)
    args = [
        "check",
        "--manifest",
        "data/fixtures/manifests/requirements.txt",
        "--event",
        "data/fixtures/django-eol/event.json",
        "--replay",
        "--ledger",
        "",
        "--webhook",
        "https://hooks.example/x",
    ]
    if delivery_state is not None:
        args += ["--delivery-state", delivery_state]
    return CliRunner().invoke(cli, [*args, *extra]), seen


@pytest.mark.parametrize("state", [None, ""], ids=["delivery-state", "legacy-digest"])
def test_check_signs_webhook_posts(monkeypatch, tmp_path, state):
    monkeypatch.setenv(ENV_VAR, SECRET.decode())
    result, seen = _check(monkeypatch, tmp_path, delivery_state=state)
    assert result.exit_code == 0, result.output
    request = seen["request"]
    assert verify_webhook_signature(
        SECRET, seen["body"], request.headers[TIMESTAMP_HEADER], request.headers[SIGNATURE_HEADER]
    )
    assert SECRET.decode() not in result.output


def test_check_without_a_secret_sends_unsigned(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_VAR, raising=False)
    result, seen = _check(monkeypatch, tmp_path)
    assert result.exit_code == 0, result.output
    assert SIGNATURE_HEADER not in seen["request"].headers


def test_check_refuses_a_short_secret_before_doing_anything(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, "too-short")
    result, seen = _check(monkeypatch, tmp_path)
    assert result.exit_code != 0
    assert "at least 32 characters" in result.output
    assert "too-short" not in result.output
    assert "request" not in seen
