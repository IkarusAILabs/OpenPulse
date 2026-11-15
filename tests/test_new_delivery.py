"""Delivery of what a run recorded for the first time (v0.21.0 item W5)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli
from core import new_delivery
from core.new_delivery import (
    DEFAULT_ISSUE_TITLE,
    MARKER,
    NewFindingsError,
    deliver_issue,
    deliver_webhook,
    deliverable,
    load_new_findings,
    render_issue_md,
    render_text,
)
from core.webhook_signing import SIGNATURE_HEADER, TIMESTAMP_HEADER, verify_webhook_signature

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "ghs_" + "t" * 36
SECRET = b"s" * 40


def _item(**over):
    item = {
        "dependency": "pkg:pypi/urllib3@2.0.0",
        "event_id": "evt-registry-1",
        "event_type": "DEPRECATION",
        "title": "urllib3 2.0.0 was yanked",
        "impact": "REVIEW",
        "relationship": "AFFECTS_PACKAGE",
        "evidence_urls": ["https://pypi.org/project/urllib3/2.0.0/"],
        "finding_class": "change",
        "first_seen": None,
    }
    item.update(over)
    return item


def _report(*items, **over):
    new = list(items) or [_item()]
    report = {"baseline": False, "new": new, "facts": 6, "new_facts": len(new), "recorded": True}
    report.update(over)
    return report


def _github(issues, calls, *, status=None):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if status is not None:
            return httpx.Response(status, json={"message": "secret detail"})
        if request.method == "GET":
            return httpx.Response(200, json=issues)
        if request.url.path.endswith("/comments"):
            return httpx.Response(201, json={"id": 1})
        return httpx.Response(201, json={"number": 77})

    return httpx.MockTransport(handler)


def _issue(number, **over):
    issue = {
        "number": number,
        "title": DEFAULT_ISSUE_TITLE,
        "body": MARKER + "\nearlier findings",
        "user": {"login": "github-actions[bot]"},
        "author_association": "NONE",
    }
    issue.update(over)
    return issue


# --- what counts as news ----------------------------------------------------


def test_only_a_run_with_news_is_deliverable():
    assert deliverable(_report())
    assert not deliverable(_report(baseline=True))
    assert not deliverable({"baseline": False, "new": [], "facts": 3, "new_facts": 0})
    assert not deliverable(_report(recorded=False))


def test_load_refuses_what_attest_does_not_write(tmp_path):
    path = tmp_path / "new.json"
    for junk in ("not json", "[]", '{"new": {}}', '{"new": ["x"]}'):
        path.write_text(junk, encoding="utf-8")
        with pytest.raises(NewFindingsError):
            load_new_findings(str(path))
    path.write_text(json.dumps(_report()), encoding="utf-8")
    assert load_new_findings(str(path))["new_facts"] == 1


# --- rendering untrusted upstream text ---------------------------------------


def test_issue_text_cannot_mention_link_or_break_the_table():
    hostile = _item(
        dependency="pkg:npm/@scope/name@1.0.0",
        title="ping @octocat, closes #1 | x `y` [a](https://evil.example)\n| new | row |",
    )
    body = render_issue_md(_report(hostile))
    row = next(line for line in body.splitlines() if "octocat" in line)
    # Five cells: the hostile title added no column and no line.
    assert row.count("|") == 6
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert all(c.startswith("`") and c.endswith("`") for c in cells[:4])
    # No backtick inside a cell can end its code span early.
    assert all("`" not in c[1:-1] for c in cells[:4])
    assert body.startswith(MARKER)


def test_only_http_urls_are_kept_and_parentheses_are_encoded():
    item = _item(
        evidence_urls=[
            "javascript:alert(1)",
            "https://example.org/a(b)",
            "https://example.org/x y",
            "https://example.org/" + "a" * 400,
            "https://example.org/2",
            "https://example.org/3",
            "https://example.org/4",
        ]
    )
    body = render_issue_md(_report(item))
    assert "javascript" not in body and "x y" not in body and "a" * 400 not in body
    assert "<https://example.org/a%28b%29>" in body
    assert "example.org/3" in body and "example.org/4" not in body
    assert "javascript" not in render_text(_report(item))


def test_long_lists_are_capped_and_counted():
    items = [_item(dependency=f"pkg:pypi/p{i}@1") for i in range(60)]
    body = render_issue_md(_report(*items))
    assert "p49@1" in body and "p50@1" not in body and "And 10 more" in body
    text = render_text(_report(*items), run_url="https://github.com/o/r/actions/runs/1")
    assert "- and 10 more" in text and text.endswith("Run: https://github.com/o/r/actions/runs/1")
    assert len(body) < 60_000


def test_a_hostile_run_url_is_dropped():
    assert "Run:" not in render_text(_report(), run_url="javascript:alert(1)")


# --- the issue ----------------------------------------------------------------


def test_the_first_delivery_opens_the_issue():
    calls: list[httpx.Request] = []
    sent = deliver_issue("o/r", _report(), token=TOKEN, transport=_github([], calls))
    assert sent == {"ok": True, "action": "created", "number": 77, "error": None}
    assert [c.method for c in calls] == ["GET", "POST"]
    assert {c.url.host for c in calls} == {"api.github.com"}
    assert all(c.headers["authorization"] == f"Bearer {TOKEN}" for c in calls)
    posted = json.loads(calls[1].content)
    assert posted["title"] == DEFAULT_ISSUE_TITLE and posted["body"].startswith(MARKER)
    assert "urllib3" in posted["body"]


def test_later_deliveries_comment_on_the_open_issue():
    calls: list[httpx.Request] = []
    issues = [_issue(9), _issue(4)]
    sent = deliver_issue("o/r", _report(), token=TOKEN, transport=_github(issues, calls))
    assert sent["ok"] and sent["action"] == "commented" and sent["number"] == 4
    assert calls[1].url.path == "/repos/o/r/issues/4/comments"


@pytest.mark.parametrize(
    "lookalike",
    [
        _issue(3, user={"login": "mallory"}),  # an outsider's issue with our title and marker
        _issue(3, pull_request={"url": "x"}),
        _issue(3, body="no marker"),
        _issue(3, title=DEFAULT_ISSUE_TITLE + " "),
        _issue(3, user=None, body=None),
    ],
)
def test_a_lookalike_issue_is_never_used(lookalike):
    calls: list[httpx.Request] = []
    sent = deliver_issue("o/r", _report(), token=TOKEN, transport=_github([lookalike], calls))
    assert sent["action"] == "created"
    assert calls[1].url.path == "/repos/o/r/issues"


def test_a_maintainers_own_issue_is_used():
    calls: list[httpx.Request] = []
    issue = _issue(5, user={"login": "alice"}, author_association="MEMBER")
    sent = deliver_issue("o/r", _report(), token=TOKEN, transport=_github([issue], calls))
    assert sent["action"] == "commented" and sent["number"] == 5


def test_a_refusal_is_reported_without_the_token_or_the_response():
    calls: list[httpx.Request] = []
    sent = deliver_issue("o/r", _report(), token=TOKEN, transport=_github([], calls, status=403))
    assert not sent["ok"]
    assert "HTTP 403" in sent["error"] and "issues: write" in sent["error"]
    assert TOKEN not in sent["error"] and "secret detail" not in sent["error"]


def test_a_redirect_is_not_followed():
    calls: list[httpx.Request] = []
    transport = httpx.MockTransport(
        lambda request: (
            calls.append(request),
            httpx.Response(302, headers={"location": "https://evil.example/"}),
        )[1]
    )
    sent = deliver_issue("o/r", _report(), token=TOKEN, transport=transport)
    assert not sent["ok"] and "redirect" in sent["error"] and len(calls) == 1


@pytest.mark.parametrize("repo", ["", "o", "o/r/x", "../r", "o/r?x=1", "https://github.com/o/r"])
def test_a_bad_repository_or_a_missing_token_makes_no_request(repo):
    calls: list[httpx.Request] = []
    assert not deliver_issue(repo, _report(), token=TOKEN, transport=_github([], calls))["ok"]
    assert not deliver_issue("o/r", _report(), token="", transport=_github([], calls))["ok"]
    assert calls == []


# --- the webhook --------------------------------------------------------------


def test_the_webhook_post_is_signed_over_the_bytes_sent():
    seen: list[httpx.Request] = []
    transport = httpx.MockTransport(lambda request: (seen.append(request), httpx.Response(200))[1])
    sent = deliver_webhook(
        "https://hooks.example.org/T/secret-path",
        _report(),
        signing_secret=SECRET,
        transport=transport,
        resolver=lambda _host: ["93.184.216.34"],
    )
    assert sent["ok"]
    request = seen[0]
    assert verify_webhook_signature(
        SECRET,
        request.content,
        request.headers[TIMESTAMP_HEADER],
        request.headers[SIGNATURE_HEADER],
    )
    assert "urllib3 2.0.0 was yanked" in json.loads(request.content)["text"]


def test_the_webhook_policy_still_applies():
    sent = deliver_webhook(
        "https://internal.example/hook", _report(), resolver=lambda _host: ["127.0.0.1"]
    )
    assert not sent["ok"] and "loopback" in sent["error"]


# --- the command ---------------------------------------------------------------


def _write(tmp_path, report):
    path = tmp_path / "new.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return str(path)


def test_the_command_sends_nothing_for_a_first_run_or_no_news(tmp_path, monkeypatch):
    def never(*_args, **_kwargs):
        raise AssertionError("nothing may be sent")

    monkeypatch.setattr(new_delivery, "deliver_issue", never)
    monkeypatch.setattr(new_delivery, "deliver_webhook", never)
    for report, reason in (
        (_report(baseline=True), "a first run is the starting point"),
        (_report(new=[], new_facts=0), "nothing new"),
    ):
        result = CliRunner().invoke(
            cli,
            ["deliver-new", _write(tmp_path, report), "--issue", "o/r", "--webhook", "https://h/x"],
        )
        assert result.exit_code == 0, result.output
        assert f"nothing sent ({reason})" in result.output


def test_the_command_delivers_to_both_and_passes_the_token_from_the_environment(
    tmp_path, monkeypatch
):
    seen = {}

    def issue(repo, report, **kwargs):
        seen["issue"] = (repo, kwargs["token"], kwargs["run_url"])
        return {"ok": True, "action": "created", "number": 12, "error": None}

    def webhook(url, report, **kwargs):
        seen["webhook"] = (url, kwargs["signing_secret"])
        return {"ok": True, "status_code": 200, "error": None}

    monkeypatch.setattr(new_delivery, "deliver_issue", issue)
    monkeypatch.setattr(new_delivery, "deliver_webhook", webhook)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)
    monkeypatch.setenv("OPENPULSE_WEBHOOK_URL", "https://hooks.example.org/x")
    monkeypatch.setenv("OPENPULSE_WEBHOOK_SECRET", SECRET.decode())
    result = CliRunner().invoke(
        cli,
        ["deliver-new", _write(tmp_path, _report()), "--issue", "o/r", "--run-url", "https://r/1"],
    )
    assert result.exit_code == 0, result.output
    assert seen["issue"] == ("o/r", TOKEN, "https://r/1")
    assert seen["webhook"] == ("https://hooks.example.org/x", SECRET)
    assert "issue #12 created" in result.output and "webhook delivered (1 new)" in result.output
    assert TOKEN not in result.output and SECRET.decode() not in result.output


def test_the_command_fails_when_a_delivery_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(
        new_delivery,
        "deliver_issue",
        lambda *_a, **_k: {"ok": False, "action": None, "number": None, "error": "HTTP 403"},
    )
    monkeypatch.delenv("OPENPULSE_WEBHOOK_URL", raising=False)
    result = CliRunner().invoke(cli, ["deliver-new", _write(tmp_path, _report()), "--issue", "o/r"])
    assert result.exit_code == 1
    assert "issue delivery failed: HTTP 403" in result.output


def test_the_command_needs_a_target_and_a_real_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENPULSE_WEBHOOK_URL", raising=False)
    result = CliRunner().invoke(cli, ["deliver-new", _write(tmp_path, _report())])
    assert result.exit_code != 0 and "give --webhook or --issue" in result.output
    junk = tmp_path / "junk.json"
    junk.write_text("[]", encoding="utf-8")
    result = CliRunner().invoke(cli, ["deliver-new", str(junk), "--issue", "o/r"])
    assert result.exit_code != 0 and "not the JSON attest writes" in result.output


# --- the Action ----------------------------------------------------------------


def _action():
    return yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))


def test_the_action_delivers_only_from_the_default_branch_with_secrets_in_env():
    action = _action()
    step = next(s for s in action["runs"]["steps"] if s.get("id") == "deliver")
    # No input is interpolated into the script: the URL, secret and token are env only.
    assert "${{" not in step["run"]
    assert step["env"]["OPENPULSE_WEBHOOK_URL"] == "${{ inputs.notify-webhook }}"
    assert step["env"]["OPENPULSE_WEBHOOK_SECRET"] == "${{ inputs.notify-webhook-secret }}"
    assert "default_branch" in step["env"]["ON_DEFAULT_BRANCH"]
    script = step["run"]
    assert script.index('"$ON_DEFAULT_BRANCH" != "true"') < script.index("deliver-new")
    assert "--webhook" not in script  # the URL never reaches argv
    assert action["outputs"]["delivery"]["value"] == "${{ steps.deliver.outputs.delivery }}"


def test_the_action_reports_a_failed_delivery_after_the_history_is_saved():
    steps = _action()["runs"]["steps"]
    names = [s.get("name") or s.get("id") or s.get("uses", "") for s in steps]
    save = next(i for i, s in enumerate(steps) if "actions/cache/save" in s.get("uses", ""))
    report = names.index("Report a failed delivery")
    assert names.index("Deliver new findings") < save < report
    assert steps[report]["if"] == "steps.deliver.outputs.delivery == 'failed'"


def test_the_action_refuses_delivery_without_a_kept_history():
    run = next(s for s in _action()["runs"]["steps"] if s.get("id") == "run")
    assert run["env"]["IN_NOTIFY_WEBHOOK_SET"] == "${{ inputs.notify-webhook != '' }}"
    assert "notify-webhook and notify-issue need history: on" in run["run"]
    assert "inputs.notify-webhook }}" not in json.dumps(run["env"])
