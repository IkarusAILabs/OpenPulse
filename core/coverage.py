"""What a PARTIAL or FAILED repository inspection did not cover, by category
(v0.18.0 item S4).

Coverage reasons are written by ``core.github_reader`` from fixed templates,
one per file or event. A summary that can read as an all-clear (``check``,
``digest``, ``warnings``, webhooks, SARIF and the job summary) names the
categories instead of a list of paths: a reader learns what kind of thing
was not inspected, and how much of it, in one line.

``tests/test_coverage_categories.py`` pins every reader template to its
category, so a new template cannot fall silently into the catch-all.
"""

from __future__ import annotations

from typing import Any

#: (category, a substring of the reader's template), checked in order.
_MATCHERS = (
    ("truncated tree", "repository tree truncated"),
    ("unsupported dependency files", "dependency file not supported"),
    ("requirements includes not inspected", "(-r/-c)"),
    ("files over the size limit", "-byte inspection limit"),
    ("repository size cap reached", "repository size cap"),
    ("file-count cap reached", "file cap ("),
    ("unsafe paths", "rejected unsafe repository path"),
)
#: Everything else the reader records: a blob that could not be fetched,
#: verified or parsed, or a repository that could not be enumerated.
UNREADABLE = "files that could not be fetched or parsed"
CATEGORIES = (*(name for name, _ in _MATCHERS), UNREADABLE)


def category(reason: str) -> str:
    for name, marker in _MATCHERS:
        if marker in reason:
            return name
    return UNREADABLE


def categories(reasons: list[str] | tuple[str, ...]) -> dict[str, int]:
    """{category: how many reasons fell in it}, in ``CATEGORIES`` order."""
    counts = dict.fromkeys(CATEGORIES, 0)
    for reason in reasons:
        counts[category(str(reason))] += 1
    return {name: n for name, n in counts.items() if n}


def describe(status: str, reasons: list[str] | tuple[str, ...]) -> str:
    """One line for a summary: ``PARTIAL - not inspected: unsupported dependency
    files (2), files over the size limit (1)``. COMPLETE and NOT_APPLICABLE
    say so plainly; a FAILED inspection says nothing in it was read."""
    if status in ("COMPLETE", "NOT_APPLICABLE"):
        return status
    if status == "FAILED":
        return "FAILED - the repository could not be read, so none of its dependencies were checked"
    found = categories(reasons)
    if not found:
        return f"{status} - not inspected: a reason was not recorded"
    parts = ", ".join(f"{name} ({n})" for name, n in found.items())
    return f"{status} - not inspected: {parts}"


def block(status: str, reasons: list[str] | tuple[str, ...]) -> dict[str, Any]:
    """The categories as a machine-readable mapping (SARIF run properties)."""
    return categories(reasons) if status not in ("COMPLETE", "NOT_APPLICABLE") else {}


__all__ = ["CATEGORIES", "UNREADABLE", "block", "categories", "category", "describe"]
