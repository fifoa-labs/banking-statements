"""
tests/processors/chase/test_signatures.py

Tests for Chase institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.chase import CHASE_SIGNATURES


def test_chase_signatures_are_stable() -> None:
    assert len(CHASE_SIGNATURES) == 3

    assert CHASE_SIGNATURES[0].institution == "chase"
    assert CHASE_SIGNATURES[0].required_markers == (
        "chase.com/cardhelp",
        "pening/Closing Date",
    )

    assert CHASE_SIGNATURES[1].institution == "chase"
    assert CHASE_SIGNATURES[1].required_markers == (
        "www.chase.com",
        "Credit Card Statement",
        "pening/Closing Date",
    )

    assert CHASE_SIGNATURES[2].institution == "chase"
    assert CHASE_SIGNATURES[2].required_markers == (
        "www.Chase.com/",
        "Credit Card Statement",
        "pening/Closing Date",
    )
