"""Shared fixtures."""

import pytest


@pytest.fixture
def ledger_clock_at_stamp(monkeypatch):
    """Seed ledger history at past dates, under the test history key.

    A ledger stamp must lie near wall-clock time (clock trust, L7), so a
    write with ``detected_at`` runs as if the clock read that stamp: the
    same as running OpenPulse on that date. Clock trust itself is tested
    in ``tests/test_clock_trust.py``, without this fixture.

    Lead times come only from keyed history (B3c), so seeded writes and
    CLI runs use ``tests.history_keys.TEST_KEY``, as a keyed deployment
    would. Unkeyed behaviour is tested in ``tests/test_keyed_adoption.py``.
    """
    from core.detections import ledger
    from core.history_key import ENV_VAR
    from tests.history_keys import TEST_KEY, TEST_KEY_TEXT

    monkeypatch.setenv(ENV_VAR, TEST_KEY_TEXT)
    real = ledger.record_detection

    def record(*args, detected_at=None, **kwargs):
        kwargs.setdefault("history_key", TEST_KEY)
        if detected_at is None:
            return real(*args, **kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(ledger, "now_iso", lambda: detected_at)
            return real(*args, detected_at=detected_at, **kwargs)

    monkeypatch.setattr(ledger, "record_detection", record)


@pytest.fixture(autouse=True)
def _isolated_delivery_state(monkeypatch, tmp_path):
    """`check --webhook` records delivery state (W1); never in the checkout."""
    monkeypatch.setenv("OPENPULSE_DELIVERY_STATE", str(tmp_path / "deliveries"))
    # project_lifecycle caches across sessions (W4); never in the real user cache.
    monkeypatch.setenv("OPENPULSE_CACHE_DIR", str(tmp_path / "lookup-cache"))
    # A developer's own signing secret must not sign the suite's webhooks (W3).
    monkeypatch.delenv("OPENPULSE_WEBHOOK_SECRET", raising=False)
    # Tests stay offline: the registry existence check (T-M1) gets no
    # response unless a test injects a stub registry.
    monkeypatch.setattr("core.registry_existence.default_head", lambda _url: 0)
