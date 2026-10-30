"""`openpulse mcp` - OpenPulse as an MCP server for AI coding agents.

Exposes the SDK-free tools in :mod:`core.agent_tools` over the official
MCP Python SDK (optional extra ``ikarus-openpulse[mcp]``, see docs/MCP.md), stdio
transport. Agents (Claude Code, Cursor, Copilot, ...) can ask, before they
add or upgrade a dependency, whether it is end-of-life, affected by an
upstream distribution/license/support change, or has advisories for the
exact version - with the evidence behind each answer.

Security posture:
- every tool is read-only; nothing is written, nothing is executed;
- file checks are confined to the server's project root (the directory
  it was started in, or ``--root``): a prompt-injected agent cannot use
  the server to parse files elsewhere on the machine;
- network access is limited to the public lifecycle/advisory APIs the
  collectors already use; ``--offline`` disables it entirely.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

INSTRUCTIONS = (
    "OpenPulse answers whether a software dependency is end-of-life, affected by an "
    "upstream change (distribution, license, support model) or has advisories for its "
    "exact version, with the evidence. Call dependency_status before adding or upgrading "
    "a dependency, check_dependency_file after editing a manifest or lockfile, and "
    "project_lifecycle to pick a supported release line. Verdicts are evidence, not "
    "decisions: UNKNOWN means not established, never safe, and NOT_AFFECTED is not a "
    "clearance. Answers are current assessments: a negative needs evidence within the "
    "freshness bound stated in evaluation_context."
)


def _confined(root: Path, path: str) -> str:
    """Resolve ``path`` inside ``root``; refuse anything that escapes it."""
    candidate = (root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"{path}: outside the server's project root ({root})")
    return str(candidate)


def _answer(call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Run one tool; expected failures reach the agent with their reason.

    The SDK reports any other exception as an opaque "Error executing tool",
    so input problems (bad path, unrecognized file, missing package name)
    are re-raised as ToolError carrying the message.
    """
    from mcp.server.mcpserver.exceptions import ToolError

    try:
        return call()
    except (ValueError, OSError) as exc:
        raise ToolError(str(exc)) from exc


def build_server(root: str | Path = ".", live: bool = True) -> Any:
    """The configured MCPServer (separate from `run` so tests can drive it)."""
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    from core import agent_tools
    from core.version import openpulse_version

    project_root = Path(root).resolve()
    lookups = agent_tools.Lookups() if live else None
    read_only = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=live)
    server = MCPServer(
        name="openpulse",
        title="OpenPulse dependency intelligence",
        instructions=INSTRUCTIONS,
        version=openpulse_version(),
    )

    @server.tool(annotations=read_only)
    def dependency_status(
        package: str = "", version: str = "", ecosystem: str = "", image: str = ""
    ) -> dict[str, Any]:
        """Evidence for ONE dependency: end-of-life / end-of-support for its version,
        curated upstream changes (distribution, license, support) and OSV advisories.

        Give either `package` (+ `ecosystem` such as PyPI, npm, Maven, Go, crates.io,
        and an exact `version`) or a container `image` ref such as `postgres:13`.
        """
        return _answer(
            lambda: agent_tools.dependency_status(
                package or None,
                version or None,
                ecosystem or None,
                image or None,
                lookups=lookups,
                live=live,
            )
        )

    @server.tool(annotations=read_only)
    def check_dependency_file(path: str) -> dict[str, Any]:
        """Check every pinned dependency in a manifest (requirements.txt, pyproject.toml,
        pom.xml, go.mod, Cargo.toml), lockfile (package-lock.json, poetry.lock,
        Cargo.lock), CycloneDX/SPDX SBOM or image list, relative to the project root.
        Unpinned entries are listed as skipped, never guessed."""
        return _answer(
            lambda: agent_tools.check_dependency_file(
                _confined(project_root, path), lookups=lookups, live=live
            )
        )

    @server.tool(annotations=read_only)
    def project_lifecycle(project: str) -> dict[str, Any]:
        """Release cycles of a project (e.g. `django`, `nodejs`, `postgresql`) with
        their end-of-life dates and which lines are still supported today."""
        def lifecycle() -> dict[str, Any]:
            if not live:
                raise ValueError("project_lifecycle needs live lookups (server runs --offline)")
            return agent_tools.project_lifecycle(project, lookups=lookups)

        return _answer(lifecycle)

    return server


def run(root: str | Path = ".", live: bool = True) -> None:
    build_server(root, live).run()
