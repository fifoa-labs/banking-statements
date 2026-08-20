"""
tests/processors/capital_one/test_signatures.py

Tests for Capital One institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.capital_one import (
    CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES,
    CAPITAL_ONE_CHECKING_SIGNATURES,
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


def test_capital_one_business_credit_card_signatures_are_stable() -> None:
    assert len(CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES) == 3

    legacy_spark, current_spark, venture_x_business = (
        CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES
    )

    assert legacy_spark.institution == "capital_one"
    assert legacy_spark.required_markers == (
        "Spark® Visa Signature Business Account Ending in",
        "days in Billing Cycle",
        "Account Summary",
        "Date Description Amount",
        "Fees",
        "Capital One",
    )

    assert current_spark.required_markers == (
        "Spark Cash credit card | Visa Signature Business ending in",
        "days in Billing Cycle",
        "Account Summary",
        "Trans Date Post Date Description Amount",
        "Fees",
        "Capital One",
    )

    assert venture_x_business.required_markers == (
        "Venture X Business card | Visa Infinite Business ending in",
        "days in Billing Cycle",
        "Account Summary",
        "Trans Date Post Date Description Amount",
        "Fees",
        "Capital One",
    )


def test_capital_one_checking_signature_is_stable() -> None:
    assert len(CAPITAL_ONE_CHECKING_SIGNATURES) == 1

    signature = CAPITAL_ONE_CHECKING_SIGNATURES[0]

    assert signature.institution == "capital_one"
    assert signature.required_markers == (
        "STATEMENT PERIOD",
        "Account Summary Cashflow Summary",
        "360 Checking - ",
        "DATE DESCRIPTION CATEGORY AMOUNT BALANCE",
        "Opening Balance",
        "Closing Balance",
        "capitalone.com",
    )


def test_capital_one_signatures_include_all_account_families() -> None:
    assert (
        *CAPITAL_ONE_CREDIT_CARD_SIGNATURES,
        *CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES,
        *CAPITAL_ONE_CHECKING_SIGNATURES,
    ) == CAPITAL_ONE_SIGNATURES
