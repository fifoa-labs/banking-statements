"""
src/banking_statements/processors/american_express/credit_card/activity/transactions.py

Transaction normalization for American Express credit-card activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import (
    TransactionDirection,
    TransactionEvent,
    to_decimal,
)
from banking_statements.domain.evidence import SourceEvidence

from .rows import AmericanExpressCreditCardActivitySection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import StatementPeriod, StatementSource

    from .rows import AmericanExpressCreditCardActivityRow


_PROCESSOR_NAME = "american_express.credit_card.v1"

_SECTION_LABELS = {
    AmericanExpressCreditCardActivitySection.PAYMENTS: "Payments",
    AmericanExpressCreditCardActivitySection.CREDITS: "Credits",
    AmericanExpressCreditCardActivitySection.CHARGES: "New Charges",
    AmericanExpressCreditCardActivitySection.FEES: "Fees",
    AmericanExpressCreditCardActivitySection.INTEREST: "Interest Charged",
}


def _parse_transaction_date(
    value: str,
    *,
    period: StatementPeriod,
) -> date:
    """Parse and validate a full American Express transaction date."""
    try:
        transaction_date = datetime.strptime(  # noqa: DTZ007
            value,
            "%m/%d/%y",
        ).date()
    except ValueError as exc:
        msg = (
            "Invalid American Express credit-card transaction calendar date: "
            f"{value!r}."
        )
        raise ValueError(msg) from exc

    if transaction_date > period.end:
        msg = (
            "American Express credit-card transaction date is after the "
            f"statement closing date: {value!r}."
        )
        raise ValueError(msg)

    return transaction_date


def _parse_amount(value: str) -> Decimal:
    """Parse an American Express activity amount including CR notation."""
    stripped = value.strip()
    is_credit = stripped.endswith(" CR")

    if is_credit:
        stripped = stripped[:-3].rstrip()

    if stripped.startswith("+"):
        stripped = stripped[1:]

    amount = to_decimal(stripped)

    if is_credit:
        return -abs(amount)

    return amount


def _transaction_direction(
    section: AmericanExpressCreditCardActivitySection,
    *,
    amount: Decimal,
) -> TransactionDirection:
    """Return economic direction for an American Express activity row."""
    if section in {
        AmericanExpressCreditCardActivitySection.PAYMENTS,
        AmericanExpressCreditCardActivitySection.CREDITS,
    }:
        return TransactionDirection.CREDIT

    if amount < Decimal("0"):
        return TransactionDirection.CREDIT

    return TransactionDirection.DEBIT


def _description(row: AmericanExpressCreditCardActivityRow) -> str:
    """Return the complete logical transaction description."""
    return " ".join(
        (
            row.description,
            *row.continuation_lines,
        )
    ).strip()


def _evidence_section(
    row: AmericanExpressCreditCardActivityRow,
) -> str:
    """Return useful source-section context for an activity row."""
    if row.card_ending is not None:
        return f"Card Ending {row.card_ending}"

    return _SECTION_LABELS[row.section]


def parse_activity_transactions(
    rows: Sequence[AmericanExpressCreditCardActivityRow],
    *,
    period: StatementPeriod,
    source: StatementSource,
) -> tuple[TransactionEvent, ...]:
    """Normalize American Express credit-card activity rows."""
    transactions: list[TransactionEvent] = []

    for sequence, row in enumerate(rows, start=1):
        amount = _parse_amount(row.amount_text)

        if amount == Decimal("0"):
            msg = (
                "American Express credit-card transaction amount must not be "
                "zero."
            )
            raise ValueError(msg)

        transaction_date = (
            period.end
            if row.date_text is None
            else _parse_transaction_date(
                row.date_text,
                period=period,
            )
        )

        transactions.append(
            TransactionEvent(
                date=transaction_date,
                amount=abs(amount),
                direction=_transaction_direction(
                    row.section,
                    amount=amount,
                ),
                description=_description(row),
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
