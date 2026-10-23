"""GitHub Marketplace constraints on the root action.yml.

The Marketplace refuses to publish a release whose action.yml breaks
these rules, and the failure only shows up on the release page, after
the tag exists. Checking them here keeps a release from being cut with
metadata that cannot be listed.
"""

from pathlib import Path

import yaml

ACTION = yaml.safe_load(Path("action.yml").read_text(encoding="utf-8"))


def test_description_fits_marketplace_limit():
    assert len(ACTION["description"]) < 125


def test_required_listing_fields():
    assert ACTION["name"].strip()
    assert ACTION["runs"]["using"] == "composite"
    assert set(ACTION["branding"]) == {"icon", "color"}
