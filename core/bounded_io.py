"""Bounded reads for every user-supplied input file.

`os.path.getsize()` before an unbounded `read()` is not a bound: a FIFO,
`/dev/zero`, or a file that grows after the check passes the size test
and is then read without limit. These helpers read at most ``limit + 1``
bytes and refuse anything longer, and turn the RecursionError that
deeply nested JSON raises into the same clean ValueError every reader
already reports. No new dependencies.
"""

from __future__ import annotations

import json
import os
from typing import Any


def read_bytes(path: str, limit: int, label: str) -> bytes:
    """At most ``limit`` bytes of ``path``; ValueError naming ``label`` beyond."""
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0  # not a regular file (FIFO, device): the read below bounds it
    if size > limit:
        raise ValueError(f"{label} is {size} bytes (limit {limit})")
    with open(path, "rb") as f:
        data = f.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"{label} exceeds {limit} bytes (limit {limit})")
    return data


def read_text(path: str, limit: int, label: str) -> str:
    """Bounded UTF-8 text read (UnicodeDecodeError propagates, as before)."""
    return read_bytes(path, limit, label).decode("utf-8")


def loads_json(data: str | bytes, label: str) -> Any:
    """`json.loads` that reports pathological nesting as a ValueError."""
    try:
        return json.loads(data)
    except RecursionError:
        raise ValueError(f"{label} nests too deeply to parse") from None
