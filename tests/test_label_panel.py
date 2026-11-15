"""The AI-panel labelling round (research/labelling/AI_PANEL_PROTOCOL.md):
packets are blind, validation fails closed, and the analysis refuses
labels that changed after they were locked."""

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "scripts"))

import _common  # noqa: E402,F401
import label_packets  # noqa: E402
import label_panel  # noqa: E402
import label_sensitivity  # noqa: E402

DATASET = json.loads(_common.DATASETS["retro"].read_text(encoding="utf-8"))


def test_packets_cover_every_pair_and_withhold_labels():
    key, packets = label_packets.build_packets(DATASET)
    assert len(key) == len(DATASET["cases"])
    assert {v["case"] for v in key.values()} == {c["id"] for c in DATASET["cases"]}
    for text in packets.values():
        assert all(f"`{nid}`" in text for nid in key)
        for case in DATASET["cases"]:
            assert case["id"] not in text
            assert case["rationale"] not in text
        assert not any(label in text for label in label_packets.LABELS)


def test_the_two_packets_order_pairs_differently():
    _, packets = label_packets.build_packets(DATASET)
    order = {
        reader: [line for line in text.splitlines() if line.startswith("- `")]
        for reader, text in packets.items()
    }
    assert sorted(order["A"]) == sorted(order["B"])
    assert order["A"] != order["B"]


def test_a_leaked_label_stops_the_build():
    data = json.loads(json.dumps(DATASET))
    data["cases"][0]["dependency"]["note"] = "in_scope"
    with pytest.raises(SystemExit, match="leaks"):
        label_packets.build_packets(data)


def test_committed_packets_match_the_builder():
    key, packets = label_packets.build_packets(DATASET)
    committed = json.loads((label_packets.OUT / "key.json").read_text(encoding="utf-8"))
    assert committed["pairs"] == key
    for reader, text in packets.items():
        on_disk = (label_packets.OUT / f"packet-{reader}.md").read_text(encoding="utf-8")
        assert on_disk.replace("\r\n", "\n").rstrip("\n") == text


@pytest.mark.parametrize(
    "lines, problem",
    [
        (['{"id": "aaaa", "label": "in_scope"}'], "unanswered"),
        (['{"id": "aaaa", "label": "maybe"}', '{"id": "bbbb", "label": "in_scope"}'], "invalid"),
        (
            ['{"id": "aaaa", "label": "in_scope"}'] * 2 + ['{"id": "bbbb", "label": "in_scope"}'],
            "duplicate",
        ),
        (['{"id": "zzzz", "label": "in_scope"}'], "unknown id"),
        (["not json"], "not JSON"),
    ],
)
def test_label_files_are_validated_fail_closed(tmp_path, lines, problem):
    path = tmp_path / "labels.jsonl"
    path.write_text("\n".join(lines), encoding="utf-8")
    _, problems = label_panel.read_labels(path, {"aaaa", "bbbb"})
    assert any(problem in p for p in problems)


def test_kappa_matches_a_hand_computed_value():
    # 10 items: 6 agree; marginals give expected agreement 0.36 -> kappa 0.375.
    pairs = [("in_scope", "in_scope")] * 4 + [("out_of_scope", "out_of_scope")] * 2
    pairs += [("in_scope", "out_of_scope")] * 2 + [("out_of_scope", "in_scope")] * 2
    first = {"in_scope": 6, "out_of_scope": 4}
    second = {"in_scope": 6, "out_of_scope": 4}
    expected = sum(first[k] * second[k] for k in first) / 100
    assert label_sensitivity.kappa(pairs) == pytest.approx((0.6 - expected) / (1 - expected))
    assert label_sensitivity.kappa([("in_scope", "in_scope")] * 3) is None


def test_rescoring_uses_the_given_labels_not_the_recorded_category():
    outcomes = [
        {"case": "x", "event": "E", "outcome": "cleared"},
        {"case": "y", "event": "E", "outcome": "unresolved"},
    ]
    as_in = label_sensitivity.score(outcomes, {"x": "in_scope", "y": "in_scope"})
    as_out = label_sensitivity.score(outcomes, {"x": "out_of_scope", "y": "in_scope"})
    assert (as_in["false_clears"], as_in["events_with_false_clear"]) == (1, 1)
    assert (as_out["false_clears"], as_out["correct"]) == (0, 1)


def test_a_label_changed_after_locking_is_refused(tmp_path, monkeypatch):
    lock = label_panel._lock()
    if not lock.get("adjudication") or not lock.get("labels"):
        pytest.skip("panel not finalised")
    copy = tmp_path / "research"
    for path in [*lock["labels"], *lock["adjudication"]]:
        target = copy.parent / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / path, target)
    first = next(iter(lock["labels"]))
    target = copy.parent / first
    target.write_text(target.read_text(encoding="utf-8") + "\n ", encoding="utf-8")
    monkeypatch.setattr(label_sensitivity, "ROOT", copy.parent)
    with pytest.raises(SystemExit, match="locked hash"):
        label_sensitivity._verify_lock()
