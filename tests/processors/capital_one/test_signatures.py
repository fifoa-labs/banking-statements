"""
tests/processors/capital_one/test_signatures.py

Tests for Capital One institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.capital_one import (
    CAPITAL_ONE_CREDIT_CARD_SIGNATURES,
    CAPITAL_ONE_SIGNATURES,
)


def test_capital_one_credit_card_signature_is_stable() -> None:
    assert len(CAPITAL_ONE_CREDIT_CARD_SIGNATURES) == 1

    signature = CAPITAL_ONE_CREDIT_CARD_SIGNATURES[0]

    assert signature.institution == "capital_one"
    assert signature.required_markers == (
        "Venture X Card | Visa Infinite ending in",
        "days in Billing Cycle",
        "Account Summary",
        "Account ending in",
        "Transactions",
        "Trans Date Post Date Description Amount",
        "Capital One",
    )


def test_capital_one_signatures_include_all_account_families() -> None:
    assert (*CAPITAL_ONE_CREDIT_CARD_SIGNATURES,) == CAPITAL_ONE_SIGNATURES
