"""
tests/processors/wellsfargo/business_checking/test_processor.py

Tests for the Wells Fargo business checking statement processor.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.business_checking import (
    WellsFargoBusinessCheckingProcessor,
)
from banking_statements.text import (
    StatementPage,
    StatementText,
    StatementWord,
)


def make_word(
    text: str,
    *,
    x0: float,
    top: float,
    width: float = 20.0,
) -> StatementWord:
    """Build positioned synthetic PDF word evidence."""
    return StatementWord(
        text=text,
        x0=x0,
        x1=x0 + width,
        top=top,
        bottom=top + 8.0,
    )


def make_statement_text(
    text: str,
    *,
    words: tuple[StatementWord, ...] = (),
) -> StatementText:
    """Build single-page statement text for processor tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
                words=words,
            ),
        )
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-wells-fargo-business-checking.pdf"),
        sha256="a" * 64,
    )


def test_processor_name() -> None:
    processor = WellsFargoBusinessCheckingProcessor()

    assert processor.name == "wellsfargo.business_checking.v1"


def test_processor_matches_supported_statement() -> None:
    processor = WellsFargoBusinessCheckingProcessor()

    result = processor.match(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Sample Business Checking",
                    (
                        "Statement period activity summary "
                        "Account number: 1234567890"
                    ),
                    "Withdrawals/Debits - 250.00",
                    "Transaction history",
                )
            )
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Wells Fargo business checking statement structure."
    )


def test_processor_rejects_unsupported_statement() -> None:
    processor = WellsFargoBusinessCheckingProcessor()

    result = processor.match(
        make_statement_text(
            "Some other banking statement",
        )
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Wells Fargo business checking markers were not found."
    )


def test_processor_parses_statement() -> None:
    processor = WellsFargoBusinessCheckingProcessor()

    statement = processor.parse(
        make_source(),
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Sample Business Checking",
                    (
                        "Statement period activity summary "
                        "Account number: 1234567890"
                    ),
                    "Beginning balance on 1/1 $1,000.00",
                    "Deposits/Credits 200.00",
                    "Withdrawals/Debits - 50.00",
                    "Ending balance on 1/31 $1,150.00",
                    "Transaction history",
                    "Date Number Description Credits Debits balance",
                    "1/10 Sample Deposit 200.00 1,200.00",
                    "1/20 Sample Payment 50.00 1,150.00",
                    "Ending balance on 1/31 1,150.00",
                    "Totals $200.00 $50.00",
                    (
                        "Fee period 01/01/2024 - 01/31/2024 "
                        "Standard monthly service fee $10.00"
                    ),
                )
            ),
            words=(
                make_word("Transaction", x0=40.0, top=20.0),
                make_word("history", x0=100.0, top=20.0),
                make_word("Date", x0=40.0, top=30.0),
                make_word("Number", x0=80.0, top=30.0),
                make_word("Description", x0=140.0, top=30.0),
                make_word("Credits", x0=410.0, top=30.0),
                make_word("Debits", x0=470.0, top=30.0),
                make_word("balance", x0=545.0, top=30.0),
                make_word("1/10", x0=40.0, top=40.0),
                make_word("Sample", x0=140.0, top=40.0),
                make_word("Deposit", x0=190.0, top=40.0),
                make_word("200.00", x0=420.0, top=40.0),
                make_word("1,200.00", x0=543.0, top=40.0),
                make_word("1/20", x0=40.0, top=50.0),
                make_word("Sample", x0=140.0, top=50.0),
                make_word("Payment", x0=190.0, top=50.0),
                make_word("50.00", x0=480.0, top=50.0),
                make_word("1,150.00", x0=543.0, top=50.0),
            ),
        ),
    )

    assert statement.institution == "wellsfargo"
    assert statement.processor == "wellsfargo.business_checking.v1"

    assert statement.account.account_type is AccountType.CHECKING
    assert statement.account.display_number == "1234567890"
    assert statement.account.last4 == "7890"

    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("1150.00")

    assert len(statement.transactions) == 2

    first, second = statement.transactions

    assert first.amount == Decimal("200.00")
    assert first.direction is TransactionDirection.CREDIT
    assert first.description == "Sample Deposit"

    assert second.amount == Decimal("50.00")
    assert second.direction is TransactionDirection.DEBIT
    assert second.description == "Sample Payment"
