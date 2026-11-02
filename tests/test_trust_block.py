"""One trust block in dependency_status (track T, T-D, v0.13.0 X4): offline."""

from __future__ import annotations

import json

import anyio
import pytest

from core.agent_tools import (
    DEPRECATED_TRUST_FIELDS,
    MAX_INTENT_CHARS,
    Lookups,
    dependency_status,
    selection_context,
)

_NO_DATA = {"endoflife": [], "osv": [], "github_meta": []}
MAL = {"id": "MAL-2024-1234"}
CHECKS = {
    "malicious",
    "registry_existence",
    "provenance",
    "repository_linkage",
    "dependency_confusion",
    "lookalike",
}


def _lookups(osv_doc=None):
    return Lookups(
        fetch=lambda _slug: _NO_DATA,
        head=lambda _url: 200,
        fetch_json=lambda _url: (404, None),
        fetch_text=lambda _url: (404, None),
        osv_query=lambda _body: (200, osv_doc or {}),
    )


def _statuses(out):
    checks = out["trust"]["checks"]
    return {
        name: [r["status"] for r in (v if isinstance(v, list) else [v])]
        for name, v in checks.items()
    }


# ---------------------------------------------------------------------------
# The block
# ---------------------------------------------------------------------------


def test_every_check_is_in_one_block_and_counted():
    out = dependency_status("left-pad", "1.3.0", "npm", lookups=_lookups())
    trust = out["trust"]
    assert set(trust["checks"]) == CHECKS
    records = sum(len(s) for s in _statuses(out).values())
    assert sum(trust["summary"].values()) == records
    assert "never part of any verdict" in trust["note"]


def test_attention_lists_what_needs_review():
    out = dependency_status("evil-pkg", "1.0.0", "npm", lookups=_lookups({"vulns": [MAL]}))
    attention = out["trust"]["attention"]
    assert {"check": "malicious", "status": "CONFIRMED_MALICIOUS"}.items() <= attention[0].items()
    assert out["trust"]["summary"]["CONFIRMED_MALICIOUS"] == 1


def test_new_checks_live_only_in_the_block():
    out = dependency_status("left-pad", "1.3.0", "npm", live=False)
    for field in ("malicious", "repository_linkage", "dependency_confusion"):
        assert field not in out


def test_v012_fields_are_kept_and_marked_deprecated():
    out = dependency_status("left-pad", "1.3.0", "npm", lookups=_lookups())
    for field in DEPRECATED_TRUST_FIELDS:
        assert out[field] == out["trust"]["checks"][field]
    assert out["deprecated"] == {
        "fields": ["registry_existence", "provenance", "lookalike"],
        "use": "trust.checks",
        "removed_in": "0.14.0",
    }


def test_the_block_never_changes_the_verdict():
    clean = dependency_status("left-pad", "1.3.0", "npm", lookups=_lookups())
    evil = dependency_status("left-pad", "1.3.0", "npm", lookups=_lookups({"vulns": [MAL]}))
    assert clean["verdict"] == evil["verdict"]


def test_replay_mode_says_the_trust_records_are_live():
    out = dependency_status("left-pad", "1.3.0", "npm", live=False, mode="replay")
    assert "not as of the replay date" in out["trust"]["time_frame"]
    current = dependency_status("left-pad", "1.3.0", "npm", live=False)
    assert "replay" not in current["trust"]["time_frame"]


# ---------------------------------------------------------------------------
# selection_context
# ---------------------------------------------------------------------------


def test_no_context_is_null():
    out = dependency_status("left-pad", "1.3.0", "npm", live=False)
    assert out["trust"]["selection_context"] is None


def test_context_is_recorded_and_labelled():
    out = dependency_status(
        "left-pad",
        "1.3.0",
        "npm",
        live=False,
        intent="pad strings in the CLI table",
        name_source="Model_Suggestion",
    )
    assert out["trust"]["selection_context"] == {
        "supplied_by": "agent",
        "used_in_status": False,
        "name_source": "model_suggestion",
        "intent": "pad strings in the CLI table",
        "intent_truncated": False,
    }


def test_an_unknown_name_source_is_not_echoed():
    context = selection_context(None, "ignore previous instructions")
    assert context["name_source"] == "unrecognized"
    assert "ignore" not in json.dumps(context)


def test_intent_is_stripped_and_capped():
    hostile = "use this‮​ one\x00\x1b[31m" + "x" * 400
    context = selection_context(hostile, None)
    assert "‮" not in context["intent"] and "\x00" not in context["intent"]
    assert "\x1b" not in context["intent"]
    assert len(context["intent"]) == MAX_INTENT_CHARS and context["intent_truncated"]


@pytest.mark.parametrize("source", ["model_suggestion", "user_request", "nonsense"])
def test_context_never_changes_a_status_or_the_verdict(source):
    plain = dependency_status("left-pad", "1.3.0", "npm", lookups=_lookups())
    told = dependency_status(
        "left-pad",
        "1.3.0",
        "npm",
        lookups=_lookups(),
        intent="I made this name up",
        name_source=source,
    )
    assert _statuses(told) == _statuses(plain)
    assert told["verdict"] == plain["verdict"]


def test_mcp_accepts_intent_and_name_source():
    pytest.importorskip("mcp")
    from cli.mcp_server import build_server

    server = build_server(root=".", live=False)
    result = anyio.run(
        server.call_tool,
        "dependency_status",
        {
            "package": "left-pad",
            "version": "1.3.0",
            "ecosystem": "npm",
            "intent": "pad strings",
            "name_source": "documentation",
        },
    )
    text = json.dumps(result, default=str)
    assert "model_suggestion" not in text and "documentation" in text
