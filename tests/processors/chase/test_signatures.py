"""
tests/processors/chase/test_signatures.py

Tests for Chase institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.chase import (
    CHASE_BUSINESS_CREDIT_CARD_SIGNATURES,
    CHASE_CHECKING_SIGNATURES,
    CHASE_CREDIT_CARD_SIGNATURES,
    CHASE_HELOC_SIGNATURES,
    CHASE_SIGNATURES,
)


def test_chase_business_credit_card_signatures_are_stable() -> None:
    assert len(CHASE_BUSINESS_CREDIT_CARD_SIGNATURES) == 2

    assert CHASE_BUSINESS_CREDIT_CARD_SIGNATURES[0].institution == "chase"
    assert CHASE_BUSINESS_CREDIT_CARD_SIGNATURES[0].required_markers == (
        "www.chase.com/ink",
        "Revolving Credit Amount",
        "pening/Closing Date",
    )

    assert CHASE_BUSINESS_CREDIT_CARD_SIGNATURES[1].institution == "chase"
    assert CHASE_BUSINESS_CREDIT_CARD_SIGNATURES[1].required_markers == (
        "chase.com/cardhelp",
        "Revolving Credit Amount",
        "pening/Closing Date",
    )


def test_chase_credit_card_signatures_are_stable() -> None:
    assert len(CHASE_CREDIT_CARD_SIGNATURES) == 3

    assert CHASE_CREDIT_CARD_SIGNATURES[0].institution == "chase"
    assert CHASE_CREDIT_CARD_SIGNATURES[0].required_markers == (
        "chase.com/cardhelp",
        "pening/Closing Date",
    )

    assert CHASE_CREDIT_CARD_SIGNATURES[1].institution == "chase"
    assert CHASE_CREDIT_CARD_SIGNATURES[1].required_markers == (
        "www.chase.com",
        "Credit Card Statement",
        "pening/Closing Date",
    )

    assert CHASE_CREDIT_CARD_SIGNATURES[2].institution == "chase"
    assert CHASE_CREDIT_CARD_SIGNATURES[2].required_markers == (
        "www.Chase.com/",
        "Credit Card Statement",
        "pening/Closing Date",
    )


def test_chase_checking_signatures_are_stable() -> None:
    assert len(CHASE_CHECKING_SIGNATURES) == 1

    assert CHASE_CHECKING_SIGNATURES[0].institution == "chase"
    assert CHASE_CHECKING_SIGNATURES[0].required_markers == (
        "JPMorgan Chase Bank, N.A.",
        "CHECKING SUMMARY",
        "TRANSACTION DETAIL",
    )


def test_chase_heloc_signatures_are_stable() -> None:
    assert len(CHASE_HELOC_SIGNATURES) == 1

    assert CHASE_HELOC_SIGNATURES[0].institution == "chase"
    assert CHASE_HELOC_SIGNATURES[0].required_markers == (
        "JPMorgan Chase Bank, N.A.",
        "Line of credit information",
        "Transaction activity",
    )


def test_chase_signatures_include_all_account_families() -> None:
    assert (
        *CHASE_BUSINESS_CREDIT_CARD_SIGNATURES,
        *CHASE_CREDIT_CARD_SIGNATURES,
        *CHASE_CHECKING_SIGNATURES,
        *CHASE_HELOC_SIGNATURES,
    ) == CHASE_SIGNATURES
