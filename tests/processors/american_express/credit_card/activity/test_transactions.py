"""
tests/processors/american_express/credit_card/activity/test_transactions.py

Tests for American Express credit-card transaction normalization.
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
from banking_statements.processors.american_express.credit_card.activity import (  # noqa: E501
    AmericanExpressCreditCardActivityRow,
    AmericanExpressCreditCardActivitySection,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic American Express statement period."""
    return StatementPeriod(
        start=date(2026, 3, 17),
        end=date(2026, 4, 15),
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-american-express.pdf"),
        sha256="a" * 64,
    )


def make_row(  # noqa: PLR0913
    section: AmericanExpressCreditCardActivitySection,
    *,
    date_text: str | None = "03/20/26",
    amount_text: str = "$12.50",
    description: str = "SAMPLE TRANSACTION",
    card_ending: str | None = None,
    continuation_lines: tuple[str, ...] = (),
) -> AmericanExpressCreditCardActivityRow:
    """Build a synthetic American Express activity row."""
    return AmericanExpressCreditCardActivityRow(
        section=section,
        date_text=date_text,
        description=description,
        amount_text=amount_text,
        card_ending=card_ending,
        continuation_lines=continuation_lines,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_normalizes_sections() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(
                AmericanExpressCreditCardActivitySection.CHARGES,
                card_ending="7-65432",
                continuation_lines=("ADDITIONAL DETAIL",),
            ),
            make_row(
                AmericanExpressCreditCardActivitySection.PAYMENTS,
                amount_text="-$5.00",
                description="SAMPLE PAYMENT",
            ),
            make_row(
                AmericanExpressCreditCardActivitySection.CREDITS,
                amount_text="$2.50 CR",
                description="SAMPLE CREDIT",
            ),
            make_row(
                AmericanExpressCreditCardActivitySection.FEES,
                date_text=None,
                amount_text="$3.00",
                description="SAMPLE FEE",
            ),
            make_row(
                AmericanExpressCreditCardActivitySection.INTEREST,
                date_text=None,
                amount_text="$1.25",
                description="SAMPLE INTEREST",
            ),
        ),
        period=make_period(),
        source=make_source(),
    )

    assert [transaction.direction for transaction in transactions] == [
        TransactionDirection.DEBIT,
        TransactionDirection.CREDIT,
        TransactionDirection.CREDIT,
        TransactionDirection.DEBIT,
        TransactionDirection.DEBIT,
    ]
    assert transactions[0].description == (
        "SAMPLE TRANSACTION ADDITIONAL DETAIL"
    )
    assert transactions[0].evidence is not None
    assert transactions[0].evidence.section == "Card Ending 7-65432"
    assert transactions[0].evidence.sequence == 1
    assert transactions[1].evidence is not None
    assert transactions[1].evidence.section == "Payments"
    assert transactions[3].date == make_period().end


def test_negative_charge_is_normalized_as_credit() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                AmericanExpressCreditCardActivitySection.CHARGES,
                amount_text="-$12.50",
            ),
        ),
        period=make_period(),
        source=make_source(),
    )[0]

    assert transaction.amount == Decimal("12.50")
    assert transaction.direction is TransactionDirection.CREDIT


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    with pytest.raises(ValueError, match="amount must not be zero"):
        parse_activity_transactions(
            (
                make_row(
                    AmericanExpressCreditCardActivitySection.CHARGES,
                    amount_text="$0.00",
                ),
            ),
            period=make_period(),
            source=make_source(),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError, match="transaction calendar date"):
        parse_activity_transactions(
            (
                make_row(
                    AmericanExpressCreditCardActivitySection.CHARGES,
                    date_text="02/30/26",
                ),
            ),
            period=make_period(),
            source=make_source(),
        )


def test_parse_activity_transactions_rejects_date_after_closing() -> None:
    with pytest.raises(ValueError, match="after the statement closing date"):
        parse_activity_transactions(
            (
                make_row(
                    AmericanExpressCreditCardActivitySection.CHARGES,
                    date_text="04/16/26",
                ),
            ),
            period=make_period(),
            source=make_source(),
        )


def test_parse_activity_transactions_handles_empty_rows() -> None:
    assert (
        parse_activity_transactions(
            (),
            period=make_period(),
            source=make_source(),
        )
        == ()
    )


def test_parse_activity_transactions_accepts_explicit_plus_amount() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                AmericanExpressCreditCardActivitySection.CHARGES,
                amount_text="+$12.50",
            ),
        ),
        period=make_period(),
        source=make_source(),
    )[0]

    assert transaction.amount == Decimal("12.50")
    assert transaction.direction is TransactionDirection.DEBIT
