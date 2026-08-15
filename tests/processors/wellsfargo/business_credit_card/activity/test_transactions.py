"""
tests/processors/wellsfargo/business_credit_card/activity/test_transactions.py

Tests for Wells Fargo business credit-card transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.business_credit_card.activity.rows import (  # noqa: E501
    WellsFargoBusinessCreditCardActivityRow,
)
from banking_statements.processors.wellsfargo.business_credit_card.activity.transactions import (  # noqa: E501
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic business-card statement period."""
    return StatementPeriod(
        start=date(2024, 12, 28),
        end=date(2025, 1, 27),
    )


def test_parse_activity_transactions_uses_columns() -> None:
    transactions = parse_activity_transactions(
        (
            WellsFargoBusinessCreditCardActivityRow(
                transaction_date="12/28",
                post_date="12/29",
                reference_number="REF001",
                description="Sample Purchase",
                credit=None,
                charge=Decimal("100.00"),
            ),
            WellsFargoBusinessCreditCardActivityRow(
                transaction_date="1/2",
                post_date="1/2",
                reference_number="REF002",
                description="Sample Payment",
                credit=Decimal("50.00"),
                charge=None,
            ),
        ),
        period=make_period(),
    )

    assert transactions[0].direction is TransactionDirection.DEBIT
    assert transactions[0].date == date(2024, 12, 28)

    assert transactions[1].direction is TransactionDirection.CREDIT
    assert transactions[1].date == date(2025, 1, 2)


def test_parse_activity_transactions_rejects_both_columns() -> None:
    with pytest.raises(
        ValueError,
        match="contains both a credit and charge",
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCreditCardActivityRow(
                    transaction_date="1/2",
                    post_date="1/2",
                    reference_number="REF001",
                    description="Sample",
                    credit=Decimal("10.00"),
                    charge=Decimal("20.00"),
                ),
            ),
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_missing_amount() -> None:
    with pytest.raises(
        ValueError,
        match="contains no transaction amount",
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCreditCardActivityRow(
                    transaction_date="1/2",
                    post_date="1/2",
                    reference_number="REF001",
                    description="Sample",
                    credit=None,
                    charge=None,
                ),
            ),
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not be zero",
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCreditCardActivityRow(
                    transaction_date="1/2",
                    post_date="1/2",
                    reference_number="REF001",
                    description="Sample",
                    credit=None,
                    charge=Decimal("0.00"),
                ),
            ),
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Invalid Wells Fargo business credit-card transaction "
            "calendar date"
        ),
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCreditCardActivityRow(
                    transaction_date="02/30",
                    post_date="03/01",
                    reference_number="REF001",
                    description="Sample Transaction",
                    credit=None,
                    charge=Decimal("25.00"),
                ),
            ),
            period=StatementPeriod(
                start=date(2024, 2, 1),
                end=date(2024, 2, 29),
            ),
        )


def test_parse_activity_transactions_rejects_invalid_prior_year_date() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Invalid Wells Fargo business credit-card transaction "
            "calendar date"
        ),
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCreditCardActivityRow(
                    transaction_date="02/29",
                    post_date="03/01",
                    reference_number="REF001",
                    description="Sample Transaction",
                    credit=None,
                    charge=Decimal("25.00"),
                ),
            ),
            period=StatementPeriod(
                start=date(2023, 12, 15),
                end=date(2024, 1, 14),
            ),
        )
