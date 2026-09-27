"""endoflife.date collector — lifecycle (EOL/EOS) source. https://endoflife.date/docs/api/"""

from __future__ import annotations

from typing import Any

import httpx

from collectors.base import BaseCollector
from collectors.errors import as_error


def parse_product(product: str, payload: Any) -> list[dict[str, Any]]:
    # API returns list of cycles: [{cycle, eol, support, latest, ...}]
    if isinstance(payload, dict):  # single-cycle shape
        payload = [payload]
    out = []
    for c in payload:
        out.append(
            {
                "collector": "endoflife",
                "product": product,
                "cycle": c.get("cycle"),
                "eol": c.get("eol"),  # date | bool | str
                "support": c.get("support"),
                "latest": c.get("latest"),
                "link": f"https://endoflife.date/{product}",
            }
        )
    return out


class EndoflifeCollector(BaseCollector):
    name = "endoflife"

    def __init__(self, slug_map: dict[str, str] | None = None, timeout: float = 15.0):
        # project_slug -> endoflife.date product, e.g. {"kafka": "apache-kafka"}
        self.slug_map = slug_map or {}
        self.timeout = timeout

    def collect(self, project_slug: str) -> list[dict[str, Any]]:
        product = self.slug_map.get(project_slug, project_slug)
        url = f"https://endoflife.date/api/{product}.json"
        try:
            r = httpx.get(url, timeout=self.timeout)
            if r.status_code == 404:
                return [
                    {
                        "collector": "endoflife",
                        "product": product,
                        "skipped": "not on endoflife.date",
                    }
                ]
            r.raise_for_status()
            return parse_product(product, r.json())
        except Exception as e:
            return [as_error("endoflife", e, product=product)]
