"""Opt-in local recording of MCP calls (M8, v0.13.0 X6)."""

from __future__ import annotations

import json
import os

import anyio
import pytest
from click.testing import CliRunner

from cli.main import cli
from core import agent_record
from core.agent_record import SCHEMA, Recorder, summarize
from core.agent_tools import check_dependency_file, dependency_status


def _lines(recorder):
    return [json.loads(line) for line in recorder.path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# The recorder
# ---------------------------------------------------------------------------


def test_each_call_is_one_line_with_a_summary_and_the_answer(tmp_path):
    recorder = Recorder(tmp_path / "rec", version="0.13.0")
    answer = dependency_status(
        "django", "4.2", "PyPI", live=False, intent="web app", name_source="documentation"
    )
    recorder.record("dependency_status", {"package": "django", "version": "4.2"}, answer=answer)
    recorder.record("dependency_status", {"package": "nope"}, error="give a package name")
    first, second = _lines(recorder)
    assert first["schema"] == SCHEMA and first["seq"] == 1 and second["seq"] == 2
    assert first["session"] == second["session"] == recorder.session
    assert first["outcome"] == "answer" and first["openpulse_version"] == "0.13.0"
    assert first["summary"]["affected"] is True
    assert first["summary"]["selection_context"]["name_source"] == "documentation"
    assert first["answer"]["verdict"] == json.loads(json.dumps(answer["verdict"]))
    assert second["outcome"] == "error" and second["error"] == "give a package name"
    assert "answer" not in second


def test_a_large_answer_keeps_its_summary_only(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_record, "MAX_ANSWER_BYTES", 100)
    recorder = Recorder(tmp_path)
    answer = dependency_status("django", "4.2", "PyPI", live=False)
    recorder.record("dependency_status", {"package": "django"}, answer=answer)
    (line,) = _lines(recorder)
    assert line["answer_omitted"] is True and "answer" not in line
    assert line["summary"]["relationship"] == answer["verdict"]["relationship"]


def test_arguments_are_capped(tmp_path):
    recorder = Recorder(tmp_path)
    recorder.record("dependency_status", {"intent": "x" * 5000}, error="bad")
    (line,) = _lines(recorder)
    assert len(line["arguments"]["intent"]) == agent_record.MAX_ARGUMENT_CHARS


def test_a_write_failure_stops_recording_and_never_raises(tmp_path, capsys):
    recorder = Recorder(tmp_path)
    recorder.path.mkdir()  # the record file path is now a directory: writes fail
    recorder.record("project_lifecycle", {"project": "django"}, error="offline")
    recorder.record("project_lifecycle", {"project": "django"}, error="offline")
    assert recorder.stopped
    assert capsys.readouterr().err.count("recording stopped") == 1


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions")
def test_files_are_owner_only(tmp_path):
    recorder = Recorder(tmp_path / "rec")
    recorder.record("project_lifecycle", {"project": "x"}, error="offline")
    assert (recorder.directory.stat().st_mode & 0o777) == 0o700
    assert (recorder.path.stat().st_mode & 0o777) == 0o600


def test_sessions_get_separate_files(tmp_path):
    a, b = Recorder(tmp_path), Recorder(tmp_path)
    assert a.path != b.path and a.path.name.startswith("mcp-")


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


def test_file_check_summary(tmp_path):
    answer = check_dependency_file(
        "data/fixtures/manifests/requirements.txt", live=False, trust_all=True
    )
    summary = summarize("check_dependency_file", answer)
    assert summary["dependencies_checked"] == answer["dependencies_checked"]
    assert summary["trust_scope"] == "all dependencies"
    assert set(summary["trust_counts"]) >= {"malicious", "lookalike"}


def test_lifecycle_summary_and_unknown_tools():
    answer = {"project": "django", "cycles": [{}, {}], "supported_cycles": ["5.2"]}
    assert summarize("project_lifecycle", answer) == {
        "project": "django",
        "cycles": 2,
        "supported_cycles": ["5.2"],
    }
    assert summarize("something_else", {}) == {}


# ---------------------------------------------------------------------------
# openpulse mcp --record
# ---------------------------------------------------------------------------


def test_mcp_offers_record_and_it_is_off_by_default():
    out = CliRunner().invoke(cli, ["mcp", "--help"]).output
    assert "--record" in out and "never sent anywhere" in out


def test_the_server_records_answers_and_errors_without_changing_them(tmp_path):
    pytest.importorskip("mcp")
    from cli.mcp_server import build_server

    record = tmp_path / "records"
    args = {"package": "django", "version": "4.2", "ecosystem": "PyPI", "name_source": "other"}
    plain = anyio.run(build_server(root=".", live=False).call_tool, "dependency_status", args)
    server = build_server(root=".", live=False, record=record)
    recorded = anyio.run(server.call_tool, "dependency_status", args)
    with pytest.raises(Exception):
        anyio.run(server.call_tool, "check_dependency_file", {"path": "../outside.txt"})

    def verdict(result):
        return json.loads(json.dumps(result, default=str)).count("AFFECTS_VERSION")

    assert verdict(plain) == verdict(recorded)
    (path,) = list(record.glob("mcp-*.jsonl"))
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [line["outcome"] for line in lines] == ["answer", "error"]
    assert lines[0]["arguments"]["name_source"] == "other"
    assert lines[1]["tool"] == "check_dependency_file" and "outside" in lines[1]["error"]


def test_no_record_means_no_files(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    from cli.mcp_server import build_server

    monkeypatch.chdir(tmp_path)
    anyio.run(
        build_server(root=tmp_path, live=False).call_tool,
        "dependency_status",
        {"package": "django", "version": "4.2", "ecosystem": "PyPI"},
    )
    assert list(tmp_path.rglob("*.jsonl")) == []
