"""
src/banking_statements/processors/penfed/heloc/activity/transactions.py

Transaction normalization for supported PenFed HELOC activity.
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

    from .rows import PenFedHelocActivityRow


_PROCESSOR_NAME = "penfed.heloc.v1"
_ACTIVITY_SECTION = "Transaction Activity"
_FINANCE_SECTION = "FINANCE CHARGES"


def _parse_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Parse and validate one PenFed HELOC activity date."""
    try:
        transaction_date = datetime.strptime(  # noqa: DTZ007
            value,
            "%m/%d/%y",
        ).date()
    except ValueError as exc:
        msg = f"Invalid PenFed HELOC transaction calendar date: {value!r}."
        raise ValueError(msg) from exc

    if not period.start <= transaction_date <= period.end:
        msg = (
            "PenFed HELOC transaction date falls outside statement period: "
            f"{value!r}."
        )
        raise ValueError(msg)

    return transaction_date


def parse_activity_transactions(
    rows: Sequence[PenFedHelocActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
    finance_charges: Decimal,
    finance_raw_text: str,
) -> tuple[TransactionEvent, ...]:
    """Normalize PenFed activity rows and the current-cycle finance charge."""
    transactions: list[TransactionEvent] = []
    sequence = 0

    for row in rows:
        if row.amount is None and row.direction is None:
            continue

        if row.amount is None or row.direction is None:
            msg = (
                "PenFed HELOC activity row has incomplete transaction "
                f"semantics: {row.description}"
            )
            raise ValueError(msg)

        if row.amount <= Decimal("0"):
            msg = "PenFed HELOC transaction amount must be positive."
            raise ValueError(msg)

        sequence += 1
        reported_date = row.effective_date or row.process_date

        transactions.append(
            TransactionEvent(
                date=_parse_transaction_date(
                    reported_date,
                    period=period,
                ),
                amount=row.amount,
                direction=row.direction,
                description=row.description,
                evidence=SourceEvidence(
                    source=source,
                    section=_ACTIVITY_SECTION,
                    raw_text=row.raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    if finance_charges < Decimal("0"):
        msg = "PenFed HELOC finance charges must not be negative."
        raise ValueError(msg)

    if finance_charges > Decimal("0"):
        sequence += 1
        transactions.append(
            TransactionEvent(
                date=period.end,
                amount=finance_charges,
                direction=TransactionDirection.DEBIT,
                description="FINANCE CHARGES",
                evidence=SourceEvidence(
                    source=source,
                    section=_FINANCE_SECTION,
                    raw_text=finance_raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
