"""
src/banking_statements/processors/wellsfargo/checking/activity/transactions.py

Transaction normalization for supported Wells Fargo checking statements.
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

    from .rows import WellsFargoCheckingActivityRow


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve an M/D transaction date against a statement period."""
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
            "Wells Fargo checking transaction date could not be resolved "
            f"uniquely: {value}"
        )
        raise ValueError(msg)

    return candidates[0]


def _normalize_row(
    row: WellsFargoCheckingActivityRow,
    *,
    period: StatementPeriod,
) -> TransactionEvent:
    """Normalize one layout-aware Wells Fargo checking activity row."""
    if row.addition is not None and row.subtraction is not None:
        msg = (
            "Wells Fargo checking transaction row contains both an "
            f"addition and subtraction: {row.description}"
        )
        raise ValueError(msg)

    if row.addition is not None:
        amount = row.addition
        direction = TransactionDirection.CREDIT
    elif row.subtraction is not None:
        amount = row.subtraction
        direction = TransactionDirection.DEBIT
    else:
        msg = (
            "Wells Fargo checking transaction row contains no transaction "
            f"amount: {row.description}"
        )
        raise ValueError(msg)

    if amount == Decimal("0"):
        msg = "Wells Fargo checking transaction amount must not be zero."
        raise ValueError(msg)

    return TransactionEvent(
        date=_resolve_transaction_date(
            row.transaction_date,
            period=period,
        ),
        amount=amount,
        direction=direction,
        description=row.description,
    )


def parse_activity_transactions(
    rows: Sequence[WellsFargoCheckingActivityRow],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize layout-aware Wells Fargo checking activity rows."""
    return tuple(
        _normalize_row(
            row,
            period=period,
        )
        for row in rows
    )
