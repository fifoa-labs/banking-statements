"""
src/banking_statements/processors/capital_one/business_credit_card/activity/
transactions.py

Transaction normalization for Capital One business credit-card activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, TransactionEvent
from banking_statements.domain.evidence import SourceEvidence

from .rows import CapitalOneBusinessCreditCardActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import CapitalOneBusinessCreditCardActivityRow


_PROCESSOR_NAME = "capital_one.business_credit_card.v1"


def _parse_month_day(value: str) -> tuple[int, int]:
    """Parse one Capital One abbreviated month/day value."""
    try:
        parsed = datetime.strptime(  # noqa: DTZ007
            f"{value} 2000",
            "%b %d %Y",
        )
    except ValueError as exc:
        msg = (
            "Invalid Capital One business credit-card transaction date: "
            f"{value!r}."
        )
        raise ValueError(msg) from exc

    return parsed.month, parsed.day


def _resolve_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Resolve Capital One activity relative to the statement closing date."""
    month, day = _parse_month_day(value)

    try:
        current_year_candidate = date(
            period.end.year,
            month,
            day,
        )
    except ValueError:
        current_year_candidate = None

    if (
        current_year_candidate is not None
        and current_year_candidate <= period.end
    ):
        return current_year_candidate

    try:
        return date(
            period.end.year - 1,
            month,
            day,
        )
    except ValueError as exc:
        msg = (
            "Invalid Capital One business credit-card transaction calendar "
            f"date: {value!r}."
        )
        raise ValueError(msg) from exc


def _transaction_direction(
    section: CapitalOneBusinessCreditCardActivitySection,
) -> TransactionDirection:
    """Return economic direction for one Capital One activity family."""
    if section is CapitalOneBusinessCreditCardActivitySection.CREDIT:
        return TransactionDirection.CREDIT

    return TransactionDirection.DEBIT


def _evidence_section(row: CapitalOneBusinessCreditCardActivityRow) -> str:
    """Return useful source-section context for one business-card row."""
    if row.card_last4 is not None:
        return f"{row.section.value}: card ending {row.card_last4}"

    return row.section.value


def parse_activity_transactions(
    rows: Sequence[CapitalOneBusinessCreditCardActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize Capital One business credit-card activity rows."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        if row.amount == Decimal("0"):
            msg = (
                "Capital One business credit-card transaction amount must "
                "not be zero."
            )
            raise ValueError(msg)

        reported_date = row.posting_date or row.transaction_date
        transaction_date = (
            period.end
            if reported_date is None
            else _resolve_transaction_date(
                reported_date,
                period=period,
            )
        )

        transactions.append(
            TransactionEvent(
                date=transaction_date,
                amount=row.amount,
                direction=_transaction_direction(row.section),
                description=row.description,
                evidence=SourceEvidence(
                    source=source,
                    section=_evidence_section(row),
                    raw_text=row.raw_text,
                    processor=_PROCESSOR_NAME,
                    sequence=sequence,
                ),
            )
        )

    return tuple(transactions)
