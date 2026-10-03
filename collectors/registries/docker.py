"""Registry collector — distribution signals (bitnami vs legacy vs secure)."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.base import BaseCollector
from collectors.errors import as_error

#: Hub pagination: 100 tags per page, up to this many pages. Observations
#: must capture the full tag set — a first-page-only window turns recency
#: churn into phantom disappearances (a tag bumped out of the window is
#: not a removal). The observation tag cap in registry.py bounds memory.
#: When pages run out before `next` clears, the probe is marked
#: truncated and diffs against it are withheld (incomparable basis).
_MAX_TAG_PAGES = 30


def docker_hub_url(namespace: str, repo: str) -> str:
    return f"https://hub.docker.com/v2/repositories/{namespace}/{repo}/tags?page_size=100"


#: A tag is *version-like* when it carries a numeric version component
#: anywhere in it (``7.2.0``, ``3.12-slim``, ``1.30-alpine3.24``). These
#: are the tags a pinned reference can resolve against. Everything else
#: a namespace serves alongside ``latest`` without carrying a version —
#: digest tags (``sha256-*``), attestation sidecars (``*.sig``,
#: ``*.att``, ``*-metadata``) — is distribution machinery, not a
#: versioned distribution. Counting those as "versioned tags" kept the
#: latest-only rule blind to mainlines that serve only machinery
#: (docs/DISCOVERIES.md case 2): a namespace whose every tag is either
#: ``latest`` or machinery pins nothing, whatever the machinery volume.
_DIGEST_OR_ATTESTATION_PREFIX = ("sha256-",)


def _is_attestation_suffix(tag: str) -> bool:
    lower = tag.lower()
    return lower.endswith(".sig") or lower.endswith(".att") or lower.endswith("-metadata")


def _is_version_like(tag: str) -> bool:
    """True when the tag carries a numeric version component.

    Generic, product-agnostic: any digit run qualifies (``7.2.0``,
    ``3.12-slim``, ``19beta4-bookworm``). Digest tags and attestation
    sidecars are never version-like no matter what they contain. The
    prefix/suffix checks are case-folded: Hub tags are lowercase by
    convention, but the guard costs one line.
    """
    if tag.lower().startswith(_DIGEST_OR_ATTESTATION_PREFIX) or _is_attestation_suffix(tag):
        return False
    return any(ch.isdigit() for ch in tag)


def parse_tags(namespace: str, repo: str, payload: dict[str, Any]) -> dict[str, Any]:
    tags = [t.get("name") for t in payload.get("results", [])]
    digests = {}
    for t in payload.get("results", []):
        if not t.get("name"):
            continue
        ds = sorted({img.get("digest") for img in t.get("images", []) if img.get("digest")})
        digests[t["name"]] = ds
    return {
        "collector": "registries",
        "registry": "docker.io",
        "namespace": namespace,
        "repo": repo,
        "tags_sample": tags,
        "digests": digests,
        "count": payload.get("count"),
        "has_versioned_tags": any(_is_version_like(t) for t in tags),
        "latest_only": bool(tags)
        and all(t == "latest" or not _is_version_like(t) for t in tags),
    }


class RegistryCollector(BaseCollector):
    name = "registries"

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def check_image(self, namespace: str, repo: str) -> dict[str, Any]:
        try:
            results: list[dict[str, Any]] = []
            count: int | None = None
            url: str | None = docker_hub_url(namespace, repo)
            pages = 0
            truncated = False
            while url is not None and pages < _MAX_TAG_PAGES:
                r = httpx.get(url, timeout=self.timeout)
                if r.status_code == 404:
                    return {
                        "collector": "registries",
                        "namespace": namespace,
                        "repo": repo,
                        "missing": True,
                    }
                r.raise_for_status()
                payload = r.json()
                if not isinstance(payload, dict):
                    raise ValueError("registry response is not a mapping")
                if count is None:
                    count = payload.get("count")
                entries = payload.get("results", [])
                if not isinstance(entries, list):
                    raise ValueError("registry results are not a list")
                results.extend(e for e in entries if isinstance(e, dict))
                url = payload.get("next")
                pages += 1
            if url is not None:
                truncated = True
            probe = parse_tags(namespace, repo, {"results": results, "count": count})
            probe["truncated"] = truncated
            return probe
        except Exception as e:
            return as_error("registries", e, namespace=namespace, repo=repo)

    def collect(self, project_slug: str) -> list[dict[str, Any]]:
        # Generic acquisition knows nothing product-specific: callers use
        # check_image(namespace, repo) directly, or a named reference set
        # from collectors/registries/reference.py for rehearsed scenarios.
        return [
            {
                "collector": "registries",
                "project": project_slug,
                "skipped": "use check_image(namespace, repo)",
            }
        ]
