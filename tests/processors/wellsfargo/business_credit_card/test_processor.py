"""
tests/processors/wellsfargo/business_credit_card/test_processor.py

Tests for the Wells Fargo business credit-card processor.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.business_credit_card import (
    WellsFargoBusinessCreditCardProcessor,
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


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-business-card.pdf"),
        sha256="a" * 64,
    )


def test_processor_name() -> None:
    assert (
        WellsFargoBusinessCreditCardProcessor().name
        == "wellsfargo.business_credit_card.v1"
    )


def test_processor_parses_statement() -> None:
    processor = WellsFargoBusinessCreditCardProcessor()

    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="\n".join(  # noqa: FLY002
                    (
                        "SAMPLE BUSINESS CARD",
                        "CONSOLIDATED BILLING CONTROL ACCOUNT STATEMENT",
                        "Account Number 1111 2222 3333 1234",
                        "Statement Closing Date 01/27/25",
                        "Days in Billing Cycle 31",
                        "Account Summary",
                        "Previous Balance $100.00",
                        "New Balance = $125.00",
                        "Transaction Details",
                    )
                ),
                words=(
                    make_word("Transaction", x0=40.0, top=20.0),
                    make_word("Details", x0=100.0, top=20.0),
                    make_word("Trans", x0=40.0, top=30.0),
                    make_word("Post", x0=80.0, top=30.0),
                    make_word("Reference", x0=120.0, top=30.0),
                    make_word("Number", x0=180.0, top=30.0),
                    make_word("Description", x0=240.0, top=30.0),
                    make_word("Credits", x0=470.0, top=30.0),
                    make_word("Charges", x0=535.0, top=30.0),
                    make_word("12/28", x0=40.0, top=40.0),
                    make_word("12/29", x0=80.0, top=40.0),
                    make_word("REF001", x0=120.0, top=40.0),
                    make_word("Sample", x0=240.0, top=40.0),
                    make_word("Purchase", x0=290.0, top=40.0),
                    make_word("25.00", x0=540.0, top=40.0),
                ),
            ),
        )
    )

    statement = processor.parse(
        make_source(),
        text,
    )

    assert statement.account.account_type is AccountType.CREDIT_CARD
    assert statement.account.last4 == "1234"
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("125.00")
    assert len(statement.transactions) == 1
    assert statement.transactions[0].amount == Decimal("25.00")
    assert statement.transactions[0].direction is TransactionDirection.DEBIT


def make_statement_text(text: str) -> StatementText:
    """Build synthetic text for processor matching."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_processor_matches_supported_statement() -> None:
    processor = WellsFargoBusinessCreditCardProcessor()

    result = processor.match(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "SAMPLE BUSINESS CARD",
                    "CONSOLIDATED BILLING CONTROL ACCOUNT STATEMENT",
                    "Statement Closing Date 01/27/25",
                    "Days in Billing Cycle 31",
                    "Account Summary",
                )
            )
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Wells Fargo business credit-card statement structure."
    )


def test_processor_rejects_unsupported_statement() -> None:
    processor = WellsFargoBusinessCreditCardProcessor()

    result = processor.match(
        make_statement_text(
            "Some other card statement",
        )
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Wells Fargo business credit-card markers were not found."
    )
