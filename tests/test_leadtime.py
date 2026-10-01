"""Lead-time unit tests: recorded per finding, never averaged."""

from core.leadtime import finding_lead_time, lead_time_days


def test_positive_lead_time():
    assert lead_time_days("2026-07-16", "2026-09-29") == 75


def test_past_effective_is_none_not_zero():
    assert lead_time_days("2026-09-26", "2026-04-30") is None


def test_unknown_dates_are_none():
    assert lead_time_days(None, "2026-09-29") is None
    assert lead_time_days("2026-09-26", None) is None
    assert lead_time_days("latest", "2026-09-29") is None
    assert lead_time_days("2026-09-26", True) is None


def test_same_day_is_zero_not_none():
    assert lead_time_days("2026-09-29", "2026-09-29") == 0


def test_finding_lead_time_uses_own_dates():
    days, detected, effective = finding_lead_time(
        {"observed_at": "2026-09-01", "effective_at": "2026-09-29"}
    )
    assert (days, detected, effective) == (28, "2026-09-01", "2026-09-29")


def test_finding_lead_time_prefers_published_and_event_date():
    days, _, _ = finding_lead_time({"published": "2026-08-01T00:00:00", "event_date": "2026-08-11"})
    assert days == 10


def test_finding_without_dates_has_no_lead_time():
    assert finding_lead_time({"analyst": "change"}) == (None, None, None)
