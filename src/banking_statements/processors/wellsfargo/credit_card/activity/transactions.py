"""
src/banking_statements/processors/wellsfargo/credit_card/activity/transactions.py

Transaction normalization for Wells Fargo credit-card activity.
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

    from .rows import WellsFargoCreditCardActivityRow


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve an MM/DD transaction date relative to statement closing date."""
    month_text, day_text = value.split("/")
    month = int(month_text)
    day = int(day_text)

    try:
        candidate = date(
            period.end.year,
            month,
            day,
        )
    except ValueError as exc:
        msg = (
            "Invalid Wells Fargo credit-card transaction calendar date: "
            f"{value!r}."
        )
        raise ValueError(msg) from exc

    if candidate <= period.end:
        return candidate

    try:
        return date(
            period.end.year - 1,
            month,
            day,
        )
    except ValueError as exc:
        msg = (
            "Invalid Wells Fargo credit-card transaction calendar date: "
            f"{value!r}."
        )
        raise ValueError(msg) from exc


def _normalize_row(
    row: WellsFargoCreditCardActivityRow,
    *,
    period: StatementPeriod,
) -> TransactionEvent:
    """Normalize one Wells Fargo credit-card activity row."""
    if row.credit is not None and row.charge is not None:
        msg = (
            "Wells Fargo credit-card row contains both a credit and charge: "
            f"{row.description}"
        )
        raise ValueError(msg)

    if row.credit is not None:
        amount = row.credit
        direction = TransactionDirection.CREDIT
    elif row.charge is not None:
        amount = row.charge
        direction = TransactionDirection.DEBIT
    else:
        msg = (
            "Wells Fargo credit-card row contains no transaction amount: "
            f"{row.description}"
        )
        raise ValueError(msg)

    if amount == Decimal("0"):
        msg = "Wells Fargo credit-card transaction amount must not be zero."
        raise ValueError(msg)

    return TransactionEvent(
        date=_resolve_transaction_date(
            row.transaction_date,
            period=period,
        ),
        amount=abs(amount),
        direction=direction,
        description=row.description,
    )


def parse_activity_transactions(
    rows: Sequence[WellsFargoCreditCardActivityRow],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize Wells Fargo credit-card activity rows."""
    return tuple(
        _normalize_row(
            row,
            period=period,
        )
        for row in rows
    )
