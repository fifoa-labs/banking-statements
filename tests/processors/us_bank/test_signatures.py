"""
tests/processors/us_bank/test_signatures.py

Tests for U.S. Bank institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.us_bank import (
    US_BANK_BUSINESS_CHECKING_SIGNATURES,
    US_BANK_CREDIT_CARD_SIGNATURES,
    US_BANK_SIGNATURES,
)


def test_us_bank_business_checking_signature_is_stable() -> None:
    signature = US_BANK_BUSINESS_CHECKING_SIGNATURES[0]
    assert signature.institution == "us_bank"
    assert signature.required_markers == (
        "U.S. BANK SILVER - BUSINESS CHECKING",
        "U.S. Bank National Association",
        "Account Summary",
        "Beginning Balance on",
        "Ending Balance on",
    )


def test_us_bank_credit_card_signature_is_stable() -> None:
    signature = US_BANK_CREDIT_CARD_SIGNATURES[0]
    assert signature.institution == "us_bank"
    assert signature.required_markers == (
        "Cardmember Service",
        "Activity Summary",
        "Previous Balance",
        "New Balance",
        "U.S. Bank",
    )


def test_us_bank_signatures_include_all_account_families() -> None:
    assert (
        *US_BANK_BUSINESS_CHECKING_SIGNATURES,
        *US_BANK_CREDIT_CARD_SIGNATURES,
    ) == US_BANK_SIGNATURES
