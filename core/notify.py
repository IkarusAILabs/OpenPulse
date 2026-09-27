"""Digest delivery — post markdown digests to a JSON-text webhook.

Target shape is the Slack incoming-webhook contract
(`{"text": "..."}`), which most generic webhook receivers also accept.
Delivery never raises: failures return `ok: False` with a redacted,
truncated message so scheduled runs report them instead of crashing.
"""

from __future__ import annotations

from typing import Any

import httpx

from collectors.errors import redact


def post_digest(webhook_url: str, markdown: str, timeout: float = 15.0) -> dict[str, Any]:
    """POST the digest; return {ok, status_code, error} (never raises)."""
    if not webhook_url.startswith(("https://", "http://")):
        return {"ok": False, "status_code": None, "error": "webhook URL must be http(s)"}
    try:
        response = httpx.post(webhook_url, json={"text": markdown}, timeout=timeout)
        response.raise_for_status()
        return {"ok": True, "status_code": response.status_code, "error": None}
    except Exception as exc:
        status = None
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            status = exc.response.status_code
        return {"ok": False, "status_code": status, "error": redact(str(exc))[:200]}
