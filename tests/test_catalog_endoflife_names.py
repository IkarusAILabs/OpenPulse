"""endoflife.date product names that differ from the catalog slug.

endoflife.date renamed these products and answers the old names with a
301, which the collector never follows, so their lifecycle data was
missing from every report (found by the November 2026 report run, which
now names sources that did not answer).
"""

import pytest

from core.entities.catalog import endoflife_map


@pytest.mark.parametrize(
    ("slug", "product"),
    [
        ("cockroach", "cockroachdb"),
        ("loki", "grafana-loki"),
        ("nest", "nestjs"),
        ("vault", "hashicorp-vault"),
    ],
)
def test_renamed_products_map_to_their_current_endoflife_name(slug, product):
    assert endoflife_map()[slug] == product
