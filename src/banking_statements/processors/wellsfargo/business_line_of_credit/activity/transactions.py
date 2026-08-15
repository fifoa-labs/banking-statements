"""
src/banking_statements/processors/wellsfargo/business_line_of_credit/activity/transactions.py

Transaction normalization for Wells Fargo business line-of-credit activity.
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

    from .rows import WellsFargoBusinessLineOfCreditActivityRow


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
            "Invalid Wells Fargo business line-of-credit transaction "
            f"calendar date: {value!r}."
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
            "Invalid Wells Fargo business line-of-credit transaction "
            f"calendar date: {value!r}."
        )
        raise ValueError(msg) from exc


def _normalize_row(
    row: WellsFargoBusinessLineOfCreditActivityRow,
    *,
    period: StatementPeriod,
) -> TransactionEvent:
    """Normalize one Wells Fargo business line-of-credit activity row."""
    if row.credit is not None and row.charge is not None:
        msg = (
            "Wells Fargo business line-of-credit row contains both "
            f"a credit and charge: {row.description}"
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
            "Wells Fargo business line-of-credit row contains no "
            f"transaction amount: {row.description}"
        )
        raise ValueError(msg)

    if amount == Decimal("0"):
        msg = (
            "Wells Fargo business line-of-credit transaction amount "
            "must not be zero."
        )
        raise ValueError(msg)

    transaction_date = (
        period.end
        if row.transaction_date is None
        else _resolve_transaction_date(
            row.transaction_date,
            period=period,
        )
    )

    return TransactionEvent(
        date=transaction_date,
        amount=abs(amount),
        direction=direction,
        description=row.description,
    )


def parse_activity_transactions(
    rows: Sequence[WellsFargoBusinessLineOfCreditActivityRow],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize Wells Fargo business line-of-credit activity rows."""
    return tuple(
        _normalize_row(
            row,
            period=period,
        )
        for row in rows
    )
