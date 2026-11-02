"""Fetch the base-branch copies of dependency files for the GitHub Action (v0.14.0 Y3).

On a pull request, the Action checks trust only for dependencies the pull
request adds or changes. That needs each file as it is on the base commit,
which a shallow checkout does not have. This fetches them through the
GitHub contents API with the job's token (passed in the environment as
``GITHUB_TOKEN``, never on the command line):

    python scripts/action_base_files.py OWNER/REPO BASE_SHA OUT_DIR PATH...

For each PATH it prints one line, ``<status>\\t<path>\\t<base file>``:

- ``found``: the base copy was written to ``<base file>``;
- ``new``: the file does not exist on the base commit (the pull request
  adds it), so all its dependencies count as added;
- ``unavailable``: the API gave no usable answer. The Action then checks
  every dependency rather than none: a failure never narrows the checks.

Inputs are validated (repository grammar, a 40-hex commit, repository-
relative paths without ``..``), and each response is size-capped.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MAX_BASE_BYTES = 25 * 1024 * 1024
_SHA = re.compile(r"[0-9a-f]{40}")
_REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,38}/[A-Za-z0-9._-]{1,100}")

#: url, token -> (http status, body bytes or None). 0 means no response.
Get = Callable[[str, str], tuple[int, bytes | None]]


def http_get(url: str, token: str) -> tuple[int, bytes | None]:
    from collectors import http

    headers = {"accept": "application/vnd.github.raw", "x-github-api-version": "2022-11-28"}
    if token:
        headers["authorization"] = f"Bearer {token}"
    try:
        response = http.get(url, max_bytes=MAX_BASE_BYTES, timeout=30, headers=headers)
    except Exception:  # network, DNS, TLS, oversize: unavailable, never a crash
        return 0, None
    return response.status_code, (response.content if response.status_code == 200 else None)


def _clean_path(path: str) -> str | None:
    parts = [p for p in path.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or ".." in parts or path.startswith("/") or ":" in parts[0]:
        return None
    return "/".join(parts)


def fetch(
    repo: str,
    ref: str,
    out_dir: str | Path,
    paths: list[str],
    token: str,
    get: Get | None = None,
) -> list[tuple[str, str, str]]:
    """[(status, path, base file)] for each path; see the module docstring."""
    get = get or http_get  # resolved at call time, so tests can replace it
    if not _REPO.fullmatch(repo) or not _SHA.fullmatch(ref):
        return [("unavailable", p, "") for p in paths]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for index, raw in enumerate(paths):
        path = _clean_path(raw)
        if path is None:
            results.append(("unavailable", raw, ""))
            continue
        url = f"https://api.github.com/repos/{repo}/contents/{quote(path)}?ref={ref}"
        status, body = get(url, token)
        if status == 404:
            results.append(("new", raw, ""))
        elif status == 200 and body is not None:
            # Same file name as the original: readers detect formats by name.
            target = out / str(index) / Path(path).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            results.append(("found", raw, str(target)))
        else:
            results.append(("unavailable", raw, ""))
    return results


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    repo, ref, out_dir, *paths = argv
    for status, path, base in fetch(repo, ref, out_dir, paths, os.environ.get("GITHUB_TOKEN", "")):
        print(f"{status}\t{path}\t{base}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
