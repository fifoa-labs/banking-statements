"""
tests/processors/discover/credit_card/activity/test_transactions.py

Tests for Discover credit-card transaction normalization.
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
from banking_statements.processors.discover.credit_card.activity import (
    DiscoverCreditCardActivityRow,
    DiscoverCreditCardActivitySection,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic period spanning a year boundary."""
    return StatementPeriod(
        start=date(2025, 12, 7),
        end=date(2026, 1, 6),
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-discover-credit-card.pdf"),
        sha256="a" * 64,
    )


def make_row(
    *,
    posting_date: str | None = "Dec 13",
    amount: Decimal = Decimal("25.00"),
    section: DiscoverCreditCardActivitySection = (
        DiscoverCreditCardActivitySection.DEBIT
    ),
) -> DiscoverCreditCardActivityRow:
    """Build one synthetic Discover credit-card activity row."""
    return DiscoverCreditCardActivityRow(
        transaction_date=posting_date,
        posting_date=posting_date,
        description="SAMPLE ACTIVITY",
        amount=amount,
        section=section,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_directions_and_dates() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(
                posting_date="Dec 13",
                section=DiscoverCreditCardActivitySection.CREDIT,
            ),
            make_row(posting_date="01/05"),
            make_row(
                posting_date=None,
                amount=Decimal("4.00"),
                section=DiscoverCreditCardActivitySection.INTEREST,
            ),
        ),
        period=make_period(),
        source=make_source(),
    )

    assert transactions[0].date == date(2025, 12, 13)
    assert transactions[0].direction is TransactionDirection.CREDIT

    assert transactions[1].date == date(2026, 1, 5)
    assert transactions[1].direction is TransactionDirection.DEBIT

    assert transactions[2].date == make_period().end
    assert transactions[2].direction is TransactionDirection.DEBIT

    assert transactions[0].evidence is not None
    assert transactions[0].evidence.source == make_source()
    assert transactions[0].evidence.section == "credit"
    assert transactions[0].evidence.raw_text == "synthetic row"
    assert transactions[0].evidence.processor == "discover.credit_card.v1"
    assert transactions[0].evidence.sequence == 1


def test_fee_is_normalized_as_debit() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                posting_date=None,
                amount=Decimal("3.00"),
                section=DiscoverCreditCardActivitySection.FEE,
            ),
        ),
        period=make_period(),
        source=make_source(),
    )[0]

    assert transaction.amount == Decimal("3.00")
    assert transaction.direction is TransactionDirection.DEBIT


def test_parse_activity_transactions_returns_empty() -> None:
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


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError, match="calendar date"):
        parse_activity_transactions(
            (make_row(posting_date="Feb 30"),),
            period=StatementPeriod(
                start=date(2026, 2, 1),
                end=date(2026, 2, 28),
            ),
            source=make_source(),
        )


def test_parse_activity_transactions_accepts_date_before_period_start() -> (
    None
):
    transaction = parse_activity_transactions(
        (
            DiscoverCreditCardActivityRow(
                transaction_date="04/08",
                posting_date=None,
                description="SAMPLE CREDIT",
                amount=Decimal("25.00"),
                section=DiscoverCreditCardActivitySection.CREDIT,
                raw_text="synthetic row",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 4, 10),
            end=date(2026, 5, 9),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2026, 4, 8)
    assert transaction.direction is TransactionDirection.CREDIT


def test_parse_activity_transactions_accepts_leap_day() -> None:
    transaction = parse_activity_transactions(
        (make_row(posting_date="02/29"),),
        period=StatementPeriod(
            start=date(2024, 2, 1),
            end=date(2024, 2, 29),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2024, 2, 29)


def test_parse_activity_transactions_rejects_leap_day_when_years_are_not_leap() -> (  # noqa: E501
    None
):
    with pytest.raises(ValueError, match="calendar date"):
        parse_activity_transactions(
            (make_row(posting_date="02/29"),),
            period=StatementPeriod(
                start=date(2025, 12, 7),
                end=date(2026, 1, 6),
            ),
            source=make_source(),
        )
