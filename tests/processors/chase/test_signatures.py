"""
tests/processors/chase/test_signatures.py

Tests for Chase institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.chase import CHASE_SIGNATURES


def test_chase_signatures_are_stable() -> None:
    assert len(CHASE_SIGNATURES) == 2

    assert CHASE_SIGNATURES[0].institution == "chase"
    assert CHASE_SIGNATURES[0].required_markers == (
        "www.chase.com/cardhelp",
        "Account Number:",
        "Opening/Closing Date",
    )

    assert CHASE_SIGNATURES[1].institution == "chase"
    assert CHASE_SIGNATURES[1].required_markers == (
        "www.chase.com/cardhelp",
        "Account number:",
        "Opening/Closing Date",
    )
