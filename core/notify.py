"""Digest delivery — post markdown digests to a JSON-text webhook.

Target shape is the Slack incoming-webhook contract
(`{"text": "..."}`), which most generic webhook receivers also accept.
Delivery never raises: failures return `ok: False` with a redacted,
truncated message so scheduled runs report them instead of crashing.

SSRF boundary (`WebhookPolicy`): webhook URLs are operator-supplied,
but OpenPulse also runs automated (cron, CI, server-side), where a
malicious or compromised config must not turn delivery into an
internal-network probe. Policy enforcement:

- https only by default (http needs explicit opt-in);
- no credentials in the URL, ever;
- every resolved IP is checked: loopback, link-local (covers the
  169.254.169.254 cloud-metadata address), RFC1918/ULA private
  ranges, CGNAT, multicast, reserved and known metadata hosts are
  rejected — if *any* resolved address is blocked, delivery is refused;
- redirects are never followed (a 3xx is a delivery failure);
- short timeout, bounded response body (streamed);
- failures never log the body, the full URL, or secrets.

Known limitation (documented, not silent): DNS is resolved before
connecting, so a hostile resolver could race the check (DNS
rebinding). Short timeouts and no-redirects bound the blast radius;
fully hostile DNS is outside the local-CLI threat model.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx

from collectors.errors import redact, safe_message

#: Well-known cloud metadata endpoints (link-local covers 169.254.x
#: on most clouds; these are the stragglers worth naming).
_METADATA_IPS = {
    "100.100.100.100",  # Alibaba Cloud
    "192.0.0.192",  # Oracle Cloud (also link-local-adjacent)
    "fd00:ec2::254",  # AWS IPv6 metadata (EC2)
}


@dataclass(frozen=True)
class WebhookPolicy:
    allow_http: bool = False
    timeout_seconds: float = 10.0
    max_response_bytes: int = 1_048_576
    user_agent: str = "openpulse-notify"


def _redacted_url(url: str) -> str:
    """Host + path for messages: no query, no fragment, no userinfo."""
    try:
        parts = urlsplit(url)
        host = parts.hostname or "?"
        port = f":{parts.port}" if parts.port else ""
        return f"{parts.scheme}://{host}{port}{parts.path or ''}"
    except ValueError:
        return "<unparseable-url>"


def _blocked_ip(ip: ipaddress._BaseAddress) -> str | None:
    if ip.exploded in _METADATA_IPS or str(ip) in _METADATA_IPS:
        return "cloud metadata endpoint"
    if ip.is_loopback:
        return "loopback"
    if ip.is_link_local:
        return "link-local (includes cloud metadata range)"
    if ip.is_multicast:
        return "multicast"
    if ip.is_reserved or ip.is_unspecified:
        return "reserved/unspecified"
    if ip.is_private:
        return "private network"
    try:
        if ip.version == 4 and ip in ipaddress.ip_network("100.64.0.0/10"):
            return "shared (CGNAT) space"
    except ValueError:
        pass
    return None


def default_resolver(host: str) -> list[str]:
    """Hostname -> IP strings (sync). Raises socket.gaierror on failure."""
    infos = socket.getaddrinfo(host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


def validate_webhook_url(
    url: str,
    policy: WebhookPolicy | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> tuple[bool, str | None]:
    """(allowed, reason). `reason` is a safe, loggable string."""
    policy = policy or WebhookPolicy()
    if not isinstance(url, str) or not url:
        return False, "webhook URL is empty"
    try:
        parts = urlsplit(url)
    except ValueError:
        return False, "webhook URL does not parse"
    scheme = parts.scheme.lower()
    if scheme == "http" and not policy.allow_http:
        return False, "http webhooks need explicit opt-in; use https"
    if scheme not in ("https", "http"):
        return False, "webhook URL must be http(s)"
    if parts.username or parts.password:
        return False, "credentials in webhook URL are never sent"
    host = parts.hostname or ""
    if not host:
        return False, "webhook URL has no host"
    resolve = resolver or default_resolver
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        blocked = _blocked_ip(literal)
        if blocked:
            return False, f"webhook host resolves to blocked {blocked} address"
        return True, None
    try:
        addresses = resolve(host)
    except Exception:
        return False, f"cannot resolve webhook host {host}"
    if not addresses:
        return False, f"webhook host {host} resolves to nothing"
    for addr in addresses:
        try:
            blocked = _blocked_ip(ipaddress.ip_address(addr))
        except ValueError:
            return False, f"webhook host {host} resolves to an unparseable address"
        if blocked:
            return False, f"webhook host {host} resolves to blocked {blocked} address"
    return True, None


def post_digest(
    webhook_url: str,
    markdown: str,
    timeout: float = 15.0,
    policy: WebhookPolicy | None = None,
    transport: httpx.BaseTransport | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> dict[str, Any]:
    """POST the digest; return {ok, status_code, error} (never raises).

    `transport`/`resolver` are injection points for offline tests.
    """
    policy = policy or WebhookPolicy()
    allowed, reason = validate_webhook_url(webhook_url, policy, resolver)
    if not allowed:
        return {"ok": False, "status_code": None, "error": reason}
    try:
        limits = httpx.Limits(max_connections=1)
        client_kwargs: dict[str, Any] = {
            "timeout": httpx.Timeout(min(timeout, policy.timeout_seconds)),
            "limits": limits,
            "follow_redirects": False,
            "headers": {"user-agent": policy.user_agent},
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        with httpx.Client(**client_kwargs) as client:
            with client.stream(
                "POST", webhook_url, json={"text": markdown}
            ) as response:
                if 300 <= response.status_code < 400:
                    return {
                        "ok": False,
                        "status_code": response.status_code,
                        "error": "redirects are never followed for webhook delivery",
                    }
                size = 0
                for chunk in response.iter_bytes(chunk_size=65536):
                    size += len(chunk)
                    if size > policy.max_response_bytes:
                        return {
                            "ok": False,
                            "status_code": response.status_code,
                            "error": "webhook response exceeded size limit",
                        }
                response.raise_for_status()
                return {"ok": True, "status_code": response.status_code, "error": None}
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else None
        return {"ok": False, "status_code": status, "error": safe_message(exc)[:200]}
    except Exception as exc:  # network, DNS, timeouts: report, never crash
        detail = safe_message(exc)[:200]
        return {"ok": False, "status_code": None, "error": redact(detail)}


__all__ = [
    "WebhookPolicy",
    "default_resolver",
    "post_digest",
    "validate_webhook_url",
]
