"""Deprecated and withdrawn packages (v0.20.0 item C4).

Exit criterion: a flag the publisher set on npm or PyPI (npm's
``deprecated``, a yanked PyPI release, the "Development Status :: 7 -
Inactive" classifier) becomes a DEPRECATION finding for review, scoped to
the package when it covers the package and to the release when it covers
one. A lifted deprecation, a partly yanked release and an unreachable
registry are never a flag.
"""

from datetime import date

import pytest
from click.testing import CliRunner

from analyzers.change_analyst import DETECTION_REGISTRY_FLAG, analyze_deprecations
from core.registry_deprecation import (
    CHECKED,
    INACTIVE_CLASSIFIER,
    NOT_PERFORMED,
    NPM_DEPRECATED,
    PACKAGE,
    PYPI_INACTIVE,
    PYPI_YANKED,
    VERSION,
    check,
    message,
    npm_deprecated,
    pypi_inactive,
    pypi_yanked,
)
from core.risk.impact import evaluate_impact

NPM = "https://registry.npmjs.org/widget"
PYPI = "https://pypi.org/pypi/widget/json"
TODAY = date(2026, 11, 9)


def _registry(responses):
    """A fake fetch: url -> (status, document); anything else is unreachable."""
    seen = []

    def fetch(url):
        seen.append(url)
        return responses.get(url, (0, None))

    fetch.seen = seen
    return fetch


def _npm(latest="2.0.0", latest_flag=None, versions=None):
    """Version documents: latest (with an optional deprecation) plus others."""
    docs = {f"{NPM}/latest": (200, {"name": "widget", "version": latest})}
    if latest_flag is not None:
        docs[f"{NPM}/latest"][1]["deprecated"] = latest_flag
    for version, flag in (versions or {}).items():
        doc = {"name": "widget", "version": version}
        if flag is not None:
            doc["deprecated"] = flag
        docs[f"{NPM}/{version}"] = (200, doc)
    return _registry(docs)


def _file(yanked=False, reason=None):
    return {"filename": "w.whl", "yanked": yanked, "yanked_reason": reason}


def _pypi(latest="2.0", classifiers=(), releases=None):
    releases = releases or {"1.0": [_file()], latest: [_file()]}
    doc = {"info": {"version": latest, "classifiers": list(classifiers)}, "releases": releases}
    return _registry({PYPI: (200, doc)})


# --- reading one flag --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("meta", "expected"),
    [
        ({"deprecated": "use gadget instead"}, (True, "use gadget instead")),
        ({"deprecated": True}, (True, None)),
        ({"deprecated": ""}, (False, None)),  # `npm deprecate pkg ""` lifts it
        ({"deprecated": "   "}, (False, None)),
        ({"deprecated": False}, (False, None)),
        ({}, (False, None)),
        ("not a document", (False, None)),
        ({"deprecated": "bad\x1b[31m text"}, (True, None)),  # flagged, message dropped
    ],
)
def test_npm_deprecated(meta, expected):
    assert npm_deprecated(meta) == expected


def test_a_message_is_bounded_and_single_line():
    assert message("one\n  two\tthree") == "one two three"
    long = message("x" * 1000)
    assert len(long) == 300 and long.endswith("…")
    assert message("\x00") is None and message(42) is None and message("") is None


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        ([_file(True, "Broken release")], (True, "Broken release")),
        ([_file(True), _file(True)], (True, None)),
        ([_file(True, "a"), _file(True, "b")], (True, None)),  # two reasons: neither is "the" one
        ([_file(True, "x"), _file(False)], (False, None)),  # partly yanked is not yanked
        ([], (False, None)),
        (None, (False, None)),
        ([{"yanked": "true"}], (False, None)),  # only a real boolean counts
    ],
)
def test_pypi_yanked(files, expected):
    assert pypi_yanked(files) == expected


def test_pypi_inactive():
    assert pypi_inactive({"classifiers": [INACTIVE_CLASSIFIER]})
    assert not pypi_inactive({"classifiers": ["Development Status :: 6 - Mature"]})
    assert not pypi_inactive({"classifiers": None})
    assert not pypi_inactive("nope")


# --- npm ---------------------------------------------------------------------------------


def test_npm_a_deprecated_latest_is_a_package_flag():
    result = check("npm", "widget", fetch_json=_npm(latest_flag="use gadget"))
    assert result["status"] == CHECKED and result["latest"] == "2.0.0"
    assert result["flags"] == [
        {"kind": NPM_DEPRECATED, "level": PACKAGE, "version": "2.0.0", "message": "use gadget"}
    ]


def test_npm_reads_version_documents_not_the_packument():
    fetch = _npm(versions={"1.0.0": "old line unsupported"})
    result = check("npm", "widget", "1.0.0", fetch_json=fetch)
    assert fetch.seen == [f"{NPM}/latest", f"{NPM}/1.0.0"]
    assert result["flags"] == [
        {
            "kind": NPM_DEPRECATED,
            "level": VERSION,
            "version": "1.0.0",
            "message": "old line unsupported",
        }
    ]


def test_npm_your_version_being_latest_is_one_flag_not_two():
    fetch = _npm(latest_flag="gone")
    result = check("npm", "widget", "2.0.0", fetch_json=fetch)
    assert fetch.seen == [f"{NPM}/latest"]
    assert [f["level"] for f in result["flags"]] == [PACKAGE]


def test_npm_a_lifted_deprecation_is_no_flag():
    result = check(
        "npm", "widget", "1.0.0", fetch_json=_npm(latest_flag="", versions={"1.0.0": ""})
    )
    assert result["status"] == CHECKED and result["flags"] == []


def test_npm_scoped_names_are_encoded():
    fetch = _registry({})
    check("npm", "@scope/widget", fetch_json=fetch)
    assert fetch.seen == ["https://registry.npmjs.org/@scope%2Fwidget/latest"]


@pytest.mark.parametrize(
    ("responses", "reason"),
    [
        ({}, "no usable answer"),
        ({f"{NPM}/latest": (404, None)}, "no such package"),
        ({f"{NPM}/latest": (200, {"version": "../../x"})}, "no usable answer"),
        (
            {f"{NPM}/latest": (200, {"version": "2.0.0"}), f"{NPM}/1.0.0": (404, None)},
            "does not list",
        ),
        ({f"{NPM}/latest": (200, {"version": "2.0.0"})}, "no usable answer"),  # version unreachable
    ],
)
def test_npm_not_performed(responses, reason):
    result = check("npm", "widget", "1.0.0", fetch_json=_registry(responses))
    assert result["status"] == NOT_PERFORMED and reason in result["reason"]
    assert result["flags"] == []


# --- PyPI --------------------------------------------------------------------------------


def test_pypi_inactive_classifier_is_a_package_flag():
    result = check("PyPI", "widget", fetch_json=_pypi(classifiers=[INACTIVE_CLASSIFIER]))
    assert result["flags"] == [
        {"kind": PYPI_INACTIVE, "level": PACKAGE, "version": "2.0", "message": None}
    ]


def test_pypi_a_yanked_release_is_a_version_flag_from_one_request():
    releases = {"1.0": [_file(True, "Broken release")], "2.0": [_file()]}
    fetch = _pypi(releases=releases)
    result = check("PyPI", "widget", "1.0.0", fetch_json=fetch)  # PEP 440: 1.0.0 == 1.0
    assert fetch.seen == [PYPI]
    assert result["flags"] == [
        {"kind": PYPI_YANKED, "level": VERSION, "version": "1.0", "message": "Broken release"}
    ]


def test_pypi_every_release_yanked_is_a_package_flag():
    releases = {"1.0": [_file(True)], "2.0": [_file(True, "abandoned")]}
    result = check("PyPI", "widget", "2.0", fetch_json=_pypi(releases=releases))
    assert result["flags"] == [
        {"kind": PYPI_YANKED, "level": PACKAGE, "version": "2.0", "message": "abandoned"}
    ]


def test_pypi_a_clean_release_has_no_flag():
    result = check("PyPI", "widget", "1.0", fetch_json=_pypi())
    assert result["status"] == CHECKED and result["flags"] == []


@pytest.mark.parametrize(
    ("responses", "version", "reason"),
    [
        ({PYPI: (404, None)}, None, "no such package"),
        ({PYPI: (200, None)}, None, "no usable answer"),
        ({PYPI: (200, {"info": {"version": "x y"}, "releases": {}})}, None, "no usable answer"),
        (
            {PYPI: (200, {"info": {"version": "2.0"}, "releases": {"2.0": [_file()], "1.5": []}})},
            "1.5",
            "does not list",  # a release without files says nothing
        ),
    ],
)
def test_pypi_not_performed(responses, version, reason):
    result = check("PyPI", "widget", version, fetch_json=_registry(responses))
    assert result["status"] == NOT_PERFORMED and reason in result["reason"]


# --- untrusted input ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ecosystem", "name", "version", "reason"),
    [
        ("Maven", "org.example/widget", None, "only npm and PyPI"),
        ("npm", "Bad Name", None, "name does not match"),
        ("npm", "widget", "1.0.0/../../x", "version does not match"),
        ("PyPI", "widget", "not a version", "version does not match"),
    ],
)
def test_untrusted_identifiers_never_reach_a_url(ecosystem, name, version, reason):
    fetch = _registry({})
    result = check(ecosystem, name, version, fetch_json=fetch)
    assert result["status"] == NOT_PERFORMED and reason in result["reason"]
    assert fetch.seen == []


def test_a_malformed_document_is_not_performed_never_a_crash():
    doc = {"info": {"version": "2.0", "classifiers": 5}, "releases": ["not", "a", "map"]}
    result = check("PyPI", "widget", "1.0", fetch_json=_registry({PYPI: (200, doc)}))
    assert result["status"] == NOT_PERFORMED


# --- findings ----------------------------------------------------------------------------


def test_a_package_deprecation_becomes_a_finding_for_review():
    result = check("npm", "widget", fetch_json=_npm(latest_flag="use gadget"))
    [finding] = analyze_deprecations(result, today=TODAY)
    assert finding["event_type"] == "DEPRECATION"
    assert finding["detection_method"] == DETECTION_REGISTRY_FLAG
    assert finding["evidence_strength"] == "strong"
    assert finding["effective_at"] is None and finding["first_detected_at"] is None
    assert finding["observed_at"] == "2026-11-09"
    assert finding["scope"] == {"kind": "package", "packages": ["pkg:npm/widget"], "versions": []}
    assert finding["affected_versions"] == ["*"]
    assert finding["title"] == "widget (npm) is deprecated by its publisher"
    assert '"use gadget"' in finding["summary"]
    assert finding["references"] == ["https://www.npmjs.com/package/widget/v/2.0.0"]
    assessed = evaluate_impact(finding, today=TODAY)
    assert assessed["eligibility"] == "REVIEW"
    assert assessed["assessment"] == "PROJECT_CHANGE"


def test_a_version_flag_is_scoped_to_that_release():
    releases = {"1.0": [_file(True, "Broken release")], "2.0": [_file()]}
    result = check("PyPI", "widget", "1.0", fetch_json=_pypi(releases=releases))
    [finding] = analyze_deprecations(result, today=TODAY)
    assert finding["title"] == "widget 1.0 (PyPI) was yanked by its publisher"
    assert finding["scope"]["versions"] == ["1.0"] and finding["affected_versions"] == ["1.0"]
    assert "The latest release is 2.0." in finding["summary"]
    assert finding["significance"] == "medium"
    assert finding["references"] == ["https://pypi.org/project/widget/1.0/"]


def test_an_inactive_classifier_is_moderate_evidence():
    result = check("PyPI", "widget", fetch_json=_pypi(classifiers=[INACTIVE_CLASSIFIER]))
    [finding] = analyze_deprecations(result, today=TODAY)
    assert finding["title"] == "widget (PyPI) declares itself inactive"
    assert finding["evidence_strength"] == "moderate"


def test_nothing_is_found_when_nothing_was_checked():
    assert analyze_deprecations({"status": NOT_PERFORMED, "flags": []}) == []
    assert analyze_deprecations({"status": CHECKED, "flags": [{"kind": "unknown"}]}) == []


# --- the commands ------------------------------------------------------------------------


def test_report_sweep_adds_package_deprecations(capsys):
    from cli.main import _catalog_deprecations

    fetch = _registry(
        {
            f"{NPM}/latest": (200, {"version": "2.0.0", "deprecated": "use gadget"}),
            "https://registry.npmjs.org/fine/latest": (200, {"version": "1.0.0"}),
        }
    )
    catalog = [
        {"slug": "w", "packages": [{"ecosystem": "npm", "name": "widget"}]},
        {"slug": "f", "packages": [{"ecosystem": "npm", "name": "fine"}]},
        {"slug": "m", "packages": [{"ecosystem": "Maven", "name": "org.example/widget"}]},
        {"slug": "gone", "packages": [{"ecosystem": "npm", "name": "gone"}]},
    ]
    findings = _catalog_deprecations(catalog, today=TODAY, fetch_json=fetch)
    assert [f["title"] for f in findings] == ["widget (npm) is deprecated by its publisher"]
    assert "deprecation not checked for pkg:npm/gone" in capsys.readouterr().out


def test_deprecation_command(monkeypatch):
    from cli.main import cli
    from core import digest_integrity

    fetch = _npm(versions={"1.0.0": "old line unsupported", "1.5.0": None})
    monkeypatch.setattr(digest_integrity, "default_fetch", fetch)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["deprecation", "--ecosystem", "npm", "--package", "widget", "--version", "1.0.0"]
    )
    assert result.exit_code == 0, result.output
    assert "[DEPRECATION]" in result.output and "old line unsupported" in result.output

    result = runner.invoke(
        cli, ["deprecation", "--ecosystem", "npm", "--package", "widget", "--version", "1.5.0"]
    )
    assert result.exit_code == 0
    assert "no deprecation or withdrawal flag on pkg:npm/widget or release 1.5.0" in result.output

    result = runner.invoke(cli, ["deprecation", "--ecosystem", "npm", "--package", "Bad Name"])
    assert result.exit_code == 1 and "not checked" in result.output
