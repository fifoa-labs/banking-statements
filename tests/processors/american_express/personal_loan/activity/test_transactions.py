"""
tests/processors/american_express/personal_loan/activity/test_transactions.py

Tests for American Express personal-loan transaction normalization.
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
from banking_statements.processors.american_express.personal_loan.activity import (  # noqa: E501
    AmericanExpressPersonalLoanActivityRow,
    AmericanExpressPersonalLoanActivitySection,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic personal-loan statement period."""
    return StatementPeriod(
        start=date(2026, 6, 12),
        end=date(2026, 7, 12),
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-personal-loan.pdf"),
        sha256="a" * 64,
    )


def make_row(
    *,
    transaction_date: str = "07/01/26",
    amount: Decimal = Decimal("25.00"),
    section: AmericanExpressPersonalLoanActivitySection = (
        AmericanExpressPersonalLoanActivitySection.INTEREST
    ),
) -> AmericanExpressPersonalLoanActivityRow:
    """Build one synthetic personal-loan activity row."""
    return AmericanExpressPersonalLoanActivityRow(
        transaction_date=transaction_date,
        description="SAMPLE ACTIVITY",
        amount=amount,
        section=section,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_debits_and_credit() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(
                transaction_date="06/26/26",
                amount=Decimal("100.00"),
                section=AmericanExpressPersonalLoanActivitySection.PAYMENT,
            ),
            make_row(),
        ),
        period=make_period(),
        source=make_source(),
    )

    assert transactions[0].date == date(2026, 6, 26)
    assert transactions[0].direction is TransactionDirection.CREDIT
    assert transactions[0].amount == Decimal("100.00")
    assert transactions[1].direction is TransactionDirection.DEBIT

    assert transactions[0].evidence is not None
    assert transactions[0].evidence.source == make_source()
    assert transactions[0].evidence.section == "payment"
    assert transactions[0].evidence.raw_text == "synthetic row"
    assert (
        transactions[0].evidence.processor
        == "american_express.personal_loan.v1"
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


@pytest.mark.parametrize("transaction_date", ["02/30/26", "13/01/26"])
def test_parse_activity_transactions_rejects_invalid_calendar_date(
    transaction_date: str,
) -> None:
    with pytest.raises(ValueError, match="transaction calendar date"):
        parse_activity_transactions(
            (make_row(transaction_date=transaction_date),),
            period=make_period(),
            source=make_source(),
        )


@pytest.mark.parametrize("transaction_date", ["06/11/26", "07/13/26"])
def test_parse_activity_transactions_rejects_out_of_period_date(
    transaction_date: str,
) -> None:
    with pytest.raises(ValueError, match="outside the statement period"):
        parse_activity_transactions(
            (make_row(transaction_date=transaction_date),),
            period=make_period(),
            source=make_source(),
        )
