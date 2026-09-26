"""Version applicability unit tests (OSV events, CPE ranges, comparison)."""

from core.versions import compare, cpe_applicable, detect_scheme, osv_applicable, satisfies


def test_compare_numeric_and_prerelease():
    assert compare("5.1", "5.1.1") == -1
    assert compare("5.1.1", "5.1.1") == 0
    assert compare("8.0", "7.4.2") == 1
    assert compare("1.0rc1", "1.0") == -1
    assert compare("latest", "1.0") is None


def test_satisfies_osv_style():
    assert satisfies("5.0", {"introduced": "0", "fixed": "5.1.1"}) is True
    assert satisfies("5.1.1", {"introduced": "0", "fixed": "5.1.1"}) is False
    assert satisfies("4.2", {"last_affected": "5.0"}) is True
    assert satisfies("5.0.1", {"last_affected": "5.0"}) is False
    assert satisfies("1.0", {}) is None


def test_satisfies_cpe_style():
    constraint = {"versionStartIncluding": "7.0", "versionEndExcluding": "7.4"}
    assert satisfies("7.2", constraint) is True
    assert satisfies("7.4", constraint) is False
    assert satisfies("6.9", constraint) is False


def test_cpe_applicable_exact_and_range():
    assert (
        cpe_applicable("8.0", {"criteria": "cpe:2.3:a:v:p:8.0:*:*:*:*:*:*:*", "vulnerable": True})
        is True
    )
    assert (
        cpe_applicable("8.0.1", {"criteria": "cpe:2.3:a:v:p:8.0:*:*:*:*:*:*:*", "vulnerable": True})
        is False
    )
    assert (
        cpe_applicable(None, {"criteria": "cpe:2.3:a:v:p:*:*:*:*:*:*:*:*", "vulnerable": True})
        is None
    )
    assert (
        cpe_applicable("1.0", {"criteria": "cpe:2.3:a:v:p:*:*:*:*:*:*:*:*", "vulnerable": False})
        is False
    )


def test_osv_introduced_last_affected_and_ranges():
    affected = {
        "ranges": [
            {"type": "ECOSYSTEM", "events": [{"introduced": "2.0"}, {"last_affected": "2.5"}]}
        ]
    }
    assert osv_applicable("2.3", affected) is True
    assert osv_applicable("2.5", affected) is True
    assert osv_applicable("2.6", affected) is False
    multi = {
        "ranges": [
            {"type": "ECOSYSTEM", "events": [{"introduced": "1.0"}, {"fixed": "1.5"}]},
            {"type": "ECOSYSTEM", "events": [{"introduced": "2.0"}, {"fixed": "2.5"}]},
        ]
    }
    assert osv_applicable("2.2", multi) is True
    assert osv_applicable("1.7", multi) is False
    assert osv_applicable(None, multi) is None


def test_osv_multiple_affected_entries_and_exact():
    affected = {"versions": ["4.2.1", "4.2.2"], "ranges": []}
    assert osv_applicable("4.2.1", affected) is True
    assert osv_applicable("4.2.3", affected) is None


def test_cpe_range_attributes():
    base = {"criteria": "cpe:2.3:a:v:p:*:*:*:*:*:*:*:*", "vulnerable": True}
    assert cpe_applicable("7.0", {**base, "versionStartIncluding": "7.0"}) is True
    assert cpe_applicable("7.0", {**base, "versionStartExcluding": "7.0"}) is False
    assert cpe_applicable("7.4", {**base, "versionEndIncluding": "7.4"}) is True
    assert cpe_applicable("7.4", {**base, "versionEndExcluding": "7.4"}) is False


def test_unknown_schemes_return_none():
    assert detect_scheme("1.0-r1") == "unknown"
    assert detect_scheme("2026.04-alpine") == "unknown"
    assert detect_scheme("v1.2.3-ubuntu") == "unknown"
    assert detect_scheme("8.0.1") == "generic"
    assert detect_scheme("1.0rc1") == "generic"
    assert compare("1.0-r1", "1.0") is None
    assert compare("8.0", "8.0", scheme="apk") is None
    assert osv_applicable("2026.04-alpine", {"ranges": [{"events": [{"fixed": "9.9"}]}]}) is None
