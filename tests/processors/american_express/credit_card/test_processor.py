"""
tests/processors/american_express/credit_card/test_processor.py

Tests for the American Express credit-card statement processor.
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
from banking_statements.processors.american_express import (
    AmericanExpressCreditCardProcessor,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-american-express.pdf"),
        sha256="a" * 64,
    )


def test_processor_name_is_stable() -> None:
    assert (
        AmericanExpressCreditCardProcessor().name
        == "american_express.credit_card.v1"
    )


def test_processor_matches_billing_statement() -> None:
    result = AmericanExpressCreditCardProcessor().match(
        make_text(
            "American Express\n"
            "Closing Date04/15/26 Account Ending7-65432\n"
            "Previous Balance $0.00\n"
            "New Charges +$12.50\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched American Express credit-card statement structure."
    )


def test_processor_rejects_notice_document() -> None:
    result = AmericanExpressCreditCardProcessor().match(
        make_text(
            "American Express Customer Care\n"
            "Closing Date04/15/26 Account Ending7-65432\n"
            "Notice of Important Changes to Your Card Member Agreement\n"
        )
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required American Express credit-card markers were not found."
    )


def test_processor_parses_statement_and_card_context() -> None:
    statement = AmericanExpressCreditCardProcessor().parse(
        make_source(),
        make_text(
            "American Express\n"
            "Closing Date04/15/26 Account Ending7-65432\n"
            "Days in Billing Period: 30\n"
            "Account Summary\n"
            "Previous Balance $100.00\n"
            "Payments/Credits -$25.00\n"
            "New Charges +$40.00\n"
            "Fees +$0.00\n"
            "Interest Charged +$0.00\n"
            "New Balance $115.00\n"
            "Payments and Credits\n"
            "Payments Amount\n"
            "03/18/26 SAMPLE PAYMENT -$25.00\n"
            "New Charges\n"
            "Detail\n"
            "Card Ending7-65432\n"
            "03/20/26 SAMPLE PURCHASE $40.00\n"
            "Fees\n"
            "Total Fees for this Period $0.00\n"
            "Interest Charged\n"
            "Total Interest Charged for this Period $0.00\n"
        ),
    )

    assert statement.institution == "american_express"
    assert statement.processor == "american_express.credit_card.v1"
    assert statement.account.account_type is AccountType.CREDIT_CARD
    assert statement.account.display_number == "7-65432"
    assert statement.account.last4 == "5432"
    assert statement.period.start == date(2026, 3, 17)
    assert statement.period.end == date(2026, 4, 15)
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("115.00")

    assert len(statement.transactions) == 2
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[0].amount == Decimal("25.00")
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert statement.transactions[1].amount == Decimal("40.00")
    assert statement.transactions[1].evidence is not None
    assert statement.transactions[1].evidence.section == "Card Ending 7-65432"
