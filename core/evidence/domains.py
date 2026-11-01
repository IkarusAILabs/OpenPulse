"""Source families from URLs (v0.9.0 item B2, finding M2).

Two pages on one site are one source, whatever names or families their
producer gives them. ``url_family`` turns a URL into the family it
belongs to:

- the registrable domain of its host (``blog.redis.io`` and
  ``redis.io/docs`` are both ``redis.io``);
- on a shared host, where unrelated owners publish side by side, the
  host plus the first path segment (``github.com/bitnami``).

The registrable domain is the last two labels, or three under a listed
two-level public suffix (``bbc.co.uk``). No public-suffix dependency:
an unlisted suffix makes the family too wide, never too narrow, so the
error only ever withholds corroboration.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

#: Hosts whose first path segment names an independent owner.
SHARED_HOSTS = frozenset(
    {
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "codeberg.org",
        "sourceforge.net",
        "medium.com",
        "dev.to",
        "hub.docker.com",
        "pypi.org",
        "www.npmjs.com",
        "npmjs.com",
    }
)

#: Two-level public suffixes under which the registrable domain has three
#: labels. Not exhaustive; see the module docstring for why that is safe.
TWO_LEVEL_SUFFIXES = frozenset(
    {
        "co.uk", "org.uk", "ac.uk", "gov.uk", "me.uk",
        "com.au", "net.au", "org.au", "edu.au",
        "co.jp", "ne.jp", "or.jp", "ac.jp",
        "com.br", "com.cn", "com.tw", "com.hk", "com.sg", "com.mx", "com.tr",
        "co.in", "co.kr", "co.nz", "co.za", "co.il",
        "github.io", "gitlab.io", "pages.dev", "netlify.app", "vercel.app",
        "herokuapp.com", "blogspot.com", "readthedocs.io", "substack.com",
    }
)  # fmt: skip


def registrable_domain(host: str) -> str:
    """``www.blog.example.co.uk`` -> ``example.co.uk``; IPs stay whole."""
    host = host.strip(".").lower()
    labels = host.split(".")
    if len(labels) <= 2 or host.replace(".", "").isdigit() or ":" in host:
        return host
    keep = 3 if ".".join(labels[-2:]) in TWO_LEVEL_SUFFIXES else 2
    return ".".join(labels[-keep:])


def url_family(url: Any) -> str | None:
    """Family a URL belongs to, or None when it has no usable host."""
    if not url:
        return None
    try:
        parts = urlsplit(str(url))
        host = (parts.hostname or "").lower()
    except ValueError:
        return None
    if not host:
        return None
    if host in SHARED_HOSTS:
        owner = parts.path.strip("/").split("/", 1)[0].lower()
        return f"{host}/{owner}" if owner else host
    return registrable_domain(host)
