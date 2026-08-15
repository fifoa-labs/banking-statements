"""
tests/processors/chase/test_signatures.py

Tests for Chase institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.chase import CHASE_SIGNATURES


def test_chase_signature_is_stable() -> None:
    assert len(CHASE_SIGNATURES) == 1

    signature = CHASE_SIGNATURES[0]

    assert signature.institution == "chase"
    assert signature.required_markers == (
        "www.chase.com/cardhelp",
        "Account Number:",
        "Opening/Closing Date",
    )
