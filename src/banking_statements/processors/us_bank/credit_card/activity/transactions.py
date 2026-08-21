"""
src/banking_statements/processors/us_bank/credit_card/activity/transactions.py

Transaction normalization for U.S. Bank credit-card activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, TransactionEvent
from banking_statements.domain.evidence import SourceEvidence

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import USBankCreditCardActivityRow


_PROCESSOR_NAME = "us_bank.credit_card.v1"


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve a U.S. Bank month/day value against the statement period."""
    try:
        parsed = datetime.strptime(  # noqa: DTZ007
            f"{value}/2000",
            "%m/%d/%Y",
        )
    except ValueError as exc:
        msg = f"Invalid U.S. Bank credit-card transaction date: {value!r}."
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
            "U.S. Bank credit-card transaction date could not be resolved "
            f"uniquely: {value}"
        )
        raise ValueError(msg)

    return candidates[0]


def parse_activity_transactions(
    rows: Sequence[USBankCreditCardActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize U.S. Bank credit-card activity rows into transactions."""
    transactions: list[TransactionEvent] = []

    for row in rows:
        if row.amount == Decimal("0"):
            continue

        sequence = len(transactions) + 1
        direction = (
            TransactionDirection.CREDIT
            if row.direction_is_credit
            else TransactionDirection.DEBIT
        )

        transactions.append(
            TransactionEvent(
                date=_resolve_transaction_date(
                    row.posting_date,
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
