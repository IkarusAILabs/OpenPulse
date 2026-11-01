"""A fixed history key for tests (never a real key)."""

import base64

from core.history_key import keyring, parse_key

TEST_KEY_TEXT = base64.b64encode(b"openpulse-test-history-key-0001!").decode()
TEST_KEY = parse_key(TEST_KEY_TEXT)
TEST_KEYS = keyring(TEST_KEY)
