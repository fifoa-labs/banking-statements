"""
tests/processors/test_base.py

Tests for processor matching models.
"""

from __future__ import annotations

from banking_statements.processors import ProcessorMatch


def test_processor_match_defaults() -> None:
    match = ProcessorMatch(matched=False)

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == ""
