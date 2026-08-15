"""
src/banking_statements/processors/chase/credit_card/activity/transactions.py

Normalize Chase credit-card activity rows into banking transactions.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

from banking_statements.domain import (
    StatementPeriod,
    TransactionDirection,
    TransactionEvent,
    to_decimal,
)

from .rows import ActivitySection

if TYPE_CHECKING:
    from .rows import ActivityRow

_DATE_PATTERN = re.compile(
    r"^(?P<month>\d{2})/(?P<day>\d{2})$",
)


def _resolve_transaction_date(
    date_text: str,
    period: StatementPeriod,
) -> date:
    """Resolve a Chase month/day value relative to statement closing date."""
    match = _DATE_PATTERN.match(date_text)

    if match is None:
        msg = f"Invalid Chase transaction date: {date_text!r}."
        raise ValueError(msg)

    month = int(match.group("month"))
    day = int(match.group("day"))

    try:
        candidate = date(
            period.end.year,
            month,
            day,
        )
    except ValueError as exc:
        msg = f"Invalid Chase transaction calendar date: {date_text!r}."
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
        msg = f"Invalid Chase transaction calendar date: {date_text!r}."
        raise ValueError(msg) from exc


def _transaction_direction(
    section: ActivitySection,
) -> TransactionDirection:
    """Return the economic direction for a Chase activity section."""
    if section is ActivitySection.PAYMENTS_AND_OTHER_CREDITS:
        return TransactionDirection.CREDIT

    return TransactionDirection.DEBIT


def parse_activity_transactions(
    rows: tuple[ActivityRow, ...],
    *,
    period: StatementPeriod,
) -> tuple[TransactionEvent, ...]:
    """Normalize Chase credit-card activity rows."""
    return tuple(
        TransactionEvent(
            date=_resolve_transaction_date(
                row.date_text,
                period,
            ),
            amount=abs(to_decimal(row.amount_text)),
            direction=_transaction_direction(row.section),
            description=row.description,
        )
        for row in rows
    )
