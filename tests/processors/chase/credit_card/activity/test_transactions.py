"""
tests/processors/chase/credit_card/activity/test_transactions.py

Tests for Chase credit-card activity transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
)
from banking_statements.processors.chase.credit_card.activity import (
    ActivityRow,
    ActivitySection,
)
from banking_statements.processors.chase.credit_card.activity.transactions import (  # noqa: E501
    parse_activity_transactions,
)


def test_parse_purchase_transaction() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PURCHASE,
                date_text="03/30",
                description="EXAMPLE MARKETPLACE",
                amount_text="18.45",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 3, 12),
            end=date(2026, 4, 11),
        ),
    )

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.date == date(2026, 3, 30)
    assert transaction.amount == Decimal("18.45")
    assert transaction.direction is TransactionDirection.DEBIT
    assert transaction.description == "EXAMPLE MARKETPLACE"


def test_parse_fee_transaction() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.FEES_CHARGED,
                date_text="07/01",
                description="ANNUAL MEMBERSHIP FEE",
                amount_text="75.00",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 6, 4),
            end=date(2026, 7, 3),
        ),
    )

    transaction = transactions[0]

    assert transaction.date == date(2026, 7, 1)
    assert transaction.amount == Decimal("75.00")
    assert transaction.direction is TransactionDirection.DEBIT
    assert transaction.description == "ANNUAL MEMBERSHIP FEE"


def test_parse_payment_and_credit_transaction() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
                date_text="07/14",
                description="ONLINE PAYMENT",
                amount_text="-245.60",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 7, 4),
            end=date(2026, 8, 3),
        ),
    )

    transaction = transactions[0]

    assert transaction.date == date(2026, 7, 14)
    assert transaction.amount == Decimal("245.60")
    assert transaction.direction is TransactionDirection.CREDIT
    assert transaction.description == "ONLINE PAYMENT"


def test_parse_multiple_transactions_preserves_order() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
                date_text="06/10",
                description="ONLINE PAYMENT",
                amount_text="-80.00",
            ),
            ActivityRow(
                section=ActivitySection.PURCHASE,
                date_text="06/17",
                description="EXAMPLE STORE",
                amount_text="24.35",
            ),
            ActivityRow(
                section=ActivitySection.FEES_CHARGED,
                date_text="07/01",
                description="ANNUAL MEMBERSHIP FEE",
                amount_text="75.00",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 6, 4),
            end=date(2026, 7, 3),
        ),
    )

    assert [transaction.description for transaction in transactions] == [
        "ONLINE PAYMENT",
        "EXAMPLE STORE",
        "ANNUAL MEMBERSHIP FEE",
    ]
    assert [transaction.direction for transaction in transactions] == [
        TransactionDirection.CREDIT,
        TransactionDirection.DEBIT,
        TransactionDirection.DEBIT,
    ]


def test_parse_activity_transactions_handles_empty_rows() -> None:
    transactions = parse_activity_transactions(
        (),
        period=StatementPeriod(
            start=date(2026, 1, 1),
            end=date(2026, 1, 31),
        ),
    )

    assert transactions == ()


def test_transaction_date_resolves_across_year_boundary() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PURCHASE,
                date_text="12/20",
                description="DECEMBER PURCHASE",
                amount_text="14.00",
            ),
            ActivityRow(
                section=ActivitySection.PURCHASE,
                date_text="01/03",
                description="JANUARY PURCHASE",
                amount_text="22.00",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 12, 15),
            end=date(2027, 1, 14),
        ),
    )

    assert transactions[0].date == date(2026, 12, 20)
    assert transactions[1].date == date(2027, 1, 3)


def test_transaction_date_can_precede_statement_period() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PURCHASE,
                date_text="05/01",
                description="EXAMPLE CAFE",
                amount_text="42.75",
            ),
        ),
        period=StatementPeriod(
            start=date(2025, 5, 4),
            end=date(2025, 6, 3),
        ),
    )

    assert transactions[0].date == date(2025, 5, 1)


def test_transaction_date_rejects_invalid_calendar_date() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase transaction calendar date",
    ):
        parse_activity_transactions(
            (
                ActivityRow(
                    section=ActivitySection.PURCHASE,
                    date_text="02/29",
                    description="INVALID DATE",
                    amount_text="12.00",
                ),
            ),
            period=StatementPeriod(
                start=date(2025, 2, 1),
                end=date(2025, 3, 1),
            ),
        )


def test_transaction_date_rejects_invalid_format() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase transaction date",
    ):
        parse_activity_transactions(
            (
                ActivityRow(
                    section=ActivitySection.PURCHASE,
                    date_text="June 17",
                    description="EXAMPLE MERCHANT",
                    amount_text="12.00",
                ),
            ),
            period=StatementPeriod(
                start=date(2026, 6, 1),
                end=date(2026, 6, 30),
            ),
        )


def test_transaction_date_rejects_impossible_calendar_date() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase transaction calendar date",
    ):
        parse_activity_transactions(
            (
                ActivityRow(
                    section=ActivitySection.PURCHASE,
                    date_text="02/30",
                    description="INVALID DATE",
                    amount_text="12.00",
                ),
            ),
            period=StatementPeriod(
                start=date(2026, 2, 1),
                end=date(2026, 3, 1),
            ),
        )


def test_transaction_date_supports_leap_day() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PURCHASE,
                date_text="02/29",
                description="LEAP DAY PURCHASE",
                amount_text="16.00",
            ),
        ),
        period=StatementPeriod(
            start=date(2024, 2, 1),
            end=date(2024, 3, 1),
        ),
    )

    assert transactions[0].date == date(2024, 2, 29)


def test_parse_interest_charge_transaction() -> None:
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.INTEREST_CHARGED,
                date_text="05/03",
                description="PURCHASE INTEREST CHARGE",
                amount_text="6.40",
            ),
        ),
        period=StatementPeriod(
            start=date(2026, 4, 4),
            end=date(2026, 5, 3),
        ),
    )

    transaction = transactions[0]

    assert transaction.date == date(2026, 5, 3)
    assert transaction.amount == Decimal("6.40")
    assert transaction.direction is TransactionDirection.DEBIT
    assert transaction.description == "PURCHASE INTEREST CHARGE"


def test_transaction_date_uses_prior_year_when_month_day_is_after_closing() -> (  # noqa: E501
    None
):
    transactions = parse_activity_transactions(
        (
            ActivityRow(
                section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
                date_text="12/24",
                description="INTEREST CHARGE REVERSAL",
                amount_text="-84.15",
            ),
        ),
        period=StatementPeriod(
            start=date(2024, 2, 25),
            end=date(2024, 3, 24),
        ),
    )

    assert transactions[0].date == date(2023, 12, 24)


def test_transaction_date_rejects_invalid_prior_year_calendar_date() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Chase transaction calendar date",
    ):
        parse_activity_transactions(
            (
                ActivityRow(
                    section=ActivitySection.PURCHASE,
                    date_text="02/29",
                    description="INVALID PRIOR YEAR DATE",
                    amount_text="12.00",
                ),
            ),
            period=StatementPeriod(
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
            ),
        )
