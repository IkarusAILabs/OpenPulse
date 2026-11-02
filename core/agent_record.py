"""Opt-in, local recording of MCP questions and answers (M8, v0.13.0 X6).

How do coding agents actually use dependency evidence: what they ask, what
they are told, and what they say about why they ask (track T research
questions RQ1 and RQ4)? ``openpulse mcp --record DIR`` appends one JSON line
per tool call to a file in DIR. Nothing is recorded unless the user passes
``--record``; nothing is ever sent anywhere. The user owns the files and
deletes them when done.

Each line (schema ``openpulse-mcp-record/1``):

- ``session``, ``seq``, ``at``, ``openpulse_version``: which call, when;
- ``tool`` and ``arguments``: what the agent asked, as given (strings capped
  at ``MAX_ARGUMENT_CHARS``);
- ``outcome``: ``answer`` or ``error``, with ``error`` holding the message;
- ``summary``: the fields research reads (verdict, trust statuses, the
  agent's selection context), always present for an answer;
- ``answer``: the full answer, unless its JSON is over
  ``MAX_ANSWER_BYTES`` (then ``answer_omitted`` is true).

Recording never changes an answer and never fails a tool call: a write
error is reported once on stderr and recording stops.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "openpulse-mcp-record/1"
MAX_ANSWER_BYTES = 256 * 1024
MAX_ARGUMENT_CHARS = 1000


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def summarize(tool: str, answer: dict[str, Any]) -> dict[str, Any]:
    """The research-relevant part of one answer, small and stable."""
    if tool == "dependency_status":
        verdict = answer.get("verdict") or {}
        trust = answer.get("trust") or {}
        return {
            "dependency": answer.get("dependency"),
            "identity_status": (answer.get("identity") or {}).get("identity_status"),
            "affected": verdict.get("affected"),
            "relationship": verdict.get("relationship"),
            "not_established": answer.get("not_established"),
            "trust_summary": trust.get("summary"),
            "trust_attention": [
                {"check": a.get("check"), "status": a.get("status")}
                for a in trust.get("attention") or []
            ],
            "selection_context": trust.get("selection_context"),
        }
    if tool == "check_dependency_file":
        trust = answer.get("trust") or {}
        return {
            "format": answer.get("format"),
            "dependencies_checked": answer.get("dependencies_checked"),
            "affected": answer.get("affected"),
            "skipped": len(answer.get("skipped") or []),
            "trust_scope": trust.get("scope"),
            "trust_counts": trust.get("counts"),
            "trust_attention": [
                {
                    "check": a.get("check"),
                    "status": a.get("status"),
                    "package": (a.get("dependency") or {}).get("package"),
                }
                for a in trust.get("attention") or []
            ],
        }
    if tool == "project_lifecycle":
        return {
            "project": answer.get("project"),
            "cycles": len(answer.get("cycles") or []),
            "supported_cycles": answer.get("supported_cycles"),
        }
    return {}


class Recorder:
    """Appends one JSON line per tool call to ``DIR/mcp-<session>.jsonl``."""

    def __init__(self, directory: str | Path, *, version: str = "") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        _restrict(self.directory, 0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.session = f"{stamp}-{secrets.token_hex(4)}"
        self.path = self.directory / f"mcp-{self.session}.jsonl"
        self.version = version
        self.seq = 0
        self.stopped = False
        self._lock = threading.Lock()

    def record(
        self,
        tool: str,
        arguments: dict[str, Any],
        answer: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Append one line; never raises."""
        if self.stopped:
            return
        with self._lock:
            self.seq += 1
            entry: dict[str, Any] = {
                "schema": SCHEMA,
                "session": self.session,
                "seq": self.seq,
                "at": _now(),
                "openpulse_version": self.version,
                "tool": tool,
                "arguments": {k: _capped(v) for k, v in arguments.items()},
                "outcome": "error" if error is not None else "answer",
            }
            if error is not None:
                entry["error"] = error[:MAX_ARGUMENT_CHARS]
            else:
                entry["summary"] = summarize(tool, answer or {})
                full = json.dumps(answer, sort_keys=True, default=str)
                if len(full.encode("utf-8")) <= MAX_ANSWER_BYTES:
                    entry["answer"] = json.loads(full)
                else:
                    entry["answer_omitted"] = True
            try:
                new = not self.path.exists()
                with open(self.path, "a", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
                if new:
                    _restrict(self.path, 0o600)
            except OSError as exc:
                self.stopped = True
                print(
                    f"openpulse mcp: recording stopped, cannot write {self.path}: "
                    f"{exc.strerror or exc}",
                    file=sys.stderr,
                )


def _capped(value: Any) -> Any:
    if isinstance(value, str):
        return value[:MAX_ARGUMENT_CHARS]
    return value


def _restrict(path: Path, mode: int) -> None:
    """Owner-only permissions where the platform has them (POSIX)."""
    if os.name == "posix":
        try:
            path.chmod(mode)
        except OSError:
            pass


__all__ = ["MAX_ANSWER_BYTES", "Recorder", "SCHEMA", "summarize"]
