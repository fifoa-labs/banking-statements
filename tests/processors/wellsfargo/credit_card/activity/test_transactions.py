"""
tests/processors/wellsfargo/credit_card/activity/test_transactions.py

Tests for Wells Fargo credit-card transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.credit_card.activity.rows import (  # noqa: E501
    WellsFargoCreditCardActivityRow,
)
from banking_statements.processors.wellsfargo.credit_card.activity.transactions import (  # noqa: E501
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a statement period spanning a year boundary."""
    return StatementPeriod(
        start=date(2023, 12, 15),
        end=date(2024, 1, 14),
    )


def test_parse_activity_transactions_uses_credit_and_charge_columns() -> None:
    transactions = parse_activity_transactions(
        (
            WellsFargoCreditCardActivityRow(
                card_last4="1234",
                transaction_date="12/20",
                post_date="12/21",
                reference_number="REF001",
                description="Sample Purchase",
                credit=None,
                charge=Decimal("50.00"),
            ),
            WellsFargoCreditCardActivityRow(
                card_last4="1234",
                transaction_date="1/5",
                post_date="1/6",
                reference_number="REF002",
                description="Sample Credit",
                credit=Decimal("25.00"),
                charge=None,
            ),
        ),
        period=make_period(),
    )

    assert len(transactions) == 2

    first, second = transactions

    assert first.date == date(2023, 12, 20)
    assert first.amount == Decimal("50.00")
    assert first.direction is TransactionDirection.DEBIT
    assert first.description == "Sample Purchase"

    assert second.date == date(2024, 1, 5)
    assert second.amount == Decimal("25.00")
    assert second.direction is TransactionDirection.CREDIT
    assert second.description == "Sample Credit"


def test_parse_activity_transactions_ignores_post_date_for_event_date() -> (
    None
):
    transactions = parse_activity_transactions(
        (
            WellsFargoCreditCardActivityRow(
                card_last4="1234",
                transaction_date="12/31",
                post_date="1/2",
                reference_number="REF001",
                description="Sample Purchase",
                credit=None,
                charge=Decimal("10.00"),
            ),
        ),
        period=make_period(),
    )

    assert transactions[0].date == date(2023, 12, 31)


def test_parse_activity_transactions_rejects_both_credit_and_charge() -> None:
    with pytest.raises(
        ValueError,
        match="contains both a credit and charge",
    ):
        parse_activity_transactions(
            (
                WellsFargoCreditCardActivityRow(
                    card_last4="1234",
                    transaction_date="12/20",
                    post_date="12/21",
                    reference_number="REF001",
                    description="Sample Transaction",
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
                WellsFargoCreditCardActivityRow(
                    card_last4="1234",
                    transaction_date="12/20",
                    post_date="12/21",
                    reference_number="REF001",
                    description="Sample Transaction",
                    credit=None,
                    charge=None,
                ),
            ),
            period=make_period(),
        )


@pytest.mark.parametrize(
    ("credit", "charge"),
    [
        (Decimal("0.00"), None),
        (None, Decimal("0.00")),
    ],
)
def test_parse_activity_transactions_rejects_zero_amount(
    credit: Decimal | None,
    charge: Decimal | None,
) -> None:
    with pytest.raises(
        ValueError,
        match="transaction amount must not be zero",
    ):
        parse_activity_transactions(
            (
                WellsFargoCreditCardActivityRow(
                    card_last4="1234",
                    transaction_date="12/20",
                    post_date="12/21",
                    reference_number="REF001",
                    description="Sample Transaction",
                    credit=credit,
                    charge=charge,
                ),
            ),
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Wells Fargo credit-card transaction calendar date",
    ):
        parse_activity_transactions(
            (
                WellsFargoCreditCardActivityRow(
                    card_last4="1234",
                    transaction_date="2/30",
                    post_date="3/1",
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


def test_parse_activity_transactions_allows_transaction_before_period_start() -> (  # noqa: E501
    None
):
    transactions = parse_activity_transactions(
        (
            WellsFargoCreditCardActivityRow(
                card_last4="1234",
                transaction_date="12/14",
                post_date="12/15",
                reference_number="REF001",
                description="Sample Purchase",
                credit=None,
                charge=Decimal("10.00"),
            ),
        ),
        period=StatementPeriod(
            start=date(2023, 12, 15),
            end=date(2024, 1, 14),
        ),
    )

    assert transactions[0].date == date(2023, 12, 14)


def test_parse_activity_transactions_rejects_invalid_prior_year_date() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Wells Fargo credit-card transaction calendar date",
    ):
        parse_activity_transactions(
            (
                WellsFargoCreditCardActivityRow(
                    card_last4="1234",
                    transaction_date="2/29",
                    post_date="3/1",
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
