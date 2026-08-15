"""
tests/processors/wellsfargo/checking/test_processor.py

Tests for the Wells Fargo checking statement processor.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.checking import (
    WellsFargoCheckingProcessor,
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
        path=Path("sample-wells-fargo-checking.pdf"),
        sha256="a" * 64,
    )


def test_processor_name() -> None:
    processor = WellsFargoCheckingProcessor()

    assert processor.name == "wellsfargo.checking.v1"


def test_processor_matches_supported_statement() -> None:
    processor = WellsFargoCheckingProcessor()

    result = processor.match(
        make_statement_text(
            "Wells Fargo College Checking\n"
            "Transaction history\n"
            "Withdrawals/Subtractions\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == "Matched Wells Fargo checking statement structure."


def test_processor_rejects_unsupported_statement() -> None:
    processor = WellsFargoCheckingProcessor()

    result = processor.match(
        make_statement_text(
            "Some other bank statement\n",
        )
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Wells Fargo checking markers were not found."
    )


def test_processor_parses_statement() -> None:
    processor = WellsFargoCheckingProcessor()

    statement = processor.parse(
        make_source(),
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Wells Fargo College Checking",
                    "Activity summary Account number: 1234567890",
                    "Beginning balance on 12/14 $1,000.00",
                    "Deposits/Additions 200.00",
                    "Withdrawals/Subtractions - 50.00",
                    "Ending balance on 1/14 $1,150.00",
                    "Transaction history",
                    "Check Deposits/ Withdrawals/ Ending daily",
                    "Date Number Description Additions Subtractions balance",
                    "12/20 Transfer From Sample Payroll 200.00 1,200.00",
                    "1/5 Bill Pay Sample Utility 50.00 1,150.00",
                    "Ending balance on 1/14 1,150.00",
                    "Totals $200.00 $50.00",
                    "Monthly service fee summary",
                    "Fee period 12/14/2018 - 01/14/2019",
                )
            ),
            words=(
                make_word("Wells", x0=40.0, top=10.0),
                make_word("Fargo", x0=70.0, top=10.0),
                make_word("College", x0=105.0, top=10.0),
                make_word("Checking", x0=150.0, top=10.0),
                make_word("Transaction", x0=40.0, top=20.0),
                make_word("history", x0=100.0, top=20.0),
                make_word("Date", x0=40.0, top=30.0),
                make_word("Description", x0=100.0, top=30.0),
                make_word("Additions", x0=407.0, top=30.0),
                make_word("Subtractions", x0=466.0, top=30.0),
                make_word("balance", x0=545.0, top=30.0),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Transfer", x0=100.0, top=40.0),
                make_word("From", x0=145.0, top=40.0),
                make_word("Sample", x0=175.0, top=40.0),
                make_word("Payroll", x0=220.0, top=40.0),
                make_word("200.00", x0=419.0, top=40.0),
                make_word("1,200.00", x0=543.0, top=40.0),
                make_word("1/5", x0=40.0, top=50.0),
                make_word("Bill", x0=100.0, top=50.0),
                make_word("Pay", x0=130.0, top=50.0),
                make_word("Sample", x0=160.0, top=50.0),
                make_word("Utility", x0=205.0, top=50.0),
                make_word("50.00", x0=488.0, top=50.0),
                make_word("1,150.00", x0=543.0, top=50.0),
            ),
        ),
    )

    assert statement.institution == "wellsfargo"
    assert statement.processor == "wellsfargo.checking.v1"

    assert statement.account.account_type is AccountType.CHECKING
    assert statement.account.display_number == "1234567890"
    assert statement.account.last4 == "7890"

    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("1150.00")

    assert len(statement.transactions) == 2

    first, second = statement.transactions

    assert first.amount == Decimal("200.00")
    assert first.direction is TransactionDirection.CREDIT
    assert first.description == "Transfer From Sample Payroll"

    assert second.amount == Decimal("50.00")
    assert second.direction is TransactionDirection.DEBIT
    assert second.description == "Bill Pay Sample Utility"
