"""
tests/processors/chase/credit_card/test_processor.py

Tests for the Chase credit-card statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.chase import ChaseCreditCardProcessor
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
    processor = ChaseCreditCardProcessor()

    assert processor.name == "chase.credit_card.v1"


def test_processor_matches_supported_structure() -> None:
    processor = ChaseCreditCardProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "Opening/Closing Date 02/01/26 - 02/28/26",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == "Matched Chase credit-card statement structure."


def test_processor_matches_historical_structure() -> None:
    processor = ChaseCreditCardProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "Credit Card Statement",
                "www.chase.com",
                "Opening/Closing Date 11/15/18 - 12/14/18",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == "Matched Chase credit-card statement structure."


def test_processor_rejects_business_credit_card_structure() -> None:
    processor = ChaseCreditCardProcessor()

    match = processor.match(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "www.chase.com/cardhelp",
                    "Revolving Credit Amount $15,000",
                    "Opening/Closing Date 05/20/26 - 06/19/26",
                )
            )
        )
    )

    assert match.matched is False
    assert match.confidence == 0


def test_processor_rejects_unsupported_structure() -> None:
    processor = ChaseCreditCardProcessor()

    match = processor.match(
        make_statement_text("Not a Chase credit-card statement"),
    )

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == (
        "Required Chase credit-card markers were not found."
    )


def test_processor_parses_statement_identity() -> None:
    processor = ChaseCreditCardProcessor()

    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "Account Number: XXXX XXXX XXXX 1234",
                "Previous Balance $0.00",
                "New Balance $0.00",
                "Opening/Closing Date 03/10/26 - 04/09/26",
                "Date of",
                "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                "Statement Date: 04/09/26",
            )
        )
    )

    statement = processor.parse(
        source,
        text,
    )

    assert statement.source is source
    assert statement.institution == "chase"
    assert statement.processor == "chase.credit_card.v1"
    assert statement.account.account_type.value == "credit_card"
    assert statement.account.display_number == "XXXX XXXX XXXX 1234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 3, 10)
    assert statement.period.end == date(2026, 4, 9)
    assert statement.balances.opening_balance == Decimal("0.00")
    assert statement.balances.closing_balance == Decimal("0.00")
    assert statement.transactions == ()


def test_processor_parses_statement_identity_and_transactions() -> None:
    processor = ChaseCreditCardProcessor()

    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "Account Number: XXXX XXXX XXXX 1234",
                "Previous Balance $0.00",
                "New Balance $18.45",
                "Opening/Closing Date 03/10/26 - 04/09/26",
                "Date of",
                "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                "Statement Date: 04/09/26",
                "PURCHASE",
                "03/30 SAMPLE MERCHANT 18.45",
                "2026 Totals Year-to-Date",
            )
        )
    )

    statement = processor.parse(
        source,
        text,
    )

    assert statement.source is source
    assert statement.institution == "chase"
    assert statement.processor == "chase.credit_card.v1"
    assert statement.account.account_type.value == "credit_card"
    assert statement.account.display_number == "XXXX XXXX XXXX 1234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 3, 10)
    assert statement.period.end == date(2026, 4, 9)
    assert statement.balances.opening_balance == Decimal("0.00")
    assert statement.balances.closing_balance == Decimal("18.45")

    assert len(statement.transactions) == 1

    transaction = statement.transactions[0]

    assert transaction.date == date(2026, 3, 30)
    assert transaction.amount == Decimal("18.45")
    assert transaction.direction is TransactionDirection.DEBIT
    assert transaction.description == "SAMPLE MERCHANT"


def test_processor_matches_when_account_number_text_is_mangled() -> None:
    processor = ChaseCreditCardProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                (
                    "A A A c CC cou CC nt OO Nu UU m NN ber TT : "
                    "1111 2222 3333 4444"
                ),
                "Opening/Closing Date 08/05/22 - 09/04/22",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100


def test_processor_matches_mangled_opening_closing_marker() -> None:
    processor = ChaseCreditCardProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "O`pening/Closing Date 12/08/20 - 01/07/21",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
