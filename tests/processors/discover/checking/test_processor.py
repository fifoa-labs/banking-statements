"""
tests/processors/discover/checking/test_processor.py

Tests for the Discover checking statement processor.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.discover import DiscoverCheckingProcessor
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_processor_name_and_matching() -> None:
    processor = DiscoverCheckingProcessor()
    assert processor.name == "discover.checking.v1"

    matched = processor.match(
        make_text(
            "CASHBACK CHECKING\n"
            "Statement Period: Apr 01, 2026 -Apr 30, 2026\n"
            "ACCOUNT SUMMARY\n"
            "Beginning Balance ..........$100.00\n"
            "Ending Balance .............$125.00\n"
            "DiscoverBank.com\n"
        )
    )
    unmatched = processor.match(make_text("Other bank statement"))

    assert matched.matched is True
    assert matched.confidence == 100
    assert matched.reason == "Matched Discover checking statement structure."
    assert unmatched.matched is False
    assert unmatched.confidence == 0
    assert (
        unmatched.reason
        == "Required Discover checking markers were not found."
    )


def test_processor_parses_and_reconciles_statement() -> None:
    statement = DiscoverCheckingProcessor().parse(
        StatementSource(path=Path("sample.pdf"), sha256="0" * 64),
        make_text(
            "CASHBACK CHECKING\n"
            "Account numberending in1234\n"
            "Statement Period: Apr 01, 2026 -Apr 30, 2026\n"
            "ACCOUNT SUMMARY\n"
            "Beginning Balance ..........................$100.00\n"
            "Ending Balance .............................$125.00\n"
            "DiscoverBank.com\n"
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Apr 10 Apr 10 SAMPLE DEPOSIT 50.00\n"
            "TOTAL DEPOSITS AND CREDITS $ 50.00\n"
            "Electronic Withdrawals\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Apr 20 Apr 20 SAMPLE PAYMENT 25.00\n"
            "TOTAL ELECTRONIC WITHDRAWALS $ 25.00\n"
        ),
    )

    assert statement.institution == "discover"
    assert statement.processor == "discover.checking.v1"
    assert statement.account.account_type is AccountType.CHECKING
    assert statement.account.last4 == "1234"
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("125.00")
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert reconcile_statement(statement).reconciled is True
