"""
tests/processors/american_express/test_signatures.py

Tests for American Express institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.american_express import (
    AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES,
    AMERICAN_EXPRESS_SIGNATURES,
)


def test_american_express_credit_card_signatures_are_stable() -> None:
    assert len(AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES) == 1

    signature = AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES[0]

    assert signature.institution == "american_express"
    assert signature.required_markers == (
        "American Express",
        "Closing Date",
        "Account Ending",
        "Previous Balance",
        "New Charges",
    )


def test_american_express_signatures_include_all_account_families() -> None:
    assert (
        *AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES,
    ) == AMERICAN_EXPRESS_SIGNATURES
