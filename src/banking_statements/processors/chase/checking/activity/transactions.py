"""
src/banking_statements/processors/chase/checking/activity/transactions.py

Transaction normalization for Chase checking statements.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import (
    TransactionDirection,
    TransactionEvent,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod

    from .rows import ChaseCheckingActivityRow


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve an MM/DD transaction date against a statement period."""
    month_text, day_text = value.split("/")
    month = int(month_text)
    day = int(day_text)

    candidates: list[date] = []

    for year in range(period.start.year - 1, period.end.year + 2):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue

        if period.start <= candidate <= period.end:
            candidates.append(candidate)

    if len(candidates) != 1:
        msg = (
            "Chase checking transaction date could not be resolved uniquely: "
            f"{value}"
        )
        raise ValueError(msg)

    return candidates[0]


def parse_activity_transactions(
    rows: Sequence[ChaseCheckingActivityRow],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize Chase checking activity rows into transactions."""
    transactions: list[TransactionEvent] = []

    for row in rows:
        if row.amount == Decimal("0"):
            msg = "Chase checking transaction amount must not be zero."
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.amount > 0
            else TransactionDirection.DEBIT
        )

        transactions.append(
            TransactionEvent(
                date=_resolve_transaction_date(
                    row.transaction_date,
                    period=period,
                ),
                amount=abs(row.amount),
                direction=direction,
                description=row.description,
            )
        )

    return tuple(transactions)
