"""
tests/processors/us_bank/credit_card/activity/test_transactions.py

Tests for U.S. Bank credit-card transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements.domain import StatementPeriod, StatementSource
from banking_statements.processors.us_bank.credit_card.activity import (
    USBankCreditCardActivityRow,
    USBankCreditCardActivitySection,
    parse_activity_transactions,
)

SOURCE = StatementSource(path=Path("sample.pdf"), sha256="synthetic")


def row(
    date_text: str,
    amount: str,
    *,
    credit: bool = False,
) -> USBankCreditCardActivityRow:
    return USBankCreditCardActivityRow(
        posting_date=date_text,
        transaction_date=None,
        description="Sample activity",
        amount=Decimal(amount),
        direction_is_credit=credit,
        section=(
            USBankCreditCardActivitySection.CREDIT
            if credit
            else USBankCreditCardActivitySection.DEBIT
        ),
        page=3,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_and_skips_zero_rows() -> None:
    result = parse_activity_transactions(
        (
            row("12/31", "10.00"),
            row("01/02", "4.00", credit=True),
            row("01/02", "0.00"),
        ),
        period=StatementPeriod(start=date(2025, 12, 30), end=date(2026, 1, 3)),
        source=SOURCE,
    )
    assert len(result) == 2
    assert result[0].date == date(2025, 12, 31)
    assert result[1].date == date(2026, 1, 2)
    assert result[0].evidence is not None
    assert result[0].evidence.sequence == 1
    assert result[1].evidence is not None
    assert result[1].evidence.sequence == 2


def test_parse_activity_transactions_rejects_bad_or_ambiguous_date() -> None:
    with pytest.raises(ValueError, match="Invalid U.S. Bank"):  # noqa: RUF043
        parse_activity_transactions(
            (row("13/40", "1.00"),),
            period=StatementPeriod(
                start=date(2026, 1, 1), end=date(2026, 1, 31)
            ),
            source=SOURCE,
        )
    with pytest.raises(ValueError, match="resolved uniquely"):
        parse_activity_transactions(
            (row("01/02", "1.00"),),
            period=StatementPeriod(
                start=date(2025, 1, 1), end=date(2026, 1, 31)
            ),
            source=SOURCE,
        )

    with pytest.raises(ValueError, match="resolved uniquely"):
        parse_activity_transactions(
            (row("02/29", "1.00"),),
            period=StatementPeriod(
                start=date(2025, 2, 28),
                end=date(2025, 3, 1),
            ),
            source=SOURCE,
        )
