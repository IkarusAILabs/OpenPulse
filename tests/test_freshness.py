"""Finding freshness: the 12-month research window."""

from datetime import date

from core.freshness import (
    ACTIVE,
    BACKGROUND,
    CURRENT,
    EXPIRED,
    NEW,
    RECENTLY_UPDATED,
    RESEARCH_WINDOW_DAYS,
    UNKNOWN,
    UPCOMING,
    classify,
    finding_age_days,
    freshness,
    is_background,
)

TODAY = date(2026, 10, 2)


def test_window_is_one_year():
    assert RESEARCH_WINDOW_DAYS == 365


def test_current_within_window():
    assert freshness({"effective_at": "2026-09-01"}, today=TODAY)[0] == CURRENT
    assert freshness({"event_date": "2025-10-03"}, today=TODAY)[0] == CURRENT


def test_background_beyond_window():
    state, reason = freshness({"effective_at": "2024-01-01"}, today=TODAY)
    assert state == BACKGROUND
    assert "12 months" in reason
    assert is_background({"effective_at": "2024-01-01"}, today=TODAY) is True


def test_upcoming_is_current_not_background():
    assert freshness({"effective_at": "2026-12-01"}, today=TODAY)[0] == CURRENT
    assert finding_age_days({"effective_at": "2026-12-01"}, today=TODAY) is None


def test_unknown_effective_is_never_background():
    assert freshness({"effective_at": None}, today=TODAY)[0] == UNKNOWN
    assert freshness({"effective_at": "not-a-date"}, today=TODAY)[0] == UNKNOWN
    assert freshness({"analyst": "change"}, today=TODAY)[0] == UNKNOWN
    assert freshness("garbage", today=TODAY)[0] == UNKNOWN
    assert is_background({"analyst": "change"}, today=TODAY) is False


def test_age_days():
    assert finding_age_days({"effective_at": "2026-09-01"}, today=TODAY) == 31
    assert finding_age_days({"effective_at": None}, today=TODAY) is None


def _eol_finding(title, effective):
    return {
        "analyst": "change",
        "event_type": "EOL",
        "signal": "lifecycle",
        "impact": "ACTION",
        "title": title,
        "lifecycle_state": "EFFECTIVE",
        "effective_at": effective,
        "scope": {"kind": "version", "versions": ["5.0"]},
        "sources": ["endoflife"],
    }


def test_rank_key_demotes_background_within_bucket():
    from reports.generate import rank_key

    current = {"event_type": "EOL", "impact": "ACTION", "title": "t",
               "scope": {"kind": "version", "versions": ["6.0"]},
               "effective_at": "2026-09-01"}
    background = dict(current, effective_at="2024-01-01")
    assert rank_key("p", current) < rank_key("p", background)


def test_monthly_report_moves_expired_to_historical():
    from reports.generate import build_report

    items = [
        {
            "project": "db-old",
            "pulse": {"facets": {}},
            "findings": [_eol_finding("db 5.0 is end-of-life", "2024-01-01")],
        },
        {
            "project": "db-new",
            "pulse": {"facets": {}},
            "findings": [_eol_finding("db 6.0 is end-of-life", "2026-09-01")],
        },
    ]
    md = build_report("2026-10", items)
    top = md.split("## Top Changes")[1].split("## Changes Requiring Attention")[0]
    assert "db 6.0 is end-of-life" in top
    assert "db 5.0 is end-of-life" not in top
    historical = md.split("### A. Historical findings")[1].split("### B.")[0]
    assert "db 5.0 is end-of-life" in historical
    assert "Status: EXPIRED" in historical
    assert "- Background findings (effective over 12 months ago): 1" in md


def test_lifecycle_planning_background_last_and_labeled():
    from reports.lifecycle import build_lifecycle_report, collect_lifecycle_status

    statuses = [
        collect_lifecycle_status(
            "old",
            {"endoflife": [{"product": "old", "cycle": "1.0", "eol": "2024-01-01"}]},
            today=TODAY,
        ),
        collect_lifecycle_status(
            "new",
            {"endoflife": [{"product": "new", "cycle": "2.0", "eol": "2026-08-01"}]},
            today=TODAY,
        ),
    ]
    md = build_lifecycle_report("2026-10", statuses, today=TODAY)
    planning = md.split("## Top Lifecycle Planning Items")[1].split("## Appendix")[0]
    assert planning.index("**new**") < planning.index("**old**")
    assert "(background: effective over 12 months ago)" in planning
    assert "- End-of-life versions older than 12 months (background): 1" in md


def _dated(announced=None, effective=None, detected=None, verified=None):
    finding = {}
    if announced:
        finding["announced_at"] = announced
    if effective:
        finding["effective_at"] = effective
    if detected:
        finding["first_detected_at"] = detected
    if verified:
        finding["observed_at"] = verified
    return finding


def test_1_new_announcement_appears():
    out, _ = classify(_dated(announced="2026-09-28", effective="2026-09-20"), today=TODAY)
    assert out == NEW


def test_2_old_announcement_future_effective_stays_visible():
    out, _ = classify(_dated(announced="2026-01-01", effective="2026-12-01"), today=TODAY)
    assert out == UPCOMING


def test_3_historical_expired_moves_out():
    out, _ = classify(_dated(announced="2025-01-01", effective="2026-10-01"), today=TODAY)
    assert out == EXPIRED


def test_4_recent_update_revives_old_event():
    out, _ = classify(
        _dated(announced="2023-01-01", detected="2026-09-20", effective="2024-01-01"),
        today=TODAY,
    )
    assert out == RECENTLY_UPDATED


def test_5_unknown_announcement_handled_safely():
    out, reasons = classify(_dated(effective="2026-11-01"), today=TODAY)
    assert out == UPCOMING
    assert reasons


def test_6_unknown_effective_handled_safely():
    out, _ = classify(_dated(verified="2026-10-02"), today=TODAY)
    assert out == ACTIVE


def test_7_announcement_not_confused_with_detection():
    # Stale detection does not revive an old announcement...
    out, _ = classify(
        _dated(announced="2023-01-01", detected="2023-05-01", verified="2026-10-02"),
        today=TODAY,
    )
    assert out == ACTIVE
    # ...but a recent detection against an old announcement does.
    out, _ = classify(
        _dated(announced="2023-01-01", detected="2026-09-20", verified="2026-10-02"),
        today=TODAY,
    )
    assert out == RECENTLY_UPDATED


def test_8_first_detection_stable():
    assert classify(_dated(detected="2026-08-03"), today=TODAY)[0] == NEW
    assert classify(_dated(detected="2026-08-03"), today=date(2026, 12, 1))[0] != NEW


def test_9_last_verified_changes():
    assert (
        classify(_dated(verified="2026-10-02"), today=TODAY)[0] == ACTIVE
    )
    assert (
        classify(_dated(verified="2020-01-01"), today=TODAY)[0] == EXPIRED
    )


def test_10_identical_input_identical_report():
    from reports.generate import build_report

    items = [
        {
            "project": "p",
            "pulse": {"facets": {}},
            "findings": [_eol_finding("db 5.0 is end-of-life", "2026-09-01")],
        }
    ]
    assert build_report("2026-10", items, today=TODAY) == build_report(
        "2026-10", items, today=TODAY
    )


def test_11_no_future_date_invented():
    out, _ = classify(_dated(effective="2026-09-01"), today=TODAY)
    assert out in (ACTIVE, RECENTLY_UPDATED, EXPIRED)
    assert out != UPCOMING


def test_12_public_report_hides_internal_metadata():
    from reports.generate import build_report

    finding = dict(
        _eol_finding("db 5.0 is end-of-life", "2026-09-01"),
        _analyst="change",
        suggested_impact="ACTION",
        parser_version="openpulse-parsers/0.4.2",
        evidence_links=["https://example.com/x"],
        distribution_model_change=True,
        stories_merged=2,
        lifecycle_state="EFFECTIVE",
    )
    md = build_report(
        "2026-10",
        [{"project": "p", "pulse": {"facets": {}}, "findings": [finding]}],
        today=TODAY,
    )
    for token in (
        "_analyst",
        "suggested impact",
        "suggested_impact",
        "parser_version",
        "parser-version",
        ".openpulse",
        "_refs",
        "evidence_links",
        "distribution_model_change",
        "stories_merged",
        "lifecycle_state",
    ):
        assert token not in md


def test_golden_a_recent_announcement_future_effective():
    out, _ = classify(
        {"announced_at": "2026-09-20", "effective_at": "2027-03-01"}, today=TODAY
    )
    assert out == UPCOMING


def test_golden_b_old_announcement_just_expired():
    out, _ = classify(
        {"announced_at": "2025-01-01", "effective_at": "2026-10-01"}, today=TODAY
    )
    assert out == EXPIRED


def test_golden_c_old_announcement_future_effective():
    out, _ = classify(
        {"announced_at": "2026-06-01", "effective_at": "2026-12-01"}, today=TODAY
    )
    assert out == UPCOMING


def test_golden_d_unknown_announcement_future_effective():
    out, _ = classify({"effective_at": "2026-11-01"}, today=TODAY)
    assert out == UPCOMING


def test_golden_e_detection_lead_time():
    from core.leadtime import lead_time_days

    assert lead_time_days("2026-08-03", "2026-12-01") == 120
    md_bits = (
        "Announcement: 2026-08-01",
        "First detected by OpenPulse: 2026-08-03",
    )
    from analyzers.report_analyst import render_finding_card

    card = render_finding_card(
        "p",
        {
            "title": "t",
            "announced_at": "2026-08-01",
            "announcement_provenance": "official",
            "first_detected_at": "2026-08-03",
            "effective_at": "2026-12-01",
            "_assessment": {"assessment": "PROJECT_CHANGE", "eligibility": "WATCH"},
            "_freshness": UPCOMING,
            "_refs": [],
        },
        "Lifecycle",
    )
    for bit in md_bits:
        assert bit in card
    assert "Detection lead time before effective date: 120 days" in card
    assert "Announcement → detection: 2 days (2026-08-01 → 2026-08-03)" in card
