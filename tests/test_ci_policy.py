from core.risk.check import DependencyVerdict, fail_on_threshold


def verdict(affected, *impacts):
    return DependencyVerdict(
        dependency="x",
        affected=affected,
        relationship="AFFECTS_VERSION" if affected else "UNKNOWN",
        verdicts=[{"affected": True, "impact": impact} for impact in impacts],
    )


def test_fail_on_affected():
    assert fail_on_threshold([verdict(True, "WATCH")], "affected")
    assert not fail_on_threshold([verdict(False, "CRITICAL")], "affected")


def test_fail_on_review_includes_action_and_critical():
    assert fail_on_threshold([verdict(True, "REVIEW")], "review")
    assert fail_on_threshold([verdict(True, "ACTION")], "review")
    assert fail_on_threshold([verdict(True, "CRITICAL")], "review")


def test_fail_on_action_preserves_strict_semantics():
    assert not fail_on_threshold([verdict(True, "REVIEW")], "action")
    assert fail_on_threshold([verdict(True, "ACTION")], "action")


def test_fail_on_critical_is_narrowest():
    assert not fail_on_threshold([verdict(True, "ACTION")], "critical")
    assert fail_on_threshold([verdict(True, "CRITICAL")], "critical")
