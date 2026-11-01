"""History key: keyed integrity for local history (v0.9.0 item B3, finding H2).

The observation chain and the detection ledger use unkeyed SHA-256, so
anyone who can write ``.openpulse/`` can edit a record and recompute
every hash. With a history key, each record also carries an HMAC that
cannot be recomputed without the key. Design: ``docs/KEYED_INTEGRITY.md``.

Where the key comes from, in order:

1. ``--history-key-file PATH``: first non-empty line, at most 4 KiB.
2. ``OPENPULSE_HISTORY_KEY``.

Retired keys (rotation, B3b) are verify-only: they come from
``--history-previous-keys-file PATH`` (one key per line, ``#`` comments)
or ``OPENPULSE_HISTORY_KEYS_PREVIOUS`` (separated by commas or
whitespace). New records are always MACed with the current key.

A key is at least 32 random bytes, written as base64 (``openpulse
history-key generate`` makes one). A key file inside a history store or
any ``.openpulse`` directory is refused: a key stored next to the data
it protects protects nothing. Without a key, history is written and
verified exactly as before, as VALID_UNKEYED at best.

Stdlib only (``hmac``, ``hashlib``, ``secrets``).
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os
import secrets
import stat
from dataclasses import dataclass, field
from pathlib import Path

ENV_VAR = "OPENPULSE_HISTORY_KEY"
PREVIOUS_ENV_VAR = "OPENPULSE_HISTORY_KEYS_PREVIOUS"
MAX_PREVIOUS_KEYS = 16
MIN_KEY_BYTES = 32
MAX_KEY_FILE_BYTES = 4096
MAC_PREFIX = "hmac-sha256:"

#: Domain separators: a MAC for one record kind never verifies as another.
OBSERVATION_DOMAIN = "openpulse-history-v1"
LEDGER_DOMAIN = "openpulse-ledger-v1"
#: A retired key's MAC over the record that hands its chain to a new key.
HANDOVER_DOMAIN = "openpulse-handover-v1"
#: Both keys' MACs over a ledger rotation entry.
ROTATION_DOMAIN = "openpulse-rotation-v1"
#: The current key's MAC over a re-baseline log entry (B4).
REBASELINE_DOMAIN = "openpulse-rebaseline-v1"


class HistoryKeyError(ValueError):
    """A history key is malformed, too short, or stored in a refused place."""


@dataclass(frozen=True)
class HistoryKey:
    secret: bytes = field(repr=False)
    key_id: str

    def mac(self, domain: str, *parts: str) -> str:
        message = "\0".join((domain, *parts)).encode("utf-8")
        return MAC_PREFIX + hmac.new(self.secret, message, hashlib.sha256).hexdigest()

    def verify(self, value: object, domain: str, *parts: str) -> bool:
        return isinstance(value, str) and hmac.compare_digest(value, self.mac(domain, *parts))


def key_id_for(secret: bytes) -> str:
    """Public identifier of a key. Reveals nothing usable about a 256-bit key."""
    return "hk1:" + hashlib.sha256(b"openpulse-key-id\0" + secret).hexdigest()[:16]


def parse_key(text: str) -> HistoryKey:
    """base64 (standard or URL-safe) -> HistoryKey, at least 32 bytes."""
    cleaned = "".join(str(text).split())
    if not cleaned:
        raise HistoryKeyError("history key is empty")
    padded = cleaned + "=" * (-len(cleaned) % 4)
    try:
        secret = base64.b64decode(padded.replace("-", "+").replace("_", "/"), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HistoryKeyError("history key is not base64") from exc
    if len(secret) < MIN_KEY_BYTES:
        raise HistoryKeyError(
            f"history key is {len(secret)} bytes; at least {MIN_KEY_BYTES} are required"
        )
    return HistoryKey(secret=secret, key_id=key_id_for(secret))


def generate_key() -> tuple[str, str]:
    """(base64 key text, key_id) for a fresh 32-byte key. Writes nothing."""
    secret = secrets.token_bytes(MIN_KEY_BYTES)
    return base64.b64encode(secret).decode("ascii"), key_id_for(secret)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def check_key_location(path: str | os.PathLike[str], store_roots: tuple[str, ...] = ()) -> None:
    """Refuse a key file inside a history store or any ``.openpulse`` directory."""
    resolved = Path(path).resolve()
    if ".openpulse" in resolved.parts:
        raise HistoryKeyError(f"history key file {path} is inside a .openpulse directory")
    for root in store_roots:
        if root and _inside(resolved, Path(root).resolve()):
            raise HistoryKeyError(f"history key file {path} is inside history store {root}")


def key_file_warning(path: str | os.PathLike[str]) -> str | None:
    """A warning when other users can read the key file (POSIX only)."""
    if os.name != "posix":
        return None
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return None
    if mode & (stat.S_IRGRP | stat.S_IROTH):
        return f"warning: history key file {path} is readable by other users (chmod 600 it)"
    return None


def load_history_key(
    key_file: str | None = None, store_roots: tuple[str, ...] = ()
) -> HistoryKey | None:
    """The configured key, or None when none is configured."""
    if key_file:
        lines = _read_key_file(key_file, store_roots)
        if not lines:
            raise HistoryKeyError("history key file does not contain a key")
        return parse_key(lines[0])
    value = os.environ.get(ENV_VAR, "").strip()
    return parse_key(value) if value else None


def _read_key_file(path: str, store_roots: tuple[str, ...]) -> list[str]:
    """Non-empty, non-comment lines of a bounded UTF-8 key file."""
    check_key_location(path, store_roots)
    with open(path, "rb") as handle:
        raw = handle.read(MAX_KEY_FILE_BYTES + 1)
    if len(raw) > MAX_KEY_FILE_BYTES:
        raise HistoryKeyError(f"history key file exceeds {MAX_KEY_FILE_BYTES} bytes")
    try:
        lines = [line.strip() for line in raw.decode("utf-8-sig").splitlines()]
    except UnicodeDecodeError as exc:
        raise HistoryKeyError("history key file is not UTF-8 text") from exc
    return [line for line in lines if line and not line.startswith("#")]


def load_previous_keys(
    keys_file: str | None = None,
    store_roots: tuple[str, ...] = (),
    current: HistoryKey | None = None,
) -> tuple[HistoryKey, ...]:
    """Retired, verify-only keys (rotation). The current key is never among them."""
    if keys_file:
        texts = _read_key_file(keys_file, store_roots)
    else:
        texts = os.environ.get(PREVIOUS_ENV_VAR, "").replace(",", " ").split()
    if len(texts) > MAX_PREVIOUS_KEYS:
        raise HistoryKeyError(f"at most {MAX_PREVIOUS_KEYS} previous history keys are accepted")
    keys: dict[str, HistoryKey] = {}
    for text in texts:
        key = parse_key(text)
        if current is None or key.key_id != current.key_id:
            keys.setdefault(key.key_id, key)
    return tuple(keys.values())


def keyring(current: HistoryKey | None, previous: tuple[HistoryKey, ...] = ()) -> dict:
    """key_id -> HistoryKey for verification: the current key and retired ones."""
    ring = {key.key_id: key for key in previous}
    if current is not None:
        ring[current.key_id] = current
    return ring
