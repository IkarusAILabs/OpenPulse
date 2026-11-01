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
- IPv4-mapped (::ffff:a.b.c.d), 6to4 (2002::/16) and NAT64
  (64:ff9b::/96, 64:ff9b:1::/48) addresses are unwrapped and the
  embedded IPv4 is checked too;
- DNS is resolved exactly once: the connection goes to a validated IP
  (`_PinnedBackend`), while TLS SNI, certificate verification and the
  Host header stay on the original hostname. A resolver that answers
  differently on a second lookup (DNS rebinding) is never asked again;
- environment proxies are not used (a proxy would resolve the host
  itself and undo the pinning);
- redirects are never followed (a 3xx is a delivery failure);
- short timeout, bounded response body (streamed);
- failures never log the body, the full URL, or secrets.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpcore
import httpx

from collectors.errors import redact, safe_message

#: Well-known cloud metadata endpoints (link-local covers 169.254.x
#: on most clouds; these are the stragglers worth naming).
_METADATA_IPS = {
    "100.100.100.100",  # Alibaba Cloud
    "192.0.0.192",  # Oracle Cloud (also link-local-adjacent)
    "fd00:ec2::254",  # AWS IPv6 metadata (EC2)
}


_NAT64_WELL_KNOWN = ipaddress.ip_network("64:ff9b::/96")
_NAT64_LOCAL_USE = ipaddress.ip_network("64:ff9b:1::/48")


@dataclass(frozen=True)
class WebhookPolicy:
    allow_http: bool = False
    timeout_seconds: float = 10.0
    max_response_bytes: int = 1_048_576
    user_agent: str = "openpulse-notify"


def _redacted_url(url: str) -> str:
    """Scheme + host for messages: no path, query, fragment or userinfo.

    The path is dropped too: for Slack/Teams/Discord incoming webhooks
    the path IS the credential.
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname or "?"
        port = f":{parts.port}" if parts.port else ""
        return f"{parts.scheme}://{host}{port}"
    except ValueError:
        return "<unparseable-url>"


def _scrub_url(text: str, url: str) -> str:
    """Remove every spelling of `url` (and its path) from a message."""
    safe = _redacted_url(url)
    text = text.replace(url, safe)
    try:
        path = urlsplit(url).path
    except ValueError:
        path = ""
    if len(path) > 1:
        text = text.replace(path, "/<redacted>")
    return redact(text)


def _embedded_ipv4(ip: ipaddress._BaseAddress) -> list[tuple[str, ipaddress.IPv4Address]]:
    """IPv4 addresses an IPv6 address carries, with the wrapping's name."""
    if ip.version != 6:
        return []
    found: list[tuple[str, ipaddress.IPv4Address]] = []
    if ip.ipv4_mapped is not None:
        found.append(("an IPv4-mapped", ip.ipv4_mapped))
    if ip.sixtofour is not None:
        found.append(("a 6to4", ip.sixtofour))
    value = int(ip)
    if ip in _NAT64_WELL_KNOWN:
        found.append(("a NAT64", ipaddress.IPv4Address(value & 0xFFFFFFFF)))
    elif ip in _NAT64_LOCAL_USE:
        # RFC 6052 /48 layout (bits 48-63 and 72-87), and the /96 layout
        # an operator may use inside the local-use prefix: check both. An
        # all-zero field means that layout is not in use.
        split = ((value >> 64) & 0xFFFF) << 16 | (value >> 40) & 0xFFFF
        for candidate in (split, value & 0xFFFFFFFF):
            if candidate:
                found.append(("a NAT64", ipaddress.IPv4Address(candidate)))
    return found


def _blocked_ip(ip: ipaddress._BaseAddress) -> str | None:
    for form, inner in _embedded_ipv4(ip):
        blocked = _blocked_ip(inner)
        if blocked:
            return f"{blocked} {inner}, embedded in {form}"
    if ip.version == 6 and ip in _NAT64_LOCAL_USE:
        return "local-use NAT64 (64:ff9b:1::/48)"
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
    """Hostname -> IP strings (sync), in getaddrinfo's preference order.

    Raises socket.gaierror on failure.
    """
    infos = socket.getaddrinfo(host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    return list(dict.fromkeys(info[4][0] for info in infos))


def _checked_addresses(
    url: str,
    policy: WebhookPolicy,
    resolver: Callable[[str], list[str]] | None,
) -> tuple[list[str], str | None]:
    """(validated IPs, reason). Resolves at most once; IPs empty on refusal."""
    if not isinstance(url, str) or not url:
        return [], "webhook URL is empty"
    try:
        parts = urlsplit(url)
    except ValueError:
        return [], "webhook URL does not parse"
    scheme = parts.scheme.lower()
    if scheme == "http" and not policy.allow_http:
        return [], "http webhooks need explicit opt-in; use https"
    if scheme not in ("https", "http"):
        return [], "webhook URL must be http(s)"
    if parts.username or parts.password:
        return [], "credentials in webhook URL are never sent"
    host = parts.hostname or ""
    if not host:
        return [], "webhook URL has no host"
    resolve = resolver or default_resolver
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        blocked = _blocked_ip(literal)
        if blocked:
            return [], f"webhook host resolves to blocked {blocked} address"
        return [str(literal)], None
    try:
        addresses = list(resolve(host))
    except Exception:
        return [], f"cannot resolve webhook host {host}"
    if not addresses:
        return [], f"webhook host {host} resolves to nothing"
    validated: list[str] = []
    for addr in addresses:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return [], f"webhook host {host} resolves to an unparseable address"
        blocked = _blocked_ip(ip)
        if blocked:
            return [], f"webhook host {host} resolves to blocked {blocked} address"
        validated.append(str(ip))
    return validated, None


def validate_webhook_url(
    url: str,
    policy: WebhookPolicy | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> tuple[bool, str | None]:
    """(allowed, reason). `reason` is a safe, loggable string."""
    addresses, reason = _checked_addresses(url, policy or WebhookPolicy(), resolver)
    return bool(addresses), reason


class _PinnedBackend(httpcore.NetworkBackend):
    """Connects `host` only, and only to its already-validated IPs.

    httpcore still passes the original hostname to `start_tls`, so SNI
    and certificate verification stay on the name; the Host header comes
    from the URL. No second DNS lookup happens anywhere.
    """

    def __init__(
        self,
        host: str,
        addresses: list[str],
        inner: httpcore.NetworkBackend | None = None,
    ) -> None:
        self._host = host.lower()
        self._addresses = list(addresses)
        self._inner = inner or httpcore.SyncBackend()

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Any = None,
    ) -> httpcore.NetworkStream:
        if host.lower() != self._host:
            raise httpcore.ConnectError("webhook connection to an unpinned host refused")
        error: Exception = httpcore.ConnectError("webhook host has no validated address")
        for address in self._addresses:
            try:
                return self._inner.connect_tcp(
                    address,
                    port,
                    timeout=timeout,
                    local_address=local_address,
                    socket_options=socket_options,
                )
            except (httpcore.ConnectError, httpcore.ConnectTimeout) as exc:
                error = exc
        raise error

    def connect_unix_socket(self, *args: Any, **kwargs: Any) -> httpcore.NetworkStream:
        raise httpcore.ConnectError("webhook delivery never uses unix sockets")

    def sleep(self, seconds: float) -> None:
        self._inner.sleep(seconds)


class _PinnedTransport(httpx.HTTPTransport):
    """httpx transport whose connection pool dials only the pinned IPs."""

    def __init__(self, host: str, addresses: list[str]) -> None:
        super().__init__()
        self._pool = httpcore.ConnectionPool(
            ssl_context=httpx.create_ssl_context(),
            max_connections=1,
            network_backend=_PinnedBackend(host, addresses),
        )


def post_digest(
    webhook_url: str,
    markdown: str,
    timeout: float = 15.0,
    policy: WebhookPolicy | None = None,
    transport: httpx.BaseTransport | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> dict[str, Any]:
    """POST the digest; return {ok, status_code, error} (never raises).

    `transport`/`resolver` are injection points for offline tests. Without
    an injected transport, the connection is pinned to the addresses the
    single resolution validated.
    """
    policy = policy or WebhookPolicy()
    addresses, reason = _checked_addresses(webhook_url, policy, resolver)
    if not addresses:
        return {"ok": False, "status_code": None, "error": reason}
    try:
        if transport is None:
            raw_host = httpx.URL(webhook_url).raw_host.decode("ascii")
            transport = _PinnedTransport(raw_host, addresses)
        client_kwargs: dict[str, Any] = {
            "timeout": httpx.Timeout(min(timeout, policy.timeout_seconds)),
            "follow_redirects": False,
            "headers": {"user-agent": policy.user_agent},
            "transport": transport,
            "trust_env": False,
        }
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
        # httpx's message embeds the full request URL; report status + host only.
        status = exc.response.status_code if exc.response is not None else None
        error = f"webhook returned HTTP {status} from {_redacted_url(webhook_url)}"
        return {"ok": False, "status_code": status, "error": error}
    except Exception as exc:  # network, DNS, timeouts: report, never crash
        detail = _scrub_url(safe_message(exc, limit=2000), webhook_url)[:200]
        return {"ok": False, "status_code": None, "error": detail}


__all__ = [
    "WebhookPolicy",
    "default_resolver",
    "post_digest",
    "validate_webhook_url",
]
