"""Structured collector errors — safe messages for pipeline output.

Raw exception strings can carry local paths, proxy config, or request
details. Collectors must return `as_error(...)` dicts instead of
`str(exc)`: a stable shape (`category`, `retryable`, `status_code`,
`safe_message`) with the raw detail kept out of findings, events, and
reports. Full tracebacks stay available locally by re-running with
tracebacks enabled — never embedded in pipeline data.

This is the shared acquisition-error policy for collectors, the
registry sweep, webhook delivery, CLI output, and stored error
records: same shape, same redaction, everywhere.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

_PATH_RE = re.compile(r"(?:[A-Za-z]:\\[^\s]*|/(?:home|root|etc|Users|tmp|var)[^\s]*)")
_SECRET_RE = re.compile(
    r"\b[\w-]*(token|secret|password|passwd|pwd|api[_-]?key|authorization)[\w-]*[=: ][^\s]*",
    re.IGNORECASE,
)
_QUERY_RE = re.compile(r"\?[^\s]*")
_URL_USERINFO_RE = re.compile(r"(https?://)[^/\s@]+@", re.IGNORECASE)
#: `Authorization: Bearer <tok>` - the header-name rule above eats only
#: the empty value after the colon, leaving the credential behind.
_AUTH_SCHEME_RE = re.compile(r"\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE)
#: Credentials recognizable by shape alone (GitHub PAT/OAuth/app, Slack).
_TOKEN_LITERAL_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprs]-[A-Za-z0-9-]{10,})"
)
#: Webhook hosts whose URL path IS the credential (Slack, Discord,
#: Teams/Office 365, Power Automate, Zapier): keep the host, drop the path.
_WEBHOOK_PATH_RE = re.compile(
    r"(https?://(?:hooks\.slack\.com|(?:canary\.|ptb\.)?discord(?:app)?\.com"
    r"|[\w.-]*\.webhook\.office\.com|outlook\.office\.com|[\w.-]*\.logic\.azure\.com"
    r"|hooks\.zapier\.com)(?::\d+)?)/[^\s'\"]*",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    """Strip paths, query strings, URL userinfo, webhook URL paths, and
    secret-looking fragments (auth schemes, known token shapes)."""
    text = _WEBHOOK_PATH_RE.sub(r"\1/<redacted>", text)
    text = _PATH_RE.sub("<path>", text)
    text = _URL_USERINFO_RE.sub(r"\1<redacted>@", text)
    text = _QUERY_RE.sub("", text)
    text = _AUTH_SCHEME_RE.sub(r"\1 <redacted>", text)
    text = _TOKEN_LITERAL_RE.sub("<redacted>", text)
    return _SECRET_RE.sub("<redacted>", text)


def classify(exc: Exception) -> tuple[str, bool]:
    """(category, retryable) for an exception."""
    if isinstance(exc, httpx.TimeoutException):
        return "network", True
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code if exc.response is not None else None
        if code == 429:
            return "rate_limit", True
        if code is not None and code >= 500:
            return "http", True
        return "http", False
    if isinstance(exc, httpx.HTTPError):
        return "network", True
    if isinstance(exc, ValueError):
        return "parse", False
    return "unknown", False


def safe_message(exc: Exception, limit: int = 200) -> str:
    """Exception class + redacted, truncated detail (no traceback, no locals)."""
    detail = redact(str(exc).replace("\n", " ").strip())
    text = f"{type(exc).__name__}: {detail}" if detail else type(exc).__name__
    return text[:limit]


def status_of(exc: Exception) -> int | None:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code
    return None


def as_error(source: str, exc: Exception, **context: Any) -> dict[str, Any]:
    """Build the canonical error dict. Keeps `error` truthy for old consumers."""
    category, retryable = classify(exc)
    return {
        "collector": source,
        "error": True,
        "category": category,
        "retryable": retryable,
        "status_code": status_of(exc),
        "safe_message": safe_message(exc),
        **context,
    }
