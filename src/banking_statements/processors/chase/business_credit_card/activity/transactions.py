"""
src/banking_statements/processors/chase/business_credit_card/activity/
transactions.py

Normalize Chase business credit-card activity rows into transactions.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, TransactionEvent
from banking_statements.domain.evidence import SourceEvidence

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import ChaseBusinessCreditCardActivityRow


_PROCESSOR_NAME = "chase.business_credit_card.v1"
_ACTIVITY_SECTION = "Account Activity"
_DATE_PATTERN = re.compile(
    r"^(?P<month>\d{2})/(?P<day>\d{2})$",
)


def _resolve_transaction_date(
    date_text: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve a Chase month/day value relative to statement closing date."""
    match = _DATE_PATTERN.fullmatch(date_text)

    if match is None:
        msg = f"Invalid Chase business credit-card date: {date_text!r}."
        raise ValueError(msg)

    month = int(match.group("month"))
    day = int(match.group("day"))

    try:
        candidate = date(period.end.year, month, day)
    except ValueError as exc:
        msg = (
            f"Invalid Chase business credit-card calendar date: {date_text!r}."
        )
        raise ValueError(msg) from exc

    if candidate <= period.end:
        return candidate

    try:
        return date(period.end.year - 1, month, day)
    except ValueError as exc:
        msg = (
            f"Invalid Chase business credit-card calendar date: {date_text!r}."
        )
        raise ValueError(msg) from exc


def parse_activity_transactions(
    rows: Sequence[ChaseBusinessCreditCardActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize signed Chase business-card activity rows."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        if row.amount == Decimal("0"):
            msg = (
                "Chase business credit-card transaction amount must not "
                "be zero."
            )
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.amount < Decimal("0")
            else TransactionDirection.DEBIT
        )

        raw_text = "\n".join((row.raw_text, *row.continuation_lines))

        transactions.append(
            TransactionEvent(
                date=_resolve_transaction_date(
                    row.date_text,
                    period=period,
                ),
                amount=abs(row.amount),
                direction=direction,
                description=row.description,
                evidence=SourceEvidence(
                    source=source,
                    page=row.page,
                    section=_ACTIVITY_SECTION,
                    raw_text=raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
