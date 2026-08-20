"""
tests/processors/american_express/business_line_of_credit/test_processor.py

Tests for the American Express business line-of-credit statement processor.
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
from banking_statements.processors.american_express import (
    AmericanExpressBusinessLineOfCreditProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-american-express-loc.pdf"),
        sha256="a" * 64,
    )


def test_processor_name_is_stable() -> None:
    assert (
        AmericanExpressBusinessLineOfCreditProcessor().name
        == "american_express.business_line_of_credit.v1"
    )


def test_processor_matches_supported_structure() -> None:
    result = AmericanExpressBusinessLineOfCreditProcessor().match(
        make_text(
            "Monthly statement\n"
            "Statement Date 04/30/2026\n"
            "For the Period 04/01/2026 - 04/30/2026\n"
            "Account number 123456\n"
            "Summary of account activity\n"
            "Previous balance $1,000.00\n"
            "+ Loans/debits $200.00\n"
            "+ Costs and fees $25.00\n"
            "- Payments/credits $100.00\n"
            "New balance $1,125.00\n"
            "Transaction Summary\n"
            "American Express Business Line of Credit Account\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched American Express business line-of-credit statement structure."
    )


def test_processor_rejects_unsupported_structure() -> None:
    result = AmericanExpressBusinessLineOfCreditProcessor().match(
        make_text("American Express account information")
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required American Express business line-of-credit markers "
        "were not found."
    )


def test_processor_parses_and_reconciles_statement() -> None:
    processor = AmericanExpressBusinessLineOfCreditProcessor()

    statement = processor.parse(
        make_source(),
        make_text(
            "Monthly statement\n"
            "Statement Date 04/30/2026\n"
            "For the Period 04/01/2026 - 04/30/2026\n"
            "Account number 123456\n"
            "Summary of account activity Payment information\n"
            "Previous balance $1,000.00 Current payment due $100.00\n"
            "+ Loans/debits $200.00 $0.00\n"
            "+ Costs and fees $25.00\n"
            "- Payments/credits $100.00\n"
            "New balance $1,125.00 Payment due date 05/15/2026\n"
            "Transaction Summary\n"
            "Date Reference number Description Amount\n"
            "04/10/2026 1234567890 SAMPLE ADVANCE $200.00\n"
            "04/20/2026 0987654321 SAMPLE FEE $25.00\n"
            "04/25/2026 1111222233 SAMPLE PAYMENT ($100.00)\n"
            "1. Sample informational text\n"
            "American Express Business Line of Credit Account\n"
        ),
    )

    assert statement.institution == "american_express"
    assert statement.processor == processor.name
    assert statement.account.account_type is AccountType.LINE_OF_CREDIT
    assert statement.account.display_number == "123456"
    assert statement.account.last4 == "3456"
    assert statement.period.start == date(2026, 4, 1)
    assert statement.period.end == date(2026, 4, 30)
    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("1125.00")

    assert len(statement.transactions) == 3
    assert statement.transactions[0].direction is TransactionDirection.DEBIT
    assert statement.transactions[0].amount == Decimal("200.00")
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert statement.transactions[1].amount == Decimal("25.00")
    assert statement.transactions[2].direction is TransactionDirection.CREDIT
    assert statement.transactions[2].amount == Decimal("100.00")

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")
