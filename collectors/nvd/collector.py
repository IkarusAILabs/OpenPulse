"""NVD collector — CVE enrichment via NVD API 2.0 keyword search.

Docs: https://nvd.nist.gov/developers/api
Rate limits: 5 req/30s without key, 50 req/30s with `apiKey` header.

A whole-catalog report makes one request per project, far past the
keyless limit, and NVD answers the excess with 403. Unpaced, each run
silently lost a different set of projects' advisories (November 2026).
So requests are paced process-wide to stay inside the limit, a
rate-limit answer is retried, and the key comes from ``NVD_API_KEY``
when none is passed. A request that still fails is an ordinary error
record, which the monthly report names as "did not answer".
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from collectors import http
from collectors.base import BaseCollector
from collectors.errors import as_error

API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEY_ENV = "NVD_API_KEY"

#: Minimum spacing between requests: 30 s / 5 requests without a key and
#: 30 s / 50 with one, plus a margin for clock skew between us and NVD.
INTERVAL_KEYLESS = 6.5
INTERVAL_KEYED = 0.7
#: Rate-limit answers worth a retry. NVD uses 403 for "too many requests".
_RETRY_STATUSES = (403, 429, 503)
MAX_ATTEMPTS = 3
#: Wait before a retry when NVD gives no Retry-After: its 30 s window.
RETRY_WAIT_KEYLESS = 30.0
RETRY_WAIT_KEYED = 6.0

# Seams for tests (tests/conftest.py makes the waits instant).
_sleep = time.sleep
_clock = time.monotonic
_pace_lock = threading.Lock()
_last_request = [float("-inf")]


def _pace(interval: float) -> None:
    """Block until ``interval`` seconds have passed since the last NVD request."""
    with _pace_lock:
        wait = _last_request[0] + interval - _clock()
        if wait > 0:
            _sleep(wait)
        _last_request[0] = _clock()


def _retry_after(response: Any, default: float) -> float:
    value = str(response.headers.get("retry-after", "")).strip()
    return float(value) if value.isdigit() and 0 < int(value) <= 300 else default


def _description(descriptions: list[dict[str, Any]]) -> str:
    for d in descriptions:
        if d.get("lang") == "en":
            return d.get("value", "")
    return descriptions[0].get("value", "") if descriptions else ""


def _cvss(metrics: dict[str, Any]) -> dict[str, Any]:
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if entries:
            data = entries[0].get("cvssData", {})
            return {
                "version": key,
                "base_score": data.get("baseScore"),
                "severity": data.get("baseSeverity"),
            }
    return {}


_RANGE_ATTRS = (
    "versionStartIncluding",
    "versionStartExcluding",
    "versionEndIncluding",
    "versionEndExcluding",
)


def _cpes(configurations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """CPE match criteria — the identity evidence keyword search cannot give."""
    out = []
    for config in configurations:
        for node in config.get("nodes", []) + config.get("children", []):
            for match in node.get("cpeMatch", []) + node.get("cpe_match", []):
                criteria = match.get("criteria")
                if criteria and not any(c["criteria"] == criteria for c in out):
                    entry = {"criteria": criteria, "vulnerable": bool(match.get("vulnerable"))}
                    for attr in _RANGE_ATTRS:
                        if match.get(attr) is not None:
                            entry[attr] = match[attr]
                    out.append(entry)
    return out


def parse_cves(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in payload.get("vulnerabilities", []):
        cve = item.get("cve", {})
        out.append(
            {
                "collector": "nvd",
                "id": cve.get("id"),
                "published": cve.get("published"),
                "last_modified": cve.get("lastModified"),
                "description": _description(cve.get("descriptions", [])),
                "cvss": _cvss(cve.get("metrics", {})),
                "cpes": _cpes(cve.get("configurations", [])),
                "references": [r.get("url") for r in cve.get("references", []) if r.get("url")],
            }
        )
    return out


class NVDCollector(BaseCollector):
    name = "nvd"

    def __init__(
        self,
        keyword_map: dict[str, str] | None = None,
        api_key: str | None = None,
        timeout: float = 20.0,
    ):
        # project_slug -> NVD keywordSearch, e.g. {"redis": "redis"}
        self.keyword_map = keyword_map or {}
        # Explicit key first, then NVD_API_KEY; never logged or stored.
        self.api_key = api_key if api_key is not None else (os.environ.get(KEY_ENV) or None)
        self.timeout = timeout

    def collect(self, project_slug: str) -> list[dict[str, Any]]:
        keyword = self.keyword_map.get(project_slug, project_slug)
        headers = {"apiKey": self.api_key} if self.api_key else {}
        interval = INTERVAL_KEYED if self.api_key else INTERVAL_KEYLESS
        retry_wait = RETRY_WAIT_KEYED if self.api_key else RETRY_WAIT_KEYLESS
        try:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                _pace(interval)
                r = http.get(
                    API,
                    params={"keywordSearch": keyword, "resultsPerPage": 20},
                    headers=headers,
                    timeout=self.timeout,
                )
                if r.status_code not in _RETRY_STATUSES or attempt == MAX_ATTEMPTS:
                    break
                _sleep(_retry_after(r, retry_wait))
            r.raise_for_status()
            vulns = parse_cves(r.json())
            return vulns or [{"collector": "nvd", "keyword": keyword, "vulns": 0}]
        except Exception as e:  # network/API failure must never crash pipeline
            return [as_error("nvd", e, project=project_slug)]
