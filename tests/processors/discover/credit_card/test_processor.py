"""
tests/processors/discover/credit_card/test_processor.py

Tests for the Discover credit-card statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.discover import DiscoverCreditCardProcessor
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-discover-credit-card.pdf"),
        sha256="a" * 64,
    )


def test_processor_name_is_stable() -> None:
    assert DiscoverCreditCardProcessor().name == "discover.credit_card.v1"


def test_processor_matches_legacy_statement() -> None:
    result = DiscoverCreditCardProcessor().match(
        make_text(
            "Discover it® Card\n"
            "Account number ending in1234\n"
            "Open Date:Dec 15, 2025- Close Date:Jan 14, 2026\n"
            "ACCOUNT SUMMARY\n"
            "Transactions\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Discover credit-card statement structure."
    )


def test_processor_matches_current_statement() -> None:
    result = DiscoverCreditCardProcessor().match(
        make_text(
            "DISCOVER IT® CARD ENDING IN 1234\n"
            "AccountSummary 03/01/2026 -03/31/2026 PaymentInformation\n"
            "PreviousBalance $100.00\n"
            "NewBalance: $125.00\n"
            "Transactions\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100


def test_processor_rejects_other_statement() -> None:
    result = DiscoverCreditCardProcessor().match(
        make_text("Other financial statement")
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Discover credit-card markers were not found."
    )


def test_processor_parses_and_reconciles_current_statement() -> None:
    statement = DiscoverCreditCardProcessor().parse(
        make_source(),
        make_text(
            "DISCOVER IT® CARD ENDING IN 1234\n"
            "AccountSummary 03/01/2026 -03/31/2026 PaymentInformation\n"
            "PreviousBalance $100.00 NewBalance MinimumPayment PaymentDueDate\n"  # noqa: E501
            "NewBalance: $132.00\n"
            "Transactions Cashback Bonus® Rewards\n"
            "DATE PAYMENTSANDCREDITS AMOUNT\n"
            "03/10 SAMPLE PAYMENT -$25.00\n"
            "DATE PURCHASES MERCHANTCATEGORY AMOUNT\n"
            "03/20 SAMPLE MARKET Grocery $50.00\n"
            "FeesandInterestCharged\n"
            "TOTALFEESFORTHISPERIOD $3.00\n"
            "TOTALINTERESTFORTHISPERIOD $4.00\n"
        ),
    )

    assert statement.institution == "discover"
    assert statement.processor == "discover.credit_card.v1"
    assert statement.account.account_type is AccountType.CREDIT_CARD
    assert statement.account.display_number == "1234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 3, 1)
    assert statement.period.end == date(2026, 3, 31)
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("132.00")

    assert len(statement.transactions) == 4
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert statement.transactions[2].description == "FEES CHARGED"
    assert statement.transactions[3].description == "INTEREST CHARGED"

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")
