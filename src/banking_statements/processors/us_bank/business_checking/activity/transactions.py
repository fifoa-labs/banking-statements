"""
src/banking_statements/processors/us_bank/business_checking/activity/
transactions.py

Transaction normalization for U.S. Bank business-checking activity.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, TransactionEvent
from banking_statements.domain.evidence import SourceEvidence

from .rows import USBankBusinessCheckingActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import USBankBusinessCheckingActivityRow


_PROCESSOR_NAME = "us_bank.business_checking.v1"


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve a U.S. Bank abbreviated checking date against the period."""
    normalized = " ".join(value.split())
    normalized = re.sub(r"^([A-Z][a-z]{2})(\d)", r"\1 \2", normalized)
    try:
        parsed = datetime.strptime(  # noqa: DTZ007
            f"{normalized} 2000",
            "%b %d %Y",
        )
    except ValueError as exc:
        msg = (
            "Invalid U.S. Bank business-checking transaction calendar date: "
            f"{value!r}."
        )
        raise ValueError(msg) from exc

    candidates: list[date] = []
    for year in range(period.start.year - 1, period.end.year + 2):
        try:
            candidate = date(year, parsed.month, parsed.day)
        except ValueError:
            continue

        if period.start <= candidate <= period.end:
            candidates.append(candidate)

    if len(candidates) != 1:
        msg = (
            "U.S. Bank business-checking transaction date could not be "
            f"resolved uniquely: {value}"
        )
        raise ValueError(msg)

    return candidates[0]


def parse_activity_transactions(
    rows: Sequence[USBankBusinessCheckingActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize U.S. Bank business-checking rows into transactions."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        if row.amount == Decimal("0"):
            msg = (
                "U.S. Bank business-checking transaction amount must not "
                "be zero."
            )
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.section is USBankBusinessCheckingActivitySection.CREDIT
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
                    page=row.page,
                    section=row.section.value,
                    raw_text=row.raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
