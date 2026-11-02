"""Build the pinned reference data for lookalike-name indicators (track T, T-A2).

Maintainer tool; network required; stdlib only. It writes, into
``data/reference/``, one separately licensed data file per source, each
recording where it came from, its version and the hash it was checked
against (``docs/research/TRACK_T_PHASE0.md``, section 3, owner-approved):

    python scripts/refresh_reference_names.py npm
        npm-high-impact (MIT) at NPM_VERSION, checked against npm's sha512
        integrity, read from lib/top.js as text (never executed).

    python scripts/refresh_reference_names.py confusables
        UTS #39 confusables.txt (Unicode License v3), refused unless its
        header says CONFUSABLES_VERSION and its sha256 is CONFUSABLES_SHA256;
        only the ASCII-to-ASCII mappings are kept (package names are ASCII).

    python scripts/refresh_reference_names.py pypi-query
        prints the dated BigQuery query over the PyPI download dataset
        (CC BY 4.0) for a maintainer with a Google Cloud account to run.

    python scripts/refresh_reference_names.py pypi RESULT.csv SNAPSHOT_DATE
        writes the PyPI reference from that query's CSV result.

Bump a pin here, rerun, review the diff, and update NOTICE.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference"
USER_AGENT = "OpenPulse-maintainer (+https://github.com/IkarusAILabs/OpenPulse)"

NPM_PACKAGE = "npm-high-impact"
NPM_VERSION = "1.13.0"
CONFUSABLES_URL = "https://www.unicode.org/Public/security/latest/confusables.txt"
CONFUSABLES_VERSION = "18.0.0"
CONFUSABLES_SHA256 = "6ed3ee967c9dfdf6677d563c9985182fbc50a2efb7d6059cd57b2e2ce18f5b92"
PYPI_TOP_N = 15000

_NPM_NAME = re.compile(r"(?:@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*")
_PYPI_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,198}[A-Za-z0-9])?")

PYPI_QUERY = """\
-- OpenPulse PyPI reference names: the {top_n} most-downloaded projects over
-- the 30 days before {snapshot}. Dataset: bigquery-public-data.pypi.file_downloads
-- (CC BY 4.0, https://docs.pypi.org/api/bigquery/). Save the result as CSV.
SELECT file.project AS project, COUNT(*) AS downloads
FROM `bigquery-public-data.pypi.file_downloads`
WHERE DATE(timestamp) BETWEEN DATE_SUB(DATE '{snapshot}', INTERVAL 30 DAY)
  AND DATE_SUB(DATE '{snapshot}', INTERVAL 1 DAY)
GROUP BY project
ORDER BY downloads DESC
LIMIT {top_n}
"""


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _write(name: str, payload: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def npm() -> Path:
    meta = json.loads(_get(f"https://registry.npmjs.org/{NPM_PACKAGE}/{NPM_VERSION}"))
    tarball = _get(meta["dist"]["tarball"])
    algorithm, _, expected = meta["dist"]["integrity"].partition("-")
    actual = base64.b64encode(hashlib.new(algorithm, tarball).digest()).decode()
    if algorithm != "sha512" or actual != expected:
        raise SystemExit(f"{NPM_PACKAGE} {NPM_VERSION}: integrity mismatch, refusing")
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
        member = archive.extractfile("package/lib/top.js")
        text = member.read().decode("utf-8") if member else ""
    names = re.findall(r"'([^'\\]+)'", text)
    valid = sorted({n for n in names if _NPM_NAME.fullmatch(n) and len(n) <= 214})
    if len(valid) < 1000:
        raise SystemExit(f"only {len(valid)} names parsed from lib/top.js: format changed?")
    return _write(
        f"npm-high-impact-{NPM_VERSION}.json",
        {
            "source": f"https://www.npmjs.com/package/{NPM_PACKAGE}/v/{NPM_VERSION}",
            "version": NPM_VERSION,
            "license": "MIT",
            "integrity": meta["dist"]["integrity"],
            "selection": "npm packages with >= 1M weekly downloads or >= 500 dependents",
            "ecosystem": "npm",
            "names": valid,
        },
    )


def confusables() -> Path:
    raw = _get(CONFUSABLES_URL)
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    if f"# Version: {CONFUSABLES_VERSION}" not in text or digest != CONFUSABLES_SHA256:
        raise SystemExit(
            f"confusables.txt is not the pinned {CONFUSABLES_VERSION} ({digest}); "
            "review the new release and bump the pins"
        )
    mappings: dict[str, str] = {}
    for line in text.splitlines():
        fields = [f.strip() for f in line.split("#", 1)[0].split(";")]
        if len(fields) < 2 or not fields[0]:
            continue
        source = [int(cp, 16) for cp in fields[0].split()]
        target = [int(cp, 16) for cp in fields[1].split()]
        if len(source) == 1 and all(cp < 0x80 for cp in source + target):
            char = chr(source[0])
            if char.isprintable() and not char.isspace():
                mappings[char] = "".join(chr(cp) for cp in target)
    date = re.search(r"# Date: (\S+)", text)
    return _write(
        f"uts39-confusables-ascii-{CONFUSABLES_VERSION}.json",
        {
            "source": CONFUSABLES_URL,
            "version": CONFUSABLES_VERSION,
            "date": date.group(1).rstrip(",") if date else None,
            "sha256_of_source": digest,
            "license": "Unicode License v3 (https://www.unicode.org/license.txt)",
            "scope": "ASCII-to-ASCII prototype mappings only",
            "mappings": dict(sorted(mappings.items())),
        },
    )


def pypi(csv_path: str, snapshot: str) -> Path:
    with open(csv_path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    names = sorted({r["project"] for r in rows if _PYPI_NAME.fullmatch(r.get("project", ""))})
    return _write(
        f"pypi-top-{snapshot}.json",
        {
            "source": "bigquery-public-data.pypi.file_downloads",
            "version": snapshot,
            "license": "CC BY 4.0 (https://docs.pypi.org/api/bigquery/)",
            "query": PYPI_QUERY.format(top_n=PYPI_TOP_N, snapshot=snapshot),
            "sha256_of_result": hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
            "ecosystem": "PyPI",
            "names": names,
        },
    )


def main(argv: list[str]) -> int:
    if argv[:1] == ["npm"]:
        print(f"wrote {npm()}")
    elif argv[:1] == ["confusables"]:
        print(f"wrote {confusables()}")
    elif argv[:1] == ["pypi-query"] and len(argv) == 2:
        print(PYPI_QUERY.format(top_n=PYPI_TOP_N, snapshot=argv[1]))
    elif argv[:1] == ["pypi"] and len(argv) == 3:
        print(f"wrote {pypi(argv[1], argv[2])}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
