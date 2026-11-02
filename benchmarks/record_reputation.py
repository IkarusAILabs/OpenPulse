"""Record the organic reputation set (track T Phase 2, T-C; v0.16.0 item Q1).

Run from the repository root, with network access (once per refresh):

    GITHUB_TOKEN=... python benchmarks/record_reputation.py

Writes ``benchmarks/fixtures/reputation/organic-<date>.json``: real,
legitimate packages with their recent releases and their GitHub
repositories, so the reputation indicators (Q2-Q4) are measured offline,
on organic projects, before they ship. The token (environment only, never
stored) raises GitHub's rate limit; it is optional for a small sample.

What is recorded, and nothing more:

- **Packages.** npm: a fixed-stride sample of the pinned npm-high-impact
  list. PyPI: the curated catalog's PyPI packages and OpenPulse's own locked
  dependencies (``requirements*.lock``): there is no approved popular-name
  list yet (decision 9).
- **Releases.** The latest ``RELEASES`` per package by publication time:
  version, time, and who published it. npm: the publishing account
  (``_npmUser``), stored only as a hash because the indicators compare
  accounts, never name them; the trusted-publishing provider when npm
  published it through one (``github``, ``gitlab``), since those releases
  share one service account; and whether the version carries attestations.
  PyPI: the publisher that PyPI's provenance for one file of the release
  names (kind, repository, workflow), as served. Verification is the
  production check's job (T-B1); here only the sequence of claims matters.
- **Repositories.** For each claimed GitHub repository: the name GitHub
  answers with (a different one means it was transferred or renamed),
  creation time, star count, and the archived and fork flags.

Every upstream string is validated before it is stored (T-F3); anything
else is recorded as null.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "benchmarks" / "fixtures" / "reputation"
RELEASES = 10
NPM_SAMPLE = 60
MAX_BYTES = 64 * 1024 * 1024
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?")
_TRUSTED = re.compile(r"[a-z][a-z0-9-]{0,19}")
_LOCK_LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==", re.MULTILINE)

#: url -> (http status, decoded JSON or None); GitHub redirects are followed.
Fetch = Callable[[str], tuple[int, Any]]


def http_fetch(url: str) -> tuple[int, Any]:
    from collectors import http
    from core.registry_existence import user_agent

    headers = {"user-agent": user_agent(), "accept": "application/json"}
    if "integrity/" in url:
        headers["accept"] = "application/vnd.pypi.integrity.v1+json"
    token = os.environ.get("GITHUB_TOKEN", "")
    github = url.startswith("https://api.github.com/")
    if github and token:
        headers["authorization"] = f"Bearer {token}"
    try:
        response = http.get(
            url, max_bytes=MAX_BYTES, timeout=60, headers=headers, follow_redirects=github
        )
    except Exception:  # network trouble or an oversized body: no answer
        return 0, None
    if response.status_code != 200:
        return response.status_code, None
    try:
        return 200, response.json()
    except ValueError:
        return 0, None


def account_hash(name: str) -> str:
    """A stable pseudonym: the indicators compare accounts, they never name them."""
    return "sha256:" + hashlib.sha256(f"npm-user:{name.strip().lower()}".encode()).hexdigest()[:16]


def _time(value: Any) -> str | None:
    text = str(value or "")
    return text if _TIME.fullmatch(text) else None


def _repository(value: Any) -> str | None:
    from core.repository_linkage import github_repository

    if isinstance(value, dict):
        value = value.get("url")
    found = github_repository(value)
    return found[0] if found else None


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def npm_sample(size: int = NPM_SAMPLE) -> list[str]:
    from core.resources import data_path

    snapshot = sorted(data_path("reference").glob("npm-high-impact-*.json"))[-1]
    names = sorted(json.loads(snapshot.read_text(encoding="utf-8"))["names"])
    step = max(1, len(names) // size)
    return names[::step][:size]


def pypi_sample() -> list[str]:
    from core.entities.catalog import load_catalog

    names = {
        str(p["name"]).lower()
        for entry in load_catalog()
        for p in entry.get("packages") or []
        if isinstance(p, dict) and p.get("ecosystem") == "PyPI" and p.get("name")
    }
    for lock in sorted(ROOT.glob("requirements*.lock")):
        names |= {m.lower() for m in _LOCK_LINE.findall(lock.read_text(encoding="utf-8"))}
    return sorted(names)


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


def record_npm(name: str, fetch: Fetch) -> dict[str, Any]:
    status, doc = fetch("https://registry.npmjs.org/" + quote(name, safe="@"))
    out: dict[str, Any] = {"ecosystem": "npm", "name": name, "status": status}
    if status != 200 or not isinstance(doc, dict):
        return out
    times = doc.get("time") if isinstance(doc.get("time"), dict) else {}
    versions = doc.get("versions") if isinstance(doc.get("versions"), dict) else {}
    dated = sorted(
        (t, v)
        for v, t in ((v, _time(times.get(v))) for v in versions)
        if t and _VERSION.fullmatch(v)
    )
    releases = []
    for published, version in dated[-RELEASES:]:
        meta = versions.get(version) if isinstance(versions.get(version), dict) else {}
        user = meta.get("_npmUser") if isinstance(meta.get("_npmUser"), dict) else {}
        account = str(user.get("name") or "")
        dist = meta.get("dist") if isinstance(meta.get("dist"), dict) else {}
        trusted = user.get("trustedPublisher")
        trusted_id = str(trusted.get("id") or "") if isinstance(trusted, dict) else ""
        releases.append(
            {
                "version": version,
                "published": published,
                "publisher": account_hash(account) if account else None,
                "trusted_publisher": trusted_id if _TRUSTED.fullmatch(trusted_id) else None,
                "attested": bool(dist.get("attestations")),
            }
        )
    out.update(
        created=_time(times.get("created")),
        repository=_repository(doc.get("repository")),
        releases=releases,
    )
    return out


def _pypi_publishers(provenance: Any) -> list[dict[str, Any]]:
    from core.provenance import _publisher

    bundles = provenance.get("attestation_bundles") if isinstance(provenance, dict) else None
    found: list[dict[str, Any]] = []
    for bundle in bundles if isinstance(bundles, list) else []:
        raw = bundle.get("publisher") if isinstance(bundle, dict) else None
        if isinstance(raw, dict):
            publisher = _publisher(raw)
            if publisher not in found:
                found.append(publisher)
    return found


def record_pypi(name: str, fetch: Fetch) -> dict[str, Any]:
    from core.provenance import _FILENAME

    status, doc = fetch(f"https://pypi.org/pypi/{quote(name)}/json")
    out: dict[str, Any] = {"ecosystem": "PyPI", "name": name, "status": status}
    if status != 200 or not isinstance(doc, dict):
        return out
    info = doc.get("info") if isinstance(doc.get("info"), dict) else {}
    urls = info.get("project_urls") if isinstance(info.get("project_urls"), dict) else {}
    repository = next(
        (r for r in (_repository(u) for u in [*urls.values(), info.get("home_page")]) if r), None
    )
    project = re.sub(r"[-_.]+", "-", name).lower()
    dated = []
    raw_releases = doc.get("releases") if isinstance(doc.get("releases"), dict) else {}
    for version, files in raw_releases.items():
        files = [f for f in files or [] if isinstance(f, dict) and not f.get("yanked")]
        names = [str(f.get("filename") or "") for f in files]
        names = [n for n in names if _FILENAME.fullmatch(n)]
        times = sorted(t for t in (_time(f.get("upload_time_iso_8601")) for f in files) if t)
        if names and times and _VERSION.fullmatch(version):
            wheel = next((n for n in names if n.endswith(".whl")), names[0])
            dated.append((times[0], version, wheel))
    releases = []
    for published, version, filename in sorted(dated)[-RELEASES:]:
        url = f"https://pypi.org/integrity/{project}/{quote(version)}/{quote(filename)}/provenance"
        p_status, provenance = fetch(url)
        releases.append(
            {
                "version": version,
                "published": published,
                "attested": True if p_status == 200 else False if p_status == 404 else None,
                "publishers": _pypi_publishers(provenance) if p_status == 200 else [],
            }
        )
    out.update(
        created=sorted(dated)[0][0] if dated else None, repository=repository, releases=releases
    )
    return out


def record_repository(repo: str, fetch: Fetch) -> dict[str, Any]:
    from core.github_reader import _valid_repo_parts

    status, doc = fetch(f"https://api.github.com/repos/{repo}")
    if status != 200 or not isinstance(doc, dict):
        return {"status": status}
    answered = str(doc.get("full_name") or "")
    owner, _, name = answered.partition("/")
    stars = doc.get("stargazers_count")
    return {
        "status": 200,
        "full_name": answered if _valid_repo_parts(owner, name) else None,
        "created": _time(doc.get("created_at")),
        "stars": stars if isinstance(stars, int) and stars >= 0 else None,
        "archived": doc.get("archived") is True,
        "fork": doc.get("fork") is True,
    }


def record(fetch: Fetch, npm: list[str], pypi: list[str], log=print) -> dict[str, Any]:
    from core.version import openpulse_version

    packages = []
    for ecosystem, names, recorder in (("npm", npm, record_npm), ("PyPI", pypi, record_pypi)):
        for index, name in enumerate(names, 1):
            packages.append(recorder(name, fetch))
            log(f"{ecosystem} {index}/{len(names)} {name}")
    repos = sorted({p["repository"] for p in packages if p.get("repository")}, key=str.lower)
    repositories = {}
    for index, repo in enumerate(repos, 1):
        repositories[repo] = record_repository(repo, fetch)
        log(f"github {index}/{len(repos)} {repo}")
    return {
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recorder": "benchmarks/record_reputation.py",
        "openpulse_version": openpulse_version(),
        "releases_per_package": RELEASES,
        "selection": {
            "npm": f"a fixed-stride sample of {len(npm)} names from the pinned "
            "npm-high-impact list (sorted)",
            "PyPI": "the curated catalog's PyPI packages and OpenPulse's own locked "
            "dependencies (requirements*.lock); no popular-name list yet (decision 9)",
        },
        "packages": packages,
        "repositories": repositories,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--npm", type=int, default=NPM_SAMPLE, help="npm packages to sample")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    doc = record(http_fetch, npm_sample(args.npm), pypi_sample())
    FIXTURES.mkdir(parents=True, exist_ok=True)
    out = FIXTURES / f"organic-{doc['recorded_at'][:10]}.json"
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} in {time.perf_counter() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
