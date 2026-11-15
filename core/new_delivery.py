"""Deliver what a run recorded for the first time (v0.21.0 item W5).

``attest --new-findings`` writes the detections a run had not seen before
(``core.new_detections``). This module sends that list somewhere a person
reads: a webhook (``core.notify``, optionally signed) or one GitHub issue.

Nothing is sent for a first run with a ledger (a baseline is not news), for
a run that recorded nothing new, or for a run whose ledger was busy.

The issue is found by a fixed title and a marker in its body, and only when
the repository itself opened it: an issue from ``github-actions[bot]`` or
from an owner, member or collaborator. Anyone can open an issue with the
same title, so an outsider's issue is never used. The first delivery opens
the issue and later ones add a comment (a comment notifies; an edited body
does not). When the issue is closed, the next new finding opens another.

Upstream text (package names, titles, URLs) is untrusted: in the issue it is
put in code spans, where ``@name`` and ``#123`` neither notify nor link,
and only http(s) evidence URLs are kept, as bare URLs.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from collectors.errors import strip_unsafe

GITHUB_API = "https://api.github.com"
MARKER = "<!-- openpulse:new-findings -->"
DEFAULT_ISSUE_TITLE = "OpenPulse: new findings in your dependencies"
#: Findings listed per delivery; the rest are counted, and the run has all.
MAX_ITEMS = 50
MAX_TEXT_CHARS = 200
MAX_URL_CHARS = 300
MAX_URLS = 3
MAX_FILE_BYTES = 8 * 1024 * 1024
#: Open issues read to find the existing one (newest first, 100 per page).
MAX_ISSUE_PAGES = 3
_TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
_ACTIONS_BOT = "github-actions[bot]"
_REPO_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}$")
_URL_RE = re.compile(r"^https?://[^\s<>\"'`|\\]+$")
_SPACE_RE = re.compile(r"\s+")
_NOT_ATTEST_JSON = "the new-findings file is not the JSON attest writes"


class NewFindingsError(ValueError):
    """The new-findings file is unreadable or not what ``attest`` writes."""


def load_new_findings(path: str) -> dict[str, Any]:
    """The report ``attest --new-findings`` wrote, shape-checked."""
    from core.bounded_io import read_bytes

    try:
        doc = json.loads(read_bytes(path, MAX_FILE_BYTES, "new-findings file").decode("utf-8"))
    except OSError as exc:
        raise NewFindingsError(f"cannot read the new-findings file: {exc.strerror}") from exc
    except UnicodeDecodeError as exc:
        raise NewFindingsError(_NOT_ATTEST_JSON) from exc
    except ValueError as exc:
        if isinstance(exc, json.JSONDecodeError):
            raise NewFindingsError(_NOT_ATTEST_JSON) from exc
        raise NewFindingsError(str(exc)) from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("new"), list):
        raise NewFindingsError(_NOT_ATTEST_JSON)
    if not all(isinstance(item, dict) for item in doc["new"]):
        raise NewFindingsError(_NOT_ATTEST_JSON)
    return doc


def deliverable(report: dict[str, Any]) -> bool:
    """True when the run has news: recorded, not a baseline, at least one new detection."""
    return bool(report.get("recorded", True)) and not report.get("baseline") and bool(report["new"])


def _plain(value: Any, limit: int = MAX_TEXT_CHARS) -> str:
    text = _SPACE_RE.sub(" ", strip_unsafe(str(value if value is not None else ""))).strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _code(value: Any) -> str:
    """Untrusted text as a table-safe code span: no mention, reference or link is made."""
    text = _plain(value).replace("`", "'").replace("|", "/").replace("\\", "/")
    return f"`{text}`" if text else "-"


def _url(value: Any) -> str | None:
    text = strip_unsafe(str(value or "")).strip()
    if len(text) > MAX_URL_CHARS or not _URL_RE.match(text):
        return None
    return text.replace("(", "%28").replace(")", "%29")


def _urls(item: dict[str, Any]) -> list[str]:
    urls = item.get("evidence_urls")
    found = [_url(u) for u in (urls if isinstance(urls, list) else [])]
    return [u for u in found if u][:MAX_URLS]


def _number(value: Any, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _counts(report: dict[str, Any]) -> str:
    new_facts = _number(report.get("new_facts"), len(report["new"]))
    return f"{new_facts} new of {_number(report.get('facts'), new_facts)} detection(s)"


def render_text(report: dict[str, Any], run_url: str | None = None) -> str:
    """Plain text for a JSON-text webhook: one line per new detection."""
    lines = [f"OpenPulse: {_counts(report)} since the last run"]
    for item in report["new"][:MAX_ITEMS]:
        line = (
            f"- {_plain(item.get('dependency'))}: {_plain(item.get('title'))} "
            f"[{_plain(item.get('impact'), 20)}]"
        )
        urls = _urls(item)
        lines.append(f"{line} {urls[0]}" if urls else line)
    hidden = len(report["new"]) - MAX_ITEMS
    if hidden > 0:
        lines.append(f"- and {hidden} more")
    run = _url(run_url)
    if run:
        lines.append(f"Run: {run}")
    return "\n".join(lines)


def render_issue_md(report: dict[str, Any], run_url: str | None = None) -> str:
    """Markdown for the issue body or a comment on it. Begins with the marker."""
    lines = [
        MARKER,
        f"**{_counts(report)} since the last run.**",
        "",
        "| Dependency | Type | What | Impact | Evidence |",
        "|---|---|---|---|---|",
    ]
    for item in report["new"][:MAX_ITEMS]:
        evidence = " ".join(f"<{url}>" for url in _urls(item)) or "-"
        lines.append(
            f"| {_code(item.get('dependency'))} | {_code(item.get('event_type'))} | "
            f"{_code(item.get('title'))} | {_code(item.get('impact'))} | {evidence} |"
        )
    hidden = len(report["new"]) - MAX_ITEMS
    if hidden > 0:
        lines += ["", f"And {hidden} more; the run lists all of them."]
    run = _url(run_url)
    if run:
        lines += ["", f"Run: <{run}>"]
    lines += [
        "",
        "Each detection is listed once, in the run that first recorded it. "
        "Closing this issue is safe: the next new finding opens another.",
    ]
    return "\n".join(lines)


def _ours(issue: Any, title: str) -> bool:
    if not isinstance(issue, dict) or "pull_request" in issue:
        return False
    if issue.get("title") != title or MARKER not in str(issue.get("body") or ""):
        return False
    user = issue.get("user") if isinstance(issue.get("user"), dict) else {}
    return (
        user.get("login") == _ACTIONS_BOT
        or issue.get("author_association") in _TRUSTED_ASSOCIATIONS
    )


def deliver_issue(
    repo: str,
    report: dict[str, Any],
    *,
    token: str | None,
    title: str = DEFAULT_ISSUE_TITLE,
    run_url: str | None = None,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Open the findings issue or comment on it; {ok, action, number, error} (never raises).

    The token goes to api.github.com only, redirects are not followed, and an
    error never contains the token or a response body.
    """
    result: dict[str, Any] = {"ok": False, "action": None, "number": None, "error": None}
    if not _REPO_RE.match(repo or ""):
        return {**result, "error": "the issue repository must be OWNER/NAME"}
    if not token:
        return {**result, "error": "an issue needs a token (GITHUB_TOKEN) with issues: write"}
    title = _plain(title) or DEFAULT_ISSUE_TITLE
    body = render_issue_md(report, run_url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "openpulse",
    }
    step = "list issues"
    try:
        with httpx.Client(
            base_url=GITHUB_API,
            headers=headers,
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        ) as client:
            existing = None
            for page in range(1, MAX_ISSUE_PAGES + 1):
                response = client.get(
                    f"/repos/{repo}/issues",
                    params={"state": "open", "per_page": 100, "page": page},
                )
                response.raise_for_status()
                issues = response.json()
                if not isinstance(issues, list):
                    return {**result, "error": "GitHub's issue list was not a list"}
                numbers = [
                    i["number"]
                    for i in issues
                    if _ours(i, title) and isinstance(i.get("number"), int)
                ]
                if numbers:
                    existing = min(numbers)
                    break
                if len(issues) < 100:
                    break
            if existing is not None:
                step = "comment"
                response = client.post(
                    f"/repos/{repo}/issues/{existing}/comments", json={"body": body}
                )
                response.raise_for_status()
                return {**result, "ok": True, "action": "commented", "number": existing}
            step = "create the issue"
            response = client.post(f"/repos/{repo}/issues", json={"title": title, "body": body})
            response.raise_for_status()
            created = response.json()
            number = created.get("number") if isinstance(created, dict) else None
            return {
                **result,
                "ok": True,
                "action": "created",
                "number": number if isinstance(number, int) else None,
            }
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if 300 <= status < 400:
            return {**result, "error": f"GitHub redirected '{step}'; redirects are not followed"}
        hint = " (does the token have issues: write?)" if status in (401, 403, 404) else ""
        return {**result, "error": f"GitHub returned HTTP {status} to '{step}'{hint}"}
    except (httpx.HTTPError, ValueError) as exc:
        return {**result, "error": f"could not {step}: {type(exc).__name__}"}


def deliver_webhook(
    url: str,
    report: dict[str, Any],
    *,
    run_url: str | None = None,
    allow_http: bool = False,
    signing_secret: bytes | None = None,
    transport: httpx.BaseTransport | None = None,
    resolver: Any = None,
) -> dict[str, Any]:
    """POST the new findings as ``{"text": ...}`` under the webhook policy (``core.notify``)."""
    from core.notify import WebhookPolicy, post_digest

    return post_digest(
        url,
        render_text(report, run_url),
        policy=WebhookPolicy(allow_http=allow_http),
        transport=transport,
        resolver=resolver,
        signing_secret=signing_secret,
    )


__all__ = [
    "DEFAULT_ISSUE_TITLE",
    "MARKER",
    "NewFindingsError",
    "deliver_issue",
    "deliver_webhook",
    "deliverable",
    "load_new_findings",
    "render_issue_md",
    "render_text",
]
