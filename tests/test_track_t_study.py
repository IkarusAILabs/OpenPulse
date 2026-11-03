"""The track T study's star-history indicators and calibration (TR4), offline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import track_t_study as study  # noqa: E402

W0 = 1_700_000_000
WEEK, DAY = study.WEEK, study.DAY


def _history(weeks, status=200):
    return {"status": status, "weeks": weeks}


def _steady(n_weeks, per_day=1, start=W0):
    return [[start + i * WEEK, *[per_day] * 7] for i in range(n_weeks)]


def test_a_steady_history_has_low_concentration():
    values = study.indicators(_history(_steady(20)))
    assert values["SH1"] == pytest.approx(1 / 20)
    assert values["SH2"] == pytest.approx(4 / 20)
    assert values["SH3"] == 1  # the busiest day is the first; its prior days are empty


def test_a_burst_is_measured_on_all_three():
    weeks = _steady(10) + [[W0 + 10 * WEEK, 0, 0, 200, 0, 0, 0, 0]]
    values = study.indicators(_history(weeks))
    assert values["SH1"] == pytest.approx(200 / 270)
    assert values["SH2"] == pytest.approx((200 + 21) / 270)
    assert values["SH3"] == 200  # median of the 8 prior weeks is 1


def test_zero_weeks_between_recorded_weeks_count_as_zero():
    weeks = [[W0, 10, 0, 0, 0, 0, 0, 0], [W0 + 10 * WEEK, 50, 0, 0, 0, 0, 0, 0]]
    values = study.indicators(_history(weeks))
    assert values["SH2"] == pytest.approx(50 / 60)  # the two weeks are not consecutive


def test_ineligible_histories_have_no_values():
    assert study.indicators(_history(_steady(5))) is None  # 35 stars
    assert study.indicators(_history(_steady(20), status="capped")) is None
    assert study.indicators({"status": 404}) is None


def test_the_split_is_fixed_by_names_and_seed_and_halves_the_set():
    names = [f"o/r{i}" for i in range(11)]
    calibration, held_out = study.split(names)
    assert study.split(list(reversed(names))) == (calibration, held_out)
    assert len(calibration) == 5 and len(held_out) == 6
    assert not set(calibration) & set(held_out)


def test_the_threshold_lets_at_most_one_percent_fire():
    values = [float(i) for i in range(1, 251)]  # 250 values: 2 may fire
    t = study.threshold(values)
    assert t == {"threshold": 248.0, "eligible": 250, "allowed_to_fire": 2, "fire": 2}
    small = study.threshold([0.5, 0.2, 0.9])  # fewer than 100: nothing may fire
    assert small["threshold"] == 0.9 and small["fire"] == 0


def test_calibration_never_reads_a_held_out_repository(monkeypatch):
    repositories = {f"o/r{i}": _history(_steady(10 + i)) for i in range(40)}
    calibration, held_out = study.split(list(repositories))
    read = []
    real = study.indicators
    monkeypatch.setattr(study, "indicators", lambda h: read.append(id(h)) or real(h))
    result = study.calibrate({"organic": {"repositories": repositories}})
    assert sorted(read) == sorted(id(repositories[n]) for n in calibration)
    assert result["split"]["organic"]["held_out"] == held_out
    assert result["thresholds"]["SH1"]["eligible"] == 20


# ---------------------------------------------------------------------------
# The run's pieces (TR6), on synthetic data only
# ---------------------------------------------------------------------------


def test_wilson_and_newcombe_intervals_match_published_values():
    w = study.wilson(5, 10)
    assert (round(w["low"], 4), round(w["high"], 4)) == (0.2366, 0.7634)
    zero = study.wilson(0, 10)
    assert zero["low"] == 0 and round(zero["high"], 4) == 0.2775
    assert study.wilson(0, 0)["rate"] is None
    # Newcombe (1998), method 10, example (a): 56/70 - 48/80.
    d = study.difference(56, 70, 48, 80)
    assert (round(d["low"], 4), round(d["high"], 4)) == (0.0524, 0.3339)


def test_the_frame_reads_mal_records_only_and_samples_by_seed(tmp_path):
    import json
    import zipfile

    archive = tmp_path / "npm-all.zip"
    with zipfile.ZipFile(archive, "w") as z:
        for i in range(30):
            z.writestr(
                f"MAL-2026-{i}.json",
                json.dumps({"affected": [{"package": {"ecosystem": "npm", "name": f"bad-{i}"}}]}),
            )
        z.writestr(
            "MAL-2026-99.json",
            json.dumps(
                {
                    "withdrawn": "2026-01-01",
                    "affected": [{"package": {"ecosystem": "npm", "name": "w"}}],
                }
            ),
        )
        z.writestr(
            "GHSA-xxxx.json",
            json.dumps({"affected": [{"package": {"ecosystem": "npm", "name": "cve-only"}}]}),
        )
        z.writestr("MAL-2026-98.json", "not json")
    names, records = study.malicious_names(archive, "npm")
    assert records == 30 and "w" not in names and "cve-only" not in names
    doc = study.frame({"npm": archive}, size=5, lookalike=10)["npm"]
    assert doc["names"] == 30 and len(doc["sample"]) == 5 and len(doc["lookalike_sample"]) == 10
    assert doc == study.frame({"npm": archive}, size=5, lookalike=10)["npm"]


def test_the_run_waits_for_registration():
    draft = "| Responsible author | **to fill at archiving** |"
    assert "to fill" in study.registered(draft, "10.5281/zenodo.1")
    archived = "| Registry | 10.5281/zenodo.1 |"
    assert study.registered(archived, "10.5281/zenodo.1") is None
    assert "does not name" in study.registered(archived, "10.5281/zenodo.2")
    assert "does not name" in study.registered(archived, "")


def test_the_run_refuses_before_registration_and_a_second_time(tmp_path, monkeypatch):
    protocol = tmp_path / "protocol.md"
    protocol.write_text("| Responsible author | **to fill at archiving** |", "utf-8")
    monkeypatch.setattr(study, "PROTOCOL", protocol)
    with pytest.raises(SystemExit, match="to fill at archiving"):
        study.run("10.5281/zenodo.1", fetch=lambda url: pytest.fail("fetched"))
    protocol.write_text("archived as 10.5281/zenodo.1", "utf-8")
    results = tmp_path / "results.json"
    results.write_text("{}", "utf-8")
    monkeypatch.setattr(study, "RESULTS", results)
    with pytest.raises(SystemExit, match="runs once"):
        study.run("10.5281/zenodo.1", fetch=lambda url: pytest.fail("fetched"))


def _star_sets():
    steady = {f"o/s{i}": _history(_steady(20)) for i in range(20)}
    burst = [[W0, 1, 1, 1, 1, 1, 1, 1], [W0 + WEEK, 0, 0, 500, 0, 0, 0, 0]]
    positives = {
        "repositories": {
            "p/a": {**_history(burst), "starscout": ["clustered"]},
            "p/b": {**_history(burst), "starscout": ["low_activity"]},
            "p/c": {**_history(_steady(20)), "starscout": ["low_activity"]},
            "p/gone": {"status": 404, "starscout": ["clustered", "low_activity"]},
        }
    }
    return {"organic": {"repositories": steady}}, positives


def test_star_results_are_aggregates_and_state_each_hypothesis():
    import json

    sets, positives = _star_sets()
    calibration = study.calibrate(sets)
    out = study.star_results(calibration, sets, positives)
    assert out["organic_held_out"]["pooled"]["eligible"] == 10
    assert out["organic_held_out"]["pooled"]["SH1"]["k"] == 0
    everyone = out["positives"]["all"]
    assert (everyone["recorded"], everyone["eligible"], everyone["unresolved"]) == (4, 3, 1)
    assert everyone["SH1"]["k"] == 2 and out["positives"]["low_activity_only"]["SH1"]["k"] == 1
    assert out["hypotheses"]["SH1"] == {"H-A1": True, "H-A2": True} and out["supported"]
    assert "p/" not in json.dumps(out)  # no positive is ever named


def test_lookalike_results_compare_malicious_with_young_organic(monkeypatch):
    from core import lookalike

    flagged = {"expres", "lodahs", "reacts"}
    monkeypatch.setattr(
        lookalike,
        "check",
        lambda eco, name: {
            "status": "SUSPICIOUS_INCONCLUSIVE" if name in flagged else "MISSING_EVIDENCE"
        },
    )
    frame_doc = {
        "npm": {"lookalike_sample": ["expres", "lodahs", "reacts", "x1"]},
        "PyPI": {"lookalike_sample": ["p1"]},
    }
    young = {"npm": ["a", "b", "c", "d"], "PyPI": ["q"]}
    out = study.lookalike_results(frame_doc, young, {"npm": ["react"], "PyPI": []})
    assert out["npm"]["malicious"]["flagged"]["k"] == 3
    assert out["npm"]["young_organic"]["flagged"]["k"] == 0
    assert out["npm"]["difference"]["difference"] == pytest.approx(0.75)
    assert out["H-B1"] is True


def test_provenance_coverage_separates_none_unknown_and_unchecked():
    doc = {
        "packages": [
            {
                "ecosystem": "npm",
                "status": 200,
                "releases": [{"attested": False}, {"attested": True}],
            },
            {"ecosystem": "npm", "status": 200, "releases": [{"attested": False}]},
            {"ecosystem": "npm", "status": 200, "releases": [{"attested": None}]},
            {"ecosystem": "npm", "status": 404},
        ]
    }
    npm = study.provenance_coverage(doc)["npm"]
    assert (npm["published"], npm["none"], npm["unknown"], npm["not_checked"]) == (1, 1, 1, 1)
    assert npm["published_rate"]["n"] == 3


def test_the_report_states_failed_hypotheses_too():
    sets, positives = _star_sets()
    stars = study.star_results(study.calibrate(sets), sets, positives)
    stars["supported"] = False
    look = {
        eco: {
            label: {"names": 0, "flagged": study.wilson(0, 0)}
            for label in ("malicious", "young_organic", "popular_organic")
        }
        | {"difference": study.difference(0, 0, 0, 0)}
        for eco in ("npm", "PyPI")
    }
    look["H-B1"] = False
    text = study.render(
        {
            "run_at": "2026-12-01T00:00:00Z",
            "registration": "10.5281/zenodo.1",
            "stars": stars,
            "lookalike": look,
            "provenance": {},
        }
    )
    assert "Q-A hypotheses not supported" in text and "H-B1 not met" in text
    assert "not an independent evaluation" in text and "p/a" not in text


def test_the_whole_run_on_synthetic_files(tmp_path, monkeypatch):
    import hashlib
    import json

    fixtures, local = tmp_path / "fixtures", tmp_path / "fixtures" / "local"
    local.mkdir(parents=True)
    sets, positives = _star_sets()
    young = {
        "repositories": {
            f"y/r{i}": {
                **_history(_steady(20)),
                "selection": {"ecosystem": "npm", "package": f"young-{i}"},
            }
            for i in range(4)
        }
    }
    files = {"organic": sets["organic"], "young": young}
    for label, doc in files.items():
        (fixtures / f"stars-{label}.json").write_text(json.dumps(doc), "utf-8")
    calibration = study.calibrate(files)
    calibration["sources"] = {
        label: {
            "sha256": hashlib.sha256((fixtures / f"stars-{label}.json").read_bytes()).hexdigest()
        }
        for label in files
    }
    (fixtures / "calibration.json").write_text(json.dumps(calibration), "utf-8")
    (local / "positives.json").write_text(json.dumps(positives), "utf-8")
    frame_doc = {
        eco: {"lookalike_sample": [f"bad-{eco.lower()}"], "sample": [f"bad-{eco.lower()}"]}
        for eco in ("npm", "PyPI")
    }
    (fixtures / "malicious-frame-2026-11-03.json").write_text(json.dumps(frame_doc), "utf-8")
    organic = {"packages": [{"ecosystem": "npm", "name": "react", "status": 404}]}
    (fixtures / "organic-packages.json").write_text(json.dumps(organic), "utf-8")
    protocol = tmp_path / "protocol.md"
    protocol.write_text("Registered as 10.5281/zenodo.1.", "utf-8")
    for name, value in {
        "FIXTURES": fixtures,
        "LOCAL": local,
        "PROTOCOL": protocol,
        "RESULTS": tmp_path / "results.json",
        "SETS": {label: f"stars-{label}.json" for label in files},
        "CALIBRATION": "calibration.json",
        "POSITIVES": "positives.json",
        "ORGANIC_PACKAGES": "organic-packages.json",
    }.items():
        monkeypatch.setattr(study, name, value)
    asked = []

    def gone(url):
        asked.append(url)
        return 404, None

    results = study.run("10.5281/zenodo.1", fetch=gone, log=lambda _m: None)
    assert results["stars"]["positives"]["all"]["recorded"] == 4
    assert results["lookalike"]["npm"]["young_organic"]["names"] == 4
    assert results["metadata"]["malicious"]["registry_answered"]["npm"] == {
        "packages": 1,
        "answered": 0,
    }
    assert results["provenance"]["young"]["npm"]["not_checked"] == 4
    assert len(asked) == 6  # 2 malicious + 4 young packages, each 404
    assert sorted(p.name for p in fixtures.glob("packages-*.json"))[0].startswith("packages-")
    text = study.render(results)
    assert "p/a" not in text and "p/gone" not in json.dumps(results)


def test_packaging_waits_for_a_filled_protocol_a_clean_tree_and_a_tag():
    draft = "| Responsible author | **to fill at archiving** |"
    problems = study.package_problems(draft, ["benchmarks/track_t_study.py"], [])
    assert len(problems) == 3
    assert study.package_problems("filled", [], ["track-t-part-a-freeze"]) == []


def test_every_bundled_file_exists():
    missing = [p for p in study.BUNDLE if not (study.ROOT / p).is_file()]
    assert missing == []


def test_a_draft_package_lists_hashes_and_never_holds_the_positives(tmp_path, monkeypatch):
    import json
    import zipfile

    monkeypatch.setattr(study, "PACKAGE_DIR", tmp_path)
    out = study.package(draft=True)
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        top = names[0].split("/", 1)[0]
        doc = json.loads(z.read(f"{top}/MANIFEST.json"))
        readme = z.read(f"{top}/README.md").decode("utf-8")
    assert top.endswith("-DRAFT") and doc["status"].startswith("DRAFT")
    assert {f["path"] for f in doc["files"]} == set(study.BUNDLE)
    assert not any("local/" in n or "positives" in n for n in names)
    assert len(doc["commit"]) == 40 and "not an independent evaluation" in readme
