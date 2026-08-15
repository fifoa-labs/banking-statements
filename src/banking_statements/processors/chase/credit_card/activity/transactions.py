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

if TYPE_CHECKING:
    from .rows import ActivityRow

_DATE_PATTERN = re.compile(
    r"^(?P<month>\d{2})/(?P<day>\d{2})$",
)


def _resolve_transaction_date(
    date_text: str,
    period: StatementPeriod,
) -> date:
    """Resolve a Chase month/day value using the statement period."""
    match = _DATE_PATTERN.match(date_text)

    if match is None:
        msg = f"Invalid Chase transaction date: {date_text!r}."
        raise ValueError(msg)

    month = int(match.group("month"))
    day = int(match.group("day"))

    candidates: list[date] = []

    for year in range(
        period.start.year,
        period.end.year + 2,
    ):
        try:
            candidates.append(
                date(
                    year,
                    month,
                    day,
                )
            )
        except ValueError:
            continue

    if not candidates:
        msg = f"Invalid Chase transaction calendar date: {date_text!r}."
        raise ValueError(msg)

    def distance_from_period(candidate: date) -> int:
        if candidate < period.start:
            return (period.start - candidate).days

        if candidate > period.end:
            return (candidate - period.end).days

        return 0

    minimum_distance = min(
        distance_from_period(candidate) for candidate in candidates
    )

    nearest = tuple(
        candidate
        for candidate in candidates
        if distance_from_period(candidate) == minimum_distance
    )

    if len(nearest) > 1:
        msg = (
            f"Transaction date {date_text!r} is ambiguous for "
            f"statement period {period.start.isoformat()}.."
            f"{period.end.isoformat()}."
        )
        raise ValueError(msg)

    return nearest[0]


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
            amount=to_decimal(row.amount_text),
            direction=TransactionDirection.DEBIT,
            description=row.description,
        )
        for row in rows
    )
