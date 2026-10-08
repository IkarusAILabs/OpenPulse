"""Compatibility tests for the frozen event vocabulary across the pipeline."""

import json
from pathlib import Path

from core.schema.enums import EventType


def test_every_core_event_type_is_represented_in_evidence_contract():
    schema_path = Path("schemas/evidence-contract/v1/schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    contract_types = set(schema["$defs"]["event_type"]["enum"])
    core_types = {event.value for event in EventType}
    assert core_types == contract_types


def test_event_type_enum_has_no_duplicate_wire_values():
    values = [event.value for event in EventType]
    assert len(values) == len(set(values))
