"""
tests/processors/capital_one/credit_card/test_processor.py

Tests for the Capital One credit-card statement processor.
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
from banking_statements.processors.capital_one import (
    CapitalOneCreditCardProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-capital-one-credit-card.pdf"),
        sha256="a" * 64,
    )


def test_processor_name_is_stable() -> None:
    assert CapitalOneCreditCardProcessor().name == "capital_one.credit_card.v1"


def test_processor_matches_supported_statement() -> None:
    result = CapitalOneCreditCardProcessor().match(
        make_text(
            "Venture X Card | Visa Infinite ending in 1234\n"
            "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            "Account Summary\n"
            "Account ending in 1234\n"
            "Capital One\n"
            "Transactions\n"
            "Trans Date Post Date Description Amount\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Capital One credit-card statement structure."
    )


def test_processor_rejects_other_statement() -> None:
    result = CapitalOneCreditCardProcessor().match(
        make_text("Other financial statement")
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Capital One credit-card markers were not found."
    )


def test_processor_parses_and_reconciles_statement() -> None:
    statement = CapitalOneCreditCardProcessor().parse(
        make_source(),
        make_text(
            "Venture X Card | Visa Infinite ending in 1234\n"
            "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            "Payment Information Account Summary\n"
            "Previous Balance $100.00\n"
            "New Balance = $132.00\n"
            "Account ending in 1234\n"
            "Capital One\n"
            "Transactions\n"
            "SAMPLE PERSON #1234: Payments, Credits and Adjustments\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 10 Mar 11 SAMPLE PAYMENT - $25.00\n"
            "SAMPLE PERSON #1234: Transactions\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 20 Mar 21 SAMPLE MARKET $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 25 Mar 25 SAMPLE FEE $3.00\n"
            "Total Fees for This Period $3.00\n"
            "Interest Charged\n"
            "Interest Charge on Purchases $4.00\n"
            "Total Interest for This Period $4.00\n"
        ),
    )

    assert statement.institution == "capital_one"
    assert statement.processor == "capital_one.credit_card.v1"
    assert statement.account.account_type is AccountType.CREDIT_CARD
    assert statement.account.display_number == "1234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 3, 1)
    assert statement.period.end == date(2026, 3, 31)
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("132.00")

    assert len(statement.transactions) == 4
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[0].date == date(2026, 3, 11)
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert statement.transactions[2].description == "SAMPLE FEE"
    assert statement.transactions[3].description == "INTEREST CHARGED"

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")
