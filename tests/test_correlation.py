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


def _diff_change(tag, direction="tag_disappeared", namespace="library", repo="nginx"):
    return {
        "type": direction,
        "namespace": namespace,
        "repository": repo,
        "tag": tag,
        "previous": ["sha256:111"],
        "current": None,
        "previous_observation_id": "obs-prev",
        "current_observation_id": "obs-cur",
        "previous_observed_at": "2026-09-01",
        "previous_hash": "sha256:prev",
        "current_hash": "sha256:cur",
        "previous_chain": "sha256:pc",
        "current_chain": "sha256:cc",
        "parser_version": "openpulse-parsers/0.4.0",
        "tags_present": ["latest", tag],
        "observed_at": "2026-10-01",
        "first_detected_at": "2026-10-01",
    }


def _diff_findings(*changes):
    from analyzers.change_analyst import analyze_diffs

    return analyze_diffs(list(changes))


def test_same_repo_disappearances_become_one_story():
    from analyzers.event_correlation import aggregate_distribution

    stories = aggregate_distribution(
        _diff_findings(_diff_change("1.0"), _diff_change("2.0"), _diff_change("3.0"))
    )
    assert len(stories) == 1
    story = stories[0]
    assert story["title"] == "3 tags disappeared from library/nginx"
    assert story["stories_merged"] == 3
    assert story["impact"] == "REVIEW"
    assert story["significance"] == "high"
    assert len(story["affected_artifacts"]) == 3
    assert [t["tag"] for t in story["observation_evidence"]["fact"]["tags"]] == [
        "1.0",
        "2.0",
        "3.0",
    ]
    # Nothing dropped: every scope ref and supporting change retained.
    assert len(story["scope"]["artifacts"]) == 3
    assert len(story["supporting"]) == 3


def test_directions_and_repos_stay_separate():
    from analyzers.event_correlation import aggregate_distribution

    stories = aggregate_distribution(
        _diff_findings(
            _diff_change("1.0"),
            _diff_change("2.0", direction="tag_appeared"),
            _diff_change("1.0", repo="redis"),
        )
    )
    assert len(stories) == 3


def test_singleton_and_heuristic_pass_through():
    from analyzers.event_correlation import aggregate_distribution

    heuristic = {
        "analyst": "change",
        "event_type": "DISTRIBUTION_CHANGE",
        "signal": "distribution",
        "title": "heuristic",
        "impact": "ACTION",
        "detection_method": "namespace_heuristic",
    }
    findings = _diff_findings(_diff_change("1.0")) + [heuristic]
    out = aggregate_distribution(findings)
    assert len(out) == 2
    assert out[0]["title"].startswith("Tag `1.0` disappeared")
    assert out[1] == heuristic
