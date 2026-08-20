"""
tests/processors/capital_one/business_credit_card/test_processor.py

Tests for the Capital One business credit-card statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.capital_one import (
    CapitalOneBusinessCreditCardProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-capital-one-business-card.pdf"),
        sha256="a" * 64,
    )


def test_processor_name_is_stable() -> None:
    assert (
        CapitalOneBusinessCreditCardProcessor().name
        == "capital_one.business_credit_card.v1"
    )


@pytest.mark.parametrize(
    "value",
    [
        (
            "Spark® Visa Signature Business Account Ending in 1234\n"
            "31 days in Billing Cycle\n"
            "Account Summary\n"
            "Date Description Amount\n"
            "Fees\n"
            "Capital One\n"
        ),
        (
            "Spark Cash credit card | Visa Signature Business ending in 1234\n"
            "31 days in Billing Cycle\n"
            "Account Summary\n"
            "Trans Date Post Date Description Amount\n"
            "Fees\n"
            "Capital One\n"
        ),
        (
            "Venture X Business card | Visa Infinite Business ending in 1234\n"
            "31 days in Billing Cycle\n"
            "Account Summary\n"
            "Trans Date Post Date Description Amount\n"
            "Fees\n"
            "Capital One\n"
        ),
    ],
)
def test_processor_matches_supported_business_layouts(value: str) -> None:
    result = CapitalOneBusinessCreditCardProcessor().match(make_text(value))

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched Capital One business credit-card statement structure."
    )


def test_processor_rejects_consumer_venture_x_statement() -> None:
    result = CapitalOneBusinessCreditCardProcessor().match(
        make_text(
            "Venture X Card | Visa Infinite ending in 1234\n"
            "Account Summary\n"
            "Trans Date Post Date Description Amount\n"
            "Capital One\n"
        )
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required Capital One business credit-card markers were not found."
    )


def test_processor_parses_and_reconciles_current_spark() -> None:
    statement = CapitalOneBusinessCreditCardProcessor().parse(
        make_source(),
        make_text(
            "Spark Cash credit card | Visa Signature Business ending in 1234\n"
            "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            "Payment Information Account Summary\n"
            "Previous Balance $100.00\n"
            "New Balance = $132.00\n"
            "Transactions\n"
            "SAMPLE PERSON #1234: Payments, Credits and Adjustments\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 10 Mar 11 SAMPLE PAYMENT - $25.00\n"
            "SAMPLE PERSON #1234: Transactions\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 20 Mar 21 SAMPLE MARKET $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 25 Mar 25 SAMPLE FEE $3.00\n"
            "Total Fees for This Period $3.00\n"
            "Interest Charged\n"
            "Total Interest for This Period $4.00\n"
        ),
    )

    assert statement.institution == "capital_one"
    assert statement.processor == "capital_one.business_credit_card.v1"
    assert statement.account.account_type is AccountType.CREDIT_CARD
    assert statement.account.display_number == "1234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 3, 1)
    assert statement.period.end == date(2026, 3, 31)
    assert statement.balances.opening_balance == Decimal("100.00")
    assert statement.balances.closing_balance == Decimal("132.00")

    assert len(statement.transactions) == 4
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[0].date == date(2026, 3, 11)
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert statement.transactions[2].description == "SAMPLE FEE"
    assert statement.transactions[3].description == "INTEREST CHARGED"

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")


def test_processor_parses_and_reconciles_legacy_spark() -> None:
    statement = CapitalOneBusinessCreditCardProcessor().parse(
        make_source(),
        make_text(
            "Spark® Visa Signature Business Account Ending in 5678\n"
            "Dec. 18, 2025 - Jan. 17, 2026 | 31 days in Billing Cycle\n"
            "Account Summary\n"
            "Previous Balance $100.00\n"
            "New Balance = $125.00\n"
            "Transactions Transactions Continued\n"
            "Date Description Amount\n"
            "Dec 20 SAMPLE PAYMENT - $25.00 Jan 5 SAMPLE PURCHASE $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Date Description Amount\n"
            "Total Fees for This Period $0.00\n"
            "Interest Charged\n"
            "Total Interest for This Period $0.00\n"
        ),
    )

    assert statement.account.last4 == "5678"
    assert len(statement.transactions) == 2
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[1].direction is TransactionDirection.DEBIT

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True


def test_processor_parses_and_reconciles_venture_x_business() -> None:
    statement = CapitalOneBusinessCreditCardProcessor().parse(
        make_source(),
        make_text(
            "Venture X Business card | Visa Infinite Business ending in 9012\n"
            "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            "Account Summary\n"
            "Previous Balance $0.00\n"
            "New Balance = $145.00\n"
            "Transactions\n"
            "SAMPLE PERSON #9012: Transactions\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 20 Mar 21 SAMPLE PURCHASE $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 25 Mar 25 SAMPLE MEMBER FEE $95.00\n"
            "Total Fees for This Period $95.00\n"
        ),
    )

    assert statement.account.last4 == "9012"
    assert len(statement.transactions) == 2

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")
