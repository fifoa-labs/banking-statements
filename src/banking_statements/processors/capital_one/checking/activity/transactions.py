"""
src/banking_statements/processors/capital_one/checking/activity/transactions.py

Transaction normalization for Capital One 360 checking activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, TransactionEvent
from banking_statements.domain.evidence import SourceEvidence

from .rows import CapitalOneCheckingActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import CapitalOneCheckingActivityRow


_PROCESSOR_NAME = "capital_one.checking.v1"


def _parse_month_day(value: str) -> tuple[int, int]:
    """Parse one Capital One checking abbreviated transaction date."""
    try:
        parsed = datetime.strptime(  # noqa: DTZ007
            f"{value} 2000",
            "%b %d %Y",
        )
    except ValueError as exc:
        msg = (
            "Invalid Capital One checking transaction calendar date: "
            f"{value!r}."
        )
        raise ValueError(msg) from exc

    return parsed.month, parsed.day


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve an abbreviated transaction date against the statement period."""
    month, day = _parse_month_day(value)
    candidates: list[date] = []

    for year in range(period.start.year - 1, period.end.year + 2):
        try:
            candidate = date(
                year,
                month,
                day,
            )
        except ValueError:
            continue

        if period.start <= candidate <= period.end:
            candidates.append(candidate)

    if len(candidates) != 1:
        msg = (
            "Capital One checking transaction date could not be resolved "
            f"uniquely: {value}"
        )
        raise ValueError(msg)

    return candidates[0]


def parse_activity_transactions(
    rows: Sequence[CapitalOneCheckingActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize Capital One checking activity rows."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        if row.amount == Decimal("0"):
            msg = "Capital One checking transaction amount must not be zero."
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.section is CapitalOneCheckingActivitySection.CREDIT
            else TransactionDirection.DEBIT
        )

        transactions.append(
            TransactionEvent(
                date=_resolve_transaction_date(
                    row.transaction_date,
                    period=period,
                ),
                amount=row.amount,
                direction=direction,
                description=row.description,
                evidence=SourceEvidence(
                    source=source,
                    section=row.section.value,
                    raw_text=row.raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
