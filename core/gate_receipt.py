"""Gate receipts: what `openpulse gate` checked, so an install can prove it
installs the same bytes (track T, T-E2; v0.17.0 item G1).

The gate judges files as they are when it runs. A receipt records that
judgement in a fixed shape: the SHA-256 of every input file, the policy and
the private-name list, the base it compared with, the OpenPulse version, the
decision with its exit code, and every violation and unchecked check. A
verification step before `pip install` or `npm ci` (item G2) re-hashes the
files and refuses any that differ.

A receipt is an integrity record within one pipeline run, not a signature:
anyone who can write the files can write a receipt. It names no upstream
text (T-F3): violations carry the condition, the check, the status and the
dependency label from your own file, never a statement.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RECEIPT_VERSION = "1.0"
DECISIONS = ("passed", "failed", "error")
_EXIT = {"passed": 0, "failed": 1, "error": 2}
_LABEL = re.compile(r"[A-Za-z0-9@/._:=+~!<>-]{1,300}")
_CONDITION = re.compile(r"(unchecked )?[a-z_]{1,64}")
_STATUS = re.compile(r"[A-Z_]{1,32}")


def sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def receipt_path(path: str | os.PathLike[str]) -> str:
    """The form a path is recorded and matched in: normalised, forward slashes."""
    return os.path.normpath(os.fspath(path)).replace("\\", "/")


def _file(path: str | os.PathLike[str] | None) -> dict[str, str] | None:
    if path is None:
        return None
    return {"path": receipt_path(path), "sha256": sha256_file(path)}


def _violation(v: dict[str, Any]) -> dict[str, Any]:
    """The fixed fields of one violation; anything unexpected is dropped."""

    def valid(pattern: re.Pattern[str], value: Any) -> str | None:
        text = str(value or "")
        return text if pattern.fullmatch(text) else None

    return {
        "condition": valid(_CONDITION, v.get("condition")),
        "check": valid(_CONDITION, v.get("check")),
        "status": valid(_STATUS, v.get("status")),
        "dependency": valid(_LABEL, v.get("dependency")),
    }


def build(
    *,
    files: list[dict[str, Any]],
    decision: str,
    version: str,
    policy: str | os.PathLike[str] | None,
    private_names: str | os.PathLike[str] | None,
    base_ref: str | None,
    base_files: list[str | os.PathLike[str] | None] | None,
    dependencies: int,
    added: int | None,
    violations: list[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, Any]:
    """A receipt document. ``files`` are ``{path, sha256, status}`` entries,
    status ``gated``, ``unreadable`` or ``missing`` (sha256 None)."""
    if decision not in DECISIONS:
        raise ValueError(f"unknown decision {decision!r}")
    if base_ref is not None:
        base: dict[str, Any] | None = {"ref": base_ref if _LABEL.fullmatch(base_ref) else None}
    elif base_files:
        base = {"files": [_file(p) for p in base_files]}
    else:
        base = None
    recorded = [_violation(v) for v in violations]
    unchecked = sum(1 for v in recorded if (v["condition"] or "").startswith("unchecked "))
    when = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return {
        "receipt_version": RECEIPT_VERSION,
        "tool": {"name": "openpulse", "version": version},
        "created_at": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": decision,
        "exit_code": _EXIT[decision],
        "files": files,
        "policy": _file(policy),
        "private_names": _file(private_names),
        "base": base,
        "counts": {
            "dependencies": dependencies,
            "added_or_changed": added,
            "violations": len(recorded) - unchecked,
            "unchecked": unchecked,
        },
        "violations": recorded,
    }


def write(receipt: dict[str, Any], path: str | os.PathLike[str]) -> None:
    """Write atomically, so a reader never sees half a receipt."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".receipt-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(receipt, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Verification before install (v0.17.0 item G2)
# ---------------------------------------------------------------------------

MAX_RECEIPT_BYTES = 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _key(path: str | os.PathLike[str]) -> str:
    """How a recorded path and a named file are matched: the same file from
    the same working directory, whatever the spelling."""
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def receipt_files(path: str | os.PathLike[str]) -> list[Path]:
    """The receipt itself, or every ``*.json`` in a directory of receipts (the
    GitHub Action writes one per gated file). ValueError when there is none."""
    target = Path(path)
    if target.is_dir():
        found = sorted(p for p in target.glob("*.json") if p.is_file())
        if not found:
            raise ValueError(f"{receipt_path(path)}: no receipt (*.json) in this directory")
        return found
    return [target]


def load(path: str | os.PathLike[str]) -> dict[str, Any]:
    """A receipt, validated enough to verify against; ValueError with the reason."""
    from core.bounded_io import read_text

    name = receipt_path(path)
    try:
        doc = json.loads(read_text(str(path), MAX_RECEIPT_BYTES, "receipt"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name}: not a readable receipt ({exc.__class__.__name__})") from None
    if not isinstance(doc, dict) or str(doc.get("receipt_version", "")).split(".")[0] != "1":
        raise ValueError(f"{name}: not an OpenPulse gate receipt (receipt_version 1.x)")
    files = doc.get("files")
    if not isinstance(files, list) or not all(
        isinstance(f, dict)
        and isinstance(f.get("path"), str)
        and (f.get("sha256") is None or _SHA256.fullmatch(str(f.get("sha256"))))
        for f in files
    ):
        raise ValueError(f"{name}: its file list is malformed")
    return doc


def verify(
    receipts: list[tuple[str, dict[str, Any]]], paths: list[str | os.PathLike[str]]
) -> list[str]:
    """Why ``paths`` may not be installed on the strength of ``receipts``
    (empty when they may). Every receipt must record a passing gate; every
    path must be a file every receipt naming it recorded as gated, with the
    same SHA-256 now."""
    problems = [
        f"{name}: the gate did not pass (decision {str(doc.get('decision'))[:16]!r}); "
        "nothing it names may be installed"
        for name, doc in receipts
        if doc.get("decision") != "passed" or doc.get("exit_code") != 0
    ]
    recorded: dict[str, list[dict[str, Any]]] = {}
    for _name, doc in receipts:
        for entry in doc["files"]:
            recorded.setdefault(_key(entry["path"]), []).append(entry)
    for path in paths:
        shown = receipt_path(path)
        entries = recorded.get(_key(path))
        if not entries:
            problems.append(f"{shown}: not in the receipt; gate it before installing it")
            continue
        if not os.path.isfile(path):
            problems.append(f"{shown}: missing now")
            continue
        if any(e.get("status") != "gated" for e in entries):
            problems.append(f"{shown}: the gate did not judge it (recorded as not gated)")
            continue
        now = sha256_file(path)
        if any(e.get("sha256") != now for e in entries):
            problems.append(f"{shown}: changed since the gate; run the gate again")
    return problems


__all__ = [
    "DECISIONS",
    "MAX_RECEIPT_BYTES",
    "RECEIPT_VERSION",
    "build",
    "load",
    "receipt_files",
    "receipt_path",
    "sha256_file",
    "verify",
    "write",
]
