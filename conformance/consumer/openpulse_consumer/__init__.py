"""Validate and read OpenPulse evidence contracts without OpenPulse (v0.19.0 P1).

A consumer of OpenPulse's evidence needs to know three things about a
document it was handed: is it a well-formed contract of the version it
claims, was it altered, and what did it establish. This package answers the
first with nothing but the published JSON Schemas and ``jsonschema``, and
the second by recomputing the content hash (P3); the outcome summary (P4)
builds on them.

It imports nothing from OpenPulse, on purpose: a third party can install it
alone (``requirements.lock`` beside it, hash-pinned) and get the same answer
OpenPulse's own validator gives.
"""

from openpulse_consumer.contract import (
    MAX_DOCUMENTS_BYTES,
    Check,
    check,
    read_jsonl,
    schemas,
    supported_versions,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_DOCUMENTS_BYTES",
    "Check",
    "__version__",
    "check",
    "read_jsonl",
    "schemas",
    "supported_versions",
]
