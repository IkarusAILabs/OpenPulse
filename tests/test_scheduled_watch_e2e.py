"""Scheduled runs, end to end (v0.21.0 item W6).

Exit criterion of Phase 15: scheduled runs over a project's own lockfile,
with the history kept between them, report an upstream change exactly once.

Each run does what the Action does with ``history: on``, ``registry-changes:
all``, ``observe-repositories: on`` and a webhook: audit the kept history,
``attest`` with the ledger, then ``deliver-new``. Nothing is read from the
network. The registry answers are the recorded npm responses for
``uuid@3.4.0`` (``data/fixtures/uuid-version-deprecated``); the "before"
answer is that same response without its ``deprecated`` field. GitHub is a
stub.
"""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from core import new_delivery

ROOT = Path(__file__).resolve().parents[1]
EVENT = str(ROOT / "data/fixtures/django-eol/event.json")
RECORDED = ROOT / "data/fixtures/uuid-version-deprecated"
NPM = "https://registry.npmjs.org/"
HISTORY_KEY = base64.b64encode(b"k" * 32).decode()
WEBHOOK = "https://hooks.example.org/services/T000/B000/not-a-real-path"


def _recorded(name):
    return json.loads((RECORDED / name).read_text(encoding="utf-8"))["response"]


class Upstream:
    """What the registry and GitHub answer today; a test changes it between runs."""

    def __init__(self):
        before = _recorded("3.4.0.json")
        before.pop("deprecated")
        self.registry = {
            NPM + "uuid/latest": _recorded("latest.json"),
            NPM + "uuid/3.4.0": before,
            NPM + "widget/latest": {"name": "widget", "version": "1.0.0", "license": "MIT"},
            NPM + "widget/1.0.0": {
                "name": "widget",
                "version": "1.0.0",
                "license": "MIT",
                "repository": {"type": "git", "url": "git+https://github.com/acme/widget.git"},
            },
        }
        self.archived = False

    def deprecate_uuid(self):
        self.registry[NPM + "uuid/3.4.0"] = _recorded("3.4.0.json")

    def fetch_json(self, url):
        if url in self.registry:
            return 200, json.loads(json.dumps(self.registry[url]))
        return 0, None

    def fetch_meta(self, repo):
        assert repo == "acme/widget"
        return {
            "collector": "github",
            "kind": "repo_meta",
            "repo": repo,
            "full_name": repo,
            "archived": self.archived,
            "pushed_at": "2026-11-01T00:00:00Z",
            "default_branch": "main",
            "license": "MIT",
        }


class Project:
    """A repository with a lockfile, a kept history and a webhook."""

    def __init__(self, root: Path):
        self.root = root
        self.lockfile = root / "package-lock.json"
        self.lockfile.write_text(
            json.dumps(
                {
                    "name": "app",
                    "lockfileVersion": 3,
                    "packages": {
                        "": {"name": "app", "version": "1.0.0"},
                        "node_modules/uuid": {"version": "3.4.0"},
                        "node_modules/widget": {"version": "1.0.0"},
                    },
                }
            ),
            encoding="utf-8",
        )
        self.observations = root / ".openpulse" / "observations"
        self.ledger = root / ".openpulse" / "detections"
        self.new_file = root / "new.json"
        self.summary = root / "summary.md"
        self.sarif = root / "results.sarif"
        self.delivered: list[str] = []
        self.runs = 0

    def scheduled_run(self):
        """One run of the Action's steps; returns the new-findings report."""
        runner = CliRunner()
        self.runs += 1
        if self.runs > 1 and (self.observations.exists() or self.ledger.exists()):
            # The restored history is audited before anything reads it (W2).
            audit = runner.invoke(
                cli,
                ["history-audit", "--require-keyed", "--store", str(self.observations),
                 "--ledger", str(self.ledger)],
            )  # fmt: skip
            assert audit.exit_code == 0, audit.output
        for stale in (self.new_file, self.summary, self.sarif):
            stale.unlink(missing_ok=True)
        attest = runner.invoke(
            cli,
            ["attest", "--lockfile", str(self.lockfile), "--event", EVENT,
             "--registry-changes", "--observe-repositories",
             "--observation-store", str(self.observations),
             "--ledger", str(self.ledger), "--new-findings", str(self.new_file),
             "--output", str(self.root / "contracts.jsonl"),
             "--sarif", str(self.sarif), "--summary", str(self.summary)],
        )  # fmt: skip
        assert attest.exit_code == 0, attest.output
        deliver = runner.invoke(cli, ["deliver-new", str(self.new_file), "--webhook", WEBHOOK])
        assert deliver.exit_code == 0, deliver.output
        return json.loads(self.new_file.read_text(encoding="utf-8"))

    def summary_text(self):
        return self.summary.read_text(encoding="utf-8")

    def sarif_rules(self):
        run = json.loads(self.sarif.read_text(encoding="utf-8"))["runs"][0]
        return sorted(r["ruleId"] for r in run["results"])

    def evict_the_cache(self):
        shutil.rmtree(self.root / ".openpulse")


@pytest.fixture
def upstream(monkeypatch):
    world = Upstream()
    monkeypatch.setattr("core.digest_integrity.default_fetch", world.fetch_json)
    monkeypatch.setattr("core.dependency_repositories.default_fetch_meta", world.fetch_meta)
    monkeypatch.setenv("OPENPULSE_HISTORY_KEY", HISTORY_KEY)
    return world


@pytest.fixture
def project(tmp_path, monkeypatch, upstream):
    project = Project(tmp_path)

    def webhook(url, report, **_kwargs):
        assert url == WEBHOOK
        project.delivered.append(new_delivery.render_text(report))
        return {"ok": True, "status_code": 200, "error": None}

    monkeypatch.setattr(new_delivery, "deliver_webhook", webhook)
    return project


def _new(report):
    return sorted((item["dependency"], item["event_type"]) for item in report["new"])


def test_an_upstream_change_between_two_scheduled_runs_is_reported_exactly_once(project, upstream):
    # Monday: nothing is wrong with either dependency. The run is the starting point.
    first = project.scheduled_run()
    assert first["baseline"] is True and first["new"] == []
    assert project.delivered == []

    # During the week the publisher deprecates the locked release and the
    # repository of the other dependency is archived. Nobody touched the lockfile.
    upstream.deprecate_uuid()
    upstream.archived = True

    # Next Monday: both changes are new, listed in the summary and delivered once.
    second = project.scheduled_run()
    assert second["baseline"] is False and second["recorded"] is True
    assert _new(second) == [("uuid==3.4.0", "DEPRECATION"), ("widget==1.0.0", "PROJECT_ARCHIVED")]
    assert all(item["first_seen"] for item in second["new"])  # keyed, so the date is a claim
    summary = project.summary_text()
    assert "2 new of 2 detection(s)." in summary
    assert "| `uuid==3.4.0` | DEPRECATION |" in summary
    assert "| `widget==1.0.0` | PROJECT_ARCHIVED |" in summary
    assert len(project.delivered) == 1
    assert "uuid==3.4.0" in project.delivered[0] and "widget==1.0.0" in project.delivered[0]
    second_rules = project.sarif_rules()
    assert "openpulse/deprecation" in second_rules and "openpulse/project-archived" in second_rules

    # The Monday after: upstream is unchanged, so nothing is new and nothing is sent again.
    third = project.scheduled_run()
    assert third["baseline"] is False and third["new"] == [] and third["new_facts"] == 0
    assert "Nothing new." in project.summary_text()
    assert len(project.delivered) == 1
    # The deprecation still holds, so the full report (SARIF) keeps showing it.
    assert "openpulse/deprecation" in project.sarif_rules()


def test_a_first_run_that_already_finds_something_delivers_nothing(project, upstream):
    upstream.deprecate_uuid()
    first = project.scheduled_run()
    assert first["baseline"] is True and _new(first) == [("uuid==3.4.0", "DEPRECATION")]
    assert "First run with this history" in project.summary_text()
    assert project.delivered == []

    second = project.scheduled_run()
    assert second["new"] == [] and project.delivered == []


def test_an_evicted_cache_starts_over_without_sending_old_news(project, upstream):
    project.scheduled_run()
    upstream.deprecate_uuid()
    project.scheduled_run()
    assert len(project.delivered) == 1

    # GitHub evicts a cache not used for 7 days: the next run has no history.
    project.evict_the_cache()
    again = project.scheduled_run()
    assert again["baseline"] is True
    assert len(project.delivered) == 1  # the known deprecation is not sent a second time
