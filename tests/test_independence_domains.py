"""Derived independence (v0.9.0 item B2, finding M2).

Two pages on one site are one source, whatever names or families their
producer gives them. Same-domain sources can't reach CORROBORATED.
"""

import pytest
from click.testing import CliRunner

from analyzers.evidence_analyst import assess_confidence
from core.evidence.domains import registrable_domain, url_family
from core.evidence.independence import independent_count
from core.evidence.policy import gate
from core.schema.models import OSSEvent


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("redis.io", "redis.io"),
        ("blog.redis.io", "redis.io"),
        ("a.b.c.redis.io", "redis.io"),
        ("www.bbc.co.uk", "bbc.co.uk"),
        ("news.bbc.co.uk", "bbc.co.uk"),
        ("REDIS.IO.", "redis.io"),
        ("bitnami.github.io", "bitnami.github.io"),
        ("10.0.0.1", "10.0.0.1"),
        ("localhost", "localhost"),
    ],
)
def test_registrable_domain(host, expected):
    assert registrable_domain(host) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://redis.io/blog/a", "redis.io"),
        ("http://docs.redis.io/", "redis.io"),
        ("https://github.com/bitnami/charts/issues/1", "github.com/bitnami"),
        ("https://github.com/Bitnami/containers", "github.com/bitnami"),
        ("https://github.com/", "github.com"),
        ("https://user@redis.io:8443/x", "redis.io"),
        ("", None),
        ("not a url", None),
        ("https://[::1/", None),
    ],
)
def test_url_family(url, expected):
    assert url_family(url) == expected


def _ev(name, url=None, family=None, derived_from=None, authority="secondary"):
    source = {"name": name, "authority": authority}
    if url:
        source["url"] = url
    if family:
        source["family"] = family
    if derived_from:
        source["derived_from"] = derived_from
    return {"source": source}


def test_same_site_with_different_names_is_one_source():
    """The M2 bug: renamed copies on one site counted twice."""
    assert independent_count([_ev("a", "https://redis.io/x"), _ev("b", "https://redis.io/y")]) == 1


def test_declared_families_cannot_split_one_site():
    evidences = [
        _ev("a", "https://blog.redis.io/x", family="redis-blog"),
        _ev("b", "https://docs.redis.io/y", family="redis-docs"),
    ]
    assert independent_count(evidences) == 1


def test_declared_family_can_still_merge_two_sites():
    evidences = [
        _ev("a", "https://redis.io/x", family="redis"),
        _ev("b", "https://redis.com/y", family="redis"),
    ]
    assert independent_count(evidences) == 1


def test_different_owners_on_a_shared_host_stay_independent():
    evidences = [
        _ev("a", "https://github.com/bitnami/charts/issues/1"),
        _ev("b", "https://github.com/someone-else/notes"),
    ]
    assert independent_count(evidences) == 2


def test_independent_sites_still_corroborate():
    evidences = [_ev("a", "https://lwn.net/x"), _ev("b", "https://www.theregister.com/y")]
    assert independent_count(evidences) == 2
    assert assess_confidence(evidences) == "CORROBORATED"


def test_links_are_transitive():
    """a~b by site, b~c by derived_from: one group, not two."""
    evidences = [
        _ev("a", "https://redis.io/x"),
        _ev("b", "https://redis.io/y"),
        _ev("c", "https://mirror.example/z", derived_from="b"),
    ]
    assert independent_count(evidences) == 1


def test_sources_without_urls_keep_pre_b2_behaviour():
    assert independent_count([_ev("a"), _ev("b")]) == 2
    assert independent_count([_ev("a", family="x"), _ev("b", family="x")]) == 1
    assert independent_count([_ev("a", family="redis"), _ev("redis")]) == 1
    assert independent_count([{"source": {}}, {"source": {}}]) == 1


def test_same_site_cannot_be_assessed_corroborated():
    evidences = [
        _ev("a", "https://redis.io/x", family="f1"),
        _ev("b", "https://www.redis.io/y", family="f2"),
    ]
    assert assess_confidence(evidences) == "EMERGING"


def _event(urls_and_families):
    return OSSEvent(
        id="evt-same-site",
        project_slug="redis",
        event_type="LICENSE_CHANGE",
        title="same site",
        summary="two pages on one site",
        confidence="CORROBORATED",
        impact="REVIEW",
        affected_artifacts=[{"kind": "docker-image", "ref": "docker.io/redis"}],
        evidences=[
            {
                "source": {
                    "name": f"src-{i}",
                    "url": url,
                    "authority": "secondary",
                    "family": family,
                    "fetched_at": "2026-10-01T00:00:00Z",
                },
                "excerpt": "x",
                "announcement_date": "2026-10-01",
            }
            for i, (url, family) in enumerate(urls_and_families)
        ],
    )


def test_gate_rejects_same_site_corroboration():
    event = _event([("https://redis.io/a", "one"), ("https://blog.redis.io/b", "two")])
    assert any("CORROBORATED requires" in v for v in gate(event))


def test_gate_accepts_independent_sites():
    event = _event([("https://lwn.net/a", None), ("https://www.theregister.com/b", None)])
    assert gate(event) == []


def test_validate_cli_rejects_same_site_corroboration(tmp_path):
    """Where users hit it: `openpulse validate --strict` fails."""
    from cli.main import cli

    path = tmp_path / "event.json"
    event = _event([("https://redis.io/a", "one"), ("https://blog.redis.io/b", "two")])
    path.write_text(event.model_dump_json(), "utf-8")
    result = CliRunner().invoke(cli, ["validate", "--event", str(path), "--strict"])
    assert result.exit_code == 1
    assert "CORROBORATED requires" in result.output
