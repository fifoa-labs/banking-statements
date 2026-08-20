"""
tests/processors/capital_one/checking/activity/test_transactions.py

Tests for Capital One checking transaction normalization.
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
from banking_statements.processors.capital_one.checking.activity import (
    CapitalOneCheckingActivityRow,
    CapitalOneCheckingActivitySection,
    parse_activity_transactions,
)


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-capital-one-checking.pdf"),
        sha256="a" * 64,
    )


def make_row(
    *,
    transaction_date: str = "Mar 5",
    amount: Decimal = Decimal("25.00"),
    section: CapitalOneCheckingActivitySection = (
        CapitalOneCheckingActivitySection.CREDIT
    ),
) -> CapitalOneCheckingActivityRow:
    """Build one synthetic Capital One checking activity row."""
    return CapitalOneCheckingActivityRow(
        transaction_date=transaction_date,
        description="SAMPLE ACTIVITY",
        amount=amount,
        balance=Decimal("125.00"),
        section=section,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_direction_and_evidence() -> (
    None
):
    transactions = parse_activity_transactions(
        (
            make_row(),
            make_row(
                transaction_date="Mar 10",
                section=CapitalOneCheckingActivitySection.DEBIT,
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 3, 1),
            end=date(2026, 3, 31),
        ),
        source=make_source(),
    )

    assert transactions[0].date == date(2026, 3, 5)
    assert transactions[0].amount == Decimal("25.00")
    assert transactions[0].direction is TransactionDirection.CREDIT
    assert transactions[1].direction is TransactionDirection.DEBIT

    assert transactions[0].evidence is not None
    assert transactions[0].evidence.source == make_source()
    assert transactions[0].evidence.section == "credit"
    assert transactions[0].evidence.raw_text == "synthetic row"
    assert transactions[0].evidence.processor == "capital_one.checking.v1"
    assert transactions[0].evidence.sequence == 1


def test_parse_activity_transactions_resolves_cross_year_date() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                transaction_date="Dec 31",
                section=CapitalOneCheckingActivitySection.DEBIT,
            ),
        ),
        period=StatementPeriod(
            start=date(2025, 12, 1),
            end=date(2026, 1, 31),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2025, 12, 31)


def test_parse_activity_transactions_accepts_quarter_period() -> None:
    transaction = parse_activity_transactions(
        (make_row(transaction_date="May 15"),),
        period=StatementPeriod(
            start=date(2026, 4, 1),
            end=date(2026, 6, 30),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2026, 5, 15)


def test_parse_activity_transactions_returns_empty() -> None:
    assert (
        parse_activity_transactions(
            (),
            period=StatementPeriod(
                start=date(2026, 3, 1),
                end=date(2026, 3, 31),
            ),
            source=make_source(),
        )
        == ()
    )


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    with pytest.raises(ValueError, match="amount must not be zero"):
        parse_activity_transactions(
            (make_row(amount=Decimal("0.00")),),
            period=StatementPeriod(
                start=date(2026, 3, 1),
                end=date(2026, 3, 31),
            ),
            source=make_source(),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError, match="calendar date"):
        parse_activity_transactions(
            (make_row(transaction_date="Feb 30"),),
            period=StatementPeriod(
                start=date(2026, 2, 1),
                end=date(2026, 2, 28),
            ),
            source=make_source(),
        )


def test_parse_activity_transactions_rejects_unresolvable_date() -> None:
    with pytest.raises(ValueError, match="could not be resolved uniquely"):
        parse_activity_transactions(
            (make_row(transaction_date="Apr 1"),),
            period=StatementPeriod(
                start=date(2026, 3, 1),
                end=date(2026, 3, 31),
            ),
            source=make_source(),
        )


def test_parse_activity_transactions_accepts_leap_day() -> None:
    transaction = parse_activity_transactions(
        (make_row(transaction_date="Feb 29"),),
        period=StatementPeriod(
            start=date(2024, 2, 1),
            end=date(2024, 2, 29),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2024, 2, 29)
