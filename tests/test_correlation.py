"""Event correlation tests: lifecycle stories, passthrough, ordering."""


def _eol(product, cycle, impact="ACTION", date="2026-08-01"):
    return {
        "analyst": "change",
        "event_type": "EOL",
        "impact": impact,
        "title": f"{product} {cycle} is end-of-life",
        "affected_versions": [cycle],
        "event_date": date,
        "supporting": [
            {
                "collector": "endoflife",
                "product": product,
                "link": f"https://endoflife.date/{product}",
            }
        ],
    }


def test_clickhouse_many_rows_become_one_story():
    from analyzers.event_correlation import aggregate_lifecycle

    findings = [_eol("clickhouse", v) for v in ("26.6", "26.5", "26.4", "25.8")]
    stories = aggregate_lifecycle(findings)
    assert len(stories) == 1
    story = stories[0]
    assert story["analyst"] == "event-correlation"
    assert story["affected_versions"] == ["26.6", "26.5", "26.4", "25.8"]
    assert story["impact"] == "ACTION"
    assert "26.6" in story["title"] and "25.8" in story["title"]


def test_past_approaching_eos_stay_separate():
    from analyzers.event_correlation import aggregate_lifecycle

    findings = [
        _eol("p", "1.0", "ACTION"),
        _eol("p", "2.0", "REVIEW"),
        {
            "analyst": "change",
            "event_type": "EOS",
            "impact": "REVIEW",
            "title": "t",
            "affected_versions": ["3.0"],
            "supporting": [],
        },
    ]
    assert len(aggregate_lifecycle(findings)) == 3


def test_singleton_and_non_lifecycle_pass_through():
    from analyzers.event_correlation import aggregate_lifecycle

    solo = _eol("p", "9.9")
    other = {"analyst": "security", "event_type": "SECURITY", "impact": "WATCH", "title": "s"}
    out = aggregate_lifecycle([solo, other])
    assert out[0] is solo
    assert out[1] is other


def test_story_unions_evidence_links():
    from analyzers.event_correlation import aggregate_lifecycle

    findings = [_eol("p", "1.0"), _eol("p", "2.0")]
    story = aggregate_lifecycle(findings)[0]
    assert story["evidence_links"] == ["https://endoflife.date/p"]
    assert len(story["supporting"]) == 2
    assert story["event_date"] == "2026-08-01"


def test_lifecycle_first_ordering():
    from analyzers.event_correlation import lifecycle_first

    items = [
        {"project": "b", "findings": [{"event_type": "EOL"}]},
        {"project": "a", "findings": [{"event_type": "DISTRIBUTION_CHANGE"}]},
    ]
    assert [i["project"] for i in lifecycle_first(items)] == ["a", "b"]
