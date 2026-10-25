"""Allow running openpulse directly via `python -m cli`.

MCP clients that cannot find the `openpulse` executable launch the
interpreter instead. They must pass `-I` (or `-P` on 3.11+): a bare
`python -m cli` searches the working directory first, so a project's own
`cli/` package would run instead of this one (docs/MCP.md).
"""

from cli.main import cli

if __name__ == "__main__":
    # prog_name keeps usage and error lines saying `openpulse`, not `python -m cli`.
    cli(prog_name="openpulse")
