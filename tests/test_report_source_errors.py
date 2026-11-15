"""A source that did not answer is disclosed, never read as "nothing found".

The November 2026 run lost vitess's NVD advisories to NVD's rate limit
and the report showed vitess as having no security changes. A failed
source is now named per project in the executive summary, the data-gaps
section and the metadata sidecar.
"""

from __future__ import annotations

from reports.generate import (
    build_report,
    build_report_metadata,
    collect_project,
    failed_sources,
    prepare_report,
    source_errors,
)

RATE_LIMITED = {
    "collector": "nvd",
    "error": True,
    "category": "rate_limit",
    "retryable": True,
    "status_code": 403,
    "safe_message": "HTTPStatusError: Client error '403 Forbidden' for url <redacted>",
}


def _raw(**sources):
    base = {"endoflife": [], "github": [], "github_meta": [], "nvd": [], "kev": [], "osv": []}
    return {**base, **sources}


def test_source_errors_keep_only_source_category_and_status():
    errors = source_errors(_raw(nvd=[RATE_LIMITED]))
    assert errors == [{"source": "nvd", "category": "rate_limit", "status_code": 403}]
    assert "safe_message" not in str(errors)


def test_a_clean_bundle_has_no_source_errors():
    assert collect_project("vitess", _raw())["source_errors"] == []


def test_failed_sources_groups_projects_per_source():
    items = [
        collect_project("vitess", _raw(nvd=[RATE_LIMITED])),
        collect_project("timescaledb", _raw()),
        collect_project(
            "postgresql", _raw(nvd=[RATE_LIMITED], osv=[{**RATE_LIMITED, "collector": "osv"}])
        ),
    ]
    assert failed_sources(items) == {"nvd": ["postgresql", "vitess"], "osv": ["postgresql"]}


def test_the_report_names_sources_that_did_not_answer():
    items = [collect_project("vitess", _raw(nvd=[RATE_LIMITED])), collect_project("db", _raw())]
    md = build_report("2026-11", items)
    assert "- Sources that did not answer: nvd for 1 project" in md
    assert "unknown, not absent" in md
    assert "**Sources that did not answer.**" in md
    assert "- nvd (1): vitess" in md
    assert "No data gaps this month" not in md


def test_a_report_without_errors_is_unchanged():
    md = build_report("2026-11", [collect_project("db", _raw())])
    assert "did not answer" not in md


def test_the_metadata_counts_failed_sources():
    items = [collect_project("vitess", _raw(nvd=[RATE_LIMITED])), collect_project("db", _raw())]
    prepared = prepare_report(items)
    meta = build_report_metadata(
        "2026-11", items, prepared["main_pairs"], prepared["historical"], sweep_included=False
    )
    assert meta["coverage"]["source_errors"] == {"nvd": 1}
    clean = build_report_metadata("2026-11", [collect_project("db", _raw())], [], [], False)
    assert clean["coverage"]["source_errors"] == {}
