"""
tests/processors/wellsfargo/business_line_of_credit/activity/test_transactions.py

Tests for Wells Fargo business line-of-credit transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.wellsfargo.business_line_of_credit.activity.rows import (  # noqa: E501
    WellsFargoBusinessLineOfCreditActivityRow,
)
from banking_statements.processors.wellsfargo.business_line_of_credit.activity.transactions import (  # noqa: E501
    parse_activity_transactions,
)


def make_row(
    *,
    transaction_date: str | None = "03/10",
    credit: Decimal | None = None,
    charge: Decimal | None = None,
    description: str = "SAMPLE ACTIVITY",
) -> WellsFargoBusinessLineOfCreditActivityRow:
    """Build a synthetic line-of-credit activity row."""
    return WellsFargoBusinessLineOfCreditActivityRow(
        transaction_date=transaction_date,
        post_date=transaction_date,
        reference_number="ABC123" if transaction_date is not None else None,
        description=description,
        credit=credit,
        charge=charge,
    )


def test_parse_activity_transactions() -> None:
    period = StatementPeriod(
        start=date(2026, 2, 20),
        end=date(2026, 3, 22),
    )

    transactions = parse_activity_transactions(
        (
            make_row(
                credit=Decimal("200.00"),
                description="SAMPLE PAYMENT",
            ),
            make_row(
                charge=Decimal("500.00"),
                description="SAMPLE ADVANCE",
            ),
            make_row(
                transaction_date=None,
                charge=Decimal("12.50"),
                description="PERIODIC FINANCE CHARGE",
            ),
        ),
        period=period,
    )

    assert transactions[0].direction is TransactionDirection.CREDIT
    assert transactions[0].amount == Decimal("200.00")
    assert transactions[0].date == date(2026, 3, 10)

    assert transactions[1].direction is TransactionDirection.DEBIT
    assert transactions[1].amount == Decimal("500.00")

    assert transactions[2].direction is TransactionDirection.DEBIT
    assert transactions[2].amount == Decimal("12.50")
    assert transactions[2].date == period.end


def test_transaction_date_can_resolve_to_previous_year() -> None:
    period = StatementPeriod(
        start=date(2025, 12, 20),
        end=date(2026, 1, 18),
    )

    transaction = parse_activity_transactions(
        (make_row(transaction_date="12/28", charge=Decimal("10.00")),),
        period=period,
    )[0]

    assert transaction.date == date(2025, 12, 28)


@pytest.mark.parametrize("transaction_date", ["02/30", "13/01"])
def test_invalid_transaction_date_raises(transaction_date: str) -> None:
    period = StatementPeriod(
        start=date(2026, 2, 20),
        end=date(2026, 3, 22),
    )

    with pytest.raises(ValueError, match="calendar date"):
        parse_activity_transactions(
            (
                make_row(
                    transaction_date=transaction_date,
                    charge=Decimal("10.00"),
                ),
            ),
            period=period,
        )


@pytest.mark.parametrize(
    "row",
    [
        make_row(
            credit=Decimal("10.00"),
            charge=Decimal("10.00"),
        ),
        make_row(),
        make_row(charge=Decimal("0.00")),
    ],
)
def test_invalid_amount_shape_raises(
    row: WellsFargoBusinessLineOfCreditActivityRow,
) -> None:
    period = StatementPeriod(
        start=date(2026, 2, 20),
        end=date(2026, 3, 22),
    )

    with pytest.raises(ValueError):  # noqa: PT011
        parse_activity_transactions((row,), period=period)


def test_invalid_prior_year_transaction_date_raises() -> None:
    period = StatementPeriod(
        start=date(2023, 12, 15),
        end=date(2024, 1, 14),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Invalid Wells Fargo business line-of-credit transaction "
            "calendar date"
        ),
    ):
        parse_activity_transactions(
            (
                make_row(
                    transaction_date="02/29",
                    charge=Decimal("10.00"),
                ),
            ),
            period=period,
        )
