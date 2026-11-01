"""Error text carries no control, bidi or zero-width characters (track T, T-F3 fix C).

Collector, reader and webhook error text reaches terminals, webhooks and
MCP agents. `collectors.errors.redact` (and so `safe_message`) turns
control characters into spaces and removes characters that reorder or
hide text, before redaction runs.
"""

from __future__ import annotations

import pytest

from collectors.errors import as_error, redact, safe_message, strip_unsafe

INVISIBLE = [
    "‮",  # right-to-left override
    "‪",  # left-to-right embedding
    "⁦",  # left-to-right isolate
    "⁩",  # pop directional isolate
    "‎",  # left-to-right mark
    "‏",  # right-to-left mark
    "​",  # zero-width space
    "‍",  # zero-width joiner
    "⁠",  # word joiner
    "﻿",  # byte-order mark / zero-width no-break space
]
CONTROLS = ["\n", "\r", "\t", "\x00", "\x07", "\x1b", "\x7f", "\x85", "\x9b"]


@pytest.mark.parametrize("char", INVISIBLE)
def test_reordering_and_hiding_characters_are_removed(char):
    assert strip_unsafe(f"evil{char}.exe") == "evil.exe"


@pytest.mark.parametrize("char", CONTROLS)
def test_control_characters_become_a_space(char):
    assert strip_unsafe(f"a{char}b") == "a b"


def test_a_run_of_controls_is_one_space():
    assert strip_unsafe("a\r\n\x1b\x07b") == "a b"


def test_ordinary_text_is_untouched():
    text = "HTTP 503 from pypi.org — Ünïcode, 日本語, emoji 🙂"
    assert strip_unsafe(text) == text


def test_a_hidden_character_cannot_split_a_secret_past_redaction():
    """Stripping runs first, so `tok<ZWSP>en=...` is still redacted."""
    assert "s3cr3t-value" not in redact("tok​en=s3cr3t-value")


def test_safe_message_and_error_records_are_clean():
    exc = ValueError("bad ‮txt.exe\r\n\x1b[2J at /home/u/secret.txt")
    message = safe_message(exc)
    assert not any(c in message for c in INVISIBLE + CONTROLS)
    assert "<path>" in message
    assert as_error("osv", exc)["safe_message"] == message
