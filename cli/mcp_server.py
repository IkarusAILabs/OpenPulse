"""`openpulse mcp` - OpenPulse as an MCP server for AI coding agents.

Exposes the SDK-free tools in :mod:`core.agent_tools` over the official
MCP Python SDK (optional extra ``ikarus-openpulse[mcp]``, see docs/MCP.md), stdio
transport. Agents (Claude Code, Cursor, Copilot, ...) can ask, before they
add or upgrade a dependency, whether it is end-of-life, affected by an
upstream distribution/license/support change, or has advisories for the
exact version - with the evidence behind each answer.

Security posture:
- every tool is read-only; nothing is executed, and nothing is written
  except, when the user passes ``--record DIR``, the local record files
  (:mod:`core.agent_record`; opt-in, never sent anywhere);
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

    from core.agent_tools import BudgetExhausted

    try:
        return call()
    except (ValueError, OSError, BudgetExhausted) as exc:
        raise ToolError(str(exc)) from exc


def build_server(
    root: str | Path = ".", live: bool = True, lookups: Any = None, record: Any = None
) -> Any:
    """The configured MCPServer (separate from `run` so tests can drive it).

    One ``Lookups`` per server session: its budget and cache span every call.
    ``lookups`` is injectable for offline tests. ``record`` is a directory
    (or a :class:`core.agent_record.Recorder`) for opt-in local recording.
    """
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    from core import agent_tools
    from core.version import openpulse_version

    project_root = Path(root).resolve()
    if lookups is None and live:
        lookups = agent_tools.Lookups(cache_dir=agent_tools.default_cache_dir())
    read_only = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=live)
    server = MCPServer(
        name="openpulse",
        title="OpenPulse dependency intelligence",
        instructions=INSTRUCTIONS,
        version=openpulse_version(),
    )

    recorder = record
    if record is not None and not hasattr(record, "record"):
        from core.agent_record import Recorder

        recorder = Recorder(record, version=openpulse_version())

    def answered(
        tool: str, arguments: dict[str, Any], call: Callable[[], dict[str, Any]]
    ) -> dict[str, Any]:
        """Run one tool and, when recording, append the call; never alters the answer."""
        try:
            result = _answer(call)
        except Exception as exc:
            if recorder is not None:
                recorder.record(tool, arguments, error=str(exc))
            raise
        if recorder is not None:
            recorder.record(tool, arguments, answer=result)
        return result

    def private_names() -> frozenset[tuple[str, str]] | None:
        """The user's private-name list under the root, read per call (T-A3)."""
        from core import dependency_confusion

        path = project_root / dependency_confusion.DEFAULT_LIST
        return dependency_confusion.load(path)[0] if path.is_file() else None

    @server.tool(annotations=read_only)
    def dependency_status(
        package: str = "",
        version: str = "",
        ecosystem: str = "",
        image: str = "",
        intent: str = "",
        name_source: str = "",
    ) -> dict[str, Any]:
        """Evidence for ONE dependency: end-of-life / end-of-support for its version,
        curated upstream changes (distribution, license, support) and OSV advisories.

        `trust` holds every trust check for a PyPI or npm package, never part of the
        verdict: a malicious-package record (`malicious`), whether the package and
        version exist in their registry (`registry_existence`: a name not found may be
        hallucinated), PyPI provenance, whether it is from the repository it claims
        (`repository_linkage`), lookalike names, and, for names on the project's
        private-name list, a public package with the same name (`dependency_confusion`).
        Review everything under `trust.attention`.

        Give either `package` (+ `ecosystem` such as PyPI, npm, Maven, Go, crates.io,
        and an exact `version`) or a container `image` ref such as `postgres:13`.
        Optionally say why you are asking: `intent` (a short sentence) and
        `name_source` (one of user_request, existing_code, documentation,
        search_result, model_suggestion, other). They are recorded in
        `trust.selection_context` and never change any status or verdict."""
        arguments = {
            "package": package,
            "version": version,
            "ecosystem": ecosystem,
            "image": image,
            "intent": intent,
            "name_source": name_source,
        }
        return answered(
            "dependency_status",
            arguments,
            lambda: agent_tools.dependency_status(
                package or None,
                version or None,
                ecosystem or None,
                image or None,
                lookups=lookups,
                live=live,
                private_names=private_names(),
                intent=intent or None,
                name_source=name_source or None,
            )
        )

    @server.tool(annotations=read_only)
    def check_dependency_file(
        path: str, base_path: str = "", trust_all: bool = False
    ) -> dict[str, Any]:
        """Check every pinned dependency in a manifest (requirements.txt, pyproject.toml,
        pom.xml, go.mod, Cargo.toml), lockfile (package-lock.json, poetry.lock,
        Cargo.lock), CycloneDX/SPDX SBOM or image list, relative to the project root.
        Unpinned entries are listed as skipped, never guessed.

        `base_path` is an earlier copy of the same file (for example the version
        before your edit): the PyPI and npm dependencies added or changed since then
        get trust checks in `trust` (known-malicious records, registry existence,
        provenance, lookalike names, and dependency confusion for names on the
        project's private-name list).
        `trust_all` runs them on every dependency instead. Trust checks are never part
        of the verdict; review anything listed under `trust.attention`."""
        return answered(
            "check_dependency_file",
            {"path": path, "base_path": base_path, "trust_all": trust_all},
            lambda: agent_tools.check_dependency_file(
                _confined(project_root, path),
                lookups=lookups,
                live=live,
                base_path=_confined(project_root, base_path) if base_path else None,
                trust_all=trust_all,
                private_names=private_names(),
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

        return answered("project_lifecycle", {"project": project}, lifecycle)

    return server


def run(root: str | Path = ".", live: bool = True, record: str | Path | None = None) -> None:
    build_server(root, live, record=record).run()
