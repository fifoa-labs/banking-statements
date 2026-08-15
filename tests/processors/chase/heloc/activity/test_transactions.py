"""
tests/processors/chase/heloc/activity/test_transactions.py

Tests for Chase HELOC transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.chase.heloc.activity import (
    ChaseHelocActivityKind,
    ChaseHelocActivityRow,
    parse_activity_transactions,
)


def make_row(
    *,
    transaction_date: str = "02/10/2026",
    amount: Decimal | None = Decimal("100.00"),
    direction: TransactionDirection | None = TransactionDirection.CREDIT,
    description: str = "SAMPLE PAYMENT",
) -> ChaseHelocActivityRow:
    """Build one synthetic Chase HELOC activity row."""
    return ChaseHelocActivityRow(
        transaction_date=transaction_date,
        kind=ChaseHelocActivityKind.FUNDS_APPLIED,
        description=description,
        amount=amount,
        direction=direction,
    )


def period() -> StatementPeriod:
    """Return a synthetic statement period."""
    return StatementPeriod(
        start=date(2026, 1, 20),
        end=date(2026, 2, 18),
    )


def test_parse_activity_transactions_adds_gross_finance_charges() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(),
            make_row(
                transaction_date="02/12/2026",
                amount=Decimal("500.00"),
                direction=TransactionDirection.DEBIT,
                description="SAMPLE ADVANCE",
            ),
        ),
        period=period(),
        finance_charges=Decimal("12.50"),
    )

    assert len(transactions) == 3
    assert transactions[0].date == date(2026, 2, 10)
    assert transactions[0].direction is TransactionDirection.CREDIT
    assert transactions[1].direction is TransactionDirection.DEBIT

    finance_charge = transactions[2]
    assert finance_charge.date == date(2026, 2, 18)
    assert finance_charge.amount == Decimal("12.50")
    assert finance_charge.direction is TransactionDirection.DEBIT
    assert finance_charge.description == "FINANCE CHARGES"


def test_informational_rows_are_skipped() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(
                amount=None,
                direction=None,
                description="PAYMENT",
            ),
        ),
        period=period(),
        finance_charges=Decimal("0.00"),
    )

    assert transactions == ()


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (
            make_row(amount=None, direction=TransactionDirection.CREDIT),
            "incomplete transaction semantics",
        ),
        (
            make_row(amount=Decimal("0.00")),
            "amount must be positive",
        ),
        (
            make_row(transaction_date="02/30/2026"),
            "calendar date",
        ),
        (
            make_row(transaction_date="03/01/2026"),
            "outside statement period",
        ),
    ],
)
def test_invalid_rows_raise(
    row: ChaseHelocActivityRow,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_activity_transactions(
            (row,),
            period=period(),
            finance_charges=Decimal("0.00"),
        )


def test_negative_finance_charges_are_rejected() -> None:
    with pytest.raises(ValueError, match="finance charges"):
        parse_activity_transactions(
            (),
            period=period(),
            finance_charges=Decimal("-1.00"),
        )
