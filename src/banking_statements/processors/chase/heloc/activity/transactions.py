"""
src/banking_statements/processors/chase/heloc/activity/transactions.py

Transaction normalization for Chase home-equity line-of-credit activity.
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

    from .rows import ChaseHelocActivityRow


def _parse_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Parse and validate a full Chase HELOC activity date."""
    try:
        month_text, day_text, year_text = value.split("/")
        transaction_date = date(
            int(year_text),
            int(month_text),
            int(day_text),
        )
    except (TypeError, ValueError) as exc:
        msg = f"Invalid Chase HELOC transaction calendar date: {value!r}."
        raise ValueError(msg) from exc

    if not period.start <= transaction_date <= period.end:
        msg = (
            "Chase HELOC transaction date falls outside statement period: "
            f"{value!r}."
        )
        raise ValueError(msg)

    return transaction_date


def parse_activity_transactions(
    rows: Sequence[ChaseHelocActivityRow],
    *,
    period: StatementPeriod,
    finance_charges: Decimal,
) -> tuple[TransactionEvent, ...]:
    """Normalize Chase HELOC activity rows and gross cycle finance charges."""
    transactions: list[TransactionEvent] = []

    for row in rows:
        if row.amount is None and row.direction is None:
            continue

        if row.amount is None or row.direction is None:
            msg = (
                "Chase HELOC activity row has incomplete transaction "
                f"semantics: {row.description}"
            )
            raise ValueError(msg)

        if row.amount <= Decimal("0"):
            msg = "Chase HELOC transaction amount must be positive."
            raise ValueError(msg)

        transactions.append(
            TransactionEvent(
                date=_parse_transaction_date(
                    row.transaction_date,
                    period=period,
                ),
                amount=row.amount,
                direction=row.direction,
                description=row.description,
            )
        )

    if finance_charges < Decimal("0"):
        msg = "Chase HELOC finance charges must not be negative."
        raise ValueError(msg)

    if finance_charges > Decimal("0"):
        transactions.append(
            TransactionEvent(
                date=period.end,
                amount=finance_charges,
                direction=TransactionDirection.DEBIT,
                description="FINANCE CHARGES",
            )
        )

    return tuple(transactions)
