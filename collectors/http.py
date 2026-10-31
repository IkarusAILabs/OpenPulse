"""Size-bounded HTTP for collectors (plan item A6b / H11).

`httpx.get(...).json()` reads the whole body into memory before anything
checks it, so one oversized or hostile response (or a gzip bomb that
decompresses to gigabytes) can exhaust a scheduled run. These helpers
stream the body and stop as soon as it passes `max_bytes`:

- a declared `Content-Length` above the cap is refused before reading;
- the cap counts *decoded* bytes, so compressed responses can't slip past;
- redirects are not followed (httpx's default, kept explicit).

They return an ordinary `httpx.Response` (status, headers, buffered
body), so collector code after the call is unchanged. Over the cap raises
`ResponseTooLarge`, a `ValueError`: `collectors.errors.as_error` reports it
as a non-retryable error record, never a crash. Collectors call these
through the module (`http.get`) so tests can patch one seam.
"""

from __future__ import annotations

from typing import Any

import httpx

#: Default per-response cap. The largest routine payloads (the CISA KEV
#: catalog, OSV results for popular packages) are a few MB.
DEFAULT_MAX_BYTES = 32 * 1024 * 1024

#: Headers that describe the wire encoding; the returned body is decoded.
_WIRE_HEADERS = {"content-encoding", "content-length", "transfer-encoding"}


class ResponseTooLarge(ValueError):
    """A response body exceeded the collector's byte cap."""


def _too_large(url: Any, max_bytes: int) -> ResponseTooLarge:
    host = httpx.URL(str(url)).host or "?"
    return ResponseTooLarge(f"response from {host} exceeds {max_bytes} bytes")


def request(
    method: str, url: str, *, max_bytes: int | None = None, **kwargs: Any
) -> httpx.Response:
    """Send one request; return the response with a body of at most `max_bytes`
    (default: `DEFAULT_MAX_BYTES`, read at call time so it can be tuned)."""
    if max_bytes is None:
        max_bytes = DEFAULT_MAX_BYTES
    kwargs.setdefault("follow_redirects", False)
    with httpx.stream(method, url, **kwargs) as resp:
        declared = resp.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > max_bytes:
            raise _too_large(url, max_bytes)
        body = bytearray()
        for chunk in resp.iter_bytes():
            body += chunk
            if len(body) > max_bytes:
                raise _too_large(url, max_bytes)
        headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in _WIRE_HEADERS]
        return httpx.Response(
            resp.status_code, headers=headers, content=bytes(body), request=resp.request
        )


def get(url: str, **kwargs: Any) -> httpx.Response:
    return request("GET", url, **kwargs)


def post(url: str, **kwargs: Any) -> httpx.Response:
    return request("POST", url, **kwargs)
