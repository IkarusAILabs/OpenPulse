"""Data collection for the upstream-source-change prevalence study.

Implements PROTOCOL.md §3-§4. Standard library only, and independent of
OpenPulse: nothing here imports the openpulse package or reads its
catalogue, so the study measures the ecosystems, not the tool.

    python collect.py frame  --out data/run --max-rank 20000
    python collect.py sample --out data/run --top 1000 --tail 1000 --seed N
    python collect.py measure --out data/run

Every HTTP response is appended to <out>/raw.jsonl.gz with its URL, status
and UTC time, so each derived value can be traced to the bytes it came
from. GitHub requests use GITHUB_TOKEN, or `gh auth token` if unset.
"""

import argparse
import gzip
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

ECOSYSTEMS = {
    # study name: (ecosyste.ms registry, OSV ecosystem)
    "npm": ("npmjs.org", "npm"),
    "pypi": ("pypi.org", "PyPI"),
    "go": ("proxy.golang.org", "Go"),
}

#: PROTOCOL.md §4, advisory signal: pre-registered terms, case-insensitive.
ADVISORY_TERMS = re.compile(
    r"unmaintained|deprecated|archived|abandoned|no longer maintained|"
    r"end of life|end-of-life",
    re.IGNORECASE,
)
#: PROTOCOL.md §4, repository URL: PyPI project_urls keys, in order.
PYPI_URL_KEYS = ("source", "sources", "source code", "repository", "code", "github", "homepage")
GO_IMPORT = re.compile(r'<meta\s+name="go-import"\s+content="([^"]+)"', re.IGNORECASE)
GITHUB_PATH = re.compile(r"github\.com[/:]+([^/\s#?]+)/([^/\s#?]+)", re.IGNORECASE)
USER_AGENT = "ikarus-prevalence-study/0.1 (+https://ikaruslabs.net/)"


def now():
    return datetime.now(UTC).isoformat(timespec="seconds")


class Http:
    """GET/POST with retries, rate-limit waits and a raw-response log."""

    def __init__(self, raw_path):
        self.raw = gzip.open(raw_path, "at", encoding="utf-8")
        self.lock = threading.Lock()
        self.github_token = os.environ.get("GITHUB_TOKEN") or self._gh_token()

    @staticmethod
    def _gh_token():
        try:
            return subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    def request(self, url, data=None, attempts=5):
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if url.startswith("https://api.github.com/") and self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        for attempt in range(attempts):
            req = urllib.request.Request(url, data=body, headers=headers)
            fetched = now()
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    status, final_url, text = (
                        resp.status,
                        resp.geturl(),
                        resp.read().decode("utf-8", "replace"),
                    )
                    resp_headers = dict(resp.headers)
            except urllib.error.HTTPError as err:
                status, final_url = err.code, err.geturl()
                text = err.read().decode("utf-8", "replace")
                resp_headers = dict(err.headers or {})
            except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
                time.sleep(2**attempt)
                if attempt == attempts - 1:
                    self._log(url, fetched, None, url, str(err))
                    return None, url, None
                continue
            if status in (403, 429) and ("rate limit" in text.lower() or status == 429):
                self._wait(resp_headers)
                continue
            if status >= 500 and attempt < attempts - 1:
                time.sleep(2**attempt)
                continue
            self._log(url, fetched, status, final_url, text)
            try:
                return status, final_url, json.loads(text) if text else None
            except json.JSONDecodeError:
                return status, final_url, text
        return None, url, None

    @staticmethod
    def _wait(headers):
        reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        retry = headers.get("Retry-After") or headers.get("retry-after")
        delay = int(retry) if retry else max(int(reset) - int(time.time()), 1) if reset else 60
        print(f"  rate limited; waiting {min(delay, 3600)}s", file=sys.stderr)
        time.sleep(min(delay, 3600) + 1)

    def _log(self, url, fetched, status, final_url, text):
        line = (
            json.dumps(
                {
                    "url": url,
                    "fetched_at": fetched,
                    "status": status,
                    "final_url": final_url,
                    "body": text,
                }
            )
            + "\n"
        )
        with self.lock:
            self.raw.write(line)

    def close(self):
        self.raw.close()


# --- frame and sample (PROTOCOL.md §3) -------------------------------------


def cmd_frame(args, http):
    os.makedirs(args.out, exist_ok=True)
    for eco, (registry, _) in ECOSYSTEMS.items():
        path = os.path.join(args.out, f"frame-{eco}.jsonl")
        rows, page = [], 1
        while len(rows) < args.max_rank:
            url = (
                f"https://packages.ecosyste.ms/api/v1/registries/{registry}/packages"
                f"?sort=dependent_repos_count&order=desc&per_page=100&page={page}"
            )
            status, _, body = http.request(url)
            if status != 200 or not body:
                sys.exit(f"frame: {url} returned {status}")
            for pkg in body:
                meta = pkg.get("repo_metadata") or {}
                rows.append(
                    {
                        "ecosystem": eco,
                        "rank": len(rows) + 1,
                        "name": pkg["name"],
                        "dependent_repos_count": pkg.get("dependent_repos_count"),
                        "dependent_packages_count": pkg.get("dependent_packages_count"),
                        "frame_repository_url": pkg.get("repository_url"),
                        "frame_archived": meta.get("archived"),
                        "frame_full_name": meta.get("full_name"),
                        "frame_previous_names": meta.get("previous_names") or [],
                        "frame_status": pkg.get("status"),
                        "frame_fetched_at": now(),
                    }
                )
            page += 1
            print(f"{eco}: {len(rows)}", file=sys.stderr)
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows[: args.max_rank]:
                fh.write(json.dumps(row) + "\n")


def cmd_sample(args, _http):
    rng = random.Random(args.seed)
    out = os.path.join(args.out, "sample.jsonl")
    with open(out, "w", encoding="utf-8") as fh:
        for eco in ECOSYSTEMS:
            frame = [
                json.loads(line)
                for line in open(os.path.join(args.out, f"frame-{eco}.jsonl"), encoding="utf-8")
            ]
            top = frame[: args.top]
            tail_pool = frame[args.top : args.tail_max_rank]
            tail = sorted(
                rng.sample(tail_pool, min(args.tail, len(tail_pool))), key=lambda r: r["rank"]
            )
            for stratum, rows in (("top", top), ("tail", tail)):
                for row in rows:
                    fh.write(json.dumps({**row, "stratum": stratum}) + "\n")


# --- measures (PROTOCOL.md §4) ---------------------------------------------


def github_repo_from_url(url):
    """owner/repo from a github.com URL, or None (PROTOCOL.md §4)."""
    if not isinstance(url, str):
        return None
    match = GITHUB_PATH.search(url)
    if not match:
        return None
    owner, repo = match.group(1), match.group(2)
    repo = re.sub(r"\.git$", "", repo).rstrip("/")
    return f"{owner}/{repo}" if owner and repo else None


def go_escape(path):
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), path)


def registry_metadata(http, eco, name):
    """Published repository URL, deprecation signal and latest release time."""
    if eco == "npm":
        # The latest version's manifest carries `repository` and
        # `deprecated`. Its release time is only in the full packument,
        # which can be many megabytes, so npm_release_time() fetches that
        # only where PROTOCOL.md §5 needs it (archived repositories).
        status, _, manifest = http.request(
            "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@") + "/latest"
        )
        if status != 200 or not isinstance(manifest, dict):
            return {"registry_status": status}
        repo = manifest.get("repository")
        repo_url = repo.get("url") if isinstance(repo, dict) else repo
        return {
            "registry_status": status,
            "latest": manifest.get("version"),
            "registry_repository_url": repo_url,
            "deprecated": bool(manifest.get("deprecated")),
            "deprecated_detail": manifest.get("deprecated") or None,
            "latest_released_at": None,
        }
    if eco == "pypi":
        status, _, body = http.request(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
        if status != 200 or not isinstance(body, dict):
            return {"registry_status": status}
        info = body.get("info") or {}
        published = info.get("project_urls") or {}
        urls = {str(k).strip().lower(): v for k, v in published.items()}
        repo_url = next((urls[k] for k in PYPI_URL_KEYS if github_repo_from_url(urls.get(k))), None)
        if repo_url is None:
            repo_url = next((v for v in published.values() if github_repo_from_url(v)), None)
        if repo_url is None and github_repo_from_url(info.get("home_page")):
            repo_url = info.get("home_page")
        inactive = "Development Status :: 7 - Inactive" in (info.get("classifiers") or [])
        files = body.get("urls") or []
        return {
            "registry_status": status,
            "latest": info.get("version"),
            "registry_repository_url": repo_url,
            "deprecated": inactive or bool(info.get("yanked")),
            "deprecated_detail": ("inactive classifier" if inactive else None)
            or (f"yanked: {info.get('yanked_reason')}" if info.get("yanked") else None),
            "latest_released_at": min((f.get("upload_time_iso_8601") for f in files), default=None),
        }
    if eco == "go":
        base = "https://proxy.golang.org/" + go_escape(name)
        status, _, body = http.request(base + "/@latest")
        repo_url = go_repository_url(http, name)
        if status != 200 or not isinstance(body, dict):
            return {"registry_status": status, "registry_repository_url": repo_url}
        version = body.get("Version")
        mstatus, _, gomod = http.request(f"{base}/@v/{go_escape(version)}.mod")
        text = gomod if isinstance(gomod, str) else ""
        dep = re.search(r"^//\s*Deprecated:(.*)$", text, re.MULTILINE)
        return {
            "registry_status": status,
            "latest": version,
            "registry_repository_url": repo_url,
            "deprecated": bool(dep),
            "deprecated_detail": dep.group(0) if dep else None,
            "latest_released_at": body.get("Time"),
            "gomod_status": mstatus,
        }
    raise ValueError(eco)


def go_repository_url(http, module):
    """Source repository of a Go module (PROTOCOL.md §4, repository URL)."""
    if module.startswith("github.com/"):
        return module
    gopkg = re.match(r"gopkg\.in/(?:([^/]+)/)?([^/.]+)\.v\d+", module)
    if gopkg:
        user, pkg = gopkg.groups()
        return f"github.com/{user or 'go-' + pkg}/{pkg}"
    status, _, page = http.request(f"https://{module}?go-get=1")
    if status != 200 or not isinstance(page, str):
        return None
    for content in GO_IMPORT.findall(page):
        prefix, _vcs, repo = (content.split() + ["", "", ""])[:3]
        if module == prefix or module.startswith(prefix + "/"):
            return repo
    return None


def npm_release_time(http, name, version):
    status, _, body = http.request(
        "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@")
    )
    if status != 200 or not isinstance(body, dict):
        return None
    return (body.get("time") or {}).get(version)


def github_state(http, full_name):
    status, final_url, body = http.request(f"https://api.github.com/repos/{full_name}")
    state = {"github_status": status, "github_requested": full_name}
    if status == 200 and isinstance(body, dict):
        returned = body.get("full_name") or ""
        state.update(
            {
                "github_full_name": returned,
                "repo_state": "unchanged" if returned.lower() == full_name.lower() else "relocated",
                "archived": bool(body.get("archived")),
                "pushed_at": body.get("pushed_at"),
                "github_redirected": final_url.rstrip("/")
                != f"https://api.github.com/repos/{full_name}",
            }
        )
    elif status in (404, 451):
        state.update({"repo_state": "unreachable", "archived": None})
    else:
        state.update({"repo_state": "error", "archived": None})
    return state


def osv_signals(http, eco, names, vuln_cache):
    """Matched advisory ids per name (PROTOCOL.md §4, advisory signal)."""
    osv_eco = ECOSYSTEMS[eco][1]
    result = {}
    for start in range(0, len(names), 500):
        chunk = names[start : start + 500]
        status, _, body = http.request(
            "https://api.osv.dev/v1/querybatch",
            data={"queries": [{"package": {"name": n, "ecosystem": osv_eco}} for n in chunk]},
        )
        if status != 200 or not isinstance(body, dict):
            sys.exit(f"OSV querybatch returned {status}")
        per_name = {
            name: [v["id"] for v in res.get("vulns") or []]
            for name, res in zip(chunk, body.get("results") or [], strict=False)
        }
        missing = sorted({vid for ids in per_name.values() for vid in ids} - set(vuln_cache))
        with ThreadPoolExecutor(max_workers=8) as pool:
            for vid, hit in zip(
                missing, pool.map(lambda v: osv_matches(http, v), missing), strict=True
            ):
                vuln_cache[vid] = hit
        for name, ids in per_name.items():
            result[name] = {
                "osv_advisories": len(ids),
                "osv_matched": [vid for vid in ids if vuln_cache[vid]],
            }
    return result


def osv_matches(http, vid):
    status, _, body = http.request(f"https://api.osv.dev/v1/vulns/{vid}")
    if status != 200 or not isinstance(body, dict):
        return False
    return bool(ADVISORY_TERMS.search(f"{body.get('summary') or ''}\n{body.get('details') or ''}"))


def cmd_measure(args, http):
    sample = [
        json.loads(line) for line in open(os.path.join(args.out, "sample.jsonl"), encoding="utf-8")
    ]
    status, _, products = http.request("https://endoflife.date/api/all.json")
    if status != 200:
        sys.exit(f"endoflife.date returned {status}")
    eol = {str(p).lower() for p in products}
    vuln_cache = {}
    out = os.path.join(args.out, "measures.jsonl")
    done = set()
    if os.path.exists(out):
        done = {(r["ecosystem"], r["name"]) for r in map(json.loads, open(out, encoding="utf-8"))}
    with open(out, "a", encoding="utf-8") as fh:
        for eco in ECOSYSTEMS:
            rows = [r for r in sample if r["ecosystem"] == eco and (eco, r["name"]) not in done]
            signals = osv_signals(http, eco, [r["name"] for r in rows], vuln_cache) if rows else {}
            for i, row in enumerate(rows, 1):
                rec = {**row, **registry_metadata(http, eco, row["name"])}
                full_name = github_repo_from_url(rec.get("registry_repository_url"))
                rec["repository"] = full_name
                if full_name:
                    rec.update(github_state(http, full_name))
                    repo_name = full_name.split("/")[1].lower()
                    if eco == "npm" and rec.get("archived") and rec.get("latest"):
                        rec["latest_released_at"] = npm_release_time(
                            http, row["name"], rec["latest"]
                        )
                else:
                    rec["repo_state"] = "excluded"
                    repo_name = None
                rec.update(signals.get(row["name"], {}))
                rec["eol_product"] = row["name"].lower() in eol or (
                    repo_name in eol if repo_name else False
                )
                rec["measured_at"] = now()
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                if i % 50 == 0:
                    print(f"{eco}: {i}/{len(rows)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("frame")
    p.add_argument("--out", required=True)
    p.add_argument("--max-rank", type=int, default=20000)
    p = sub.add_parser("sample")
    p.add_argument("--out", required=True)
    p.add_argument("--top", type=int, default=1000)
    p.add_argument("--tail", type=int, default=1000)
    p.add_argument("--tail-max-rank", type=int, default=20000)
    p.add_argument("--seed", type=int, required=True)
    p = sub.add_parser("measure")
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    http = Http(os.path.join(args.out, "raw.jsonl.gz"))
    try:
        {"frame": cmd_frame, "sample": cmd_sample, "measure": cmd_measure}[args.cmd](args, http)
    finally:
        http.close()


if __name__ == "__main__":
    main()
