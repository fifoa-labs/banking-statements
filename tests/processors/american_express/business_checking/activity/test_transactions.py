"""
tests/processors/american_express/business_checking/activity/test_transactions.py

Tests for American Express business-checking transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.american_express.business_checking.activity import (  # noqa: E501
    AmericanExpressBusinessCheckingActivityRow,
    AmericanExpressBusinessCheckingActivitySection,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic American Express business-checking period."""
    return StatementPeriod(
        start=date(2026, 4, 1),
        end=date(2026, 4, 30),
    )


def test_parse_activity_transactions_normalizes_credit_and_debit() -> None:
    transactions = parse_activity_transactions(
        (
            AmericanExpressBusinessCheckingActivityRow(
                transaction_date="04/05/2026",
                description="SAMPLE DEPOSIT",
                amount=Decimal("200.00"),
                balance=Decimal("1200.00"),
                section=AmericanExpressBusinessCheckingActivitySection.CREDIT,
            ),
            AmericanExpressBusinessCheckingActivityRow(
                transaction_date="04/10/2026",
                description="SAMPLE PAYMENT",
                amount=Decimal("50.00"),
                balance=Decimal("1150.00"),
                section=AmericanExpressBusinessCheckingActivitySection.DEBIT,
            ),
        ),
        period=make_period(),
    )

    assert len(transactions) == 2

    deposit = transactions[0]
    assert deposit.date == date(2026, 4, 5)
    assert deposit.amount == Decimal("200.00")
    assert deposit.direction is TransactionDirection.CREDIT
    assert deposit.description == "SAMPLE DEPOSIT"

    payment = transactions[1]
    assert payment.date == date(2026, 4, 10)
    assert payment.amount == Decimal("50.00")
    assert payment.direction is TransactionDirection.DEBIT
    assert payment.description == "SAMPLE PAYMENT"


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    rows = (
        AmericanExpressBusinessCheckingActivityRow(
            transaction_date="04/05/2026",
            description="ZERO TRANSACTION",
            amount=Decimal("0.00"),
            balance=Decimal("1000.00"),
            section=AmericanExpressBusinessCheckingActivitySection.CREDIT,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking transaction amount must "  # noqa: RUF043
            "not be zero."
        ),
    ):
        parse_activity_transactions(
            rows,
            period=make_period(),
        )


def test_parse_activity_transactions_accepts_previous_day_activity() -> None:
    transactions = parse_activity_transactions(
        (
            AmericanExpressBusinessCheckingActivityRow(
                transaction_date="03/31/2026",
                description="INTEREST DEPOSIT",
                amount=Decimal("3.31"),
                balance=Decimal("3.31"),
                section=(
                    AmericanExpressBusinessCheckingActivitySection.CREDIT
                ),
            ),
        ),
        period=make_period(),
    )

    assert len(transactions) == 1
    assert transactions[0].date == date(2026, 3, 31)
    assert transactions[0].amount == Decimal("3.31")
    assert transactions[0].direction is TransactionDirection.CREDIT


def test_parse_activity_transactions_rejects_date_before_supported_boundary() -> (  # noqa: E501
    None
):
    rows = (
        AmericanExpressBusinessCheckingActivityRow(
            transaction_date="03/30/2026",
            description="OUTSIDE PERIOD",
            amount=Decimal("10.00"),
            balance=Decimal("1010.00"),
            section=AmericanExpressBusinessCheckingActivitySection.CREDIT,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking transaction date is "
            "outside the supported statement boundary"
        ),
    ):
        parse_activity_transactions(
            rows,
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_date_after_period() -> None:
    rows = (
        AmericanExpressBusinessCheckingActivityRow(
            transaction_date="05/01/2026",
            description="OUTSIDE PERIOD",
            amount=Decimal("10.00"),
            balance=Decimal("1010.00"),
            section=AmericanExpressBusinessCheckingActivitySection.CREDIT,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking transaction date is "
            "outside the supported statement boundary"
        ),
    ):
        parse_activity_transactions(
            rows,
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    rows = (
        AmericanExpressBusinessCheckingActivityRow(
            transaction_date="04/31/2026",
            description="INVALID DATE",
            amount=Decimal("10.00"),
            balance=Decimal("1010.00"),
            section=AmericanExpressBusinessCheckingActivitySection.CREDIT,
        ),
    )

    with pytest.raises(ValueError):  # noqa: PT011
        parse_activity_transactions(
            rows,
            period=make_period(),
        )


def test_parse_activity_transactions_returns_empty_for_no_rows() -> None:
    assert (
        parse_activity_transactions(
            (),
            period=make_period(),
        )
        == ()
    )
