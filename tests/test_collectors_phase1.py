def _nvd_payload():
    return {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-0001",
                    "published": "2024-01-01T00:00:00.000",
                    "lastModified": "2024-01-02T00:00:00.000",
                    "descriptions": [{"lang": "en", "value": "Test vuln"}],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "cvssData": {
                                    "baseScore": 9.8,
                                    "baseSeverity": "CRITICAL",
                                }
                            }
                        ]
                    },
                    "references": [{"url": "https://example.com/advisory"}],
                }
            },
            {
                "cve": {
                    "id": "CVE-2024-0002",
                    "published": "2024-02-01T00:00:00.000",
                    "descriptions": [{"lang": "en", "value": "No metrics yet"}],
                    "metrics": {},
                    "references": [],
                }
            },
        ]
    }


def test_nvd_parse():
    from collectors.nvd.collector import parse_cves

    out = parse_cves(_nvd_payload())
    assert out[0]["id"] == "CVE-2024-0001"
    assert out[0]["cvss"]["base_score"] == 9.8
    assert out[0]["references"] == ["https://example.com/advisory"]
    assert out[1]["cvss"] == {}


def _cve_payload():
    return {
        "cveMetadata": {
            "cveId": "CVE-2024-0001",
            "state": "PUBLISHED",
            "assignerShortName": "test-cna",
            "datePublished": "2024-01-01T00:00:00.000Z",
        },
        "containers": {
            "cna": {
                "descriptions": [{"lang": "en", "value": "Test vuln"}],
                "affected": [
                    {
                        "vendor": "testvendor",
                        "product": "testproduct",
                        "versions": [{"version": "1.0"}],
                    }
                ],
                "references": [{"url": "https://example.com/fix"}],
            }
        },
    }


def test_cve_parse():
    from collectors.cve.collector import parse_record

    out = parse_record(_cve_payload())
    assert out["id"] == "CVE-2024-0001"
    assert out["state"] == "PUBLISHED"
    assert out["affected"][0]["product"] == "testproduct"
    assert out["references"] == ["https://example.com/fix"]


def test_cve_rejects_non_id():
    from collectors.cve.collector import CVECollector

    out = CVECollector().collect("redis")
    assert "skipped" in out[0]


def _kev_catalog():
    return {
        "vulnerabilities": [
            {
                "cveID": "CVE-2024-0001",
                "vendorProject": "TestVendor",
                "product": "TestProduct",
                "vulnerabilityName": "Test Vuln",
                "dateAdded": "2024-03-01",
                "dueDate": "2024-03-22",
                "requiredAction": "Apply updates.",
            }
        ]
    }


def test_kev_filter_by_cve():
    from collectors.kev.collector import filter_catalog

    out = filter_catalog(_kev_catalog(), "cve-2024-0001")
    assert len(out) == 1
    assert out[0]["product"] == "TestProduct"


def test_kev_filter_no_match():
    from collectors.kev.collector import filter_catalog

    assert filter_catalog(_kev_catalog(), "nosuchproject") == []


def _osv_payload():
    return {
        "vulns": [
            {
                "id": "GHSA-24wv-mv5m-xv4h",
                "aliases": ["CVE-2023-28858", "PYSEC-2023-45"],
                "summary": "Redis vulnerability via crafted Lua scripts",
                "severity": [{"type": "CVSS_V3", "score": 7.2}],
                "affected": [
                    {
                        "package": {"name": "redis", "ecosystem": "PyPI"},
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [{"fixed": "4.5.4"}],
                            }
                        ],
                    }
                ],
                "references": [{"url": "https://example.com/ghsa"}],
            }
        ]
    }


def test_osv_parse_extracts_cve_id_from_aliases():
    from collectors.osv.collector import parse_vulns

    out = parse_vulns("redis", "PyPI", _osv_payload())
    assert len(out) == 1
    # Live OSV PyPI records key on GHSA/PYSEC ids; correlate() only merges
    # entries carrying a CVE id, so the first CVE alias must surface.
    assert out[0]["id"] == "GHSA-24wv-mv5m-xv4h"
    assert out[0]["cve_id"] == "CVE-2023-28858"
    assert out[0]["package"] == "redis"
    assert out[0]["ecosystem"] == "PyPI"


def test_osv_parse_without_cve_alias():
    from collectors.osv.collector import parse_vulns

    payload = {
        "vulns": [
            {
                "id": "GHSA-nope-nope-nope",
                "aliases": ["PYSEC-2023-99"],
                "affected": [{"package": {"name": "redis", "ecosystem": "PyPI"}, "ranges": []}],
            }
        ]
    }
    out = parse_vulns("redis", "PyPI", payload)
    assert out[0]["cve_id"] is None


def test_osv_map_from_catalog():
    from core.entities.catalog import load_catalog, osv_map

    mapping = osv_map(load_catalog())
    # Catalog entries with a verified (package, ecosystem) pair only.
    assert mapping["redis"] == ("redis", "PyPI")
    assert mapping["django"] == ("django", "PyPI")
    assert mapping["fastapi"] == ("fastapi", "PyPI")
    # Entries without an osv block are absent, never guessed.
    assert "bitnami" not in mapping
    assert "kafka" not in mapping


def test_osv_live_findings_are_affects_package():
    from analyzers.security_analyst import correlate
    from collectors.osv.collector import parse_vulns
    from core.entities.catalog import project_context

    entries = parse_vulns("redis", "PyPI", _osv_payload())
    findings = correlate({"osv": entries}, project_context("redis"))
    assert len(findings) == 1
    finding = findings[0]
    assert finding["cve_id"] == "CVE-2023-28858"
    assert finding["relationship"] == "AFFECTS_PACKAGE"
    assert finding["match_method"] == "osv_package"
    assert finding["sources"] == ["osv"]
    assert "osv:PyPI/redis" in finding["identity_evidence"]


def test_osv_skips_unmapped_slug():
    from collectors.osv.collector import OSVCollector

    collector = OSVCollector({})
    out = collector.collect("kafka")
    assert len(out) == 1
    assert out[0].get("skipped")
    assert out[0]["collector"] == "osv"
