"""The GitHub Action's pre-install gate: its ``gate`` input (v0.15.0 item Z3).

Runs ``openpulse gate`` on each file of the ``gate`` input, before the
workflow installs anything. On a pull request each file is compared with
its copy on the base commit, read through the contents API like the trust
checks (``scripts/action_base_files.py``), so a shallow checkout is enough.
The policy and the private-name list also come from the base branch when it
has them: a pull request cannot weaken its own gate.

Inputs arrive as environment variables, never on the command line:

- ``IN_GATE``: whitespace-separated dependency files;
- ``IN_POLICY``: the policy path (empty: ``.openpulse/policy.yml``);
- ``IN_BASE_SHA``: the base commit (empty outside pull requests);
- ``GITHUB_REPOSITORY``, ``GITHUB_TOKEN``, ``GITHUB_OUTPUT``, ``RUNNER_TEMP``.

Each file's gate writes a receipt (v0.17.0 item G2) into a fresh directory,
named in the ``receipts`` output: a later step runs
``openpulse gate --verify-receipt <that directory> FILE...`` immediately
before installing, and refuses any file that changed since the gate.

A base file that cannot be read never narrows the checks: that file is
checked in full. Exit 0 when the gate ran (``threshold-breached`` in
``GITHUB_OUTPUT`` says whether it found a violation), 2 on a usage error.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import action_base_files  # noqa: E402

DEFAULT_POLICY = ".openpulse/policy.yml"
DEFAULT_PRIVATE = ".openpulse/private-packages.txt"


def _gate(args: list[str]) -> int:
    """`openpulse gate` in process: its exit code."""
    import click

    from cli.main import cli

    try:
        cli.main(args, prog_name="openpulse", standalone_mode=False)
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def _repository_file(path: str) -> bool:
    """A path the contents API can name: relative, inside the repository."""
    return bool(path) and action_base_files._clean_path(path) is not None


def run(
    files: list[str],
    *,
    repo: str,
    base_sha: str,
    policy: str,
    token: str,
    out_dir: str,
    get: action_base_files.Get | None = None,
    receipt_dir: str | None = None,
) -> tuple[int, bool]:
    """(exit code, threshold breached) for the gate over ``files``."""
    if not files:
        print("::error title=OpenPulse gate::the gate input names no file")
        return 2, False
    bases: dict[int, str] = {}
    policy_path = policy or DEFAULT_POLICY
    private_path = DEFAULT_PRIVATE if Path(DEFAULT_PRIVATE).is_file() else ""
    if base_sha:
        settings = [p for p in (policy_path, DEFAULT_PRIVATE) if _repository_file(p)]
        fetched = action_base_files.fetch(repo, base_sha, out_dir, files + settings, token, get)
        for index, (status, path, base) in enumerate(fetched):
            if index < len(files):
                if status == "found":
                    bases[index] = base
                elif status == "unavailable":
                    print(
                        f"::warning title=OpenPulse gate::could not read the base copy of "
                        f"{path}; checking every dependency in it"
                    )
            elif status == "found":
                if path == DEFAULT_PRIVATE:
                    private_path = base
                else:
                    print("OpenPulse gate: using the base branch's trust policy")
                    policy_path = base
            elif status == "unavailable":
                print(
                    "::warning title=OpenPulse gate::could not read the base branch's "
                    f"{path}; using this pull request's copy"
                )
    else:
        print("OpenPulse gate: no base commit (not a pull request), every dependency is checked")

    codes = []
    for index, path in enumerate(files):
        args = ["gate", path]
        if index in bases:
            args += ["--base", bases[index]]
        if policy or Path(policy_path).is_file():
            args += ["--policy", policy_path]
        if private_path:
            args += ["--private-names", private_path]
        if receipt_dir:
            args += ["--receipt", str(Path(receipt_dir) / f"receipt-{index}.json")]
        codes.append(_gate(args))
    if any(code not in (0, 1) for code in codes):
        return 2, False
    return 0, 1 in codes


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)  # notices in order with the gate's stderr
    files = os.environ.get("IN_GATE", "").split()
    # Threat: the job token reaching the trust lookups - only the base-file
    # reads use it, as in the attest step.
    token = os.environ.pop("GITHUB_TOKEN", "")
    scratch = tempfile.mkdtemp(prefix="openpulse-gate-base-", dir=os.environ.get("RUNNER_TEMP"))
    receipts = tempfile.mkdtemp(
        prefix="openpulse-gate-receipts-", dir=os.environ.get("RUNNER_TEMP")
    )
    code, breached = run(
        files,
        repo=os.environ.get("GITHUB_REPOSITORY", ""),
        base_sha=os.environ.get("IN_BASE_SHA", ""),
        policy=os.environ.get("IN_POLICY", ""),
        token=token,
        out_dir=scratch,
        receipt_dir=receipts,
    )
    output = os.environ.get("GITHUB_OUTPUT")
    if output and code == 0:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"threshold-breached={'true' if breached else 'false'}\n")
            fh.write(f"receipts={receipts}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
