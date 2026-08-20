"""
tests/processors/capital_one/credit_card/activity/test_transactions.py

Tests for Capital One credit-card transaction normalization.
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
from banking_statements.processors.capital_one.credit_card.activity import (
    CapitalOneCreditCardActivityRow,
    CapitalOneCreditCardActivitySection,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic period spanning a year boundary."""
    return StatementPeriod(
        start=date(2025, 12, 19),
        end=date(2026, 1, 18),
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-capital-one-credit-card.pdf"),
        sha256="a" * 64,
    )


def make_row(
    *,
    transaction_date: str | None = "Dec 18",
    posting_date: str | None = "Dec 19",
    amount: Decimal = Decimal("25.00"),
    section: CapitalOneCreditCardActivitySection = (
        CapitalOneCreditCardActivitySection.DEBIT
    ),
    card_last4: str | None = "1234",
) -> CapitalOneCreditCardActivityRow:
    """Build one synthetic Capital One credit-card activity row."""
    return CapitalOneCreditCardActivityRow(
        transaction_date=transaction_date,
        posting_date=posting_date,
        description="SAMPLE ACTIVITY",
        amount=amount,
        section=section,
        card_last4=card_last4,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_prefers_posting_date() -> None:
    transaction = parse_activity_transactions(
        (make_row(),),
        period=make_period(),
        source=make_source(),
    )[0]

    assert transaction.date == date(2025, 12, 19)
    assert transaction.amount == Decimal("25.00")
    assert transaction.direction is TransactionDirection.DEBIT
    assert transaction.description == "SAMPLE ACTIVITY"

    assert transaction.evidence is not None
    assert transaction.evidence.source == make_source()
    assert transaction.evidence.section == "debit: card ending 1234"
    assert transaction.evidence.raw_text == "synthetic row"
    assert transaction.evidence.processor == "capital_one.credit_card.v1"
    assert transaction.evidence.sequence == 1


def test_parse_activity_transactions_normalizes_credit_and_undated_interest() -> (  # noqa: E501
    None
):
    transactions = parse_activity_transactions(
        (
            make_row(
                transaction_date="Jan 5",
                posting_date="Jan 6",
                section=CapitalOneCreditCardActivitySection.CREDIT,
            ),
            make_row(
                transaction_date=None,
                posting_date=None,
                amount=Decimal("4.00"),
                section=CapitalOneCreditCardActivitySection.INTEREST,
                card_last4=None,
            ),
        ),
        period=make_period(),
        source=make_source(),
    )

    assert transactions[0].date == date(2026, 1, 6)
    assert transactions[0].direction is TransactionDirection.CREDIT

    assert transactions[1].date == make_period().end
    assert transactions[1].direction is TransactionDirection.DEBIT
    assert transactions[1].evidence is not None
    assert transactions[1].evidence.section == "interest"


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


def test_transaction_date_uses_prior_year_when_needed() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                transaction_date="Dec 30",
                posting_date="Dec 31",
            ),
        ),
        period=StatementPeriod(
            start=date(2025, 12, 19),
            end=date(2026, 1, 18),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2025, 12, 31)


def test_transaction_date_accepts_prior_year_leap_day() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                transaction_date="Feb 28",
                posting_date="Feb 29",
            ),
        ),
        period=StatementPeriod(
            start=date(2024, 12, 19),
            end=date(2025, 1, 18),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2024, 2, 29)


def test_transaction_date_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError, match="calendar date"):
        parse_activity_transactions(
            (
                make_row(
                    transaction_date="Feb 28",
                    posting_date="Feb 29",
                ),
            ),
            period=StatementPeriod(
                start=date(2023, 12, 19),
                end=date(2024, 1, 18),
            ),
            source=make_source(),
        )


def test_transaction_date_rejects_invalid_text() -> None:
    with pytest.raises(ValueError, match="transaction date"):
        parse_activity_transactions(
            (
                make_row(
                    transaction_date="Bad Date",
                    posting_date=None,
                ),
            ),
            period=make_period(),
            source=make_source(),
        )
