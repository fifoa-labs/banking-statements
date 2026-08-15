"""
tests/processors/wellsfargo/credit_card/test_processor.py

Tests for the Wells Fargo credit-card statement processor.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.credit_card import (
    WellsFargoCreditCardProcessor,
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
        path=Path("sample-wells-fargo-credit-card.pdf"),
        sha256="a" * 64,
    )


def test_processor_name() -> None:
    processor = WellsFargoCreditCardProcessor()

    assert processor.name == "wellsfargo.credit_card.v1"


def test_processor_matches_supported_statement() -> None:
    processor = WellsFargoCreditCardProcessor()

    result = processor.match(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "WELLS FARGO SAMPLE VISA CARD",
                    "Account ending in 1234",
                    "Statement Period 12/15/2023 to 01/14/2024",
                    "Account Summary",
                    "Transactions",
                )
            )
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Wells Fargo credit-card statement structure."
    )


def test_processor_rejects_unsupported_statement() -> None:
    processor = WellsFargoCreditCardProcessor()

    result = processor.match(
        make_statement_text(
            "Some other card statement",
        )
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Wells Fargo credit-card markers were not found."
    )


def test_processor_parses_statement() -> None:
    processor = WellsFargoCreditCardProcessor()

    statement = processor.parse(
        make_source(),
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "WELLS FARGO SAMPLE VISA CARD",
                    "Account ending in 1234",
                    "Statement Period 12/15/2023 to 01/14/2024",
                    "Account Summary",
                    "Previous Balance $100.00",
                    "- Payments $25.00",
                    "- Other Credits $0.00",
                    "+ Purchases, Balance Transfers & $50.00",
                    "Other Charges",
                    "+ Fees Charged $0.00",
                    "+ Interest Charged $0.00",
                    "= New Balance $125.00",
                    "Transactions",
                    "Card Trans Post Reference Number Description Credits Charges",  # noqa: E501
                    "Ending Date Date",
                    "in",
                    "1234 12/20 12/21 REF001 Sample Purchase 50.00",
                    "1234 12/22 12/23 REF002 Sample Payment 25.00",
                )
            ),
            words=(
                make_word("Transactions", x0=40.0, top=20.0),
                make_word("Card", x0=40.0, top=30.0),
                make_word("Trans", x0=80.0, top=30.0),
                make_word("Post", x0=120.0, top=30.0),
                make_word("Reference", x0=160.0, top=30.0),
                make_word("Number", x0=220.0, top=30.0),
                make_word("Description", x0=280.0, top=30.0),
                make_word("Credits", x0=470.0, top=30.0),
                make_word("Charges", x0=535.0, top=30.0),
                make_word("1234", x0=40.0, top=40.0),
                make_word("12/20", x0=80.0, top=40.0),
                make_word("12/21", x0=120.0, top=40.0),
                make_word("REF001", x0=160.0, top=40.0),
                make_word("Sample", x0=280.0, top=40.0),
                make_word("Purchase", x0=330.0, top=40.0),
                make_word("50.00", x0=540.0, top=40.0),
                make_word("1234", x0=40.0, top=50.0),
                make_word("12/22", x0=80.0, top=50.0),
                make_word("12/23", x0=120.0, top=50.0),
                make_word("REF002", x0=160.0, top=50.0),
                make_word("Sample", x0=280.0, top=50.0),
                make_word("Payment", x0=330.0, top=50.0),
                make_word("25.00", x0=475.0, top=50.0),
            ),
        ),
    )

    assert statement.institution == "wellsfargo"
    assert statement.processor == "wellsfargo.credit_card.v1"

    assert statement.account.account_type is AccountType.CREDIT_CARD
    assert statement.account.display_number == "1234"
    assert statement.account.last4 == "1234"

    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("125.00")

    assert len(statement.transactions) == 2

    first, second = statement.transactions

    assert first.amount == Decimal("50.00")
    assert first.direction is TransactionDirection.DEBIT
    assert first.description == "Sample Purchase"

    assert second.amount == Decimal("25.00")
    assert second.direction is TransactionDirection.CREDIT
    assert second.description == "Sample Payment"
