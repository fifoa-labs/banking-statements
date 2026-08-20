"""
tests/processors/american_express/test_signatures.py

Tests for American Express institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.american_express import (
    AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES,
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


def test_american_express_business_checking_signatures_are_stable() -> None:
    assert len(AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES) == 2

    legacy_signature = AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES[0]
    current_signature = AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES[1]

    assert legacy_signature.institution == "american_express"
    assert legacy_signature.required_markers == (
        "Business Checking Account Statement",
        "StatementPeriod",
        "AccountEnding",
        "BeginningBalance",
        "EndingBalance",
        "Account Activity",
    )

    assert current_signature.institution == "american_express"
    assert current_signature.required_markers == (
        "Business Checking Account Statement",
        "Statement Date:",
        "Account Ending:",
        "Beginning Balance as of",
        "Ending Balance as of",
        "Account Activity",
    )


def test_american_express_signatures_include_all_account_families() -> None:
    assert (
        *AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES,
        *AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES,
    ) == AMERICAN_EXPRESS_SIGNATURES
