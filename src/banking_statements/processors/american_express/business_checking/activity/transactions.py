"""
src/banking_statements/processors/american_express/business_checking/activity/transactions.py

Transaction normalization for American Express business-checking statements.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import (
    TransactionDirection,
    TransactionEvent,
)

from .rows import AmericanExpressBusinessCheckingActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod

    from .rows import AmericanExpressBusinessCheckingActivityRow


def parse_activity_transactions(
    rows: Sequence[AmericanExpressBusinessCheckingActivityRow],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize American Express business-checking activity rows."""
    transactions: list[TransactionEvent] = []

    for row in rows:
        if row.amount == Decimal("0"):
            msg = (
                "American Express business-checking transaction amount must "
                "not be zero."
            )
            raise ValueError(msg)

        transaction_date = datetime.strptime(  # noqa: DTZ007
            row.transaction_date,
            "%m/%d/%Y",
        ).date()

        earliest_allowed_date = period.start - timedelta(days=1)

        if not earliest_allowed_date <= transaction_date <= period.end:
            msg = (
                "American Express business-checking transaction date is "
                f"outside the supported statement boundary: {row.transaction_date}"  # noqa: E501
            )
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.section
            is AmericanExpressBusinessCheckingActivitySection.CREDIT
            else TransactionDirection.DEBIT
        )

        transactions.append(
            TransactionEvent(
                date=transaction_date,
                amount=row.amount,
                direction=direction,
                description=row.description,
            )
        )

    return tuple(transactions)
