"""
src/banking_statements/processors/wellsfargo/business_checking/activity/transactions.py

Transaction normalization for Wells Fargo business checking activity.
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

    from .rows import WellsFargoBusinessCheckingActivityRow


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
            "Wells Fargo business checking transaction date could not be "
            f"resolved uniquely: {value}"
        )
        raise ValueError(msg)

    return candidates[0]


def _normalize_row(
    row: WellsFargoBusinessCheckingActivityRow,
    *,
    period: StatementPeriod,
) -> TransactionEvent:
    """Normalize one Wells Fargo business checking activity row."""
    if row.credit is not None and row.debit is not None:
        msg = (
            "Wells Fargo business checking row contains both credit and debit: "  # noqa: E501
            f"{row.description}"
        )
        raise ValueError(msg)

    if row.credit is not None:
        amount = row.credit
        direction = TransactionDirection.CREDIT
    elif row.debit is not None:
        amount = row.debit
        direction = TransactionDirection.DEBIT
    else:
        msg = (
            "Wells Fargo business checking row contains no transaction amount: "  # noqa: E501
            f"{row.description}"
        )
        raise ValueError(msg)

    if amount == Decimal("0"):
        msg = "Wells Fargo business checking transaction amount must not be zero."  # noqa: E501
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
    rows: Sequence[WellsFargoBusinessCheckingActivityRow],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize Wells Fargo business checking activity rows."""
    return tuple(
        _normalize_row(
            row,
            period=period,
        )
        for row in rows
    )
