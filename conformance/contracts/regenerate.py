"""Regenerate the released-contract corpus from the commits that produced it (v0.19.0 P5).

For every published evidence-contract version, the release that first emitted
it is checked out from git (by a pinned commit, so a moved tag is refused),
and its own ``openpulse attest`` writes ``<version>/documents.jsonl`` from the
fixtures shipped in that same tree. Nothing of today's code touches those
documents. ``<version>/negatives.jsonl`` holds one copy of the first document
per mutation, each breaking exactly one rule; the mutations that should be
caught by the schema alone are re-hashed, so the hash cannot catch them first.
``MANIFEST.json`` records the producer, its command, each document's content
hash, and each negative's mutation and the JSON path it must be rejected at.

Usage, from the repository root (needs the full git history and tags):

    python conformance/contracts/regenerate.py           # rewrite the corpus
    python conformance/contracts/regenerate.py --check   # exit 1 on drift

``--check`` regenerates into a temporary directory and compares content
hashes, which leave out ``provenance.generation_timestamp``: the one value
that differs between two runs of the same producer.

The producers run in a stripped environment (no variable whose name holds
TOKEN, KEY, SECRET, PASSWORD or starts with OPENPULSE/GITHUB/PYTHON), from
the extracted tree, with ``--replay`` where the release has it.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "conformance" / "consumer"))

from openpulse_consumer.hashes import v1_content_hash, v2_content_hash  # noqa: E402

#: (contract version, git ref, the commit it must resolve to, a note, uses --replay)
PRODUCERS: tuple[tuple[str, str, str, str, bool], ...] = (
    (
        "1.0.0",
        "d68f5338c80b25edfcb70e00c331192884c429d9",
        "d68f5338c80b25edfcb70e00c331192884c429d9",
        "untagged: the parent of f772695, which replaced 1.0 with 1.1 (v0.6.0 was never tagged)",
        False,
    ),
    (
        "1.1.0",
        "v0.6.1",
        "ab8089d7cce09104aa7a02b69f84a08065582903",
        "first tag emitting 1.1",
        False,
    ),
    ("1.2.0", "v0.8.0", "f4b1c10b08b0009805f2ddbe251498afc6a376fa", "first tag emitting 1.2", True),
    ("2.0.0", "v0.9.0", "aae94e10d49f980b5cd93105ac20aca3c6538abb", "first tag emitting 2.0", True),
    (
        "2.1.0",
        "v0.10.0",
        "134d302bc0b1e522bdad1dd0e812b65b28786581",
        "first tag emitting 2.1",
        True,
    ),
    (
        "2.2.0",
        "v0.13.0",
        "a6419587146e21300c30569be8fa1b8fb2495253",
        "first tag emitting 2.2",
        True,
    ),
    (
        "2.3.0",
        "v0.16.0",
        "9a33183db391f5043331374602cf0f6ce1695e8d",
        "first tag emitting 2.3",
        True,
    ),
    (
        "2.4.0",
        "v0.18.0",
        "fdba61afa255b37acbeb9713eb793d896afc915d",
        "first tag emitting 2.4",
        True,
    ),
)
INPUTS = (
    "--watchlist",
    "data/fixtures/watchlist_sample.yaml",
    "--event",
    "data/fixtures/django-eol/event.json",
)
_SCRUB = re.compile(r"TOKEN|KEY|SECRET|PASSWORD|^OPENPULSE|^GITHUB|^PYTHON", re.IGNORECASE)
_RUN_CLI = "import sys; sys.path.insert(0, '.'); from cli.main import cli; cli()"


def rehash(doc: dict[str, Any]) -> dict[str, Any]:
    rule = v2_content_hash if doc["contract_version"].startswith("2.") else v1_content_hash
    doc["provenance"]["content_hash"] = rule(doc)
    return doc


def _changed(doc: dict[str, Any]) -> None:
    current = doc["assessment"]["relationship"]
    doc["assessment"]["relationship"] = (
        "AFFECTS_PROJECT" if current != "AFFECTS_PROJECT" else "UNKNOWN"
    )


def _provenance_version(doc: dict[str, Any]) -> None:
    other = "1.2.0" if doc["contract_version"] == "2.0.0" else "2.0.0"
    doc["provenance"]["contract_version"] = other


#: name -> (mutation, re-hash after it, the path it is rejected at, 2.x only)
MUTATIONS: dict[str, tuple[Callable[[dict[str, Any]], Any], bool, str, bool]] = {
    "changed after hashing": (_changed, False, "$.provenance.content_hash", False),
    "unknown field": (lambda d: d.update(surprise=True), True, "$", False),
    "missing field": (lambda d: d.pop("unknowns"), False, "$", False),
    "unpublished version": (
        lambda d: d.update(contract_version="9.9.9"),
        False,
        "$.contract_version",
        False,
    ),
    "provenance version differs": (
        _provenance_version,
        True,
        "$.provenance.contract_version",
        False,
    ),
    "relationship outside the vocabulary": (
        lambda d: d["assessment"].update(relationship="SAFE"),
        True,
        "$.assessment.relationship",
        False,
    ),
    "impossible date": (
        lambda d: d["temporal"].update(announcement_date="2026-02-30"),
        True,
        "$.temporal.announcement_date",
        False,
    ),
    "other hash method": (
        lambda d: d["provenance"].update(content_hash_method="sha256"),
        False,
        "$.provenance.content_hash_method",
        True,
    ),
}


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def _commit(ref: str) -> str:
    return _git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()


def _extract(commit: str, into: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(_git("archive", "--format=tar", commit))) as tar:
        tar.extractall(into, filter="data")


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not _SCRUB.search(k)}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def produce(
    version: str, ref: str, pinned: str, replay: bool, work: Path
) -> tuple[str, list[dict]]:
    """Run the producer at ``ref``; returns its commit and the documents it wrote."""
    commit = _commit(ref)
    if pinned and commit != pinned:
        raise SystemExit(f"{ref} resolves to {commit}, not the pinned {pinned}: refusing")
    tree = work / version
    _extract(commit, tree)
    out = work / f"{version}.jsonl"
    command = [sys.executable, "-c", _RUN_CLI, "attest", *INPUTS]
    if replay:
        command.append("--replay")
    command += ["--output", str(out)]
    done = subprocess.run(command, cwd=tree, env=_env(), capture_output=True, text=True)
    if done.returncode:
        raise SystemExit(f"{ref} attest failed ({done.returncode}):\n{done.stderr[-2000:]}")
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    found = {d["contract_version"] for d in docs}
    if not docs or found != {version}:
        raise SystemExit(f"{ref} wrote {sorted(found) or 'nothing'}, expected {version}")
    return commit, docs


def negatives(doc: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    out = []
    for name, (mutate, hashed, path, v2_only) in MUTATIONS.items():
        if v2_only and not doc["contract_version"].startswith("2."):
            continue
        bad = copy.deepcopy(doc)
        mutate(bad)
        if hashed:
            rehash(bad)
        out.append((name, path, bad))
    return out


def _jsonl(docs: list[dict]) -> str:
    return "".join(json.dumps(d, sort_keys=True, ensure_ascii=False) + "\n" for d in docs)


def build(target: Path) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "description": "Documents written by each released contract version's own producer "
        "(conformance/contracts/regenerate.py), and one-rule negatives derived from them.",
        "inputs": list(INPUTS),
        "versions": {},
    }
    with tempfile.TemporaryDirectory() as tmp:
        for version, ref, pinned, note, replay in PRODUCERS:
            commit, docs = produce(version, ref, pinned, replay, Path(tmp))
            bad = negatives(docs[0])
            folder = target / version
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "documents.jsonl").write_text(_jsonl(docs), encoding="utf-8", newline="\n")
            (folder / "negatives.jsonl").write_text(
                _jsonl([d for _n, _p, d in bad]), encoding="utf-8", newline="\n"
            )
            manifest["versions"][version] = {
                "producer": ref,
                "commit": commit,
                "note": note,
                "replay": replay,
                "documents": [d["provenance"]["content_hash"] for d in docs],
                "negatives": [{"mutation": n, "rejected_at": p} for n, p, _d in bad],
            }
    (target / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the corpus has drifted")
    args = parser.parse_args(argv)
    if not args.check:
        build(HERE)
        print(f"wrote {HERE}")
        return 0
    committed = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        fresh = build(Path(tmp))
    if fresh != committed:
        for version in sorted(set(fresh["versions"]) | set(committed["versions"])):
            if fresh["versions"].get(version) != committed["versions"].get(version):
                print(f"{version}: the corpus differs from what its producer writes now")
        return 1
    print(f"corpus matches its producers ({len(fresh['versions'])} versions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
