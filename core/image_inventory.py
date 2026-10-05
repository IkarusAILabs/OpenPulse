"""Image inventory input — container refs become checkable deps.

A container image inventory is the deployment-side counterpart of a
watchlist: the `image:tag` (or pinned `image@sha256:...`) list a team
actually runs. Entries map to `{kind: image, ref}` through the same
identity semantics the watchlist path already uses
(`split_image_ref`/`tag_of` — no second matching engine), then flow
through `core.risk.check.check_dependency` unchanged.

Accepted shapes (autodetected, because inventories come from `docker
images --format`, Helm values dumps, and by hand):

- one ref per line; blank lines and `#` comments allowed
- a simple YAML list of string refs (`- redis:7.2`)
- a YAML mapping with an `images:` list of string refs

Malformed lines are skipped and recorded, never guessed into refs;
tag-vs-digest pinning policy lives in `core.risk.match`
(`tag_vs_digest_policy`) and is enforced by tests, not re-derived here.
No new dependencies; no network.
"""

from __future__ import annotations

import os
import re
from typing import Any

#: Size cap for inventory files. The 50MB `MAX_SBOM_BYTES` allowance
#: exists because SBOMs are legitimately multi-MB; an inventory is one
#: ref per line, so 1MB (~80k refs) is generous and keeps the
#: bounded-read policy: no unbounded file into memory.
MAX_INVENTORY_BYTES = 1024 * 1024

_REF_CHARS = re.compile(r"^[A-Za-z0-9._/\-:@]+$")


def _ref_ok(ref: str) -> bool:
    """Cheap structural sanity: non-empty, plausible characters only.

    Deliberately permissive about the exact grammar (registries
    disagree); the identity layer (`split_image_ref`) owns real
    parsing. This only refuses lines that cannot be a ref at all —
    including bare names like `redis`, which resolve to the Hub
    library namespace downstream.
    """
    return bool(ref) and bool(_REF_CHARS.match(ref))


def _normalize_entry(entry: Any, origin: str) -> tuple[dict[str, Any] | None, str | None]:
    """One inventory entry -> (dep, None) or (None, skip reason).

    Always a 2-tuple: a bare dict return would unpack its keys when
    callers write `dep, reason = ...` — a failure mode this function
    exists to make impossible.
    """
    if isinstance(entry, dict):
        # A YAML list item written as a mapping is the one structured
        # form worth accepting: `{ref: ...}` mirrors the watchlist.
        ref = entry.get("ref")
        if isinstance(ref, str) and _ref_ok(ref.strip()):
            return {"kind": "image", "ref": ref.strip()}, None
        return None, f"{origin}: mapping entry needs a string `ref`"
    if isinstance(entry, str):
        ref = entry.strip()
        if not ref:
            return None, f"{origin}: empty entry"
        if not _ref_ok(ref):
            return None, f"`{ref}` is not a plausible image ref"
        return {"kind": "image", "ref": ref}, None
    return None, f"{origin}: entry must be a string (or mapping with `ref`)"


def load_image_inventory_doc(
    doc: Any, source: str = "inventory"
) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse an already-loaded inventory document (YAML or string).

    Autodetects the three shapes; returns (deps, skipped) where every
    refusal is recorded, never guessed. Pure function.
    """
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    if isinstance(doc, str):
        lines = [ln.strip() for ln in doc.splitlines()]
        entries: list[Any] = [ln for ln in lines if ln and not ln.startswith("#")]
        for i, entry in enumerate(entries):
            dep, reason = _normalize_entry(entry, f"line {i + 1}")
            if dep is None:
                skipped.append(reason)
            else:
                deps.append(dep)
        return deps, skipped
    if isinstance(doc, list):
        for i, entry in enumerate(doc):
            dep, reason = _normalize_entry(entry, f"entry #{i + 1}")
            if dep is None:
                skipped.append(reason)
            else:
                deps.append(dep)
        return deps, skipped
    if isinstance(doc, dict):
        images = doc.get("images")
        if not isinstance(images, list):
            raise ValueError(f"{source} must be a ref list, or a mapping with an `images` list")
        return load_image_inventory_doc(images, source=source)
    raise ValueError(f"{source} must be a ref list, a `images:` mapping, or one ref per line")


def read_image_inventory(path: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Load an inventory file from disk (line/YAML autodetect).

    Bounded read: over the cap is a clean ValueError naming it.
    """
    size = os.path.getsize(path)
    if size > MAX_INVENTORY_BYTES:
        raise ValueError(f"{source_label(path)} is {size} bytes (limit {MAX_INVENTORY_BYTES})")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # YAML list/mapping vs plain line format: a leading `- ` item or
    # a mapping key is YAML; anything else is treated as line format.
    stripped = text.strip()
    if stripped.startswith("-") or stripped.startswith("images:") or "\nimages:" in text:
        try:
            import yaml

            doc = yaml.safe_load(stripped)
        except yaml.YAMLError as e:
            raise ValueError(f"{path}: not a parseable inventory ({e})") from e
        return load_image_inventory_doc(doc, source=source_label(path))
    return load_image_inventory_doc(stripped, source=source_label(path))


def source_label(path: str) -> str:
    """Stable label for messages: the basename, or the path as given."""
    return os.path.basename(path) if path else "inventory"
