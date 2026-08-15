"""
tests/processors/chase/checking/activity/test_transactions.py

Tests for Chase checking transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.chase.checking.activity import (
    ChaseCheckingActivityRow,
    parse_activity_transactions,
)


def test_parse_activity_transactions_normalizes_credit_and_debit() -> None:
    transactions = parse_activity_transactions(
        (
            ChaseCheckingActivityRow(
                transaction_date="01/05",
                description="SAMPLE DEPOSIT",
                amount=Decimal("200.00"),
                balance=Decimal("1200.00"),
            ),
            ChaseCheckingActivityRow(
                transaction_date="01/10",
                description="SAMPLE PAYMENT",
                amount=Decimal("-50.00"),
                balance=Decimal("1150.00"),
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 1, 1),
            end=date(2026, 1, 31),
        ),
    )

    assert len(transactions) == 2

    deposit = transactions[0]
    assert deposit.date == date(2026, 1, 5)
    assert deposit.amount == Decimal("200.00")
    assert deposit.direction is TransactionDirection.CREDIT
    assert deposit.description == "SAMPLE DEPOSIT"

    payment = transactions[1]
    assert payment.date == date(2026, 1, 10)
    assert payment.amount == Decimal("50.00")
    assert payment.direction is TransactionDirection.DEBIT
    assert payment.description == "SAMPLE PAYMENT"


def test_parse_activity_transactions_resolves_cross_year_dates() -> None:
    transactions = parse_activity_transactions(
        (
            ChaseCheckingActivityRow(
                transaction_date="12/24",
                description="SAMPLE PAYMENT",
                amount=Decimal("-25.00"),
                balance=Decimal("975.00"),
            ),
            ChaseCheckingActivityRow(
                transaction_date="01/03",
                description="SAMPLE DEPOSIT",
                amount=Decimal("100.00"),
                balance=Decimal("1075.00"),
            ),
        ),
        period=StatementPeriod(
            start=date(2025, 12, 22),
            end=date(2026, 1, 23),
        ),
    )

    assert transactions[0].date == date(2025, 12, 24)
    assert transactions[1].date == date(2026, 1, 3)


def test_parse_activity_transactions_rejects_zero_amount() -> None:
    rows = (
        ChaseCheckingActivityRow(
            transaction_date="01/05",
            description="ZERO TRANSACTION",
            amount=Decimal("0.00"),
            balance=Decimal("1000.00"),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Chase checking transaction amount must not be zero.",  # noqa: RUF043
    ):
        parse_activity_transactions(
            rows,
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
        )


def test_parse_activity_transactions_rejects_unresolvable_date() -> None:
    rows = (
        ChaseCheckingActivityRow(
            transaction_date="02/15",
            description="OUTSIDE PERIOD",
            amount=Decimal("-10.00"),
            balance=Decimal("990.00"),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Chase checking transaction date could not be resolved uniquely: "
            "02/15"
        ),
    ):
        parse_activity_transactions(
            rows,
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
        )


def test_parse_activity_transactions_rejects_invalid_calendar_date() -> None:
    rows = (
        ChaseCheckingActivityRow(
            transaction_date="02/30",
            description="INVALID DATE",
            amount=Decimal("-10.00"),
            balance=Decimal("990.00"),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Chase checking transaction date could not be resolved uniquely: "
            "02/30"
        ),
    ):
        parse_activity_transactions(
            rows,
            period=StatementPeriod(
                start=date(2026, 2, 1),
                end=date(2026, 2, 28),
            ),
        )


def test_parse_activity_transactions_returns_empty_for_no_rows() -> None:
    transactions = parse_activity_transactions(
        (),
        period=StatementPeriod(
            start=date(2026, 1, 1),
            end=date(2026, 1, 31),
        ),
    )

    assert transactions == ()
