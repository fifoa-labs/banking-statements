"""
tests/processors/discover/checking/activity/test_transactions.py

Tests for Discover checking transaction normalization.
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
from banking_statements.processors.discover.checking.activity import (
    DiscoverCheckingActivityRow,
    DiscoverCheckingActivitySection,
    parse_activity_transactions,
)


def period() -> StatementPeriod:
    return StatementPeriod(start=date(2025, 12, 20), end=date(2026, 1, 31))


def source() -> StatementSource:
    return StatementSource(path=Path("sample-discover.pdf"), sha256="a" * 64)


def row(
    effective_date: str,
    *,
    section: DiscoverCheckingActivitySection,
    amount: str = "25.00",
    posting_date: str | None = None,
) -> DiscoverCheckingActivityRow:
    return DiscoverCheckingActivityRow(
        effective_date=effective_date,
        posting_date=posting_date or effective_date,
        description="SAMPLE ACTIVITY",
        amount=Decimal(amount),
        section=section,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_directions_and_dates() -> None:
    transactions = parse_activity_transactions(
        (
            row("Dec 24", section=DiscoverCheckingActivitySection.CREDIT),
            row("Jan 05", section=DiscoverCheckingActivitySection.DEBIT),
        ),
        period=period(),
        source=source(),
    )

    assert transactions[0].date == date(2025, 12, 24)
    assert transactions[0].direction is TransactionDirection.CREDIT
    assert transactions[1].date == date(2026, 1, 5)
    assert transactions[1].direction is TransactionDirection.DEBIT
    assert transactions[0].evidence is not None
    assert transactions[0].evidence.section == "credit"
    assert transactions[0].evidence.raw_text == "synthetic row"
    assert transactions[0].evidence.processor == "discover.checking.v1"
    assert transactions[0].evidence.sequence == 1


def test_parse_activity_transactions_returns_empty() -> None:
    assert (
        parse_activity_transactions((), period=period(), source=source()) == ()
    )


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    with pytest.raises(ValueError, match="amount must not be zero"):
        parse_activity_transactions(
            (
                row(
                    "Jan 05",
                    section=DiscoverCheckingActivitySection.CREDIT,
                    amount="0.00",
                ),
            ),
            period=period(),
            source=source(),
        )


def test_parse_activity_transactions_rejects_unresolvable_date() -> None:
    with pytest.raises(ValueError, match="could not be resolved uniquely"):
        parse_activity_transactions(
            (row("Feb 15", section=DiscoverCheckingActivitySection.CREDIT),),
            period=period(),
            source=source(),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError, match="calendar date"):
        parse_activity_transactions(
            (row("Feb 30", section=DiscoverCheckingActivitySection.CREDIT),),
            period=StatementPeriod(
                start=date(2026, 2, 1),
                end=date(2026, 2, 28),
            ),
            source=source(),
        )


def test_parse_activity_transactions_accepts_leap_day() -> None:
    transactions = parse_activity_transactions(
        (row("Feb 29", section=DiscoverCheckingActivitySection.CREDIT),),
        period=StatementPeriod(
            start=date(2024, 2, 1),
            end=date(2024, 2, 29),
        ),
        source=source(),
    )

    assert transactions[0].date == date(2024, 2, 29)


def test_parse_activity_transactions_uses_posting_date() -> None:
    transactions = parse_activity_transactions(
        (
            row(
                "Dec 31",
                posting_date="Jan 11",
                section=DiscoverCheckingActivitySection.CREDIT,
                amount="58.63",
            ),
        ),
        period=StatementPeriod(
            start=date(2023, 1, 1),
            end=date(2023, 1, 31),
        ),
        source=source(),
    )

    assert transactions[0].date == date(2023, 1, 11)
    assert transactions[0].amount == Decimal("58.63")
    assert transactions[0].direction is TransactionDirection.CREDIT
