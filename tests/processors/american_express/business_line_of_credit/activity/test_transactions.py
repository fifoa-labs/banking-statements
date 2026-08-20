"""
tests/processors/american_express/business_line_of_credit/activity/test_transactions.py

Tests for American Express business line-of-credit transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements.domain import (
    StatementPeriod,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.american_express.business_line_of_credit.activity import (  # noqa: E501
    AmericanExpressBusinessLineOfCreditActivityRow,
    AmericanExpressBusinessLineOfCreditActivitySection,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic statement period."""
    return StatementPeriod(
        start=date(2026, 4, 1),
        end=date(2026, 4, 30),
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-american-express-loc.pdf"),
        sha256="a" * 64,
    )


def make_row(
    *,
    transaction_date: str = "04/10/2026",
    amount: Decimal = Decimal("25.00"),
    section: AmericanExpressBusinessLineOfCreditActivitySection = (
        AmericanExpressBusinessLineOfCreditActivitySection.DEBIT
    ),
) -> AmericanExpressBusinessLineOfCreditActivityRow:
    """Build one synthetic activity row."""
    return AmericanExpressBusinessLineOfCreditActivityRow(
        transaction_date=transaction_date,
        reference_number="1234567890",
        description="SAMPLE ACTIVITY",
        amount=amount,
        section=section,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_debit_and_credit() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(),
            make_row(
                transaction_date="04/15/2026",
                amount=Decimal("10.00"),
                section=(
                    AmericanExpressBusinessLineOfCreditActivitySection.CREDIT
                ),
            ),
        ),
        period=make_period(),
        source=make_source(),
    )

    assert len(transactions) == 2

    assert transactions[0].date == date(2026, 4, 10)
    assert transactions[0].amount == Decimal("25.00")
    assert transactions[0].direction is TransactionDirection.DEBIT
    assert transactions[0].description == "SAMPLE ACTIVITY"

    assert transactions[1].date == date(2026, 4, 15)
    assert transactions[1].amount == Decimal("10.00")
    assert transactions[1].direction is TransactionDirection.CREDIT

    assert transactions[0].evidence is not None
    assert transactions[0].evidence.source == make_source()
    assert transactions[0].evidence.section == "Transaction Summary"
    assert transactions[0].evidence.raw_text == "synthetic row"
    assert (
        transactions[0].evidence.processor
        == "american_express.business_line_of_credit.v1"
    )
    assert transactions[0].evidence.sequence == 1
    assert transactions[1].evidence is not None
    assert transactions[1].evidence.sequence == 2


def test_parse_activity_transactions_returns_empty_for_no_rows() -> None:
    assert (
        parse_activity_transactions(
            (),
            period=make_period(),
            source=make_source(),
        )
        == ()
    )


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    with pytest.raises(ValueError, match="amount must not be zero"):
        parse_activity_transactions(
            (make_row(amount=Decimal("0.00")),),
            period=make_period(),
            source=make_source(),
        )


@pytest.mark.parametrize(
    "transaction_date",
    [
        "04/31/2026",
        "13/01/2026",
    ],
)
def test_parse_activity_transactions_rejects_invalid_calendar_date(
    transaction_date: str,
) -> None:
    with pytest.raises(ValueError, match="transaction calendar date"):
        parse_activity_transactions(
            (make_row(transaction_date=transaction_date),),
            period=make_period(),
            source=make_source(),
        )


@pytest.mark.parametrize(
    "transaction_date",
    [
        "03/31/2026",
        "05/01/2026",
    ],
)
def test_parse_activity_transactions_rejects_date_outside_period(
    transaction_date: str,
) -> None:
    with pytest.raises(ValueError, match="outside the statement period"):
        parse_activity_transactions(
            (make_row(transaction_date=transaction_date),),
            period=make_period(),
            source=make_source(),
        )
