"""
tests/processors/wellsfargo/business_checking/activity/test_transactions.py

Tests for Wells Fargo business checking transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.business_checking.activity.rows import (  # noqa: E501
    WellsFargoBusinessCheckingActivityRow,
)
from banking_statements.processors.wellsfargo.business_checking.activity.transactions import (  # noqa: E501
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a statement period spanning a year boundary."""
    return StatementPeriod(
        start=date(2023, 12, 15),
        end=date(2024, 1, 14),
    )


def test_parse_activity_transactions_uses_credit_and_debit_columns() -> None:
    transactions = parse_activity_transactions(
        (
            WellsFargoBusinessCheckingActivityRow(
                transaction_date="12/20",
                description="Sample Deposit",
                credit=Decimal("200.00"),
                debit=None,
                balance=Decimal("1200.00"),
            ),
            WellsFargoBusinessCheckingActivityRow(
                transaction_date="1/5",
                description="Sample Payment",
                credit=None,
                debit=Decimal("50.00"),
                balance=Decimal("1150.00"),
            ),
        ),
        period=make_period(),
    )

    assert len(transactions) == 2

    first, second = transactions

    assert first.date == date(2023, 12, 20)
    assert first.amount == Decimal("200.00")
    assert first.direction is TransactionDirection.CREDIT
    assert first.description == "Sample Deposit"

    assert second.date == date(2024, 1, 5)
    assert second.amount == Decimal("50.00")
    assert second.direction is TransactionDirection.DEBIT
    assert second.description == "Sample Payment"


def test_parse_activity_transactions_does_not_require_running_balance() -> (
    None
):
    transactions = parse_activity_transactions(
        (
            WellsFargoBusinessCheckingActivityRow(
                transaction_date="12/20",
                description="Sample Deposit",
                credit=Decimal("200.00"),
                debit=None,
                balance=None,
            ),
        ),
        period=make_period(),
    )

    assert transactions[0].amount == Decimal("200.00")
    assert transactions[0].direction is TransactionDirection.CREDIT


def test_parse_activity_transactions_rejects_both_credit_and_debit() -> None:
    with pytest.raises(
        ValueError,
        match="contains both credit and debit",
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCheckingActivityRow(
                    transaction_date="12/20",
                    description="Sample Transaction",
                    credit=Decimal("100.00"),
                    debit=Decimal("25.00"),
                    balance=None,
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
                WellsFargoBusinessCheckingActivityRow(
                    transaction_date="12/20",
                    description="Sample Transaction",
                    credit=None,
                    debit=None,
                    balance=Decimal("1000.00"),
                ),
            ),
            period=make_period(),
        )


@pytest.mark.parametrize(
    ("credit", "debit"),
    [
        (Decimal("0.00"), None),
        (None, Decimal("0.00")),
    ],
)
def test_parse_activity_transactions_rejects_zero_amount(
    credit: Decimal | None,
    debit: Decimal | None,
) -> None:
    with pytest.raises(
        ValueError,
        match="transaction amount must not be zero",
    ):
        parse_activity_transactions(
            (
                WellsFargoBusinessCheckingActivityRow(
                    transaction_date="12/20",
                    description="Sample Transaction",
                    credit=credit,
                    debit=debit,
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
                WellsFargoBusinessCheckingActivityRow(
                    transaction_date="2/30",
                    description="Sample Transaction",
                    credit=None,
                    debit=Decimal("25.00"),
                    balance=None,
                ),
            ),
            period=StatementPeriod(
                start=date(2024, 2, 1),
                end=date(2024, 2, 29),
            ),
        )
