"""Dependency-Track uploader (core/dtrack.py) - offline, MockTransport."""

import json

import httpx
import pytest
from click.testing import CliRunner

from cli.main import cli
from core import dtrack

PROJECT = "11111111-2222-3333-4444-555555555555"


def _contracts(tmp_path):
    out = tmp_path / "contracts.jsonl"
    result = CliRunner().invoke(
        cli,
        [
            "attest",
            "--manifest",
            "data/fixtures/manifests/requirements.txt",
            "--images",
            "data/fixtures/images/inventory_sample.txt",
            "--event",
            "data/fixtures/django-eol/event.json",
            "--event",
            "data/fixtures/bitnami/event.json",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    return out, [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]


class FakeDT:
    """Minimal Dependency-Track: records calls, knows some components."""

    def __init__(self, components, existing=()):
        self.components = components  # (name, version) -> uuid
        self.vulns = set(existing)
        self.calls = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, request.url.path, dict(request.url.params)))
        assert request.headers.get("X-Api-Key") == "k"
        path = request.url.path
        if request.method == "PUT" and path == "/api/v1/vulnerability":
            body = json.loads(request.content)
            if body["vulnId"] in self.vulns:
                return httpx.Response(409, text="exists")
            self.vulns.add(body["vulnId"])
            return httpx.Response(201, json=body)
        if request.method == "GET" and path == "/api/v1/component/identity":
            params = request.url.params
            assert params["project"] == PROJECT
            uuid = self.components.get((params.get("name"), params.get("version")))
            return httpx.Response(200, json=[{"uuid": uuid}] if uuid else [])
        if request.method == "POST" and "/component/" in path:
            return httpx.Response(200)
        if request.method == "GET" and path == "/api/v1/project/lookup":
            return httpx.Response(200, json={"uuid": PROJECT})
        return httpx.Response(404)


def _client(fake):
    return httpx.Client(
        base_url="https://dt.example",
        headers={"X-Api-Key": "k"},
        transport=httpx.MockTransport(fake),
    )


def test_plan_pushes_only_affected_pairs_one_vuln_per_event(tmp_path):
    _, docs = _contracts(tmp_path)
    planned = dtrack.plan(docs)
    ids = [p["vulnerability"]["vulnId"] for p in planned]
    assert ids == sorted(set(ids))
    assert "OPENPULSE-evt-django-2026-eol-001" in ids
    affected = {
        (d["event_context"]["id"], d["affected_dependency"]["label"])
        for d in docs
        if d["assessment"]["affected"]
    }
    planned_pairs = {
        (p["vulnerability"]["vulnId"].removeprefix("OPENPULSE-"), c["label"])
        for p in planned
        for c in p["components"]
    }
    assert planned_pairs == affected


def test_vulnerability_payload(tmp_path):
    _, docs = _contracts(tmp_path)
    django = next(
        p for p in dtrack.plan(docs) if p["vulnerability"]["vulnId"].endswith("django-2026-eol-001")
    )
    vuln = django["vulnerability"]
    assert vuln["source"] == "INTERNAL"
    assert vuln["severity"] == "HIGH"
    assert "* https://endoflife.date/django" in vuln["references"].splitlines()
    assert vuln["recommendation"]
    assert django["components"][0]["identity"] == {"name": "django", "version": "4.2"}


def test_upload_creates_assigns_and_reports_missing(tmp_path):
    _, docs = _contracts(tmp_path)
    fake = FakeDT({("django", "4.2"): "c-django"})
    report = dtrack.upload(_client(fake), PROJECT, dtrack.plan(docs))
    assert "OPENPULSE-evt-django-2026-eol-001" in report["created"]
    assert "OPENPULSE-evt-django-2026-eol-001 -> django==4.2" in report["assigned"]
    assert report["not_found"]  # bitnami images are not components of this fake project
    assert report["errors"] == []
    assigned = [c for c in fake.calls if c[0] == "POST"]
    assert assigned[0][1] == (
        "/api/v1/vulnerability/source/INTERNAL/vuln/OPENPULSE-evt-django-2026-eol-001"
        "/component/c-django"
    )


def test_rerun_reuses_existing_vulnerability(tmp_path):
    _, docs = _contracts(tmp_path)
    fake = FakeDT({("django", "4.2"): "c"}, existing={"OPENPULSE-evt-django-2026-eol-001"})
    report = dtrack.upload(_client(fake), PROJECT, dtrack.plan(docs))
    assert "OPENPULSE-evt-django-2026-eol-001" in report["existing"]
    assert "OPENPULSE-evt-django-2026-eol-001 -> django==4.2" in report["assigned"]


def test_server_errors_are_reported_without_the_api_key(tmp_path):
    _, docs = _contracts(tmp_path)

    def broken(request):
        return httpx.Response(500, text="boom")

    report = dtrack.upload(_client(broken), PROJECT, dtrack.plan(docs))
    assert report["errors"]
    assert all("k" != e and "X-Api-Key" not in e for e in report["errors"])


@pytest.mark.parametrize(
    "label,coords",
    [
        ("django==4.2", {"name": "django", "version": "4.2"}),
        ("com.itextpdf:itext-core==8.0.2", {"group": "com.itextpdf", "name": "itext-core",
                                            "version": "8.0.2"}),
        ("@angular/core==17.0.0", {"group": "@angular", "name": "core", "version": "17.0.0"}),
        ("docker.io/bitnami/redis:7.2", {"name": "redis", "version": "7.2"}),
        ("postgres:13", {"name": "postgres", "version": "13"}),
        ("localhost:5000/team/app:1.0", {"name": "app", "version": "1.0"}),
        ("docker.io/redis@sha256:" + "a" * 64, {"name": "redis"}),
    ],
)
def test_coordinates(label, coords):
    assert dtrack._coordinates(label) == coords


@pytest.mark.parametrize(
    "url,ok",
    [
        ("https://dt.example", True),
        ("https://dt.example:8443/sub/", True),
        ("http://dt.example", False),
        ("https://user:pw@dt.example", False),
        ("https://dt.example/?x=1", False),
        ("ftp://dt.example", False),
    ],
)
def test_url_policy(url, ok):
    if ok:
        assert dtrack.check_url(url).startswith("https://")
    else:
        with pytest.raises(ValueError):
            dtrack.check_url(url)
    assert dtrack.check_url("http://dt.example", allow_http=True) == "http://dt.example"


def test_cli_dry_run_sends_nothing(tmp_path, monkeypatch):
    path, _ = _contracts(tmp_path)
    monkeypatch.delenv(dtrack.API_KEY_ENV, raising=False)
    result = CliRunner().invoke(cli, ["dependency-track", "--contracts", str(path), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "OPENPULSE-evt-django-2026-eol-001 [HIGH]" in result.output


def test_cli_requires_the_api_key_from_the_environment(tmp_path, monkeypatch):
    path, _ = _contracts(tmp_path)
    monkeypatch.delenv(dtrack.API_KEY_ENV, raising=False)
    result = CliRunner().invoke(
        cli,
        ["dependency-track", "--contracts", str(path), "--url", "https://dt.example",
         "--project-uuid", PROJECT],
    )
    assert result.exit_code != 0
    assert dtrack.API_KEY_ENV in result.output
