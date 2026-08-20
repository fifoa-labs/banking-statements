"""
tests/processors/capital_one/checking/test_processor.py

Tests for the Capital One checking statement processor.
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
    CapitalOneCheckingProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-capital-one-checking.pdf"),
        sha256="a" * 64,
    )


def supported_prefix() -> str:
    """Return synthetic supported Capital One checking structure."""
    return (
        "Here's your March 2026 bank statement. STATEMENT PERIOD\n"
        "Mar 1 - Mar 31, 2026\n"
        "Account Summary Cashflow Summary\n"
        "360 Checking...1234 $100.00 $125.00\n"
        "360 Checking - 70000001234\n"
        "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
        "Mar 1 Opening Balance $100.00\n"
        "capitalone.com\n"
    )


def test_processor_name_is_stable() -> None:
    assert CapitalOneCheckingProcessor().name == "capital_one.checking.v1"


def test_processor_matches_supported_statement() -> None:
    result = CapitalOneCheckingProcessor().match(
        make_text(
            supported_prefix() + "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Mar 31 Closing Balance $100.00\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Capital One checking statement structure."
    )


def test_processor_rejects_other_statement() -> None:
    result = CapitalOneCheckingProcessor().match(
        make_text("Other bank statement")
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Capital One checking markers were not found."
    )


def test_processor_parses_and_reconciles_statement() -> None:
    statement = CapitalOneCheckingProcessor().parse(
        make_source(),
        make_text(
            "Here's your March 2026 bank statement. STATEMENT PERIOD\n"
            "Mar 1 - Mar 31, 2026\n"
            "Account Summary Cashflow Summary\n"
            "360 Checking...1234 $100.00 $125.00\n"
            "360 Checking - 70000001234\n"
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Mar 1 Opening Balance $100.00\n"
            "Page 1 of 2\n"
            "capitalone.com\n"
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Mar 5 SAMPLE PAYROLL Credit + $50.00 $150.00\n"
            "Mar 10 SAMPLE PAYMENT Debit - $25.00 $125.00\n"
            "Mar 31 Closing Balance $125.00\n"
            "Fees Summary\n"
        ),
    )

    assert statement.institution == "capital_one"
    assert statement.processor == "capital_one.checking.v1"
    assert statement.account.account_type is AccountType.CHECKING
    assert statement.account.display_number == "70000001234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 3, 1)
    assert statement.period.end == date(2026, 3, 31)
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("125.00")

    assert len(statement.transactions) == 2
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[1].direction is TransactionDirection.DEBIT

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")
