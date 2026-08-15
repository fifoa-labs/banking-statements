"""
tests/processors/chase/test_signatures.py

Tests for Chase institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.chase import CHASE_SIGNATURES


def test_chase_signatures_are_stable() -> None:
    assert len(CHASE_SIGNATURES) == 1

    signature = CHASE_SIGNATURES[0]

    assert signature.institution == "chase"
    assert signature.required_markers == (
        "chase.com/cardhelp",
        "pening/Closing Date",
    )
