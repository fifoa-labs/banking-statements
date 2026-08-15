"""
src/banking_statements/processors/chase/heloc/activity/rows.py

Transaction-activity row parsing for Chase home-equity
line-of-credit statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from banking_statements.domain import TransactionDirection, to_decimal

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class ChaseHelocActivityKind(StrEnum):
    """Supported Chase HELOC activity-row families."""

    INITIAL_FUNDING = "initial_funding"
    FEE_ASSESSED = "fee_assessed"
    FEE_PAID = "fee_paid"
    ADDITIONAL_PRINCIPAL_PAYMENT = "additional_principal_payment"
    PAYMENT_ALLOCATION = "payment_allocation"
    FUNDS_APPLIED = "funds_applied"
    FUNDS_REVERSED = "funds_reversed"
    BALANCE_ADVANCE = "balance_advance"


@dataclass(frozen=True, slots=True)
class ChaseHelocActivityRow:
    """One normalized raw Chase HELOC activity row."""

    transaction_date: str
    kind: ChaseHelocActivityKind
    description: str
    amount: Decimal | None
    direction: TransactionDirection | None


_ROW_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<body>.+)$",
)

_AMOUNT_PATTERN = re.compile(
    r"(?:\(\$?[\d,]+\.\d{2}\)|-?\$?[\d,]+\.\d{2})",
)

_ACTIVITY_START = "Transaction activity"
_ACTIVITY_END_MARKERS = (
    "Additional information",
    "Finance charge calculations",
)

_KINDS = (
    ("INITIAL FUNDING", ChaseHelocActivityKind.INITIAL_FUNDING),
    ("FIN CHARGE-ORIG FEE ASSES", ChaseHelocActivityKind.FEE_ASSESSED),
    ("FIN CHARGE-ORIG FEE PAID", ChaseHelocActivityKind.FEE_PAID),
    (
        "ADDITIONAL PRINCIPAL PYMT",
        ChaseHelocActivityKind.ADDITIONAL_PRINCIPAL_PAYMENT,
    ),
    ("PAYMENT", ChaseHelocActivityKind.PAYMENT_ALLOCATION),
    ("FUNDS APPLIED", ChaseHelocActivityKind.FUNDS_APPLIED),
    ("FUNDS REVERSED", ChaseHelocActivityKind.FUNDS_REVERSED),
    ("BALANCE ADVANCE", ChaseHelocActivityKind.BALANCE_ADVANCE),
)


def _extract_activity_text(text: str) -> str:
    """Return the Chase HELOC transaction-activity region."""
    start = text.rfind(_ACTIVITY_START)

    if start < 0:
        return ""

    body = text[start + len(_ACTIVITY_START) :]
    end_positions = tuple(
        position
        for marker in _ACTIVITY_END_MARKERS
        if (position := body.find(marker)) >= 0
    )

    if end_positions:
        body = body[: min(end_positions)]

    return body


def _kind_for_body(body: str) -> ChaseHelocActivityKind | None:
    """Return the recognized activity kind for one dated row body."""
    for prefix, kind in _KINDS:
        if body.startswith(prefix):
            return kind

    return None


def _amounts(body: str) -> tuple[Decimal, ...]:
    """Return all monetary values appearing in one activity row."""
    return tuple(
        to_decimal(match.group()) for match in _AMOUNT_PATTERN.finditer(body)
    )


def _nonzero_last(values: tuple[Decimal, ...], *, description: str) -> Decimal:
    """Return the rightmost non-zero monetary value."""
    for value in reversed(values):
        if value != Decimal("0"):
            return abs(value)

    msg = f"Chase HELOC activity row has no non-zero amount: {description}"
    raise ValueError(msg)


def _positive_first(
    values: tuple[Decimal, ...],
    *,
    description: str,
) -> Decimal:
    """Return the first positive monetary value."""
    if not values:
        msg = f"Chase HELOC activity row has no amount: {description}"
        raise ValueError(msg)

    value = values[0]

    if value <= Decimal("0"):
        msg = (
            "Chase HELOC activity row has invalid received amount: "
            f"{description}"
        )
        raise ValueError(msg)

    return value


def _normalize_amount(
    kind: ChaseHelocActivityKind,
    values: tuple[Decimal, ...],
    *,
    description: str,
) -> tuple[Decimal | None, TransactionDirection | None]:
    """Return the economic amount and direction for one Chase HELOC row."""
    if kind in {
        ChaseHelocActivityKind.PAYMENT_ALLOCATION,
        ChaseHelocActivityKind.FUNDS_REVERSED,
    }:
        return None, None

    if kind is ChaseHelocActivityKind.FUNDS_APPLIED:
        if not values:
            msg = f"Chase HELOC funds-applied row has no amount: {description}"
            raise ValueError(msg)

        received = values[0]

        if received == Decimal("0"):
            return None, None

        if received < Decimal("0"):
            msg = (
                "Chase HELOC funds-applied received amount must not be "
                f"negative: {description}"
            )
            raise ValueError(msg)

        return received, TransactionDirection.CREDIT

    if kind in {
        ChaseHelocActivityKind.ADDITIONAL_PRINCIPAL_PAYMENT,
        ChaseHelocActivityKind.FEE_PAID,
    }:
        return (
            _positive_first(values, description=description),
            TransactionDirection.CREDIT,
        )

    return (
        _nonzero_last(values, description=description),
        TransactionDirection.DEBIT,
    )


def parse_activity_rows(
    text: StatementText,
) -> tuple[ChaseHelocActivityRow, ...]:
    """Parse Chase HELOC transaction-activity rows."""
    rows: list[ChaseHelocActivityRow] = []

    transaction_date: str | None = None

    for raw_line in _extract_activity_text(text.text).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        match = _ROW_PATTERN.match(line)

        if match is not None:
            transaction_date = match.group("date")
            body = match.group("body")
        else:
            body = line

        kind = _kind_for_body(body)

        if kind is None:
            if match is not None:
                msg = f"Unrecognized Chase HELOC transaction row: {line}"
                raise ValueError(msg)
            continue

        if transaction_date is None:
            msg = (
                "Chase HELOC undated transaction row has no preceding "
                f"transaction date: {line}"
            )
            raise ValueError(msg)

        values = _amounts(body)
        amount, direction = _normalize_amount(
            kind,
            values,
            description=body,
        )

        description = re.sub(r"\s+Revolving\b", "", body)
        description = _AMOUNT_PATTERN.sub("", description)
        description = " ".join(description.split())

        rows.append(
            ChaseHelocActivityRow(
                transaction_date=transaction_date,
                kind=kind,
                description=description,
                amount=amount,
                direction=direction,
            )
        )

    return tuple(rows)
