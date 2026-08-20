"""
src/banking_statements/processors/american_express/personal_loan/activity/transactions.py

Transaction normalization for American Express personal-loan activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, TransactionEvent
from banking_statements.domain.evidence import SourceEvidence

from .rows import AmericanExpressPersonalLoanActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import AmericanExpressPersonalLoanActivityRow


_PROCESSOR_NAME = "american_express.personal_loan.v1"


def _parse_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Parse and validate a personal-loan activity date."""
    try:
        transaction_date = datetime.strptime(  # noqa: DTZ007
            value,
            "%m/%d/%y",
        ).date()
    except ValueError as exc:
        msg = (
            "Invalid American Express personal-loan transaction calendar "
            f"date: {value!r}."
        )
        raise ValueError(msg) from exc

    if not period.start <= transaction_date <= period.end:
        msg = (
            "American Express personal-loan transaction date is outside "
            f"the statement period: {value!r}."
        )
        raise ValueError(msg)

    return transaction_date


def parse_activity_transactions(
    rows: Sequence[AmericanExpressPersonalLoanActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize American Express personal-loan activity rows."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        if row.amount == Decimal("0"):
            msg = (
                "American Express personal-loan transaction amount "
                "must not be zero."
            )
            raise ValueError(msg)

        direction = (
            TransactionDirection.CREDIT
            if row.section
            is AmericanExpressPersonalLoanActivitySection.PAYMENT
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
                    section=row.section.value,
                    raw_text=row.raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
