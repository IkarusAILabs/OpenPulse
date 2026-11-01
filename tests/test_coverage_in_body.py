"""Digest, warnings and the webhook body show a repository not fully read (#102)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from cli.main import cli
from tests.test_check import _patch_inspection

LINE = "Repository inspection coverage:"
INPUTS = ["--watchlist", "data/fixtures/watchlist_sample.yaml"]
EVENT = ["--event", "data/fixtures/django-eol/event.json", "--replay", "--ledger", ""]
REPO = ["--github-repo", "owner/repo"]


def _run(*args):
    return CliRunner().invoke(cli, list(args))


@pytest.mark.parametrize("command", ["digest", "warnings"])
@pytest.mark.parametrize("coverage", ["FAILED", "PARTIAL"])
def test_markdown_body_names_incomplete_coverage(monkeypatch, command, coverage):
    _patch_inspection(monkeypatch, coverage)
    result = _run(command, *INPUTS, *REPO, *EVENT)
    assert result.exit_code == 0, result.output
    assert f"> ⚠️ {LINE} {coverage} — {coverage.lower()} scan reason." in result.output


@pytest.mark.parametrize("command", ["digest", "warnings"])
def test_json_output_carries_the_note(monkeypatch, command):
    _patch_inspection(monkeypatch, "FAILED")
    result = _run(command, *INPUTS, *REPO, *EVENT, "--output", "json")
    assert result.exit_code == 0, result.output
    body = json.loads(result.output[result.output.index("{") :])
    assert body["coverage_note"].startswith(f"⚠️ {LINE} FAILED")


@pytest.mark.parametrize("command", ["digest", "warnings"])
def test_no_line_when_complete_or_without_a_repository(monkeypatch, command):
    plain = _run(command, *INPUTS, *EVENT)
    assert plain.exit_code == 0, plain.output
    assert LINE not in plain.output
    _patch_inspection(monkeypatch, "COMPLETE")
    complete = _run(command, *INPUTS, *REPO, *EVENT)
    assert complete.exit_code == 0, complete.output
    assert LINE not in complete.output

    # Same body apart from the run-level preamble a repository run prints.
    def body(output):
        return [
            line
            for line in output.split("# ", 1)[1].splitlines()
            if not line.startswith("Generated")
        ]

    assert body(complete.output) == body(plain.output)


@pytest.mark.parametrize("coverage", ["FAILED", "PARTIAL"])
def test_webhook_payload_carries_the_line(monkeypatch, tmp_path, coverage):
    import core.notify as notify

    sent = {}
    monkeypatch.setattr(
        notify,
        "post_digest",
        lambda url, text, **kw: sent.update(text=text) or {"ok": True, "status_code": 200},
    )
    _patch_inspection(monkeypatch, coverage)
    result = _run(
        "check",
        *INPUTS,
        *REPO,
        *EVENT,
        "--webhook",
        "https://hooks.example/x",
        "--delivery-state",
        str(tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert f"{LINE} {coverage}" in sent["text"]
    title, rest = sent["text"].split("\n", 1)
    assert title.startswith("# ") and rest.lstrip().startswith("> ⚠️")


def test_webhook_payload_is_unchanged_without_a_repository(monkeypatch):
    import core.notify as notify

    sent = {}
    monkeypatch.setattr(
        notify,
        "post_digest",
        lambda url, text, **kw: sent.update(text=text) or {"ok": True, "status_code": 200},
    )
    result = _run(
        "check", *INPUTS, *EVENT, "--webhook", "https://hooks.example/x", "--delivery-state", ""
    )
    assert result.exit_code == 0, result.output
    assert LINE not in sent["text"]
