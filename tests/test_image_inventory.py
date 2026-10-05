"""Image inventory input tests: reader, CLI wiring, tag-vs-digest policy.

Parity is the acceptance bar: every inventory entry must produce the
identical verdict the same ref produces through --watchlist. The
tag-vs-digest policy is enforced here too — a moving tag never
reports digest-level certainty.
"""

import json

import pytest

from core.image_inventory import (
    MAX_INVENTORY_BYTES,
    load_image_inventory_doc,
    read_image_inventory,
)
from core.risk.check import check_dependency
from core.risk.match import digest_of, event_affects_ref, tag_vs_digest_policy
from core.schema.models import Artifact, OSSEvent

FIXTURE = "data/fixtures/images/inventory_sample.txt"
EVENT = "data/fixtures/bitnami/event.json"


@pytest.fixture(scope="module")
def event():
    return OSSEvent(**json.load(open(EVENT, encoding="utf-8")))


@pytest.fixture(scope="module")
def digest_event(event):
    """Same event, but the artifact is named by digest, not tag."""
    clone = event.model_copy(deep=True)
    clone.affected_artifacts = [
        Artifact(kind="docker-image", ref="docker.io/bitnami/redis@sha256:aaa")
    ]
    clone.scope = None
    return clone


# ---------------------------------------------------------------- reader


class TestReader:
    def test_line_format_with_comments_and_blanks(self):

        deps, skipped = load_image_inventory_doc(
            "# header\n\nredis:7.2\n\n# mid comment\ndocker.io/library/nginx:1.27\n"
        )

        assert deps == [
            {"kind": "image", "ref": "redis:7.2"},
            {"kind": "image", "ref": "docker.io/library/nginx:1.27"},
        ]

        assert skipped == []

    def test_digest_pinned_line_is_kept_verbatim(self):

        deps, _ = load_image_inventory_doc("bitnami/redis@sha256:abc123\n")

        assert deps == [{"kind": "image", "ref": "bitnami/redis@sha256:abc123"}]

    def test_malformed_line_is_skipped_and_recorded(self):

        deps, skipped = load_image_inventory_doc("redis:7.2\nnot a ref!\n??\n")

        assert deps == [{"kind": "image", "ref": "redis:7.2"}]

        assert len(skipped) == 2

        assert "not a ref!" in skipped[0]

    def test_yaml_list_shape(self):

        deps, skipped = load_image_inventory_doc(["redis:7.2", "nginx:1.27"])

        assert deps == [
            {"kind": "image", "ref": "redis:7.2"},
            {"kind": "image", "ref": "nginx:1.27"},
        ]

        assert skipped == []

    def test_yaml_images_mapping_shape(self):

        deps, skipped = load_image_inventory_doc({"images": ["redis:7.2", {"ref": "nginx:1.27"}]})

        assert deps == [
            {"kind": "image", "ref": "redis:7.2"},
            {"kind": "image", "ref": "nginx:1.27"},
        ]

        assert skipped == []

    def test_mapping_without_string_ref_is_skipped(self):

        deps, skipped = load_image_inventory_doc([{"ref": 5}, {"image": "redis:7.2"}])

        assert deps == []

        assert len(skipped) == 2

        assert "needs a string `ref`" in skipped[0]

    def test_non_mapping_non_list_is_refused(self):

        with pytest.raises(ValueError):
            load_image_inventory_doc(42)

    def test_mapping_without_images_key_is_refused(self):

        with pytest.raises(ValueError):
            load_image_inventory_doc({"dependencies": []})

    def test_read_from_disk_line_format(self):

        deps, skipped = read_image_inventory(FIXTURE)

        assert len(deps) == 4

        assert skipped == []

        assert deps[0] == {"kind": "image", "ref": "docker.io/bitnami/redis:7.2"}

        assert deps[1]["ref"] == "docker.io/redis:7.2"

        assert deps[2]["ref"].startswith("docker.io/redis@sha256:5d1e9f06")

        assert deps[3]["ref"].startswith("docker.io/redis@sha256:0000")

    def test_read_yaml_list_from_disk(self, tmp_path):

        path = tmp_path / "inventory.yaml"

        path.write_text(
            "# images in yaml\nimages:\n  - redis:7.2\n  - nginx:1.27\n",
            encoding="utf-8",
        )

        deps, skipped = read_image_inventory(str(path))

        assert len(deps) == 2

        assert skipped == []

    def test_read_dash_list_from_disk(self, tmp_path):

        path = tmp_path / "inventory.yaml"

        path.write_text("- redis:7.2\n- nginx:1.27\n", encoding="utf-8")

        deps, skipped = read_image_inventory(str(path))

        assert len(deps) == 2

    def test_size_cap_refuses_huge_files(self, tmp_path):

        path = tmp_path / "big.txt"

        path.write_bytes(b"x" * (MAX_INVENTORY_BYTES + 1))

        with pytest.raises(ValueError, match="limit"):
            read_image_inventory(str(path))

    def test_bounded_read_accepts_under_cap(self, tmp_path):
        path = tmp_path / "small.txt"
        path.write_text("redis:7.2\n", encoding="utf-8")
        deps, _ = read_image_inventory(str(path))
        assert deps == [{"kind": "image", "ref": "redis:7.2"}]


# ---------------------------------------------------------------- policy


class TestTagVsDigestPolicy:
    def test_digest_of_extracts_pinned_digest(self):
        assert digest_of("redis@sha256:abc") == "sha256:abc"
        assert digest_of("docker.io/bitnami/redis:7.2") is None
        assert digest_of("redis@") is None
        assert digest_of("redis") is None

    def test_tag_vs_tag_has_no_policy_opinion(self):
        # Same pinning form: the caller's tag semantics apply unchanged.
        assert tag_vs_digest_policy("redis:7.2", "redis:7.2") == {}

    def test_digest_vs_digest_equal_is_exact(self):
        assert tag_vs_digest_policy("redis@sha256:aaa", "redis@sha256:aaa") == {}

    def test_digest_vs_digest_different_is_not_affected(self, digest_event):
        result = event_affects_ref(digest_event, "docker.io/bitnami/redis@sha256:bbb")
        assert result["relationship"] == "NOT_AFFECTED"
        assert result["affected"] is False
        assert "pins digest" in result["detail"]

    def test_digest_vs_digest_equal_still_affects_artifact(self, digest_event):
        result = event_affects_ref(digest_event, "docker.io/bitnami/redis@sha256:aaa")
        assert result["relationship"] == "AFFECTS_ARTIFACT"
        assert result["affected"] is True

    def test_mixed_pinning_is_related_never_digest_certainty(self, digest_event):
        """A moving tag never reports digest-level certainty (acceptance)."""
        result = event_affects_ref(digest_event, "docker.io/bitnami/redis:7.2")
        assert result["relationship"] == "RELATED"
        assert result["affected"] is False
        assert "mix pinning forms" in result["detail"]

    def test_mixed_pinning_flips_direction_too(self, event):
        """Dep pins a digest, event artifact names a tag: same policy."""
        result = event_affects_ref(event, "docker.io/bitnami/redis@sha256:zzz")
        assert result["relationship"] == "RELATED"
        assert result["affected"] is False
        assert "never reports digest-level certainty" in result["detail"]

    def test_mixed_pinning_does_not_false_clear(self, digest_event):
        """RELATED must not degrade into NOT_AFFECTED: no tag observation
        exists, so the pinned bytes are unevaluated, not cleared."""
        result = event_affects_ref(digest_event, "docker.io/bitnami/redis:7.2")
        assert result["relationship"] not in ("AFFECTS_ARTIFACT", "NOT_AFFECTED")

    def test_check_dependency_confidence_for_mixed_pinning(self, event):
        verdict = check_dependency(
            {"kind": "image", "ref": "docker.io/bitnami/redis@sha256:zzz"}, [event]
        )
        assert verdict.affected is False
        assert verdict.relationship == "RELATED"
        # RELATED caps at UNVERIFIED by the decision matrix - the mixed
        # pinning uncertainty is visible in the confidence too.
        assert verdict.confidence == "UNVERIFIED"

    def test_check_dependency_digest_parity_with_watchlist(self, event):
        """Digest-pinned dep through the whole check path: same repo as the
        tag-named artifact -> RELATED (uncertainty), not CONFIRMED."""
        verdict = check_dependency(
            {"kind": "image", "ref": "docker.io/bitnami/redis@sha256:zzz"}, [event]
        )
        assert verdict.relationship == "RELATED"
        assert verdict.affected is False


# ---------------------------------------------------------------- parity


class TestWatchlistParity:
    def test_inventory_entries_match_watchlist_verdicts(self, event):
        """Acceptance: identical verdicts for the same refs via watchlist."""
        deps, _ = read_image_inventory(FIXTURE)
        watchlist_doc = {"dependencies": [{"ref": dep["ref"]} for dep in deps]}
        from core.risk.check import load_watchlist_doc

        watchlist_deps = load_watchlist_doc(watchlist_doc)
        assert [d["ref"] for d in watchlist_deps] == [d["ref"] for d in deps]
        for dep, wl in zip(deps, watchlist_deps):
            v1 = check_dependency(dep, [event])
            v2 = check_dependency(wl, [event])
            assert v1.relationship == v2.relationship
            assert v1.affected == v2.affected
            assert v1.confidence == v2.confidence
            assert v1.reason == v2.reason


# ---------------------------------------------------------------- CLI


class TestCheckCliImages:
    def _run(self, *args):
        from click.testing import CliRunner

        from cli.main import cli

        return CliRunner().invoke(cli, ["check", *args])

    def test_images_only_run(self):
        out = self._run("--images", FIXTURE, "--event", EVENT)
        assert out.exit_code == 0, out.output
        assert "images: 4 image ref(s) from inventory" in out.output
        assert "docker.io/bitnami/redis:7.2: AFFECTED" in out.output
        assert "docker.io/redis:7.2: NOT_AFFECTED" in out.output
        assert "1/4 dependencies affected" in out.output

    def test_images_composes_with_watchlist(self):
        out = self._run(
            "--images",
            FIXTURE,
            "--watchlist",
            "data/fixtures/watchlist_sample.yaml",
            "--event",
            EVENT,
        )
        assert out.exit_code == 0, out.output
        # 4 inventory + 3 watchlist entries; bitnami/redis:7.2 appears in
        # both inputs and matches the event artifact both times.
        assert "2/7 dependencies affected" in out.output

    def test_images_skip_reasons_are_echoed(self, tmp_path):
        path = tmp_path / "inventory.txt"
        path.write_text("redis:7.2" + chr(10) + "not a ref!" + chr(10), encoding="utf-8")
        out = self._run("--images", str(path), "--event", EVENT)
        assert out.exit_code == 0, out.output
        assert "! skipped: `not a ref!` is not a plausible image ref" in out.output
        assert "images: 1 image ref(s) from inventory" in out.output

    def test_images_all_skipped_reports_nothing_checkable(self, tmp_path):
        path = tmp_path / "inventory.txt"
        path.write_text("not a ref!" + chr(10) + "also not one" + chr(10), encoding="utf-8")
        out = self._run("--images", str(path), "--event", EVENT)
        assert out.exit_code != 0
        assert "no checkable dependencies" in out.output

    def test_images_strict_fires_when_affected(self):
        out = self._run("--images", FIXTURE, "--event", EVENT, "--strict")
        assert out.exit_code == 1

    def test_images_composes_with_sbom(self):
        out = self._run(
            "--images",
            FIXTURE,
            "--sbom",
            "data/fixtures/sbom/cyclonedx.json",
            "--event",
            EVENT,
        )
        assert out.exit_code == 0, out.output
        # 4 inventory + 3 mapped SBOM = 7; bitnami/redis:7.2 in both.
        assert "2/7 dependencies affected" in out.output

    def test_images_digest_output(self):
        out = self._run("--images", FIXTURE, "--event", EVENT, "--digest")
        assert out.exit_code == 0, out.output
        assert "# OpenPulse watchlist digest" in out.output
        assert "1/4 dependencies affected" in out.output


class TestBareNames:
    def test_bare_name_resolves_to_hub_library(self):
        """`redis` (no tag, no namespace) is a valid ref: the identity
        layer maps it to docker.io/library/redis, so it must not be
        skipped as malformed."""
        deps, skipped = load_image_inventory_doc("redis" + chr(10) + "nginx:1.27" + chr(10))
        assert deps == [
            {"kind": "image", "ref": "redis"},
            {"kind": "image", "ref": "nginx:1.27"},
        ]
        assert skipped == []
        from core.risk.match import split_image_ref

        assert split_image_ref("redis") == ("docker.io", "library", "redis")

    def test_bare_name_verdict_matches_watchlist_parity(self, event):
        v1 = check_dependency({"kind": "image", "ref": "redis"}, [event])
        v2 = check_dependency({"kind": "image", "ref": "docker.io/library/redis"}, [event])
        assert v1.relationship == v2.relationship == "NOT_AFFECTED"
