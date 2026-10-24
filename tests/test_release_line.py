"""Release-line scope semantics - a cycle covers its patch releases.

Regression: lifecycle events are scoped to release lines (endoflife.date
cycles `4.2`, `13`), but scope matching compared versions for equality, so
every real pin (`django==4.2.11`, `postgres:13.5`) was reported
NOT_AFFECTED - a false clear - and unparseable versions were cleared too.
The fixtures pinned the cycle number itself (`django==4.2`), which hid it.
"""

import json
from datetime import date

import pytest

from core.risk.check import check_dependency
from core.schema.models import OSSEvent
from core.versions import in_release_line


@pytest.mark.parametrize(
    "version,line,expected",
    [
        ("4.2", "4.2", True),
        ("4.2.0", "4.2", True),
        ("4.2.11", "4.2", True),
        ("4.2.11", "4", True),
        ("13.5", "13", True),
        ("4.20.1", "4.2", False),
        ("130", "13", False),
        ("5.0", "4.2", False),
        ("4.2", "4.2.11", False),
        ("weird-ver", "4.2", None),
    ],
)
def test_in_release_line(version, line, expected):
    assert in_release_line(version, line) is expected


def _django_eol():
    with open("data/fixtures/django-eol/event.json", encoding="utf-8") as f:
        return OSSEvent(**json.load(f))


def _postgres_eol():
    from analyzers.change_analyst import analyze_endoflife
    from analyzers.lifecycle_events import finding_to_event

    with open("data/fixtures/postgresql/raw_bundle.json", encoding="utf-8") as f:
        raw = json.load(f)
    today = date(2026, 10, 24)
    return [
        finding_to_event(f, "postgresql", today=today)
        for f in analyze_endoflife(raw["endoflife"], today=today)
        if f["event_type"] == "EOL"
    ]


@pytest.mark.parametrize("version", ["4.2.11", "4.2.16", "4.2.0"])
def test_patch_pins_inside_an_eol_cycle_are_affected(version):
    verdict = check_dependency(
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": version},
        [_django_eol()],
    )
    assert verdict.affected is True
    assert verdict.relationship == "AFFECTS_VERSION"


@pytest.mark.parametrize("version", ["4.20.1", "5.0", "5.2.3"])
def test_other_release_lines_are_still_cleared(version):
    verdict = check_dependency(
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": version},
        [_django_eol()],
    )
    assert verdict.relationship == "NOT_AFFECTED"


def test_unparseable_version_is_never_cleared():
    verdict = check_dependency(
        {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "weird-ver"},
        [_django_eol()],
    )
    assert verdict.relationship != "NOT_AFFECTED"
    assert verdict.affected is False


@pytest.mark.parametrize(
    "ref", ["docker.io/postgres:13", "docker.io/postgres:13.5", "postgres:13.5-alpine"]
)
def test_image_tags_inside_an_eol_cycle_are_affected(ref):
    verdict = check_dependency({"kind": "image", "ref": ref}, _postgres_eol())
    assert verdict.relationship == "AFFECTS_VERSION"


@pytest.mark.parametrize("ref", ["docker.io/postgres:17.1", "docker.io/postgres:130"])
def test_image_tags_outside_the_cycle_are_cleared(ref):
    verdict = check_dependency({"kind": "image", "ref": ref}, _postgres_eol())
    assert verdict.relationship == "NOT_AFFECTED"


def test_lockfile_patch_pin_reaches_the_eol_event(tmp_path):
    """End to end through the lockfile reader, as a real poetry.lock reads."""
    from core.lockfile_reader import read_lockfile

    text = open("data/fixtures/lockfiles/poetry.lock", encoding="utf-8").read()
    lock = tmp_path / "poetry.lock"
    lock.write_text(text.replace('version = "4.2"', 'version = "4.2.16"', 1), encoding="utf-8")
    deps, _, _ = read_lockfile(str(lock))
    django = next(d for d in deps if d["package"] == "django")
    assert django["version"] == "4.2.16"
    assert check_dependency(django, [_django_eol()]).affected is True
