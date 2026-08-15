"""
tests/processors/chase/checking/test_processor.py

Tests for the Chase checking statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.chase import ChaseCheckingProcessor
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for processor tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_processor_name_is_stable() -> None:
    processor = ChaseCheckingProcessor()

    assert processor.name == "chase.checking.v1"


def test_processor_matches_supported_structure() -> None:
    processor = ChaseCheckingProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "JPMorgan Chase Bank, N.A.",
                "CHECKING SUMMARY Chase Total Checking",
                "TRANSACTION DETAIL",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == "Matched Chase checking statement structure."


def test_processor_rejects_unsupported_structure() -> None:
    processor = ChaseCheckingProcessor()

    match = processor.match(
        make_statement_text("Not a Chase checking statement"),
    )

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == ("Required Chase checking markers were not found.")


def test_processor_parses_statement() -> None:
    processor = ChaseCheckingProcessor()

    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "January 1, 2026 through January 31, 2026",
                "JPMorgan Chase Bank, N.A.",
                "Account Number: 000000000001234",
                "CHECKING SUMMARY Chase Total Checking",
                "Beginning Balance $1,000.00",
                "Ending Balance $1,150.00",
                "*start*transactiondetail",
                "TRANSACTION DETAIL",
                "DATE DESCRIPTION AMOUNT BALANCE",
                "Beginning Balance $1,000.00",
                "01/05 SAMPLE DEPOSIT 200.00 1,200.00",
                "01/10 SAMPLE PAYMENT -50.00 1,150.00",
                "Ending Balance $1,150.00",
                "*end*transactiondetail",
            )
        )
    )

    statement = processor.parse(source, text)

    assert statement.source is source
    assert statement.institution == "chase"
    assert statement.processor == "chase.checking.v1"

    assert statement.account.account_type.value == "checking"
    assert statement.account.display_number == "000000000001234"
    assert statement.account.last4 == "1234"

    assert statement.period.start == date(2026, 1, 1)
    assert statement.period.end == date(2026, 1, 31)

    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("1150.00")

    assert len(statement.transactions) == 2

    deposit = statement.transactions[0]
    assert deposit.date == date(2026, 1, 5)
    assert deposit.amount == Decimal("200.00")
    assert deposit.direction is TransactionDirection.CREDIT
    assert deposit.description == "SAMPLE DEPOSIT"

    payment = statement.transactions[1]
    assert payment.date == date(2026, 1, 10)
    assert payment.amount == Decimal("50.00")
    assert payment.direction is TransactionDirection.DEBIT
    assert payment.description == "SAMPLE PAYMENT"
