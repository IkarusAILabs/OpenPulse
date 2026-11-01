"""Derived source authority (v0.9.0 item B1, finding M1).

``authority`` on a source is a string the producer supplies. Before B1,
any source that said ``official`` could carry an event to CONFIRMED.
Now ``official`` is derived, never taken on trust: a source counts as
official for a project only when its URL is https and names a location
on that project's allowlist in ``data/official_domains.yaml``. Anything
else claiming ``official`` is read as ``secondary``, and the reason is
returned so the gate can report it.

Allowlist entries:

- ``djangoproject.com``: that host, or any dot-boundary subdomain
  (``www.djangoproject.com``; never ``evil-djangoproject.com`` or
  ``djangoproject.com.evil.com``).
- ``github.com/bitnami``: exactly that host, and paths at or under that
  path segment (``/bitnami``, ``/bitnami/charts``; never
  ``/bitnami-fork``). Shared hosts such as github.com are only ever
  listed with a path, so another organisation's page never counts.

Fail-closed: no allowlist for the project, a non-https URL, a non-ASCII
host (an IDN must be listed in its ``xn--`` form), userinfo, a port other
than 443, or an unparseable URL all mean "not official".
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit

import yaml

from core.resources import data_path

DEFAULT_PATH = data_path("official_domains.yaml")

#: Authority a source claiming ``official`` is read as when the claim
#: cannot be derived.
DOWNGRADED = "secondary"


@lru_cache(maxsize=4)
def load_official_domains(path: str | None = None) -> dict[str, tuple[str, ...]]:
    """slug -> allowlist entries. A missing file means no project has any."""
    try:
        with open(path or DEFAULT_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError("official_domains.yaml must map project slugs to lists")
    out: dict[str, tuple[str, ...]] = {}
    for slug, entries in data.items():
        if not isinstance(entries, list):
            raise ValueError(f"official_domains for {slug!r} must be a list")
        out[str(slug)] = tuple(str(e).strip().lower().rstrip("/") for e in entries)
    return out


def _split(url: str) -> tuple[str, str] | None:
    """(host, path) of an https URL fit for allowlisting, else None."""
    try:
        parts = urlsplit(str(url))
        port = parts.port
    except ValueError:
        return None
    if parts.scheme.lower() != "https" or parts.username is not None:
        return None
    if port not in (None, 443):
        return None
    host = (parts.hostname or "").lower()
    if not host or not host.isascii():
        return None
    return host, parts.path.lower()


def _matches(host: str, path: str, entry: str) -> bool:
    entry_host, _, entry_path = entry.partition("/")
    if entry_path:
        prefix = "/" + entry_path
        return host == entry_host and (path == prefix or path.startswith(prefix + "/"))
    return host == entry_host or host.endswith("." + entry_host)


def is_official(
    url: Any, project_slug: str, domains: dict[str, tuple[str, ...]] | None = None
) -> bool:
    """True when ``url`` is an https location on the project's allowlist."""
    entries = (load_official_domains() if domains is None else domains).get(str(project_slug))
    split = _split(str(url)) if url is not None else None
    if not entries or split is None:
        return False
    host, path = split
    return any(_matches(host, path, entry) for entry in entries)


def _field(source: Any, name: str) -> Any:
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def derive_authority(
    source: Any, project_slug: str, domains: dict[str, tuple[str, ...]] | None = None
) -> tuple[str, str | None]:
    """(authority to use, downgrade reason or None) for one source.

    Only ``official`` is derived; other values pass through unchanged.
    """
    claimed = str(_field(source, "authority") or "")
    if claimed != "official":
        return claimed, None
    url = _field(source, "url")
    if is_official(url, project_slug, domains):
        return "official", None
    name = _field(source, "name") or "?"
    return DOWNGRADED, (
        f"source {name!r} claims authority=official, but {url} is not an https "
        f"location on the official_domains allowlist for {project_slug!r}"
    )
