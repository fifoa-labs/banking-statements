"""
tests/processors/us_bank/business_checking/activity/test_transactions.py

Tests for U.S. Bank business-checking transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements.domain import StatementPeriod, StatementSource
from banking_statements.processors.us_bank.business_checking.activity import (
    USBankBusinessCheckingActivityRow,
    USBankBusinessCheckingActivitySection,
    parse_activity_transactions,
)

SOURCE = StatementSource(path=Path("sample.pdf"), sha256="synthetic")


def row(
    date_text: str,
    amount: str,
    *,
    credit: bool = True,
) -> USBankBusinessCheckingActivityRow:
    return USBankBusinessCheckingActivityRow(
        transaction_date=date_text,
        description="Sample activity",
        amount=Decimal(amount),
        section=(
            USBankBusinessCheckingActivitySection.CREDIT
            if credit
            else USBankBusinessCheckingActivitySection.DEBIT
        ),
        page=2,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_directions() -> None:
    result = parse_activity_transactions(
        (row("Dec31", "10.00"), row("Jan 2", "4.00", credit=False)),
        period=StatementPeriod(start=date(2025, 12, 30), end=date(2026, 1, 2)),
        source=SOURCE,
    )
    assert [transaction.date for transaction in result] == [
        date(2025, 12, 31),
        date(2026, 1, 2),
    ]
    assert result[0].evidence is not None
    assert result[0].evidence.page == 2
    assert result[0].evidence.sequence == 1
    assert result[1].evidence is not None
    assert result[1].evidence.sequence == 2


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    with pytest.raises(ValueError, match="must not be zero"):
        parse_activity_transactions(
            (row("Jan 2", "0.00"),),
            period=StatementPeriod(
                start=date(2026, 1, 1), end=date(2026, 1, 31)
            ),
            source=SOURCE,
        )


def test_parse_activity_transactions_rejects_bad_or_ambiguous_date() -> None:
    with pytest.raises(ValueError, match="Invalid U.S. Bank"):  # noqa: RUF043
        parse_activity_transactions(
            (row("Bad", "1.00"),),
            period=StatementPeriod(
                start=date(2026, 1, 1), end=date(2026, 1, 31)
            ),
            source=SOURCE,
        )
    with pytest.raises(ValueError, match="resolved uniquely"):
        parse_activity_transactions(
            (row("Jan 2", "1.00"),),
            period=StatementPeriod(
                start=date(2025, 1, 1), end=date(2026, 1, 31)
            ),
            source=SOURCE,
        )

    with pytest.raises(ValueError, match="resolved uniquely"):
        parse_activity_transactions(
            (row("Feb 29", "1.00"),),
            period=StatementPeriod(
                start=date(2025, 2, 28),
                end=date(2025, 3, 1),
            ),
            source=SOURCE,
        )
