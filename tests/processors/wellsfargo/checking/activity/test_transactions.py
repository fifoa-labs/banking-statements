"""
tests/processors/wellsfargo/checking/activity/test_transactions.py

Tests for Wells Fargo checking transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.checking.activity.rows import (
    WellsFargoCheckingActivityRow,
)
from banking_statements.processors.wellsfargo.checking.activity.transactions import (  # noqa: E501
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a statement period spanning a year boundary."""
    return StatementPeriod(
        start=date(2018, 12, 14),
        end=date(2019, 1, 14),
    )


def test_parse_activity_transactions_uses_statement_columns() -> None:
    transactions = parse_activity_transactions(
        (
            WellsFargoCheckingActivityRow(
                transaction_date="12/20",
                description="Sample Incoming Transaction",
                addition=Decimal("200.00"),
                subtraction=None,
                balance=Decimal("1200.00"),
            ),
            WellsFargoCheckingActivityRow(
                transaction_date="1/5",
                description="Sample Outgoing Transaction",
                addition=None,
                subtraction=Decimal("50.00"),
                balance=Decimal("1150.00"),
            ),
        ),
        period=make_period(),
    )

    assert len(transactions) == 2

    first, second = transactions

    assert first.date == date(2018, 12, 20)
    assert first.amount == Decimal("200.00")
    assert first.direction is TransactionDirection.CREDIT
    assert first.description == "Sample Incoming Transaction"

    assert second.date == date(2019, 1, 5)
    assert second.amount == Decimal("50.00")
    assert second.direction is TransactionDirection.DEBIT
    assert second.description == "Sample Outgoing Transaction"


def test_parse_activity_transactions_does_not_require_running_balance() -> (
    None
):
    transactions = parse_activity_transactions(
        (
            WellsFargoCheckingActivityRow(
                transaction_date="12/20",
                description="Sample Transaction",
                addition=Decimal("200.00"),
                subtraction=None,
                balance=None,
            ),
        ),
        period=make_period(),
    )

    assert transactions[0].amount == Decimal("200.00")
    assert transactions[0].direction is TransactionDirection.CREDIT


def test_parse_activity_transactions_rejects_both_transaction_columns() -> (
    None
):
    with pytest.raises(
        ValueError,
        match="contains both an addition and subtraction",
    ):
        parse_activity_transactions(
            (
                WellsFargoCheckingActivityRow(
                    transaction_date="12/20",
                    description="Sample Transaction",
                    addition=Decimal("100.00"),
                    subtraction=Decimal("25.00"),
                    balance=None,
                ),
            ),
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_missing_transaction_amount() -> (
    None
):
    with pytest.raises(
        ValueError,
        match="contains no transaction amount",
    ):
        parse_activity_transactions(
            (
                WellsFargoCheckingActivityRow(
                    transaction_date="12/20",
                    description="Sample Transaction",
                    addition=None,
                    subtraction=None,
                    balance=Decimal("1000.00"),
                ),
            ),
            period=make_period(),
        )


@pytest.mark.parametrize(
    ("addition", "subtraction"),
    [
        (Decimal("0.00"), None),
        (None, Decimal("0.00")),
    ],
)
def test_parse_activity_transactions_rejects_zero_amount(
    addition: Decimal | None,
    subtraction: Decimal | None,
) -> None:
    with pytest.raises(
        ValueError,
        match="transaction amount must not be zero",
    ):
        parse_activity_transactions(
            (
                WellsFargoCheckingActivityRow(
                    transaction_date="12/20",
                    description="Sample Transaction",
                    addition=addition,
                    subtraction=subtraction,
                    balance=None,
                ),
            ),
            period=make_period(),
        )


def test_parse_activity_transactions_rejects_unresolvable_date() -> None:
    with pytest.raises(
        ValueError,
        match="transaction date could not be resolved uniquely",
    ):
        parse_activity_transactions(
            (
                WellsFargoCheckingActivityRow(
                    transaction_date="2/30",
                    description="Sample Transaction",
                    addition=Decimal("25.00"),
                    subtraction=None,
                    balance=None,
                ),
            ),
            period=StatementPeriod(
                start=date(2019, 2, 1),
                end=date(2019, 2, 28),
            ),
        )
