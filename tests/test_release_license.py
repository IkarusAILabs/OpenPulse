"""License changes between releases (v0.20.0 item C3).

Exit criterion: a license change between two releases of an npm or PyPI
package is reported from the licenses the registry records per release,
in version order (a backport never reads as a flip back), with the
releases it compared. Two spellings of one license, a release with no
license, a prerelease and an unreachable registry are never a change.
"""

from datetime import date

import pytest
from click.testing import CliRunner

from analyzers.change_analyst import DETECTION_RELEASE_METADATA, analyze_release_license_changes
from core.release_license import (
    COMPARED,
    NOT_PERFORMED,
    check,
    differs,
    npm_license,
    pypi_license,
    transitions,
)
from core.risk.impact import evaluate_impact

NPM = "https://registry.npmjs.org/widget"
PYPI = "https://pypi.org/pypi/widget/json"


def _registry(responses):
    """A fake fetch: url -> (status, document); anything else is unreachable."""
    seen = []

    def fetch(url):
        seen.append(url)
        return responses.get(url, (0, None))

    fetch.seen = seen
    return fetch


def _packument(*releases):
    """releases: (version, published, license value or a raw version document)."""
    versions, times = {}, {}
    for version, published, value in releases:
        versions[version] = value if isinstance(value, dict) else {"license": value}
        times[version] = published
    return {"name": "widget", "versions": versions, "time": times}


# --- reading one release's license ------------------------------------------------------


@pytest.mark.parametrize(
    ("meta", "expected"),
    [
        ({"license": "MIT"}, ("declared", "MIT")),
        ({"license": {"type": "BSD-3-Clause", "url": "x"}}, ("declared", "BSD-3-Clause")),
        (
            {"licenses": [{"type": "MIT"}, {"type": "Apache-2.0"}]},
            ("declared", "Apache-2.0 OR MIT"),
        ),
        ({"license": "UNLICENSED"}, ("declared", "UNLICENSED")),
        ({"license": "MIT\nfake"}, ("declared", "MIT fake")),
        ({"license": "x" * 129}, None),
        ({"license": "UNKNOWN"}, None),
        ({}, None),
        ("not a mapping", None),
    ],
)
def test_npm_license(meta, expected):
    assert npm_license(meta) == expected


def test_pypi_license_prefers_the_expression_then_a_short_field_then_classifiers():
    classifiers = ["License :: OSI Approved :: MIT License", "Programming Language :: Python"]
    assert pypi_license(
        {"license_expression": "MIT", "license": "BSD", "classifiers": classifiers}
    ) == ("expression", "MIT")
    assert pypi_license({"license": "BSD-3-Clause", "classifiers": classifiers}) == (
        "field",
        "BSD-3-Clause",
    )
    full_text = "Copyright (c) 2020\nPermission is hereby granted..."
    assert pypi_license({"license": full_text, "classifiers": classifiers}) == (
        "classifier",
        "MIT License",
    )
    assert pypi_license({"license": "UNKNOWN", "classifiers": []}) is None


def test_differs_only_compares_like_with_like():
    assert differs(("declared", "MIT"), ("declared", "BUSL-1.1")) is True
    assert differs(("declared", "MIT"), ("declared", "mit")) is False
    assert differs(("declared", "(MIT OR Apache-2.0)"), ("declared", "MIT OR Apache-2.0")) is False
    assert differs(("field", "MIT"), ("classifier", "MIT License")) is None  # two spellings
    assert differs(("field", "MIT"), ("expression", "MIT")) is False
    assert differs(None, ("declared", "MIT")) is None


def test_a_release_without_a_license_is_skipped_not_a_change():
    releases = [
        {"version": "1.0.0", "published": None, "license": ("declared", "MIT")},
        {"version": "1.1.0", "published": None, "license": None},
        {"version": "1.2.0", "published": None, "license": ("declared", "MIT")},
    ]
    assert transitions(releases) == []


# --- npm --------------------------------------------------------------------------------


def _relicensed():
    return _packument(
        ("1.0.0", "2025-01-01T00:00:00.000Z", "BSD-3-Clause"),
        ("1.1.0", "2025-03-01T00:00:00.000Z", "BSD-3-Clause"),
        ("2.0.0-rc.1", "2025-05-01T00:00:00.000Z", "MIT"),
        ("2.0.0", "2025-06-01T00:00:00.000Z", "MIT"),
        # A backport published after 2.0.0 keeps the old license.
        ("1.2.0", "2025-07-01T00:00:00.000Z", "BSD-3-Clause"),
        ("2.1.0", "2025-09-01T00:00:00.000Z", "MIT"),
    )


def test_npm_transitions_follow_version_order_not_publish_time():
    result = check("npm", "widget", fetch_json=_registry({NPM: (200, _relicensed())}))
    assert result["status"] == COMPARED
    assert result["purl"] == "pkg:npm/widget"
    assert result["latest"] == {
        "version": "2.1.0",
        "license": "MIT",
        "published": "2025-09-01T00:00:00.000Z",
    }
    assert result["releases_compared"] == 5  # the prerelease is left out
    assert result["transitions"] == [
        {
            "from_version": "1.2.0",
            "to_version": "2.0.0",
            "from_license": "BSD-3-Clause",
            "to_license": "MIT",
            "published": "2025-06-01T00:00:00.000Z",
            "between_compared": True,
        }
    ]


def test_with_a_version_every_change_after_it_is_listed():
    doc = _packument(
        ("1.0.0", "2025-01-01T00:00:00.000Z", "MIT"),
        ("2.0.0", "2025-02-01T00:00:00.000Z", "Apache-2.0"),
        ("3.0.0", "2025-03-01T00:00:00.000Z", "BUSL-1.1"),
    )
    fetch = _registry({NPM: (200, doc)})
    after_one = check("npm", "widget", "1.0.0", fetch_json=fetch)["transitions"]
    assert [t["to_version"] for t in after_one] == ["2.0.0", "3.0.0"]
    after_two = check("npm", "widget", "2.0.0", fetch_json=fetch)["transitions"]
    assert [t["to_version"] for t in after_two] == ["3.0.0"]
    assert check("npm", "widget", "3.0.0", fetch_json=fetch)["transitions"] == []
    # Without a version: the most recent change only.
    assert [t["to_version"] for t in check("npm", "widget", fetch_json=fetch)["transitions"]] == [
        "3.0.0"
    ]


def test_scoped_npm_packages_get_an_encoded_purl():
    url = "https://registry.npmjs.org/@acme/widget"
    doc = _packument(("1.0.0", "2025-01-01T00:00:00.000Z", "MIT"))
    result = check("npm", "@acme/widget", fetch_json=_registry({url: (200, doc)}))
    assert result["purl"] == "pkg:npm/%40acme/widget"


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        ((404, None), "no such package"),
        ((500, None), "no usable answer"),
        ((0, None), "over the size cap"),
        ((200, ["not", "a", "packument"]), "no usable answer"),
        ((200, {"versions": {"1.0.0-beta": {"license": "MIT"}}}), "no main-line release"),
    ],
)
def test_npm_without_an_answer_is_not_performed(response, reason):
    result = check("npm", "widget", fetch_json=_registry({NPM: response}))
    assert result["status"] == NOT_PERFORMED
    assert reason in result["reason"]
    assert result["transitions"] == []


def test_a_version_the_registry_does_not_list_is_not_performed():
    result = check("npm", "widget", "9.9.9", fetch_json=_registry({NPM: (200, _relicensed())}))
    assert result["status"] == NOT_PERFORMED
    assert "not a main-line release" in result["reason"]


@pytest.mark.parametrize(
    ("ecosystem", "name", "version", "reason"),
    [
        ("Maven", "org.example/widget", None, "only npm and PyPI"),
        ("npm", "../etc/passwd", None, "grammar"),
        ("npm", "Widget", None, "grammar"),
        ("npm", "widget", "1.0.0/../x", "grammar"),
        ("PyPI", "wid get", None, "grammar"),
    ],
)
def test_untrusted_identifiers_never_reach_a_url(ecosystem, name, version, reason):
    fetch = _registry({})
    result = check(ecosystem, name, version, fetch_json=fetch)
    assert result["status"] == NOT_PERFORMED and reason in result["reason"]
    assert fetch.seen == []


def test_a_malformed_document_is_not_performed_never_a_crash():
    doc = {"versions": {"1.0.0": {"license": "MIT"}}, "time": "not a mapping"}
    assert check("npm", "widget", fetch_json=_registry({NPM: (200, doc)}))["status"] == COMPARED
    result = check("PyPI", "widget", fetch_json=_registry({PYPI: (200, {"info": 5})}))
    assert result["status"] == NOT_PERFORMED


# --- PyPI -------------------------------------------------------------------------------


def _files(when):
    return [{"filename": "widget-x.tar.gz", "upload_time_iso_8601": when}]


def _pypi(latest_info, versions):
    return {
        "info": {"version": latest_info.pop("version"), **latest_info},
        "releases": {
            v: _files(f"2025-0{i + 1}-01T00:00:00.000000Z") for i, v in enumerate(versions)
        },
    }


def test_pypi_compares_the_latest_with_the_release_before_it():
    project = _pypi({"version": "2.0", "license_expression": "BUSL-1.1"}, ["1.0", "1.1", "2.0"])
    fetch = _registry(
        {
            PYPI: (200, project),
            "https://pypi.org/pypi/widget/1.1/json": (200, {"info": {"license_expression": "MIT"}}),
        }
    )
    result = check("PyPI", "widget", fetch_json=fetch)
    assert result["status"] == COMPARED
    assert result["releases_compared"] == 2
    assert result["transitions"] == [
        {
            "from_version": "1.1",
            "to_version": "2.0",
            "from_license": "MIT",
            "to_license": "BUSL-1.1",
            "published": "2025-03-01T00:00:00.000000Z",
            "between_compared": True,
        }
    ]
    assert len(fetch.seen) == 2


def test_pypi_with_a_distant_version_says_the_releases_between_were_not_compared():
    project = _pypi({"version": "3.0", "license": "Apache-2.0"}, ["1.0", "2.0", "2.1rc1", "3.0"])
    fetch = _registry(
        {
            PYPI: (200, project),
            "https://pypi.org/pypi/widget/1.0/json": (200, {"info": {"license": "MIT"}}),
        }
    )
    # PEP 440: 1.0.0 is the registry's 1.0.
    result = check("PyPI", "widget", "1.0.0", fetch_json=fetch)
    [transition] = result["transitions"]
    assert (transition["from_version"], transition["to_version"]) == ("1.0", "3.0")
    assert transition["between_compared"] is False


def test_pypi_two_spellings_are_not_comparable_and_not_a_change():
    project = _pypi(
        {
            "version": "2.0",
            "license": None,
            "classifiers": ["License :: OSI Approved :: MIT License"],
        },
        ["1.0", "2.0"],
    )
    fetch = _registry(
        {
            PYPI: (200, project),
            "https://pypi.org/pypi/widget/1.0/json": (200, {"info": {"license": "MIT"}}),
        }
    )
    result = check("PyPI", "widget", fetch_json=fetch)
    assert result["transitions"] == []
    assert result["not_comparable"] == [{"from_version": "1.0", "to_version": "2.0"}]


def test_pypi_with_one_release_has_nothing_to_compare():
    project = _pypi({"version": "1.0", "license": "MIT"}, ["1.0"])
    result = check("PyPI", "widget", fetch_json=_registry({PYPI: (200, project)}))
    assert result["status"] == NOT_PERFORMED and "no earlier release" in result["reason"]


# --- findings ---------------------------------------------------------------------------


def test_a_transition_becomes_a_license_change_for_review():
    result = check("npm", "widget", "1.0.0", fetch_json=_registry({NPM: (200, _relicensed())}))
    [finding] = analyze_release_license_changes(result, today=date(2026, 11, 8))
    assert finding["event_type"] == "LICENSE_CHANGE"
    assert finding["detection_method"] == DETECTION_RELEASE_METADATA
    assert finding["evidence_strength"] == "moderate"
    assert finding["effective_at"] == "2025-06-01T00:00:00.000Z"
    assert finding["first_detected_at"] is None
    assert finding["affected_artifacts"] == [{"kind": "package", "ref": "pkg:npm/widget"}]
    assert finding["scope"]["packages"] == ["pkg:npm/widget"]
    assert finding["references"] == ["https://www.npmjs.com/package/widget/v/2.0.0"]
    assert "from BSD-3-Clause to MIT in 2.0.0" in finding["title"]
    assert finding["registry_evidence"]["between_compared"] is True
    assessed = evaluate_impact(finding, today=date(2026, 11, 8))
    assert assessed["eligibility"] == "REVIEW"


def test_a_change_with_uncompared_releases_between_says_so():
    result = {
        "status": COMPARED,
        "ecosystem": "PyPI",
        "name": "widget",
        "purl": "pkg:pypi/widget",
        "releases_compared": 2,
        "transitions": [
            {
                "from_version": "1.0",
                "to_version": "3.0",
                "from_license": "MIT",
                "to_license": "BUSL-1.1",
                "published": "2026-01-01T00:00:00Z",
                "between_compared": False,
            }
        ],
    }
    [finding] = analyze_release_license_changes(result)
    assert "by 3.0" in finding["title"]
    assert "somewhere after 1.0, at the latest in 3.0" in finding["summary"]
    assert finding["references"] == ["https://pypi.org/project/widget/3.0/"]


def test_nothing_is_found_when_nothing_was_compared():
    assert analyze_release_license_changes({"status": NOT_PERFORMED, "transitions": []}) == []


# --- the commands -----------------------------------------------------------------------


def test_report_sweep_keeps_only_recent_release_license_changes(capsys):
    from cli.main import _catalog_release_licenses

    recent = _packument(
        ("1.0.0", "2026-01-01T00:00:00.000Z", "MIT"),
        ("2.0.0", "2026-10-01T00:00:00.000Z", "BUSL-1.1"),
    )
    old = _packument(
        ("1.0.0", "2017-01-01T00:00:00.000Z", "BSD-3-Clause"),
        ("2.0.0", "2017-09-26T00:00:00.000Z", "MIT"),
    )
    fetch = _registry(
        {
            NPM: (200, recent),
            "https://registry.npmjs.org/oldie": (200, old),
        }
    )
    catalog = [
        {"slug": "w", "packages": [{"ecosystem": "npm", "name": "widget"}]},
        {"slug": "o", "packages": [{"ecosystem": "npm", "name": "oldie"}]},
        {"slug": "m", "packages": [{"ecosystem": "Maven", "name": "org.example/widget"}]},
        {"slug": "gone", "packages": [{"ecosystem": "npm", "name": "gone"}]},
    ]
    findings = _catalog_release_licenses(catalog, today=date(2026, 11, 8), fetch_json=fetch)
    assert [f["title"] for f in findings] == [
        "widget (npm) changed its license from MIT to BUSL-1.1 in 2.0.0"
    ]
    assert "release licenses skipped for pkg:npm/gone" in capsys.readouterr().out


def test_release_license_command(monkeypatch):
    from cli.main import cli
    from core import digest_integrity

    monkeypatch.setattr(digest_integrity, "default_fetch", _registry({NPM: (200, _relicensed())}))
    runner = CliRunner()
    result = runner.invoke(
        cli, ["release-license", "--ecosystem", "npm", "--package", "widget", "--version", "1.0.0"]
    )
    assert result.exit_code == 0, result.output
    assert "latest 2.1.0 is licensed MIT" in result.output
    assert "[LICENSE_CHANGE]" in result.output

    result = runner.invoke(
        cli, ["release-license", "--ecosystem", "npm", "--package", "widget", "--version", "2.1.0"]
    )
    assert result.exit_code == 0 and "no license change after 2.1.0" in result.output

    result = runner.invoke(cli, ["release-license", "--ecosystem", "npm", "--package", "Bad Name"])
    assert result.exit_code == 1 and "not compared" in result.output


# --- an empty store is refused ----------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["observe-github", "--repo", "a/b", "--store", ""],
        ["observe", "--namespace", "a", "--repo", "b", "--store", " "],
    ],
)
def test_an_empty_observation_store_is_refused(argv, tmp_path, monkeypatch):
    from cli.main import cli

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, argv)
    assert result.exit_code == 2
    assert "needs a directory" in result.output
    assert list(tmp_path.iterdir()) == []
