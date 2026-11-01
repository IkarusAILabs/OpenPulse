"""Shared fixtures."""

import pytest


@pytest.fixture
def ledger_clock_at_stamp(monkeypatch):
    """Seed ledger history at past dates.

    A ledger stamp must lie near wall-clock time (clock trust, L7), so a
    write with ``detected_at`` runs as if the clock read that stamp: the
    same as running OpenPulse on that date. Clock trust itself is tested
    in ``tests/test_clock_trust.py``, without this fixture.
    """
    from core.detections import ledger

    real = ledger.record_detection

    def record(*args, detected_at=None, **kwargs):
        if detected_at is None:
            return real(*args, **kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(ledger, "now_iso", lambda: detected_at)
            return real(*args, detected_at=detected_at, **kwargs)

    monkeypatch.setattr(ledger, "record_detection", record)
