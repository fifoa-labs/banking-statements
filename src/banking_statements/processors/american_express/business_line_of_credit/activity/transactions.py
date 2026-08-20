"""
src/banking_statements/processors/american_express/business_line_of_credit/activity/transactions.py

Transaction normalization for American Express
business line-of-credit activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import (
    TransactionDirection,
    TransactionEvent,
)
from banking_statements.domain.evidence import SourceEvidence

from .rows import AmericanExpressBusinessLineOfCreditActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import AmericanExpressBusinessLineOfCreditActivityRow


_PROCESSOR_NAME = "american_express.business_line_of_credit.v1"
_EVIDENCE_SECTION = "Transaction Summary"


def _parse_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Parse and validate a business line-of-credit transaction date."""
    try:
        transaction_date = datetime.strptime(  # noqa: DTZ007
            value,
            "%m/%d/%Y",
        ).date()
    except ValueError as exc:
        msg = (
            "Invalid American Express business line-of-credit transaction "
            f"calendar date: {value!r}."
        )
        raise ValueError(msg) from exc

    if not period.start <= transaction_date <= period.end:
        msg = (
            "American Express business line-of-credit transaction date is "
            f"outside the statement period: {value!r}."
        )
        raise ValueError(msg)

    return transaction_date


def parse_activity_transactions(
    rows: Sequence[AmericanExpressBusinessLineOfCreditActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize American Express business line-of-credit activity rows."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        if row.amount == Decimal("0"):
            msg = (
                "American Express business line-of-credit transaction amount "
                "must not be zero."
            )
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.section
            is AmericanExpressBusinessLineOfCreditActivitySection.CREDIT
            else TransactionDirection.DEBIT
        )

        transactions.append(
            TransactionEvent(
                date=_parse_transaction_date(
                    row.transaction_date,
                    period=period,
                ),
                amount=row.amount,
                direction=direction,
                description=row.description,
                evidence=SourceEvidence(
                    source=source,
                    section=_EVIDENCE_SECTION,
                    raw_text=row.raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
