"""
tests/processors/american_express/business_checking/test_processor.py

Tests for the American Express business-checking statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.american_express import (
    AmericanExpressBusinessCheckingProcessor,
)
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
    processor = AmericanExpressBusinessCheckingProcessor()

    assert processor.name == "american_express.business_checking.v1"


def test_processor_matches_supported_structure() -> None:
    processor = AmericanExpressBusinessCheckingProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "Business Checking Account Statement",
                "StatementPeriod",
                "AccountEnding *4625",
                "BeginningBalance $1,000.00)",
                "EndingBalance $1,150.00)",
                "Account Activity",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == (
        "Matched American Express business-checking statement structure."
    )


def test_processor_rejects_unsupported_structure() -> None:
    processor = AmericanExpressBusinessCheckingProcessor()

    match = processor.match(
        make_statement_text("Not an American Express business statement"),
    )

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == (
        "Required American Express business-checking markers were not found."
    )


def test_processor_parses_statement() -> None:
    processor = AmericanExpressBusinessCheckingProcessor()

    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "Business Checking Account Statement",
                "StatementPeriod",
                "04/01/2026 - 04/30/2026",
                "AccountEnding *4625",
                "AccountName General Operations",
                "Statement Summary as of 04/30/2026",
                "BeginningBalance $1,000.00)",
                "TotalDebitsThisPeriod $(50.00)",
                "TotalCreditsThisPeriod $200.00)",
                "EndingBalance $1,150.00)",
                "Account Activity",
                "Date Description Credits Debits Balance",
                "04/01/2026 BeginningBalance $1,000.00)",
                "04/05/2026 SAMPLE DEPOSIT $200.00 $1,200.00)",
                "04/10/2026 SAMPLE PAYMENT $50.00 $1,150.00)",
                "04/30/2026 EndingBalance $1,150.00)",
                "24/7 Account Access | World-Class Service",
            )
        )
    )

    statement = processor.parse(
        source,
        text,
    )

    assert statement.source is source
    assert statement.institution == "american_express"
    assert statement.processor == "american_express.business_checking.v1"

    assert statement.account.account_type.value == "checking"
    assert statement.account.display_number == "4625"
    assert statement.account.last4 == "4625"

    assert statement.period.start == date(2026, 4, 1)
    assert statement.period.end == date(2026, 4, 30)

    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("1150.00")

    assert len(statement.transactions) == 2

    deposit = statement.transactions[0]
    assert deposit.date == date(2026, 4, 5)
    assert deposit.amount == Decimal("200.00")
    assert deposit.direction is TransactionDirection.CREDIT
    assert deposit.description == "SAMPLE DEPOSIT"

    payment = statement.transactions[1]
    assert payment.date == date(2026, 4, 10)
    assert payment.amount == Decimal("50.00")
    assert payment.direction is TransactionDirection.DEBIT
    assert payment.description == "SAMPLE PAYMENT"
