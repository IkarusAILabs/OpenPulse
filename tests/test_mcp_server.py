"""`openpulse mcp` over the official MCP SDK (optional extra).

Skipped when the SDK is absent (the main CI job); CI's `mcp` job installs
requirements-mcp.lock and runs this file for real.
"""

import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp.server.mcpserver")

import anyio  # noqa: E402  (installed with the SDK)

from cli.mcp_server import build_server  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def _call(server, name, args):
    return anyio.run(server.call_tool, name, args)


def test_tools_are_listed_read_only():
    server = build_server(REPO, live=False)
    tools = {t.name: t for t in anyio.run(server.list_tools)}
    assert set(tools) == {"dependency_status", "check_dependency_file", "project_lifecycle"}
    for tool in tools.values():
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.destructive_hint is False
        assert tool.annotations.open_world_hint is False  # --offline


def test_dependency_status_returns_structured_evidence():
    server = build_server(REPO, live=False)
    result = _call(
        server, "dependency_status", {"package": "django", "version": "4.2", "ecosystem": "PyPI"}
    )
    assert result.is_error is False
    payload = result.structured_content
    if "result" in payload and "verdict" not in payload:
        payload = payload["result"]
    assert payload["verdict"]["affected"] is True
    assert payload["causes"][0]["event"] == "evt-django-2026-eol-001"


def test_file_checks_stay_inside_the_project_root(tmp_path):
    outside = tmp_path / "requirements.txt"
    outside.write_text("django==4.2\n", encoding="utf-8")
    server = build_server(REPO, live=False)
    with pytest.raises(Exception, match="outside the server's project root"):
        _call(server, "check_dependency_file", {"path": str(outside)})
    with pytest.raises(Exception, match="outside the server's project root"):
        _call(server, "check_dependency_file", {"path": "../" + outside.name})


def test_file_check_inside_root_works():
    server = build_server(REPO, live=False)
    result = _call(
        server, "check_dependency_file", {"path": "data/fixtures/manifests/requirements.txt"}
    )
    payload = result.structured_content
    if "result" in payload and "affected" not in payload:
        payload = payload["result"]
    assert payload["affected"] == ["django==4.2"]


def test_stdio_end_to_end_with_the_sdk_client(tmp_path):
    """A real MCP client talks to `openpulse mcp --offline` over stdio.

    Launched the way docs/MCP.md documents it - interpreter + safe-path
    flag + `-m cli` - from a directory that is NOT the OpenPulse checkout,
    as real clients do (they start servers inside the user's project).
    """
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    safe_path = "-P" if sys.version_info >= (3, 11) else "-I"
    params = StdioServerParameters(
        command=sys.executable,
        args=[safe_path, "-m", "cli", "mcp", "--offline", "--root", str(REPO)],
        cwd=str(tmp_path),
    )

    async def session():
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                init = await client.initialize()
                assert init.server_info.name == "openpulse"
                names = {t.name for t in (await client.list_tools()).tools}
                assert "dependency_status" in names
                result = await client.call_tool(
                    "dependency_status", {"image": "docker.io/bitnami/redis:7.2"}
                )
                assert result.is_error is False
                return result

    result = anyio.run(session)
    text = "".join(getattr(block, "text", "") for block in result.content)
    assert "bitnami-redis-stack" in text


def test_offline_lifecycle_explains_why():
    server = build_server(REPO, live=False)
    with pytest.raises(Exception, match="needs live lookups"):
        _call(server, "project_lifecycle", {"project": "django"})
