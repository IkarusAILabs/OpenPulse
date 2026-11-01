"""Signed webhook payloads (v0.11.0 W3, #78).

A webhook receiver could not tell an OpenPulse alert from a request
anyone else posted to the same URL, and a captured request could be
replayed. With a webhook secret, every post carries two headers:

- ``X-OpenPulse-Timestamp``: Unix time in whole seconds, at signing.
- ``X-OpenPulse-Signature``: ``v1=`` + hex HMAC-SHA256 under the secret
  over ``"<timestamp>." + body``, where ``body`` is the exact request
  bytes.

A receiver recomputes the HMAC over the raw body it received (never a
re-serialized copy), compares in constant time, and rejects a timestamp
more than ``TOLERANCE_SECONDS`` from its own clock: that bounds how long
a captured request can be replayed. ``verify_webhook_signature`` does
all three and is stdlib only, so a receiver can copy this file.

The secret comes from ``OPENPULSE_WEBHOOK_SECRET`` or the first
non-empty line of ``--webhook-secret-file`` (at most 4 KiB) and must be
at least ``MIN_SECRET_CHARS`` characters (``openssl rand -hex 32`` makes
one). It is never printed.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

ENV_VAR = "OPENPULSE_WEBHOOK_SECRET"
TIMESTAMP_HEADER = "X-OpenPulse-Timestamp"
SIGNATURE_HEADER = "X-OpenPulse-Signature"
SCHEME = "v1"
#: Largest distance between the signing time and the receiver's clock.
TOLERANCE_SECONDS = 300
MIN_SECRET_CHARS = 32
MAX_SECRET_FILE_BYTES = 4096


class WebhookSecretError(ValueError):
    """A webhook secret is missing, too short or unreadable. Never contains it."""


def _mac(secret: bytes, timestamp: str, body: bytes) -> str:
    return hmac.new(secret, timestamp.encode("ascii") + b"." + body, hashlib.sha256).hexdigest()


def sign(secret: bytes, body: bytes, timestamp: int | None = None) -> dict[str, str]:
    """The two signature headers for ``body``."""
    stamp = str(int(time.time()) if timestamp is None else int(timestamp))
    return {
        TIMESTAMP_HEADER: stamp,
        SIGNATURE_HEADER: f"{SCHEME}={_mac(secret, stamp, body)}",
    }


def verify_webhook_signature(
    secret: bytes,
    body: bytes,
    timestamp: str | None,
    signature: str | None,
    *,
    now: float | None = None,
    tolerance: int = TOLERANCE_SECONDS,
) -> bool:
    """Receiver side: True only for an authentic body signed within the window."""
    if not timestamp or not signature or not timestamp.isdigit():
        return False
    clock = time.time() if now is None else now
    if abs(clock - int(timestamp)) > tolerance:
        return False
    scheme, _, value = signature.partition("=")
    if scheme != SCHEME or not value:
        return False
    return hmac.compare_digest(value, _mac(secret, timestamp, body))


def parse_secret(text: str) -> bytes:
    secret = text.strip()
    if len(secret) < MIN_SECRET_CHARS:
        raise WebhookSecretError(
            f"webhook secret must be at least {MIN_SECRET_CHARS} characters "
            "(openssl rand -hex 32 makes one)"
        )
    return secret.encode("utf-8")


def load_webhook_secret(secret_file: str | None = None) -> bytes | None:
    """``--webhook-secret-file`` first, then ``OPENPULSE_WEBHOOK_SECRET``; None when neither."""
    if secret_file:
        from core.bounded_io import read_bytes

        raw = read_bytes(secret_file, MAX_SECRET_FILE_BYTES, "webhook secret file")
        try:
            lines = [line for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
        except UnicodeDecodeError as exc:
            raise WebhookSecretError("webhook secret file is not UTF-8 text") from exc
        if not lines:
            raise WebhookSecretError("webhook secret file is empty")
        return parse_secret(lines[0])
    value = os.environ.get(ENV_VAR)
    return parse_secret(value) if value else None


__all__ = [
    "ENV_VAR",
    "SIGNATURE_HEADER",
    "TIMESTAMP_HEADER",
    "TOLERANCE_SECONDS",
    "WebhookSecretError",
    "load_webhook_secret",
    "sign",
    "verify_webhook_signature",
]
