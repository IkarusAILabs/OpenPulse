"""Lead-time unit tests: first detection, never estimates."""

from datetime import date, datetime, timezone

from core.leadtime import finding_lead_time, lead_time_days, parse_day, temporal_roles


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


def test_timezone_offsets_parse_to_calendar_day():
    assert parse_day("2026-09-29T23:30:00+02:00") == date(2026, 9, 29)
    assert parse_day("2026-09-29T00:30:00Z") == date(2026, 9, 29)
    assert parse_day(datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)) == date(2026, 9, 29)


def test_manipulated_timestamps_are_none():
    assert parse_day("not-a-date") is None
    assert parse_day("99999-99-99") is None
    assert parse_day({"$ne": None}) is None
    assert parse_day(["2026-09-29"]) is None
    assert lead_time_days("2026-13-45", "2026-09-29") is None


def test_finding_uses_first_detected_only():
    days, detected, effective = finding_lead_time(
        {
            "observed_at": "2026-09-20",  # re-observation: must not stand in
            "first_detected_at": "2026-09-01",
            "effective_at": "2026-09-29",
        }
    )
    assert (days, detected, effective) == (28, "2026-09-01", "2026-09-29")


def test_finding_without_first_detection_makes_no_claim():
    # observed_at alone is NOT first detection — never estimate it.
    assert finding_lead_time(
        {"observed_at": "2026-09-01", "effective_at": "2026-09-29"}
    ) == (None, None, None)
    assert finding_lead_time({"analyst": "change"}) == (None, None, None)
    assert finding_lead_time("garbage") == (None, None, None)


def test_temporal_roles_never_conflate():
    roles = temporal_roles(
        {
            "published": "2026-08-01",
            "first_detected_at": "2026-08-05",
            "observed_at": "2026-09-01",
            "effective_at": "2026-09-29",
        }
    )
    assert roles["published_at"] == date(2026, 8, 1)
    assert roles["first_detected_at"] == date(2026, 8, 5)
    assert roles["last_observed_at"] == date(2026, 9, 1)
    assert roles["effective_at"] == date(2026, 9, 29)
