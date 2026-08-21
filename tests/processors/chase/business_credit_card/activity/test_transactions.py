"""
tests/processors/chase/business_credit_card/activity/test_transactions.py

Tests for Chase business credit-card transaction normalization.
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
from banking_statements.processors.chase.business_credit_card.activity import (
    ChaseBusinessCreditCardActivityRow,
    parse_activity_transactions,
)


def make_row(
    *,
    date_text: str = "06/12",
    description: str = "SAMPLE PURCHASE",
    amount: str = "24.35",
    page: int = 2,
    continuation_lines: tuple[str, ...] = (),
) -> ChaseBusinessCreditCardActivityRow:
    """Build one synthetic Chase business-card activity row."""
    raw_text = f"{date_text} {description} {amount}"
    return ChaseBusinessCreditCardActivityRow(
        date_text=date_text,
        description=description,
        amount=Decimal(amount),
        page=page,
        raw_text=raw_text,
        continuation_lines=continuation_lines,
    )


def make_source() -> StatementSource:
    """Build synthetic statement source identity."""
    return StatementSource(
        path=Path("sample.pdf"),
        sha256="0" * 64,
    )


def test_signed_amounts_determine_credit_card_direction() -> None:
    source = make_source()
    transactions = parse_activity_transactions(
        (
            make_row(
                date_text="06/10",
                description="SAMPLE PAYMENT",
                amount="-125.00",
            ),
            make_row(
                date_text="06/12",
                description="SAMPLE PURCHASE",
                amount="24.35",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 6, 1),
            end=date(2026, 6, 30),
        ),
        source=source,
    )

    assert transactions[0].amount == Decimal("125.00")
    assert transactions[0].direction is TransactionDirection.CREDIT
    assert transactions[1].amount == Decimal("24.35")
    assert transactions[1].direction is TransactionDirection.DEBIT

    assert transactions[0].evidence is not None
    assert transactions[0].evidence.source is source
    assert transactions[0].evidence.page == 2
    assert transactions[0].evidence.section == "Account Activity"
    assert transactions[0].evidence.processor == (
        "chase.business_credit_card.v1"
    )
    assert transactions[0].evidence.sequence == 1


def test_raw_evidence_preserves_foreign_currency_continuation() -> None:
    transaction = parse_activity_transactions(
        (
            make_row(
                description="SAMPLE FOREIGN MERCHANT",
                amount="8.81",
                continuation_lines=(
                    "06/13 EUR",
                    "7.60 X 1.159210526 (EXCHG RATE)",
                ),
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 6, 1),
            end=date(2026, 6, 30),
        ),
        source=make_source(),
    )[0]

    assert transaction.evidence is not None
    assert transaction.evidence.raw_text == (
        "06/12 SAMPLE FOREIGN MERCHANT 8.81\n"
        "06/13 EUR\n"
        "7.60 X 1.159210526 (EXCHG RATE)"
    )


def test_transaction_date_resolves_across_year_boundary() -> None:
    transactions = parse_activity_transactions(
        (
            make_row(date_text="12/28", amount="14.00"),
            make_row(date_text="01/03", amount="22.00"),
        ),
        period=StatementPeriod(
            start=date(2025, 12, 20),
            end=date(2026, 1, 19),
        ),
        source=make_source(),
    )

    assert transactions[0].date == date(2025, 12, 28)
    assert transactions[1].date == date(2026, 1, 3)


def test_transaction_date_can_precede_statement_period() -> None:
    transaction = parse_activity_transactions(
        (make_row(date_text="06/06", amount="42.00"),),
        period=StatementPeriod(
            start=date(2026, 6, 8),
            end=date(2026, 7, 7),
        ),
        source=make_source(),
    )[0]

    assert transaction.date == date(2026, 6, 6)


def test_invalid_transaction_date_format_raises() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase business credit-card date",
    ):
        parse_activity_transactions(
            (make_row(date_text="June 12"),),
            period=StatementPeriod(
                start=date(2026, 6, 1),
                end=date(2026, 6, 30),
            ),
            source=make_source(),
        )


def test_invalid_current_year_calendar_date_raises() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase business credit-card calendar date",
    ):
        parse_activity_transactions(
            (make_row(date_text="02/30"),),
            period=StatementPeriod(
                start=date(2026, 2, 1),
                end=date(2026, 3, 1),
            ),
            source=make_source(),
        )


def test_invalid_prior_year_calendar_date_raises() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase business credit-card calendar date",
    ):
        parse_activity_transactions(
            (make_row(date_text="02/29"),),
            period=StatementPeriod(
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
            ),
            source=make_source(),
        )


def test_zero_amount_raises() -> None:
    with pytest.raises(
        ValueError,
        match="transaction amount must not be zero",
    ):
        parse_activity_transactions(
            (make_row(amount="0.00"),),
            period=StatementPeriod(
                start=date(2026, 6, 1),
                end=date(2026, 6, 30),
            ),
            source=make_source(),
        )


def test_empty_rows_return_empty_transactions() -> None:
    assert (
        parse_activity_transactions(
            (),
            period=StatementPeriod(
                start=date(2026, 6, 1),
                end=date(2026, 6, 30),
            ),
            source=make_source(),
        )
        == ()
    )
