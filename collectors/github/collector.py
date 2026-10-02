"""GitHub releases collector — upstream source of truth for tags, archive/deprecation signals."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.base import BaseCollector
from collectors.errors import as_error

API = "https://api.github.com/repos/{repo}/releases?per_page=20"
REPO_API = "https://api.github.com/repos/{repo}"


def parse_releases(repo: str, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in payload:
        out.append(
            {
                "collector": "github",
                "repo": repo,
                "tag": r.get("tag_name"),
                "name": r.get("name"),
                "published_at": r.get("published_at"),
                "prerelease": bool(r.get("prerelease")),
                "url": r.get("html_url"),
            }
        )
    return out


def parse_repo(repo: str, payload: dict[str, Any]) -> dict[str, Any]:
    lic = payload.get("license") or {}
    return {
        "collector": "github",
        "kind": "repo_meta",
        "repo": repo,
        # Actual path from the API response: renames/transfers answer
        # here, not in the queried path. The analyst compares the two.
        "full_name": payload.get("full_name"),
        "archived": bool(payload.get("archived")),
        "pushed_at": payload.get("pushed_at"),
        "default_branch": payload.get("default_branch"),
        "license": lic.get("spdx_id") or lic.get("key"),
        "stargazers": payload.get("stargazers_count"),
        "url": payload.get("html_url"),
    }


class GitHubCollector(BaseCollector):
    name = "github"

    def __init__(
        self,
        repo_map: dict[str, str] | None = None,
        timeout: float = 15.0,
        token: str | None = None,
    ):
        # project_slug -> "org/repo", e.g. {"redis": "redis/redis"}
        self.repo_map = repo_map or {}
        self.timeout = timeout
        self.token = token

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def collect(self, project_slug: str) -> list[dict[str, Any]]:
        repo = self.repo_map.get(project_slug)
        if not repo:
            return [
                {
                    "collector": "github",
                    "project": project_slug,
                    "skipped": f"no repo mapping for {project_slug}",
                }
            ]
        try:
            r = httpx.get(
                API.format(repo=repo),
                timeout=self.timeout,
                headers=self._headers(),
            )
            r.raise_for_status()
            return parse_releases(repo, r.json())
        except Exception as e:  # network/API failure must never crash pipeline
            return [as_error("github", e, project=project_slug, repo=repo)]

    def fetch_repo_meta(self, project_slug: str) -> dict[str, Any]:
        """Repository metadata (archived flag, push date) for lifecycle rules."""

        repo = self.repo_map.get(project_slug)
        if not repo:
            return {
                "collector": "github",
                "project": project_slug,
                "skipped": f"no repo mapping for {project_slug}",
            }
        try:
            r = httpx.get(
                REPO_API.format(repo=repo),
                timeout=self.timeout,
                headers=self._headers(),
            )
            r.raise_for_status()
            return parse_repo(repo, r.json())
        except Exception as e:
            return [as_error("github", e, project=project_slug, repo=repo)][0]
