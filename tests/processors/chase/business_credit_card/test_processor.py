"""
tests/processors/chase/business_credit_card/test_processor.py

Tests for the Chase business credit-card statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import StatementSource, TransactionDirection
from banking_statements.processors.chase import (
    ChaseBusinessCreditCardProcessor,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for processor tests."""
    return StatementText(pages=(StatementPage(number=1, text=text),))


def test_processor_name_is_stable() -> None:
    assert ChaseBusinessCreditCardProcessor().name == (
        "chase.business_credit_card.v1"
    )


def test_processor_matches_historical_ink_structure() -> None:
    match = ChaseBusinessCreditCardProcessor().match(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Credit Card Statement",
                    "www.chase.com/ink",
                    "Revolving Credit Amount $10,000",
                    "Opening/Closing Date 12/08/18 - 01/07/19",
                )
            )
        )
    )

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == (
        "Matched Chase business credit-card statement structure."
    )


def test_processor_matches_current_business_structure() -> None:
    match = ChaseBusinessCreditCardProcessor().match(
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

    assert match.matched is True
    assert match.confidence == 100


def test_processor_rejects_consumer_credit_card_structure() -> None:
    match = ChaseBusinessCreditCardProcessor().match(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "www.chase.com/cardhelp",
                    "Opening/Closing Date 05/20/26 - 06/19/26",
                )
            )
        )
    )

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == (
        "Required Chase business credit-card markers were not found."
    )


def test_processor_parses_signed_business_activity() -> None:
    processor = ChaseBusinessCreditCardProcessor()
    source = StatementSource(path=Path("sample.pdf"), sha256="0" * 64)
    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "Account Number: XXXX XXXX XXXX 1234",
                "Previous Balance $100.00",
                "Payment, Credits -$75.00",
                "Purchases +$25.00",
                "Fees Charged +$5.00",
                "Interest Charged $0.00",
                "New Balance $55.00",
                "Opening/Closing Date 06/01/26 - 06/30/26",
                "Revolving Credit Amount $15,000",
                "Statement Date: 06/30/26",
                "ACCOUNT ACTIVITY",
                "Date of",
                "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                "06/10 SAMPLE PAYMENT -75.00",
                "06/15 SAMPLE PURCHASE 25.00",
                "06/20 SAMPLE FEE 5.00",
                "2026 Totals Year-to-Date",
            )
        )
    )

    statement = processor.parse(source, text)

    assert statement.source is source
    assert statement.institution == "chase"
    assert statement.processor == processor.name
    assert statement.account.account_type.value == "credit_card"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 6, 1)
    assert statement.period.end == date(2026, 6, 30)
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("55.00")
    assert [
        transaction.direction for transaction in statement.transactions
    ] == [
        TransactionDirection.CREDIT,
        TransactionDirection.DEBIT,
        TransactionDirection.DEBIT,
    ]
    assert [transaction.amount for transaction in statement.transactions] == [
        Decimal("75.00"),
        Decimal("25.00"),
        Decimal("5.00"),
    ]


def test_processor_parses_zero_activity_business_statement() -> None:
    processor = ChaseBusinessCreditCardProcessor()
    source = StatementSource(path=Path("sample.pdf"), sha256="0" * 64)
    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "Account Number: XXXX XXXX XXXX 4321",
                "Previous Balance -$15.00",
                "New Balance -$15.00",
                "Opening/Closing Date 06/01/26 - 06/30/26",
                "Revolving Credit Amount $15,000",
                "Statement Date: 06/30/26",
            )
        )
    )

    statement = processor.parse(source, text)

    assert statement.transactions == ()
    assert statement.balances.opening_balance == Decimal("-15.00")
    assert statement.balances.closing_balance == Decimal("-15.00")
