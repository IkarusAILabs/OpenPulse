"""Derived source authority (v0.9.0 item B1, finding M1).

``official`` is derived from ``data/official_domains.yaml``, never taken
from the source's own claim. A forged ``official`` must not reach
CONFIRMED.
"""

import json

import pytest
from click.testing import CliRunner

from core.evidence.authority import derive_authority, is_official, load_official_domains
from core.evidence.policy import gate
from core.schema.models import OSSEvent

DOMAINS = {
    "django": ("djangoproject.com", "github.com/django"),
    "redis": ("redis.io",),
}


@pytest.mark.parametrize(
    "url",
    [
        "https://djangoproject.com/",
        "https://www.djangoproject.com/download/",
        "https://WWW.DjangoProject.com/download/",
        "https://docs.djangoproject.com:443/en/5.0/",
        "https://github.com/django",
        "https://github.com/django/django/releases",
        "https://github.com/Django/django",
    ],
)
def test_allowlisted_https_locations_are_official(url):
    assert is_official(url, "django", DOMAINS)


@pytest.mark.parametrize(
    "url",
    [
        # lookalike hosts
        "https://evil-redis.io/",
        "https://redis.io.evil.com/",
        "https://redisio.com/",
        # wrong scheme, credentials, port
        "http://redis.io/",
        "ftp://redis.io/",
        "https://redis.io@evil.com/",
        "https://user@redis.io/",
        "https://redis.io:8443/",
        # internationalised lookalikes (Cyrillic "е"), raw and punycode
        "https://rеdis.io/",
        "https://xn--rdis-5qd.io/",
        # garbage
        "redis.io",
        "",
        "https://[::1/",
    ],
)
def test_lookalike_or_unsafe_locations_are_not_official(url):
    assert not is_official(url, "redis", DOMAINS)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/django-fork/django",
        "https://github.com/djangoproject",
        "https://gist.github.com/django/abc",
        "https://github.com/evil/django",
        "https://github.com/",
    ],
)
def test_shared_host_counts_only_under_the_listed_path(url):
    assert not is_official(url, "django", DOMAINS)


def test_project_without_allowlist_has_no_official_sources():
    assert not is_official("https://www.djangoproject.com/", "unlisted", DOMAINS)
    assert not is_official("https://www.djangoproject.com/", "redis", DOMAINS)


def test_derive_authority_downgrades_with_a_reason():
    forged = {"name": "x", "authority": "official", "url": "https://evil-redis.io/"}
    authority, reason = derive_authority(forged, "redis", DOMAINS)
    assert authority == "secondary"
    assert reason == (
        "source 'x' claims authority=official, but https://evil-redis.io/ is not "
        "an https location on the official_domains allowlist for 'redis'"
    )
    # Only official is derived; other claims pass through untouched.
    assert derive_authority({"authority": "primary", "url": "http://x"}, "redis", DOMAINS) == (
        "primary",
        None,
    )


def _event(url: str, project: str = "django", event_type: str = "LICENSE_CHANGE") -> OSSEvent:
    return OSSEvent(
        id="evt-forged",
        project_slug=project,
        event_type=event_type,
        title="forged",
        summary="forged official source",
        confidence="CONFIRMED",
        impact="REVIEW",
        affected_artifacts=[{"kind": "pypi", "ref": "django"}],
        evidences=[
            {
                "source": {
                    "name": "claimed-official",
                    "url": url,
                    "authority": "official",
                    "fetched_at": "2026-10-01T00:00:00Z",
                },
                "excerpt": "x",
                "announcement_date": "2026-10-01",
            }
        ],
    )


@pytest.mark.parametrize(
    "url",
    ["https://djangoproject.com.evil.com/", "http://www.djangoproject.com/"],
)
def test_forged_official_cannot_reach_confirmed(url):
    violations = gate(_event(url))
    assert any("CONFIRMED requires" in v for v in violations)
    assert any("not an https location on the official_domains allowlist" in v for v in violations)


def test_forged_official_cannot_confirm_a_lifecycle_event():
    violations = gate(_event("https://evil.example/", event_type="EOL"))
    assert any("CONFIRMED requires" in v for v in violations)


def test_allowlisted_official_still_confirms():
    assert gate(_event("https://www.djangoproject.com/download/")) == []


def test_validate_cli_rejects_a_forged_official(tmp_path):
    """Where users hit it: `openpulse validate --strict` fails."""
    from cli.main import cli

    path = tmp_path / "event.json"
    path.write_text(_event("https://djangoproject.com.evil.com/").model_dump_json(), "utf-8")
    result = CliRunner().invoke(cli, ["validate", "--event", str(path), "--strict"])
    assert result.exit_code == 1
    assert "official_domains allowlist" in result.output


def test_curated_official_fixtures_pass_the_gate():
    """No curated fixture loses CONFIRMED except the synthetic leftpad one."""
    for name in (
        "bitnami",
        "breaking-change-migration",
        "django-eol",
        "itext-license",
        "spark-mainline-empty",
        "terraform-support-change",
    ):
        with open(f"data/fixtures/{name}/event.json", encoding="utf-8") as f:
            assert gate(OSSEvent(**json.load(f))) == [], name


def test_allowlist_hygiene():
    """Shared hosts are listed only with a path; entries are bare locations."""
    shared = {"github.com", "gitlab.com", "bitbucket.org", "medium.com", "dev.to"}
    domains = load_official_domains()
    assert domains, "data/official_domains.yaml is missing or empty"
    for slug, entries in domains.items():
        assert entries, slug
        for entry in entries:
            assert "://" not in entry and " " not in entry, (slug, entry)
            host = entry.split("/", 1)[0]
            assert host.isascii() and "." in host, (slug, entry)
            if host in shared:
                assert "/" in entry, f"{slug}: shared host {host} needs a path"
