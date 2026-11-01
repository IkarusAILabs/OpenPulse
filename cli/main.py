"""openpulse CLI — validate + pulse + analyze + demo-bitnami."""

import json
import sys
from typing import Any

import click

from analyzers import change_analyst, report_analyst, security_analyst
from core.entities.resolve import resolve_project
from core.schema.models import OSSEvent
from core.version import openpulse_version


@click.group()
@click.version_option(version=openpulse_version(), prog_name="openpulse")
def cli():
    _check_catalog()


def _check_catalog() -> None:
    """Fail every command cleanly on a broken catalog, before any verdict (#144)."""
    from core.entities.catalog import CatalogCollisionError, catalog_alias_map, load_catalog

    try:
        catalog_alias_map(load_catalog())
    except FileNotFoundError:
        pass  # no catalog: identity resolution falls back to self, as documented
    except CatalogCollisionError as exc:
        raise click.ClickException(
            f"{exc}. Fix data/canonical_projects.yaml so each alias and image "
            "names one project."
        ) from exc


MAX_INPUT_BYTES = 1_000_000
MAX_EVIDENCES = 100
MAX_ARTIFACTS = 500


def _resolve_github_token(
    github_repo: str, github_token: str, github_token_file: str | None
) -> str | None:
    """Resolve CLI credentials while keeping token values out of output.

    Only a run that inspects a repository needs a token: without
    ``--github-repo`` the token file is never opened, so a stale or
    rotated path in shared cron/CI flags cannot fail an unrelated run.
    """
    from core.github_reader import get_github_token

    if github_token:
        _echo(
            "warning: --github-token is deprecated; use GITHUB_TOKEN or "
            "--github-token-file instead",
            err=True,
        )
    if not github_repo:
        return None
    try:
        return get_github_token(github_token, github_token_file)
    except OSError as exc:
        raise click.ClickException(f"cannot read GitHub token file: {exc.strerror or exc}") from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


def _history_key_option(func):
    """--history-key-file and --history-previous-keys-file (B3, B3b)."""
    func = click.option(
        "--history-previous-keys-file",
        default=None,
        type=click.Path(dir_okay=False),
        help=(
            "File of retired history keys, one per line, used only to verify "
            "and hand over (else OPENPULSE_HISTORY_KEYS_PREVIOUS)"
        ),
    )(func)
    return click.option(
        "--history-key-file",
        default=None,
        type=click.Path(dir_okay=False),
        help=(
            "File holding the history key that MACs local history "
            "(else OPENPULSE_HISTORY_KEY; see: openpulse history-key generate)"
        ),
    )(func)


def _load_history_key(key_file: str | None, previous_file: str | None, *store_roots: str):
    """(current key or None, retired keys). Never echoes key material."""
    from core.history_key import (
        HistoryKeyError,
        key_file_warning,
        load_history_key,
        load_previous_keys,
    )

    roots = tuple(r for r in store_roots if r)
    try:
        key = load_history_key(key_file, roots)
        previous = load_previous_keys(previous_file, roots, current=key)
    except OSError as exc:
        raise click.ClickException(f"cannot read history key file: {exc.strerror or exc}") from exc
    except HistoryKeyError as exc:
        raise click.ClickException(str(exc)) from exc
    if previous and key is None:
        raise click.ClickException(
            "previous history keys need a current key (OPENPULSE_HISTORY_KEY or "
            "--history-key-file): retired keys only verify and hand over"
        )
    for path in (key_file, previous_file):
        if path and (warning := key_file_warning(path)):
            _echo(warning, err=True)
    return key, previous


def _history_keyring(key_file: str | None, previous_file: str | None, *store_roots: str):
    """key_id -> HistoryKey (current and retired) for reading keyed history."""
    from core.history_key import keyring

    return keyring(*_load_history_key(key_file, previous_file, *(r for r in store_roots if r)))


def _sarif_uri(path: str) -> str:
    """SARIF artifact uri for an input file: relative to the working
    directory (the repository root in CI) when possible, POSIX slashes."""
    from pathlib import Path as _Path

    candidate = _Path(path)
    try:
        candidate = candidate.resolve().relative_to(_Path.cwd().resolve())
    except ValueError:
        pass
    return candidate.as_posix()


def _load_json(path: str) -> dict:
    """Bounded JSON load: size cap + clean errors (no tracebacks to users)."""
    from core.bounded_io import loads_json, read_text

    try:
        return loads_json(read_text(path, MAX_INPUT_BYTES, path), path)
    except OSError as e:
        raise click.ClickException(f"cannot read {path}: {e.strerror or e}")
    except json.JSONDecodeError as e:
        raise click.ClickException(f"{path} is not valid JSON: {e}")
    except UnicodeDecodeError:
        raise click.ClickException(f"{path} is not UTF-8 text")
    except ValueError as e:  # over the size cap, or nests too deeply
        raise click.ClickException(str(e))


#: Raw collector bundles are legitimately multi-MB: same cap as SBOMs.
MAX_BUNDLE_BYTES = 50 * 1024 * 1024


def _load_bundle(path) -> dict:
    """Bounded raw-bundle load (`--raw-bundle-dir`), clean errors."""
    from core.bounded_io import loads_json, read_text

    try:
        return loads_json(read_text(str(path), MAX_BUNDLE_BYTES, str(path)), str(path))
    except OSError as e:
        raise click.ClickException(f"cannot read {path}: {e.strerror or e}")
    except UnicodeDecodeError:
        raise click.ClickException(f"{path} is not UTF-8 text")
    except ValueError as e:  # invalid JSON, over the cap, or nests too deeply
        raise click.ClickException(f"{path}: {e}")


def _load_event(path: str) -> OSSEvent:
    from pydantic import ValidationError

    data = _load_json(path)
    if isinstance(data, dict):
        if len(data.get("evidences", [])) > MAX_EVIDENCES:
            raise click.ClickException(f"too many evidences (limit {MAX_EVIDENCES})")
        if len(data.get("affected_artifacts", [])) > MAX_ARTIFACTS:
            raise click.ClickException(f"too many artifacts (limit {MAX_ARTIFACTS})")
    try:
        return OSSEvent(**data)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(p) for p in first["loc"])
        raise click.ClickException(f"{path} fails schema at `{loc}`: {first['msg']}")


@cli.command()
@click.option("--event", required=True, help="Path to OSSEvent JSON fixture")
@click.option("--strict", is_flag=True, help="Fail if evidence gate violations exist")
def validate(event, strict):
    e = _load_event(event)
    from core.evidence.policy import gate

    violations = gate(e)
    _echo(
        f"OK {e.id} [{e.event_type.value}] confidence={e.confidence.value} impact={e.impact.value}"
    )
    if violations:
        _echo("GATE VIOLATIONS:")
        for v in violations:
            _echo(f"  - {v}")
        if strict:
            raise SystemExit(1)
    else:
        _echo("gate: PASS")


@cli.command()
@click.option("--project", required=True, help="Project slug or artifact ref")
@click.option("--show-signals", is_flag=True, help="Show facet signals (always shown)")
@click.option(
    "--raw-bundle", type=click.Path(exists=True), help="Offline raw collector bundle JSON"
)
def pulse(project, show_signals, raw_bundle):
    """OSS Pulse: computed facet status for one project (live or offline bundle)."""
    from core.entities.catalog import project_context
    from core.pulse import compute_pulse, format_pulse

    slug = resolve_project(project)
    if raw_bundle:
        raw = _load_json(raw_bundle)
    else:
        raw = _live_bundle(slug)
    findings = change_analyst.analyze(raw)
    findings += security_analyst.correlate(raw, project_context(slug))
    metas = [e for e in raw.get("github_meta", []) if e.get("kind") == "repo_meta"]
    activity = {"releases": raw.get("github", []), "repo_meta": metas[0] if metas else None}
    _echo(format_pulse(compute_pulse(slug, findings=findings, activity=activity)))


def _live_bundle(slug):
    """Run live collectors; each degrades to error/skipped dicts, never raises."""
    import os as _os

    from collectors.endoflife.collector import EndoflifeCollector
    from collectors.github.collector import GitHubCollector
    from collectors.kev.collector import KEVCollector
    from collectors.nvd.collector import NVDCollector
    from collectors.osv.collector import OSVCollector
    from collectors.registries.docker import RegistryCollector
    from collectors.registries.reference import bitnami_distribution_probes
    from core.entities.catalog import endoflife_map, load_catalog, osv_map

    token = _os.environ.get("GITHUB_TOKEN") or _os.environ.get("GH_TOKEN")
    repo_map = {e["slug"]: e["github"] for e in load_catalog() if e.get("github")}
    github = GitHubCollector(repo_map, token=token)
    registries = RegistryCollector()
    endoflife = EndoflifeCollector(endoflife_map())
    osv = OSVCollector(osv_map())
    return {
        "endoflife": endoflife.collect(slug),
        "github": github.collect(slug),
        "github_meta": [github.fetch_repo_meta(slug)],
        "nvd": NVDCollector().collect(slug),
        "kev": KEVCollector().collect(slug),
        "osv": osv.collect(slug),
        # Bitnami is a rehearsed reference scenario, not generic acquisition.
        "registries": bitnami_distribution_probes(registries)
        if slug == "bitnami"
        else registries.collect(slug),
    }


@cli.command()
@click.option("--project", required=True, help="Project slug or artifact ref")
@click.option(
    "--raw-bundle", type=click.Path(exists=True), help="Offline raw collector bundle JSON"
)
@click.option(
    "--version",
    "project_version",
    default=None,
    help="Deployed version (enables version-applicability checks)",
)
def analyze(project, raw_bundle, project_version):
    """Run analysts over live collectors (or an offline bundle) and print findings."""
    slug = resolve_project(project)
    if raw_bundle:
        raw = _load_json(raw_bundle)
        _echo(f"bundle: {raw_bundle}")
    else:
        raw = _live_bundle(slug)
        for name, entries in raw.items():
            problems = [e for e in entries if e.get("error") or e.get("skipped")]
            _echo(f"collector {name}: {len(entries)} records ({len(problems)} error/skipped)")
    change = change_analyst.analyze(raw)
    from core.entities.catalog import project_context

    context = project_context(slug)
    if project_version:
        context["version"] = project_version
    security = security_analyst.correlate(raw, context)
    _echo(f"\n## Change findings ({len(change)})")
    for finding in change:
        _echo("\n" + report_analyst.render_finding_md(finding))
    _echo(f"\n## Security findings ({len(security)})")
    for finding in security[:10]:
        _echo("\n" + report_analyst.render_finding_md(finding))
    _echo("\nnote: findings are proposals — Evidence Analyst + gate decide events.")


@cli.command(name="mcp")
@click.option(
    "--root",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    show_default=True,
    help="Project root: check_dependency_file only reads files inside it",
)
@click.option(
    "--offline",
    is_flag=True,
    help="No network: answer from the bundled curated events only",
)
def mcp_command(root, offline):
    """MCP server (stdio) for AI coding agents: dependency evidence as tools.

    Needs the optional `mcp` extra (see docs/MCP.md).
    """
    try:
        import mcp.server.mcpserver  # noqa: F401  (optional SDK present?)
    except ImportError:
        from core.version import install_hint

        raise click.ClickException(
            f"the MCP server needs the optional SDK: {install_hint('mcp')}"
        ) from None
    from cli.mcp_server import run

    run(root=root, live=not offline)


@cli.command(name="dependency-track")
@click.option(
    "--contracts",
    "contracts_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Evidence-contract JSONL written by `openpulse attest --output`",
)
@click.option("--url", default="", help="Dependency-Track base URL (e.g. https://dtrack.example)")
@click.option("--project-uuid", default="", help="Target project UUID")
@click.option("--project-name", default="", help="Target project name (with --project-version)")
@click.option("--project-version", default="", help="Target project version")
@click.option("--dry-run", is_flag=True, help="Print the plan; send nothing")
@click.option("--allow-http", is_flag=True, help="Opt in to a plain-http Dependency-Track URL")
@click.option("--timeout", default=30.0, show_default=True, help="Per-request timeout (seconds)")
def dependency_track(
    contracts_path, url, project_uuid, project_name, project_version, dry_run, allow_http, timeout
):
    """Push affected findings into Dependency-Track as INTERNAL vulnerabilities.

    One vulnerability per OpenPulse event (OPENPULSE-<event id>), assigned to the
    project's matching components. API key from the OPENPULSE_DTRACK_API_KEY
    environment variable (never argv); needs VULNERABILITY_MANAGEMENT and
    PORTFOLIO_MANAGEMENT.
    """
    import os

    import httpx

    from core import dtrack
    from core.bounded_io import read_text

    try:
        text = read_text(contracts_path, MAX_BUNDLE_BYTES, contracts_path)
        docs = [json.loads(line) for line in text.splitlines() if line.strip()]
    except (OSError, ValueError) as e:
        raise click.ClickException(f"{contracts_path}: {e}")
    planned = dtrack.plan(docs)
    pairs = sum(len(p["components"]) for p in planned)
    _echo(f"plan: {len(planned)} vulnerability(ies), {pairs} affected component(s)")
    if dry_run:
        for item in planned:
            vuln = item["vulnerability"]
            _echo(f"  {vuln['vulnId']} [{vuln['severity']}] {vuln['title']}")
            for component in item["components"]:
                _echo(f"    -> {component['label']} {component['identity']}")
        return
    if not planned:
        _echo("nothing affected: nothing to push")
        return
    api_key = os.environ.get(dtrack.API_KEY_ENV, "")
    if not api_key:
        raise click.ClickException(
            f"set {dtrack.API_KEY_ENV} (the API key is never read from argv)"
        )
    try:
        base = dtrack.check_url(url, allow_http=allow_http)
    except ValueError as e:
        raise click.ClickException(str(e))
    if not project_uuid and not (project_name and project_version):
        raise click.ClickException("give --project-uuid, or --project-name and --project-version")
    with httpx.Client(
        base_url=base,
        headers={"X-Api-Key": api_key, "User-Agent": "openpulse-dtrack"},
        timeout=timeout,
        follow_redirects=False,
    ) as client:
        try:
            uuid = project_uuid or dtrack.lookup_project(client, project_name, project_version)
        except (httpx.HTTPError, ValueError) as e:
            from collectors.errors import safe_message

            raise click.ClickException(f"project lookup failed: {safe_message(e)}")
        report = dtrack.upload(client, uuid, planned)
    _echo(
        f"created {len(report['created'])}, existing {len(report['existing'])}, "
        f"assigned {len(report['assigned'])}, not found {len(report['not_found'])}, "
        f"errors {len(report['errors'])}"
    )
    for label in report["not_found"]:
        _echo(f"! not a component of the project: {label}")
    for error in report["errors"]:
        _echo(f"! error: {error}")
    if report["errors"]:
        raise SystemExit(1)


@cli.group(name="history-key")
def history_key_group():
    """Manage the key that MACs local history (B3, docs/KEYED_INTEGRITY.md)."""


@history_key_group.command(name="generate")
def history_key_generate():
    """Print a fresh 32-byte history key and its key_id. Writes no file.

    Store the key outside .openpulse/ (a file with mode 600, or a CI
    secret) and pass it as OPENPULSE_HISTORY_KEY or --history-key-file.
    """
    from core.history_key import generate_key

    key, key_id = generate_key()
    _echo(key)
    _echo(f"key_id: {key_id}", err=True)


@cli.command(name="anchor")
@click.option("--store", default=".openpulse/observations", help="Observation history root")
@click.option("--ledger", "ledger_root", default=".openpulse/detections", help="Ledger root")
@click.option(
    "--out",
    default="",
    type=click.Path(dir_okay=False),
    help="Write the anchor JSON here (default: stdout). Keep it outside .openpulse/",
)
@_history_key_option
def anchor_command(store, ledger_root, out, history_key_file=None, history_previous_keys_file=None):
    """Checkpoint the local history, to keep where the store's writer cannot reach (B5).

    Records every observation history's tip, the detection ledger's
    entries and Merkle root, and the rotation log. With a history key the
    anchor is MACed. Commit it to git or upload it as a CI artifact, then
    check the store against it with `openpulse verify --anchor`.
    """
    import json as _json
    from pathlib import Path as _Path

    from core.anchor import build_anchor

    history_key, _previous = _load_history_key(
        history_key_file, history_previous_keys_file, store, ledger_root
    )
    if out and ".openpulse" in _Path(out).resolve().parts:
        raise click.ClickException(
            "an anchor inside .openpulse/ anchors nothing: write it elsewhere"
        )
    built = build_anchor(store, ledger_root, history_key=history_key)
    text = _json.dumps(built, indent=2, sort_keys=True) + "\n"
    if out:
        _Path(out).write_text(text, encoding="utf-8")
        _echo(f"wrote {out}", err=True)
    else:
        click.echo(text, nl=False)
    _echo(
        f"anchored {len(built['observations'])} histories, "
        f"{len(built['ledger']['entries'])} ledger entries "
        f"(merkle root {built['ledger']['merkle_root']}); "
        f"{'MACed with ' + history_key.key_id if history_key else 'unsigned (no history key)'}",
        err=True,
    )


@cli.command(name="verify")
@click.option(
    "--anchor", "anchor_path", required=True, type=click.Path(exists=True, dir_okay=False)
)
@click.option("--store", default=".openpulse/observations", help="Observation history root")
@click.option("--ledger", "ledger_root", default=".openpulse/detections", help="Ledger root")
@click.option(
    "--require-signed",
    is_flag=True,
    help="Fail unless the anchor's MAC verifies under a supplied history key",
)
@click.option("--json", "as_json", is_flag=True, help="Print the result as JSON")
@_history_key_option
def verify_command(
    anchor_path,
    store,
    ledger_root,
    require_signed=False,
    as_json=False,
    history_key_file=None,
    history_previous_keys_file=None,
):
    """Check the local history against an anchor; exit 1 when anything anchored is gone (B5)."""
    import json as _json

    from core.anchor import OK, verify_anchor
    from core.bounded_io import loads_json, read_text
    from core.history_key import keyring

    try:
        anchor = loads_json(read_text(anchor_path, MAX_BUNDLE_BYTES, anchor_path), anchor_path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise click.ClickException(f"{anchor_path} is not anchor JSON: {exc}") from exc
    if not isinstance(anchor, dict):
        raise click.ClickException(f"{anchor_path} is not anchor JSON")
    keys = keyring(
        *_load_history_key(history_key_file, history_previous_keys_file, store, ledger_root)
    )
    result = verify_anchor(anchor, store, ledger_root, keys)
    failed = result["status"] != OK or (require_signed and result["signature"] != "VALID")
    if as_json:
        click.echo(_json.dumps(result, indent=2, sort_keys=True))
    else:
        _echo(f"anchor {anchor_path}: {result['status']} (signature {result['signature']})")
        for v in result["violations"]:
            _echo(f"! {v['kind']} {v['subject']}: {v['detail']}")
        for n in result["notices"]:
            _echo(f"- {n['kind']} {n['subject']}: {n['detail']}")
        if require_signed and result["signature"] != "VALID":
            _echo("! the anchor is not signed by a supplied history key (--require-signed)")
    if failed:
        raise SystemExit(1)


@cli.command(name="demo-bitnami")
def demo_bitnami():
    """Offline north-star demo: Bitnami event -> gate -> who is affected -> report."""
    from core.evidence.policy import gate
    from core.risk.match import event_affects_ref

    event = _load_event("data/fixtures/bitnami/event.json")
    violations = gate(event)
    _echo(
        "(Historical replay: recorded August 2025 distribution event; "
        "live registry state may have moved on.)"
    )
    _echo(f"event: {event.id} [{event.event_type.value}]")
    _echo(f"confidence={event.confidence.value} impact={event.impact.value}")
    _echo(f"gate: {'PASS' if not violations else violations}")
    watchlist = [
        "docker.io/bitnami/redis:7.2",
        "docker.io/bitnami/postgresql:16",
        "docker.io/bitnamilegacy/redis:7.2",
        "docker.io/redis:7.2",
        "postgres:16",
        "nginx:latest",
    ]
    _echo("\n## Impact on sample watchlist")
    for ref in watchlist:
        result = event_affects_ref(event, ref)
        icon = "🚨" if result["affected"] else "✅"
        _echo(f"{icon} {ref}: [{result['relationship']}] {result['detail']}")
    _echo("\n" + report_analyst.render_event_md(event))


@cli.command()
@click.option("--namespace", required=True, help="Registry namespace (e.g. bitnami)")
@click.option("--repo", "repository", required=True, help="Repository (e.g. redis)")
@click.option("--store", default=".openpulse/observations", help="History root directory")
@click.option(
    "--rebaseline",
    is_flag=True,
    help=(
        "Accept a refused history (ROLLBACK, ROLLBACK_SUSPECTED, DOWNGRADE, BROKEN): "
        "a rollback is accepted at its current tip, anything else is quarantined "
        "and restarted. Needs --reason"
    ),
)
@click.option("--reason", default="", help="Why the re-baseline is justified (logged)")
@_history_key_option
def observe(
    namespace,
    repository,
    store,
    rebaseline=False,
    reason="",
    history_key_file=None,
    history_previous_keys_file=None,
):
    """Probe a Docker Hub repo, persist the observation, diff against history."""
    from collectors.registries.docker import RegistryCollector
    from core.observations.sweep import observe_repository, validate_rebaseline_reason

    if reason and not rebaseline:
        raise click.ClickException("--reason is only used with --rebaseline")
    if rebaseline:
        try:
            reason = validate_rebaseline_reason(reason)
        except ValueError as exc:
            raise click.ClickException(f"--rebaseline needs --reason: {exc}") from exc
    history_key, previous_keys = _load_history_key(
        history_key_file, history_previous_keys_file, store
    )
    probe = RegistryCollector().check_image(namespace, repository)
    if probe.get("error"):
        _echo(f"error: {probe.get('safe_message')} (category={probe.get('category')})")
        raise SystemExit(1)
    result = observe_repository(
        "docker.io",
        namespace,
        repository,
        probe,
        store_root=store,
        history_key=history_key,
        previous_keys=previous_keys,
        rebaseline_reason=reason if rebaseline else None,
    )
    if result["error"] is not None:
        _echo(
            f"error: {result['error'].get('safe_message')} "
            f"(category={result['error'].get('category')})"
        )
        raise SystemExit(1)
    _echo(f"saved: {result['saved_path']}")
    _echo(f"history integrity: {result.get('history_integrity')}")
    if result["history_status"] == "REBASELINED" and rebaseline:
        _echo("re-baselined: reason logged in rebaselines.json; no change claims this run.")
        return
    if result["history_status"] == "GENESIS":
        _echo("baseline recorded — no previous observation, no change claims.")
        return
    if not result["changes"]:
        _echo("no changes since last observation.")
        return
    for change in result["changes"]:
        _echo(
            f"- {change['type']}: {change.get('tag') or ''} "
            f"{change.get('previous')} -> {change.get('current')}"
        )
    for finding in change_analyst.analyze_diffs(result["changes"]):
        _echo("\n" + report_analyst.render_finding_md(finding))


@cli.command()
@click.option("--month", required=True, help="Report month, e.g. 2026-09")
@click.option("--projects", default="", help="Comma-separated slugs (default: whole catalog)")
@click.option(
    "--raw-bundle-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Offline {slug}.json bundles",
)
@click.option("--out", default="", help="Output path (default reports/{month}-openpulse.md)")
@click.option("--since", default="", help="Recency floor for dated findings (YYYY-MM-DD)")
@click.option("--include-related", is_flag=True, help="Narrate RELATED findings too")
@click.option(
    "--with-sweep",
    is_flag=True,
    help="Run live distribution sweep first and include its findings",
)
@click.option("--store", default=".openpulse/observations", help="History root for --with-sweep")
@click.option(
    "--ledger",
    "ledger_root",
    default=".openpulse/detections",
    show_default=True,
    help="Durable detection ledger root ('' disables; feeds first_detected_at in findings)",
)
@click.option(
    "--metadata-out",
    default="",
    help="Metadata JSON path (default: <out> with .meta.json extension)",
)
@_history_key_option
def report(
    month,
    projects,
    raw_bundle_dir,
    out,
    since,
    include_related,
    with_sweep,
    store,
    ledger_root,
    metadata_out,
    history_key_file=None,
    history_previous_keys_file=None,
):
    """Monthly OSS Dependency Risk Report over seed projects."""
    import json as _json
    from pathlib import Path as _Path

    from core.entities.catalog import load_catalog
    from reports.generate import (
        build_report,
        build_report_metadata,
        collect_project,
        prepare_report,
    )

    slugs = [s.strip() for s in projects.split(",") if s.strip()] or [
        e["slug"] for e in load_catalog()
    ]
    items = []
    for slug in slugs:
        raw = None
        if raw_bundle_dir:
            bundle = _Path(raw_bundle_dir) / f"{slug}.json"
            if bundle.exists():
                raw = _load_bundle(bundle)
        if raw is None:
            if raw_bundle_dir:
                _echo(f"skip {slug}: no bundle in {raw_bundle_dir}")
                continue
            raw = _live_bundle(slug)
        items.append(collect_project(slug, raw))
    import os

    from core.history_key import keyring

    history_key, previous_keys = _load_history_key(
        history_key_file, history_previous_keys_file, store, ledger_root
    )
    history_keys = keyring(history_key, previous_keys)
    sweep_findings: list = []
    if with_sweep:
        from collectors.registries.docker import RegistryCollector
        from core.entities.catalog import load_catalog as _load_catalog
        from core.observations.sweep import sweep_catalog

        catalog = _load_catalog()
        wanted = set(slugs)
        selected = [e for e in catalog if e.get("slug") in wanted]
        _echo("running distribution sweep...")
        sweep_findings = sweep_catalog(
            selected,
            RegistryCollector().check_image,
            store_root=store,
            history_key=history_key,
            previous_keys=previous_keys,
        )["findings"]
        _echo(f"sweep findings: {len(sweep_findings)}")
    notes = [
        "Collectors: endoflife.date, GitHub releases + repo metadata, NVD, CISA KEV, Docker Hub.",
        "GitHub calls authenticated (5000 req/hr budget)."
        if (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        else "GitHub calls unauthenticated (60 req/hr budget); some repos may show gaps.",
        "NVD queried without API key (5 req/30s); misses degrade to gaps, not findings.",
        "Keyword-associated CVE records without identity evidence are held back, not narrated.",
        "Public intelligence describes project-level change; whether it affects "
        "YOUR dependencies needs a watchlist (`openpulse check`).",
    ]
    if (ledger_root or with_sweep) and not history_keys:
        from core.digest import UNKEYED_LEAD_TIME_NOTE

        notes.append(UNKEYED_LEAD_TIME_NOTE)
    markdown = build_report(
        month,
        items,
        since=since or None,
        include_related=include_related,
        notes=notes,
        sweep_findings=sweep_findings,
        ledger_root=ledger_root or None,
        history_keys=history_keys,
    )
    destination = out or f"reports/{month}-openpulse.md"
    _Path(destination).write_text(markdown + "\n", encoding="utf-8")
    _echo(f"wrote {destination} ({len(items)} projects)")
    prepared = prepare_report(
        items,
        sweep_findings,
        since=since or None,
        include_related=include_related,
        ledger_root=ledger_root or None,
        history_keys=history_keys,
    )
    metadata = build_report_metadata(
        month,
        items,
        prepared["pairs"],
        prepared["historical"],
        sweep_included=bool(with_sweep),
    )
    meta_destination = metadata_out or (str(destination).removesuffix(".md") + ".meta.json")
    _Path(meta_destination).write_text(_json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    _echo(f"wrote {meta_destination}")


@cli.command(name="lifecycle-report")
@click.option("--month", required=True, help="Report month, e.g. 2026-09")
@click.option("--projects", default="", help="Comma-separated slugs (default: whole catalog)")
@click.option(
    "--raw-bundle-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Offline {slug}.json bundles",
)
@click.option("--out", default="", help="Output path (default reports/lifecycle-{month}.md)")
def lifecycle_report(month, projects, raw_bundle_dir, out):
    """Lifecycle posture and planning view over seed projects."""
    from pathlib import Path as _Path

    from core.entities.catalog import endoflife_map, load_catalog
    from reports.lifecycle import build_lifecycle_report, collect_lifecycle_status

    slugs = [s.strip() for s in projects.split(",") if s.strip()] or [
        e["slug"] for e in load_catalog()
    ]
    live_collector = None
    statuses = []
    for slug in slugs:
        raw = None
        if raw_bundle_dir:
            bundle = _Path(raw_bundle_dir) / f"{slug}.json"
            if bundle.exists():
                raw = _load_bundle(bundle)
        if raw is None:
            if raw_bundle_dir:
                _echo(f"skip {slug}: no bundle in {raw_bundle_dir}")
                continue
            if live_collector is None:
                from collectors.endoflife.collector import EndoflifeCollector

                live_collector = EndoflifeCollector(endoflife_map())
            raw = {"endoflife": live_collector.collect(slug)}
        statuses.append(collect_lifecycle_status(slug, raw))
    markdown = build_lifecycle_report(month, statuses)
    destination = out or f"reports/lifecycle-{month}.md"
    _Path(destination).write_text(markdown + "\n", encoding="utf-8")
    _echo(f"wrote {destination} ({len(statuses)} projects)")


def _load_yaml(path: str) -> dict:
    """Bounded YAML load with clean errors (mirrors _load_json)."""
    import yaml as _yaml

    from core.bounded_io import read_text

    try:
        data = _yaml.safe_load(read_text(path, MAX_INPUT_BYTES, path))
    except OSError as e:
        raise click.ClickException(f"cannot read {path}: {e.strerror or e}")
    except _yaml.YAMLError as e:
        raise click.ClickException(f"{path} is not valid YAML: {e}")
    except UnicodeDecodeError:
        raise click.ClickException(f"{path} is not UTF-8 text")
    except RecursionError:
        raise click.ClickException(f"{path} nests too deeply to parse")
    except ValueError as e:  # over the size cap
        raise click.ClickException(str(e))
    if not isinstance(data, dict):
        raise click.ClickException(f"{path} must contain a mapping")
    return data


_GLYPH_FALLBACKS = {
    "🚨": "[affected]",
    "✅": "[ok]",
    "ℹ️": "[related]",
    "ℹ": "[related]",
    "❓": "[unknown]",
    # facet status symbols (core.pulse.SYMBOL)
    "🟢": "[ok]",
    "🟡": "[watch]",
    "🟠": "[review]",
    "🔴": "[action]",
    # impact badges (analyzers.report_analyst.BADGE) + the unknown-impact dot
    "⚪": "[unknown]",
}


def _safe_text(text: Any, stream: Any = None) -> str:
    """Format text safely for output streams that cannot encode unicode glyphs."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    target = stream or sys.stdout
    encoding = (
        getattr(target, "encoding", None) or getattr(sys.__stdout__, "encoding", None) or "utf-8"
    )
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, LookupError):
        pass

    out = text
    for glyph, ascii_marker in _GLYPH_FALLBACKS.items():
        out = out.replace(glyph, ascii_marker)
    try:
        out.encode(encoding)
        return out
    except (UnicodeEncodeError, LookupError):
        out = out.replace("—", "-").replace("–", "-")
    try:
        out.encode(encoding)
        return out
    except (UnicodeEncodeError, LookupError):
        return out.encode(encoding, errors="replace").decode(encoding)


def _echo(msg: Any = "", **kwargs: Any) -> None:
    """Echo helper falling back to ASCII markers when the stream cannot encode glyphs."""
    file = kwargs.get("file")
    stream = file or (sys.stderr if kwargs.get("err") else sys.stdout)
    click.echo(_safe_text(msg, stream=stream), **kwargs)


def _evaluation_options(command):
    """The frame a negative is admitted in (TR-2026-01 N4), as for the agent tools.

    By default a verdict command runs in the *current* mode: a negative
    needs evidence fetched within 90 days of the start of today (UTC), so a stale event can
    associate a dependency but never clear it. ``--replay`` drops the
    bound for replaying recorded evidence, and the run says so.
    """
    command = click.option(
        "--as-of",
        default=None,
        help="Evaluate as of this ISO date or time, UTC (default: the start of today)",
    )(command)
    command = click.option(
        "--max-evidence-age-days",
        type=click.IntRange(min=0),
        default=None,
        help="Freshness bound for negatives, in days [default: 90]",
    )(command)
    return click.option(
        "--replay",
        is_flag=True,
        help="Replay recorded evidence with no freshness bound: a negative may then rest "
        "on evidence of any age",
    )(command)


def _evaluation(replay: bool, max_evidence_age_days: int | None, as_of: str | None):
    """The run's Evaluation (``core.agent_tools``), announced on stderr."""
    from datetime import datetime, timezone

    from core.agent_tools import CURRENT, REPLAY, Evaluation

    if replay and (max_evidence_age_days is not None or as_of):
        raise click.UsageError(
            "--replay applies no freshness bound; drop --max-evidence-age-days and --as-of"
        )
    when = None
    if as_of:
        try:
            when = datetime.fromisoformat(as_of)
        except ValueError as exc:
            raise click.BadParameter(f"not an ISO date or time: {as_of}") from exc
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
    # The start of today (UTC) by default, so two runs on one day emit
    # identical documents.
    evaluation = Evaluation(
        REPLAY if replay else CURRENT,
        as_of=when,
        max_evidence_age_days=max_evidence_age_days,
        today=datetime.now(timezone.utc).date(),
    )
    if evaluation.bounded:
        _echo(
            f"evaluation: current, {evaluation.max_evidence_age.days}-day freshness bound "
            f"as of {evaluation.as_of.date()}: stale or contested events cannot clear",
            err=True,
        )
    else:
        _echo(
            "evaluation: replay, no freshness bound: a negative may rest on evidence of any age",
            err=True,
        )
    return evaluation


_COVERAGE_RANK = {"COMPLETE": 0, "PARTIAL": 1, "FAILED": 2}


def _coverage_summary(inspections) -> tuple[str, list[str]]:
    """Aggregate repository inspections into one run-level status.

    This is deliberately independent of the dependency results: a
    FAILED/PARTIAL scan that yielded zero dependencies still must not
    look clean when other inputs contributed dependencies.
    """
    status = "COMPLETE"
    reasons: list[str] = []
    for inspection in inspections:
        current = getattr(inspection, "coverage", "COMPLETE")
        if _COVERAGE_RANK.get(current, 0) > _COVERAGE_RANK.get(status, 0):
            status = current
        for reason in getattr(inspection, "coverage_reasons", []) or []:
            if reason not in reasons:
                reasons.append(reason)
    return status, reasons


def _echo_run_coverage(inspections) -> str:
    """Print the run-level repository coverage (if any) and return it."""
    status, reasons = _coverage_summary(inspections)
    if inspections:
        _echo(f"repository inspection coverage: {status}")
        for reason in reasons:
            _echo(f"   - {reason}")
    return status


def _github_auth_options(func):
    """Shared GitHub credential options for commands that can inspect a repository."""
    func = click.option(
        "--github-token-file",
        type=click.Path(exists=True, dir_okay=False),
        default=None,
        help="Read a GitHub token from the first line of PATH (maximum 4 KiB)",
    )(func)
    func = click.option(
        "--github-token",
        "github_token",
        type=str,
        default=None,
        show_default=False,
        help="Deprecated: GitHub token in argv; prefer GITHUB_TOKEN or --github-token-file",
    )(func)
    return func


def _load_check_inputs(
    watchlist,
    sbom,
    spdx,
    images,
    lockfile,
    manifest,
    github_repo,
    github_token,
    events,
    raw_bundle_dir,
):
    """Shared input loading for check and digest (one path, not two).

    Loads watchlist/SBOM/SPDX/images/lockfile/manifest/github-repo deps + events +
    offline bundles with the exact per-input echo discipline and
    skip-reason reporting the check command established: same
    errors, same messages, same composable semantics. Both commands
    stay in lockstep: a new input flag joins HERE, not in a copy.
    """
    from pathlib import Path as _Path

    from core.entities.resolve import resolve_project as _resolve
    from core.risk.check import load_watchlist_doc

    has_input = watchlist or sbom or spdx or images or lockfile or manifest or github_repo
    if not has_input:
        raise click.ClickException(
            "check needs --watchlist, --sbom, --spdx, --images, --lockfile and/or --manifest"
        )
    deps: list[Any] = []
    inspections: list[Any] = []
    if watchlist:
        try:
            deps = load_watchlist_doc(_load_yaml(watchlist))
        except ValueError as e:
            raise click.ClickException(f"{watchlist}: {e}")
    skipped: list[str] = []
    if sbom:
        from core.sbom_reader import read_sbom

        try:
            sbom_deps, skipped = read_sbom(sbom)
        except json.JSONDecodeError as e:
            # Must precede the ValueError handler: JSONDecodeError
            # SUBCLASSES ValueError, so the reverse order makes this
            # branch dead code and loses the specific message.
            raise click.ClickException(f"{sbom} is not valid JSON: {e}")
        except ValueError as e:
            raise click.ClickException(f"{sbom}: {e}")
        if sbom_deps:
            _echo(f"sbom: {len(sbom_deps)} mapped component(s), {len(skipped)} skipped")
            deps = [*deps, *sbom_deps]
        elif skipped:
            _echo(f"sbom: 0 mapped, {len(skipped)} skipped — nothing checkable in this SBOM")
        for line in skipped:
            _echo(f"! skipped: {line}")
    if spdx:
        from core.sbom_reader import read_spdx

        try:
            spdx_deps, spdx_skipped = read_spdx(spdx)
        except json.JSONDecodeError as e:
            # Same ordering rule as --sbom: JSONDecodeError SUBCLASSES
            # ValueError, so it must be caught first or its branch is
            # dead code and the specific message is lost.
            raise click.ClickException(f"{spdx} is not valid JSON: {e}")
        except ValueError as e:
            raise click.ClickException(f"{spdx}: {e}")
        if spdx_deps:
            _echo(f"spdx: {len(spdx_deps)} mapped package(s), {len(spdx_skipped)} skipped")
            deps = [*deps, *spdx_deps]
        elif spdx_skipped:
            _echo(f"spdx: 0 mapped, {len(spdx_skipped)} skipped — nothing checkable in this SPDX")
        for line in spdx_skipped:
            _echo(f"! skipped: {line}")
    if images:
        from core.image_inventory import read_image_inventory

        try:
            img_deps, img_skipped = read_image_inventory(images)
        except ValueError as e:
            raise click.ClickException(f"{images}: {e}")
        for line in img_skipped:
            _echo(f"! skipped: {line}")
        if img_deps:
            _echo(f"images: {len(img_deps)} image ref(s) from inventory")
            deps = [*deps, *img_deps]
        elif img_skipped:
            _echo(
                f"images: 0 usable, {len(img_skipped)} skipped — "
                "nothing checkable in this inventory"
            )
    if lockfile:
        from core.lockfile_reader import read_lockfile

        try:
            lock_deps, lock_skipped, lock_format = read_lockfile(lockfile)
        except ValueError as e:
            raise click.ClickException(f"{lockfile}: {e}")
        label = {"npm": "package-lock", "poetry": "poetry.lock", "cargo": "Cargo.lock"}[lock_format]
        if lock_deps:
            _echo(
                f"lockfile ({label}): {len(lock_deps)} pinned package(s), "
                f"{len(lock_skipped)} skipped"
            )
            deps = [*deps, *lock_deps]
        elif lock_skipped:
            _echo(
                f"lockfile ({label}): 0 pinned, "
                f"{len(lock_skipped)} skipped — nothing checkable in this lockfile"
            )
        for line in lock_skipped:
            _echo(f"! skipped: {line}")
    if manifest:
        from core.manifest_reader import read_manifest

        try:
            man_deps, man_skipped, man_format = read_manifest(manifest)
        except ValueError as e:
            raise click.ClickException(f"{manifest}: {e}")
        label = {
            "requirements": "requirements.txt",
            "pyproject": "pyproject.toml",
            "pom": "pom.xml",
            "go": "go.mod",
            "cargo": "Cargo.toml",
        }[man_format]
        if man_deps:
            _echo(
                f"manifest ({label}): {len(man_deps)} pinned package(s), {len(man_skipped)} skipped"
            )
            deps = [*deps, *man_deps]
        elif man_skipped:
            _echo(
                f"manifest ({label}): 0 pinned, "
                f"{len(man_skipped)} skipped — nothing checkable in this manifest"
            )
        for line in man_skipped:
            _echo(f"! skipped: {line}")
    if github_repo:
        from core.github_reader import inspect_github_repo

        try:
            inspection = inspect_github_repo(github_repo, cli_token=github_token)
        except ValueError as e:
            raise click.ClickException(f"{github_repo}: {e}")
        for err in inspection.errors:
            _echo(f"! error: {err.get('safe_message', 'unknown error')}")
        for line in inspection.skipped:
            _echo(f"! skipped: {line}")
        for reason in inspection.coverage_reasons:
            _echo(f"! coverage: {reason}")
        _echo(f"github-repo ({github_repo}): inspection coverage {inspection.coverage}")
        inspections.append(inspection)
        if inspection.dependencies:
            _echo(
                f"github-repo ({github_repo}): "
                f"{len(inspection.dependencies)} dependency(s) from repository"
            )
            deps = [*deps, *inspection.dependencies]
        elif inspection.skipped and not inspection.errors:
            _echo(
                f"github-repo ({github_repo}): 0 usable, "
                f"{len(inspection.skipped)} skipped — nothing checkable in this repository"
            )
    loaded_events = [_load_event(path) for path in events]
    bundles = {}
    if raw_bundle_dir:
        from core.entities.identity import package_trust

        for dep in deps:
            if dep["kind"] != "package":
                continue
            # The security stream reads bundles under the package's trust
            # slug (PyPI `redis` -> `redis-py`); a file named by the plain
            # resolution is still accepted, stored under that same key.
            slug = package_trust(str(dep["package"]), dep.get("ecosystem"))["slug"]
            for name in dict.fromkeys((slug, _resolve(dep["package"]))):
                bundle = _Path(raw_bundle_dir) / f"{name}.json"
                if slug and name and bundle.exists() and slug not in bundles:
                    bundles[slug] = _load_bundle(bundle)
    if not deps:
        raise click.ClickException(
            "no checkable dependencies (watchlist/SBOM/lockfile/manifest/images yielded nothing)"
        )
    return deps, loaded_events, bundles, inspections


@cli.command()
@_evaluation_options
@click.option(
    "--watchlist", required=False, type=click.Path(exists=True), help="Watchlist YAML file"
)
@click.option(
    "--sbom",
    "sbom",
    type=click.Path(exists=True),
    help="CycloneDX SBOM (JSON, spec 1.4/1.5) — composable with --watchlist/--spdx",
)
@click.option(
    "--spdx",
    "spdx",
    type=click.Path(exists=True),
    help="SPDX SBOM (JSON, 2.x) — composable with --watchlist/--sbom",
)
@click.option(
    "--images",
    "images",
    type=click.Path(exists=True),
    help="Container image inventory (one ref per line, or a YAML list) "
    "— composable with --watchlist/--sbom/--spdx",
)
@click.option(
    "--lockfile",
    "lockfile",
    type=click.Path(exists=True),
    help="Lockfile (package-lock.json / poetry.lock / Cargo.lock) — pinned entries only, "
    "composable with --watchlist/--sbom/--spdx",
)
@click.option(
    "--manifest",
    "manifest",
    type=click.Path(exists=True),
    help="Package manifest (requirements.txt / pyproject.toml / pom.xml / go.mod / Cargo.toml) "
    "— composable with --watchlist/--sbom/--spdx/--lockfile/--images",
)
@click.option(
    "--github-repo",
    "github_repo",
    type=str,
    help="GitHub repository (owner/repo or https://github.com/owner/repo) "
    "— discovers dependency files recursively, composable with all other inputs",
)
@_github_auth_options
@click.option(
    "--event",
    "events",
    multiple=True,
    type=click.Path(exists=True),
    help="Intelligence event JSON (repeatable)",
)
@click.option(
    "--raw-bundle-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Offline {slug}.json bundles for version checks",
)
@click.option("--strict", is_flag=True, help="Exit 1 when any dependency is affected")
@click.option(
    "--fail-on-partial",
    is_flag=True,
    help="Exit 1 when repository inspection coverage is PARTIAL or FAILED "
    "(report-only by default; FAILED always fails under --strict)",
)
@click.option(
    "--fail-on",
    type=click.Choice(["affected", "review", "action", "critical"]),
    default=None,
    show_default=False,
    help="CI exit threshold: affected, review, action, or critical",
)
@click.option(
    "--ledger",
    "ledger_root",
    default=".openpulse/detections",
    show_default=True,
    help="Durable first-detection ledger root (recording is the default; '' disables)",
)
@click.option(
    "--digest",
    is_flag=True,
    help="Print grouped digest instead of per-dependency lines (cron-friendly)",
)
@click.option(
    "--webhook",
    default="",
    envvar="OPENPULSE_WEBHOOK_URL",
    show_envvar=True,
    help=(
        "POST the digest markdown to a JSON-text webhook (e.g. Slack incoming). "
        "Prefer the env var: argv is visible in the process list"
    ),
)
@click.option(
    "--webhook-allow-http",
    is_flag=True,
    help="Opt in to plain-http webhooks (https is required by default)",
)
@_history_key_option
def check(
    watchlist,
    sbom,
    spdx,
    images,
    lockfile,
    manifest,
    events,
    raw_bundle_dir,
    strict,
    fail_on,
    ledger_root,
    digest,
    webhook,
    webhook_allow_http,
    fail_on_partial,
    github_repo="",
    github_token="",
    github_token_file=None,
    replay=False,
    max_evidence_age_days=None,
    as_of=None,
    history_key_file=None,
    history_previous_keys_file=None,
):
    """Dependency Early Warning: evaluate a watchlist against events."""
    from core.risk.check import check_dependency

    github_token = _resolve_github_token(github_repo, github_token, github_token_file)
    deps, loaded_events, bundles, inspections = _load_check_inputs(
        watchlist,
        sbom,
        spdx,
        images,
        lockfile,
        manifest,
        github_repo,
        github_token,
        events,
        raw_bundle_dir,
    )
    run_coverage = _echo_run_coverage(inspections)
    coverage_failed = run_coverage == "FAILED"
    coverage_blocked = fail_on_partial and run_coverage in ("PARTIAL", "FAILED")
    affected = 0
    # A flag, not a subcommand: digest is a presentation of the same run,
    # so --strict semantics stay identical in both shapes.
    evaluation = _evaluation(replay, max_evidence_age_days, as_of)
    results = [
        check_dependency(
            dep,
            loaded_events,
            bundles,
            as_of=evaluation.as_of,
            max_evidence_age=evaluation.max_evidence_age,
        )
        for dep in deps
    ]
    # Durable detection ledger: an empty --ledger value disables it
    # (per-run behavior, exactly like today); anything else is the root.
    # Acquisition is best-effort BY DESIGN: the ledger is an
    # enrichment, never a prerequisite - a busy lock must degrade the
    # run to today's no-ledger output, not crash the command a cron
    # schedule depends on.
    if ledger_root:
        from core.detections.ledger import keyed_first_seen, record_detection
        from core.history_key import keyring
        from core.risk.check import detections_from_verdicts

        history_key, previous_keys = _load_history_key(
            history_key_file, history_previous_keys_file, ledger_root
        )
        try:
            for fact in detections_from_verdicts(results, loaded_events):
                record_detection(
                    fact["project"],
                    fact["finding_class"],
                    fact["subject"],
                    scope=fact["scope"],
                    root=ledger_root,
                    history_key=history_key,
                    previous_keys=previous_keys,
                )
        except TimeoutError:
            _echo("ledger busy - detections not recorded this run", err=True)
        else:
            for result in results:
                # Earliest across ALL of this verdict's recorded facts, not
                # the first recorded fact: a dependency can carry a fresh
                # lifecycle cause and a security record detected days earlier
                # (lifecycle causes are appended before security ones), and
                # the reported first detection must be the earliest of them.
                # Reads are lock-free (atomic file reads), so they cannot
                # hit the busy lock the writes just passed.
                earliest = min(
                    (
                        seen
                        for fact in detections_from_verdicts([result], loaded_events)
                        if (
                            seen := keyed_first_seen(
                                fact["project"],
                                fact["finding_class"],
                                fact["subject"],
                                scope=fact["scope"],
                                root=ledger_root,
                                keys=keyring(history_key, previous_keys),
                            )
                        )
                    ),
                    default=None,
                )
                if earliest:
                    result.first_detected = str(earliest)[:10]
    if digest or webhook:
        from analyzers.report_analyst import render_check_digest

        text = render_check_digest(results)
        _echo(text)
        if webhook:
            from core.notify import WebhookPolicy, post_digest

            delivery = post_digest(
                webhook, text, policy=WebhookPolicy(allow_http=webhook_allow_http)
            )
            if delivery["ok"]:
                _echo(f"posted digest (http {delivery['status_code']})")
            else:
                # Delivery failure must not mask the check result itself.
                _echo(f"webhook delivery failed: {delivery['error']}")
        affected = sum(1 for r in results if r.affected)
        _echo(f"\n{affected}/{len(deps)} dependencies affected")
        from core.risk.check import fail_on_threshold

        threshold = fail_on or ("action" if strict else "")
        if threshold and fail_on_threshold(results, threshold):
            raise SystemExit(1)
        if coverage_blocked or (strict and coverage_failed):
            raise SystemExit(1)
        return
    for dep, result in zip(deps, results):
        label = dep.get("ref") or f"{dep.get('package')}=={dep.get('version') or '?'}"
        relationship = result.relationship
        if result.affected:
            affected += 1
            first_note = (
                f" · first detected {result.first_detected}" if result.first_detected else ""
            )
            _echo(f"🚨 {label}: AFFECTED ({relationship}){first_note}")
            for verdict in result.verdicts:
                if verdict["affected"]:
                    _echo(f"   - [{verdict['impact']}] {verdict['detail']}")
        elif relationship == "NOT_AFFECTED":
            _echo(f"✅ {label}: NOT_AFFECTED — {result.reason}")
        elif relationship == "RELATED":
            _echo(f"ℹ️ {label}: RELATED — {result.reason}")
        else:
            _echo(f"❓ {label}: UNKNOWN — evaluated, no applicable evidence")
    incomplete = [r for r in results if r.inspection_coverage != "COMPLETE"]
    if incomplete:
        reasons = sorted({reason for r in incomplete for reason in r.inspection_coverage_reasons})
        _echo(
            f"⚠️  inspection coverage: {len(incomplete)}/{len(results)} dependency(s) not "
            "COMPLETE — results below are not a clean bill of health"
        )
        for reason in reasons:
            _echo(f"   - {reason}")
    _echo(f"\n{affected}/{len(deps)} dependencies affected")
    from core.risk.check import fail_on_threshold, strict_affected

    # Same gate as the digest branch: --fail-on must not depend on
    # the presentation (it was silently ignored here before).
    if fail_on and fail_on_threshold(results, fail_on):
        raise SystemExit(1)
    if strict and strict_affected(results):
        raise SystemExit(1)
    if coverage_blocked or (strict and coverage_failed):
        raise SystemExit(1)


@cli.command()
@_evaluation_options
@click.option(
    "--watchlist", required=False, type=click.Path(exists=True), help="Watchlist YAML file"
)
@click.option(
    "--sbom",
    "sbom",
    type=click.Path(exists=True),
    help="CycloneDX SBOM (JSON, spec 1.4/1.5) — composable with --watchlist/--spdx",
)
@click.option(
    "--spdx",
    "spdx",
    type=click.Path(exists=True),
    help="SPDX SBOM (JSON, 2.x) — composable with --watchlist/--sbom",
)
@click.option(
    "--images",
    "images",
    type=click.Path(exists=True),
    help="Container image inventory — composable with all other inputs",
)
@click.option(
    "--lockfile",
    "lockfile",
    type=click.Path(exists=True),
    help="Lockfile (package-lock.json / poetry.lock / Cargo.lock) — pinned entries only, "
    "composable with --watchlist/--sbom/--spdx",
)
@click.option(
    "--manifest",
    "manifest",
    type=click.Path(exists=True),
    help="Package manifest (requirements.txt / pyproject.toml / pom.xml / go.mod / Cargo.toml) "
    "— composable with --watchlist/--sbom/--spdx/--lockfile/--images",
)
@click.option(
    "--github-repo",
    "github_repo",
    type=str,
    help="GitHub repository (owner/repo or https://github.com/owner/repo) "
    "— discovers dependency files recursively, composable with all other inputs",
)
@_github_auth_options
@click.option(
    "--event",
    "events",
    multiple=True,
    type=click.Path(exists=True),
    help="Intelligence event JSON (repeatable)",
)
@click.option(
    "--raw-bundle-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Offline {slug}.json bundles for security correlation",
)
@click.option(
    "--window-days",
    default=90,
    show_default=True,
    help="Warning window: keep changes effective within N days of today",
)
@click.option(
    "--output",
    "output",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Briefing format: markdown (human) or JSON (machine)",
)
@click.option(
    "--ledger",
    "ledger_root",
    default=".openpulse/detections",
    show_default=True,
    help="Durable first-detection ledger root (read-only; `openpulse check` records)",
)
@_history_key_option
def digest(
    watchlist,
    sbom,
    spdx,
    images,
    lockfile,
    manifest,
    events,
    raw_bundle_dir,
    window_days,
    output,
    ledger_root,
    github_repo="",
    github_token="",
    github_token_file=None,
    replay=False,
    max_evidence_age_days=None,
    as_of=None,
    history_key_file=None,
    history_previous_keys_file=None,
):
    """M6 Early Warning: alert digest - upcoming deadlines for YOUR dependencies."""
    from core.digest import build_digest, render_digest_md
    from core.risk.check import check_dependency

    github_token = _resolve_github_token(github_repo, github_token, github_token_file)
    if ledger_root == "":
        ledger_root = None  # read digests without a ledger: no lead-time claims
    deps, loaded_events, bundles, _inspections = _load_check_inputs(
        watchlist,
        sbom,
        spdx,
        images,
        lockfile,
        manifest,
        github_repo,
        github_token,
        events,
        raw_bundle_dir,
    )
    if not loaded_events:
        raise click.ClickException(
            "digest needs at least one --event: deadlines come from event"
            " evidence, not from the ledger alone"
        )
    evaluation = _evaluation(replay, max_evidence_age_days, as_of)
    results = [
        check_dependency(
            dep,
            loaded_events,
            bundles,
            as_of=evaluation.as_of,
            max_evidence_age=evaluation.max_evidence_age,
        )
        for dep in deps
    ]
    built = build_digest(
        results,
        loaded_events,
        ledger_root=ledger_root,
        window_days=window_days,
        history_keys=_history_keyring(history_key_file, history_previous_keys_file, ledger_root),
    )
    if output == "json":
        import json as _json

        _echo(_json.dumps(built, indent=2))
        return
    _echo(render_digest_md(built))


@cli.command()
@_evaluation_options
@click.option(
    "--watchlist",
    required=False,
    type=click.Path(exists=True),
    help="Watchlist YAML file",
)
@click.option(
    "--sbom",
    "sbom",
    type=click.Path(exists=True),
    help="CycloneDX SBOM (JSON, spec 1.4/1.5) — composable with --watchlist/--spdx",
)
@click.option(
    "--spdx",
    "spdx",
    type=click.Path(exists=True),
    help="SPDX SBOM (JSON, 2.x) — composable with --watchlist/--sbom",
)
@click.option(
    "--images",
    "images",
    type=click.Path(exists=True),
    help="Container image inventory — composable with all other inputs",
)
@click.option(
    "--lockfile",
    "lockfile",
    type=click.Path(exists=True),
    help="Lockfile (package-lock.json / poetry.lock / Cargo.lock) — pinned entries only, "
    "composable with --watchlist/--sbom/--spdx",
)
@click.option(
    "--manifest",
    "manifest",
    type=click.Path(exists=True),
    help="Package manifest (requirements.txt / pyproject.toml / pom.xml / go.mod / Cargo.toml) "
    "— composable with --watchlist/--sbom/--spdx/--lockfile/--images",
)
@click.option(
    "--github-repo",
    "github_repo",
    type=str,
    help="GitHub repository (owner/repo or https://github.com/owner/repo) "
    "— discovers dependency files recursively, composable with all other inputs",
)
@_github_auth_options
@click.option(
    "--event",
    "events",
    multiple=True,
    type=click.Path(exists=True),
    help="Intelligence event JSON (repeatable)",
)
@click.option(
    "--raw-bundle-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Offline {slug}.json bundles for version checks",
)
@click.option(
    "--window-days",
    default=90,
    show_default=True,
    help="Warning window: keep changes effective within N days of today",
)
@click.option(
    "--output",
    "output",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Briefing format: markdown (human) or JSON (machine)",
)
@click.option(
    "--ledger",
    "ledger_root",
    default=".openpulse/detections",
    show_default=True,
    help="Durable first-detection ledger root (read-only; `openpulse check` records)",
)
@_history_key_option
def warnings(
    watchlist,
    sbom,
    spdx,
    images,
    lockfile,
    manifest,
    events,
    raw_bundle_dir,
    window_days,
    output,
    ledger_root,
    github_repo="",
    github_token="",
    github_token_file=None,
    replay=False,
    max_evidence_age_days=None,
    as_of=None,
    history_key_file=None,
    history_previous_keys_file=None,
):
    """M6 Early Warning: warning deadlines for YOUR upcoming changes."""
    from core.risk.check import check_dependency
    from core.warnings import build_warnings, render_warnings_md

    github_token = _resolve_github_token(github_repo, github_token, github_token_file)
    if ledger_root == "":
        ledger_root = None  # read warnings without a ledger: no lead-time claims
    deps, loaded_events, bundles, _inspections = _load_check_inputs(
        watchlist,
        sbom,
        spdx,
        images,
        lockfile,
        manifest,
        github_repo,
        github_token,
        events,
        raw_bundle_dir,
    )
    if not loaded_events:
        raise click.ClickException(
            "warnings needs at least one --event: deadlines come from event"
            " evidence, not from the ledger alone"
        )
    evaluation = _evaluation(replay, max_evidence_age_days, as_of)
    results = [
        check_dependency(
            dep,
            loaded_events,
            bundles,
            as_of=evaluation.as_of,
            max_evidence_age=evaluation.max_evidence_age,
        )
        for dep in deps
    ]
    built = build_warnings(
        results,
        loaded_events,
        ledger_root=ledger_root,
        window_days=window_days,
        history_keys=_history_keyring(history_key_file, history_previous_keys_file, ledger_root),
    )
    if output == "json":
        import json as _json

        _echo(_json.dumps(built, indent=2))
        return
    _echo(render_warnings_md(built))


@cli.command()
@_evaluation_options
@click.option(
    "--watchlist",
    required=False,
    type=click.Path(exists=True),
    help="Watchlist YAML file",
)
@click.option(
    "--sbom",
    "sbom",
    type=click.Path(exists=True),
    help="CycloneDX SBOM (JSON, spec 1.4/1.5) - composable with the other sources",
)
@click.option(
    "--spdx",
    "spdx",
    type=click.Path(exists=True),
    help="SPDX SBOM (JSON, 2.x) - composable with the other sources",
)
@click.option(
    "--images",
    "images",
    type=click.Path(exists=True),
    help="Container image inventory (one ref per line or a YAML list)",
)
@click.option(
    "--lockfile",
    "lockfile",
    type=click.Path(exists=True),
    help="Lockfile (package-lock.json / poetry.lock / Cargo.lock), pinned entries only",
)
@click.option(
    "--manifest",
    "manifest",
    type=click.Path(exists=True),
    help="Package manifest (requirements.txt / pyproject.toml / pom.xml / go.mod / Cargo.toml) "
    "— composable with --watchlist/--sbom/--spdx/--lockfile/--images",
)
@click.option(
    "--github-repo",
    "github_repo",
    type=str,
    help="GitHub repository (owner/repo or https://github.com/owner/repo) "
    "— discovers dependency files recursively, composable with all other inputs",
)
@_github_auth_options
@click.option(
    "--event",
    "events",
    multiple=True,
    type=click.Path(exists=True),
    help="Intelligence event JSON (repeatable)",
)
@click.option(
    "--raw-bundle-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Offline {slug}.json bundles for version checks",
)
@click.option(
    "--output",
    "output",
    default="",
    type=click.Path(),
    help="Write JSONL here (default: stdout)",
)
@click.option(
    "--sarif",
    "sarif_path",
    default="",
    type=click.Path(dir_okay=False),
    help="Also write these contracts as a SARIF 2.1.0 log (GitHub Code Scanning)",
)
@click.option(
    "--summary",
    "summary_path",
    default="",
    type=click.Path(dir_okay=False),
    help="Also append a Markdown summary of the SARIF results to PATH (e.g. $GITHUB_STEP_SUMMARY)",
)
@click.option(
    "--defectdojo",
    "defectdojo_path",
    default="",
    type=click.Path(dir_okay=False),
    help="Also write these contracts as DefectDojo 'Generic Findings Import' JSON",
)
@click.option(
    "--fail-on",
    type=click.Choice(["affected", "review", "action", "critical"]),
    default=None,
    help="Exit 1 after writing every output when the same threshold `check --fail-on` "
    "uses is breached",
)
def attest(
    watchlist,
    sbom,
    spdx,
    images,
    lockfile,
    manifest,
    github_repo,
    github_token,
    github_token_file,
    events,
    raw_bundle_dir,
    output,
    sarif_path="",
    summary_path="",
    defectdojo_path="",
    fail_on=None,
    replay=False,
    max_evidence_age_days=None,
    as_of=None,
):
    """Emit one evidence-contract v1 document per dependency × event pair.

    JSONL: one schema-valid contract per line, so stdout stays
    pipeable; progress chatter goes to stderr. Each document is
    independently verifiable: provenance.content_hash recomputes from
    the content alone (docs/EVIDENCE_CONTRACT.md).
    """
    github_token = _resolve_github_token(github_repo, github_token, github_token_file)
    NL = chr(10)
    import json as _json
    from pathlib import Path as _Path

    from core.evidence_contract import build_contract, validate_contract
    from core.risk.check import check_dependency, load_watchlist_doc

    has_input = watchlist or sbom or spdx or images or lockfile or manifest or github_repo
    if not has_input:
        raise click.ClickException(
            "attest needs --watchlist, --sbom, --spdx, --images, --lockfile and/or --manifest"
        )
    if not events:
        raise click.ClickException("attest needs at least one --event")
    deps: list[Any] = []
    #: SARIF artifact uri per dependency (same order as deps).
    uris: list[str] = []
    inspections: list[Any] = []
    if watchlist:
        try:
            deps = load_watchlist_doc(_load_yaml(watchlist))
            uris = [_sarif_uri(watchlist)] * len(deps)
        except ValueError as e:
            raise click.ClickException(f"{watchlist}: {e}")
    if sbom:
        from core.sbom_reader import read_sbom

        try:
            sbom_deps, _ = read_sbom(sbom)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"{sbom} is not valid JSON: {e}")
        except ValueError as e:
            raise click.ClickException(f"{sbom}: {e}")
        if sbom_deps:
            _echo(f"sbom: {len(sbom_deps)} mapped component(s)", err=True)
            deps = [*deps, *sbom_deps]
            uris += [_sarif_uri(sbom)] * len(sbom_deps)
    if spdx:
        from core.sbom_reader import read_spdx

        try:
            spdx_deps, _ = read_spdx(spdx)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"{spdx} is not valid JSON: {e}")
        except ValueError as e:
            raise click.ClickException(f"{spdx}: {e}")
        if spdx_deps:
            _echo(f"spdx: {len(spdx_deps)} mapped package(s)", err=True)
            deps = [*deps, *spdx_deps]
            uris += [_sarif_uri(spdx)] * len(spdx_deps)
    if images:
        from core.image_inventory import read_image_inventory

        try:
            img_deps, _ = read_image_inventory(images)
        except ValueError as e:
            raise click.ClickException(f"{images}: {e}")
        if img_deps:
            _echo(f"images: {len(img_deps)} image ref(s)", err=True)
            deps = [*deps, *img_deps]
            uris += [_sarif_uri(images)] * len(img_deps)
    if lockfile:
        from core.lockfile_reader import read_lockfile

        try:
            lock_deps, _, lock_format = read_lockfile(lockfile)
        except ValueError as e:
            raise click.ClickException(f"{lockfile}: {e}")
        if lock_deps:
            _echo(f"lockfile ({lock_format}): {len(lock_deps)} pinned package(s)", err=True)
            deps = [*deps, *lock_deps]
            uris += [_sarif_uri(lockfile)] * len(lock_deps)
    if manifest:
        from core.manifest_reader import read_manifest

        try:
            man_deps, _, man_format = read_manifest(manifest)
        except ValueError as e:
            raise click.ClickException(f"{manifest}: {e}")
        label = {
            "requirements": "requirements.txt",
            "pyproject": "pyproject.toml",
            "pom": "pom.xml",
            "go": "go.mod",
            "cargo": "Cargo.toml",
        }[man_format]
        if man_deps:
            _echo(f"manifest ({label}): {len(man_deps)} pinned package(s)", err=True)
            deps = [*deps, *man_deps]
            uris += [_sarif_uri(manifest)] * len(man_deps)
    if github_repo:
        from core.github_reader import inspect_github_repo

        try:
            inspection = inspect_github_repo(github_repo, cli_token=github_token)
        except ValueError as e:
            raise click.ClickException(f"{github_repo}: {e}")
        for err in inspection.errors:
            _echo(f"! error: {err.get('safe_message', 'unknown error')}", err=True)
        for line in inspection.skipped:
            _echo(f"! skipped: {line}", err=True)
        for reason in inspection.coverage_reasons:
            _echo(f"! coverage: {reason}", err=True)
        _echo(
            f"github-repo ({github_repo}): inspection coverage {inspection.coverage}",
            err=True,
        )
        inspections.append(inspection)
        if inspection.dependencies:
            _echo(
                f"github-repo ({github_repo}): "
                f"{len(inspection.dependencies)} dependency(s) from repository",
                err=True,
            )
            deps = [*deps, *inspection.dependencies]
            uris += [_sarif_uri(d.get("path") or ".") for d in inspection.dependencies]
        elif inspection.skipped and not inspection.errors:
            _echo(
                f"github-repo ({github_repo}): 0 usable, "
                f"{len(inspection.skipped)} skipped — nothing checkable in this repository",
                err=True,
            )
    if not deps:
        raise click.ClickException(
            "no checkable dependencies (watchlist/SBOM/lockfile/manifest/images yielded nothing)"
        )
    loaded_events = [_load_event(path) for path in events]
    bundles = {}
    if raw_bundle_dir:
        from core.entities.resolve import resolve_project as _resolve

        for dep in deps:
            if dep["kind"] != "package":
                continue
            slug = _resolve(dep["package"])
            bundle = _Path(raw_bundle_dir) / f"{slug}.json"
            if bundle.exists():
                bundles[slug] = _load_bundle(bundle)
    # Repository-level coverage: a FAILED/PARTIAL scan must reach every
    # emitted contract, even when the dependency came from another input,
    # so a partially read repository is never attested as clean.
    coverage_override = None
    if inspections:
        run_status, run_reasons = _coverage_summary(inspections)
        _echo(f"repository inspection coverage: {run_status}", err=True)
        for reason in run_reasons:
            _echo(f"   - {reason}", err=True)
        coverage_override = {"status": run_status, "reasons": run_reasons}
    evaluation = _evaluation(replay, max_evidence_age_days, as_of)
    # One contract per dependency x event: the attested pair is the
    # unit of consumption, not the combined verdict over all events.
    lines: list[str] = []
    rendered: list[tuple[dict[str, Any], str]] = []
    for dep, uri in zip(deps, uris, strict=True):
        for event in loaded_events:
            verdict = check_dependency(
                dep,
                [event],
                bundles,
                as_of=evaluation.as_of,
                max_evidence_age=evaluation.max_evidence_age,
            )
            doc = build_contract(
                event,
                verdict,
                inspection_coverage=coverage_override,
                as_of=evaluation.as_of,
                max_evidence_age=evaluation.max_evidence_age,
            )
            problems = validate_contract(doc)
            if problems:
                # A document OpenPulse itself cannot validate must
                # never reach a consumer: fail loudly, emit nothing.
                raise SystemExit(
                    f"internal error: contract for {dep} vs {event.id} failed schema: {problems}"
                )
            lines.append(_json.dumps(doc, sort_keys=True))
            rendered.append((doc, uri))
    if sarif_path or summary_path:
        from core.sarif import build_sarif, render_summary

        sarif_doc = build_sarif(
            rendered,
            tool_version=openpulse_version(),
            coverage=coverage_override,
        )
        if sarif_path:
            _Path(sarif_path).write_text(
                _json.dumps(sarif_doc, indent=2, sort_keys=True) + NL, encoding="utf-8"
            )
            count = len(sarif_doc["runs"][0]["results"])
            _echo(f"wrote {sarif_path} ({count} result(s))", err=True)
        if summary_path:
            # Append, never truncate: $GITHUB_STEP_SUMMARY is shared by
            # every step of the job.
            with open(summary_path, "a", encoding="utf-8") as handle:
                handle.write(render_summary(sarif_doc))
    if defectdojo_path:
        from core.defectdojo import build_findings

        dojo = build_findings(rendered)
        _Path(defectdojo_path).write_text(
            _json.dumps(dojo, indent=2, sort_keys=True) + NL, encoding="utf-8"
        )
        _echo(f"wrote {defectdojo_path} ({len(dojo['findings'])} finding(s))", err=True)
    if output:
        _Path(output).write_text(NL.join(lines) + NL, encoding="utf-8")
        _echo(f"wrote {output} ({len(lines)} contract(s))", err=True)
    else:
        for line in lines:
            click.echo(line)
    if fail_on:
        from core.risk.check import fail_on_threshold

        # The combined per-dependency verdict, exactly as `check` gates
        # it, so one run yields both the evidence and the CI decision.
        combined = [
            check_dependency(
                dep,
                loaded_events,
                bundles,
                as_of=evaluation.as_of,
                max_evidence_age=evaluation.max_evidence_age,
            )
            for dep in deps
        ]
        if fail_on_threshold(combined, fail_on):
            _echo(f"fail-on {fail_on}: threshold breached", err=True)
            raise SystemExit(1)


@cli.command()
@click.option("--store", default=".openpulse/observations", help="History root directory")
@click.option(
    "--projects", default="", help="Comma-separated slugs (default: every image in the catalog)"
)
@click.option("--out", default="", help="Write findings JSON here (default: print only)")
@_history_key_option
def sweep(store, projects, out, history_key_file=None, history_previous_keys_file=None):
    """Distribution discovery: probe every catalog image, diff against history."""
    from collectors.registries.docker import RegistryCollector
    from core.entities.catalog import load_catalog
    from core.observations.sweep import sweep_catalog, sweep_targets

    history_key, previous_keys = _load_history_key(
        history_key_file, history_previous_keys_file, store
    )
    catalog = load_catalog()
    slugs = [s.strip() for s in projects.split(",") if s.strip()] or None
    targets = sweep_targets(catalog)
    _echo(f"probing {len(targets)} catalog images...")
    collector = RegistryCollector()
    result = sweep_catalog(
        catalog,
        collector.check_image,
        store_root=store,
        slugs=slugs,
        history_key=history_key,
        previous_keys=previous_keys,
    )
    _echo(
        f"observations: {len(result['observations'])}, "
        f"changes: {len(result['changes'])}, "
        f"findings: {len(result['findings'])}, "
        f"errors: {len(result['errors'])}"
    )
    _echo(f"history key: {history_key.key_id if history_key else 'none (history is unkeyed)'}")
    for finding in result["findings"]:
        _echo(f"- [{finding['impact']}] {finding['title']}")
    for error in result["errors"]:
        _echo(f"! {error.get('slug')}: {error.get('safe_message')}")
    if not result["changes"]:
        _echo("no changes since last observations (first sightings are baselines).")
    if out:
        import json as _json
        from pathlib import Path as _Path

        _Path(out).write_text(_json.dumps(result["findings"], indent=2), encoding="utf-8")
        _echo(f"wrote {out}")


@cli.command()
@click.option("--watchlist", type=click.Path(exists=True), help="Watchlist YAML file")
@click.option("--sbom", type=click.Path(exists=True), help="CycloneDX SBOM (JSON)")
@click.option("--spdx", type=click.Path(exists=True), help="SPDX SBOM (JSON, 2.x)")
@click.option("--images", type=click.Path(exists=True), help="Container image inventory")
@click.option(
    "--lockfile", type=click.Path(exists=True), help="package-lock.json / poetry.lock / Cargo.lock"
)
@click.option(
    "--manifest",
    type=click.Path(exists=True),
    help="requirements.txt / pyproject.toml / pom.xml / go.mod / Cargo.toml",
)
@click.option(
    "--github-repo", "github_repo", type=str, default="", help="GitHub repository to inspect"
)
@_github_auth_options
@click.option(
    "--out",
    required=True,
    type=click.Path(file_okay=False),
    help="Directory for discovered event JSON (pass each to check --event)",
)
@click.option(
    "--max-targets",
    default=200,
    show_default=True,
    type=click.IntRange(min=1),
    help="Probe at most this many repositories/images (GitHub's anonymous quota is 60/hour)",
)
@click.option(
    "--max-packages",
    default=500,
    show_default=True,
    type=click.IntRange(min=1),
    help="Query OSV for at most this many packages",
)
def discover(
    watchlist,
    sbom,
    spdx,
    images,
    lockfile,
    manifest,
    github_repo,
    github_token,
    github_token_file,
    out,
    max_targets,
    max_packages,
):
    """Inventory-driven discovery: probe the repositories and images your
    dependencies name, and write the events their changes support.

    Targets come from the dependencies, not the catalog: Go module paths
    (github.com, gopkg.in, golang.org/x), github.com references and
    Docker Hub images. Every npm, PyPI, Maven, Go and crates.io package is
    also queried on OSV by its own name, so malicious and compromised
    versions are decided without a catalog entry; those advisories are
    written as bundles under OUT/bundles. Anything else is listed as
    unmapped with its reason. This is the networked step; check stays
    offline on what it writes.
    """
    import re as _re
    from pathlib import Path as _Path

    from core.discovery import discover as _discover
    from core.github_reader import get_github_token

    if github_token:
        _echo(
            "warning: --github-token is deprecated; use GITHUB_TOKEN or "
            "--github-token-file instead",
            err=True,
        )
    try:
        token = get_github_token(github_token, github_token_file)
    except OSError as exc:
        raise click.ClickException(f"cannot read GitHub token file: {exc.strerror or exc}") from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    deps, _events, _bundles, _inspections = _load_check_inputs(
        watchlist, sbom, spdx, images, lockfile, manifest, github_repo, token, (), None
    )
    result = _discover(deps, token, max_targets=max_targets, max_packages=max_packages)
    _echo(
        f"discover: {len(deps)} dependency(s) -> {len(result.targets)} target(s), "
        f"{len(result.unmapped)} unmapped"
    )
    for label, reason in result.unmapped:
        _echo(f"! unmapped: {label}: {reason}")
    if result.skipped_targets:
        _echo(f"! not probed: {len(result.skipped_targets)} target(s) over --max-targets")
    for target, message in result.errors:
        _echo(f"! error: {target.kind} {target.name}: {message}")
    directory = _Path(out)
    directory.mkdir(parents=True, exist_ok=True)
    for event in result.events:
        name = _re.sub(r"[^A-Za-z0-9._-]+", "_", event.id) + ".json"
        (directory / name).write_text(event.model_dump_json(indent=2), encoding="utf-8")
        _echo(f"- [{event.event_type.value}] {event.title} -> {directory / name}")
    _echo(f"{len(result.events)} event(s) written to {directory}")
    bundle_dir = directory / "bundles"
    for slug, raw in sorted(result.bundles.items()):
        path = bundle_dir / f"{slug}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    _echo(
        f"osv: {result.advisories} advisory record(s) for {len(result.bundles)} package(s)"
        + (f" -> check --raw-bundle-dir {bundle_dir}" if result.bundles else "")
    )
