"""
src/banking_statements/processors/penfed/heloc/activity/rows.py

Logical transaction-activity row parsing for supported PenFed HELOC statements.
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


class PenFedHelocActivityKind(StrEnum):
    """Supported PenFed HELOC transaction-activity families."""

    PRINCIPAL_CURTAILMENT = "principal_curtailment"
    PAYMENT_RECEIVED = "payment_received"
    RETURNED_CHECK_FEE = "returned_check_fee"
    NSF_RETURNED_CHECK_REVERSAL = "nsf_returned_check_reversal"


@dataclass(frozen=True, slots=True)
class PenFedHelocActivityRow:
    """One reconstructed PenFed HELOC transaction-activity row."""

    process_date: str
    effective_date: str | None
    kind: PenFedHelocActivityKind
    description: str
    total_amount: Decimal
    principal_applied: Decimal
    interest: Decimal
    escrow: Decimal
    fees: Decimal
    other: Decimal
    amount: Decimal | None
    direction: TransactionDirection | None
    raw_text: str


_AMOUNT = r"(?:\(\$?[\d,]+\.\d{2}\)|-?\$?[\d,]+\.\d{2})"

_ROW_PATTERN = re.compile(
    rf"^(?P<process>\d{{2}}/\d{{2}}/\d{{2}})\s+"
    rf"(?:(?P<effective>\d{{2}}/\d{{2}}/\d{{2}})\s+)?"
    rf"(?P<description>.+?)\s+"
    rf"(?P<total>{_AMOUNT})\s+"
    rf"(?P<principal>{_AMOUNT})\s+"
    rf"(?P<interest>{_AMOUNT})\s+"
    rf"(?P<escrow>{_AMOUNT})\s+"
    rf"(?P<fees>{_AMOUNT})\s+"
    rf"(?P<other>{_AMOUNT})$",
)

_DATED_PREFIX_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{2}\b")

_ACTIVITY_START_PATTERN = re.compile(
    r"^Transaction Activity \(\d{2}/\d{2}/\d{2}\s+through\s+"
    r"\d{2}/\d{2}/\d{2}\)$",
)

_DESCRIPTION_KINDS = {
    "PRINCIPAL CURTAILMENT PAYMENT": PenFedHelocActivityKind.PRINCIPAL_CURTAILMENT,  # noqa: E501
    "PAYMENT RECEIVED (NON-LOCKBOX)": PenFedHelocActivityKind.PAYMENT_RECEIVED,
    "PAYMENT RECEIVED": PenFedHelocActivityKind.PAYMENT_RECEIVED,
    "RETURNED CHECK FEE": PenFedHelocActivityKind.RETURNED_CHECK_FEE,
    "NSF/RETURNED CHECK REVERSAL": (
        PenFedHelocActivityKind.NSF_RETURNED_CHECK_REVERSAL
    ),
}

_ACTIVITY_STOP_MARKERS = frozenset({"FINANCE CHARGES"})


def _non_total_values(
    *,
    principal: Decimal,
    interest: Decimal,
    escrow: Decimal,
    fees: Decimal,
    other: Decimal,
) -> tuple[Decimal, ...]:
    """Return the PenFed allocation columns after Total Amount."""
    return (principal, interest, escrow, fees, other)


def _principal_curtailment_semantics(
    *,
    total: Decimal,
    principal: Decimal,
    allocations: tuple[Decimal, ...],
    raw_text: str,
) -> tuple[Decimal, TransactionDirection]:
    """Validate and normalize one principal-curtailment payment."""
    if total <= Decimal("0") or principal != total or any(allocations[1:]):
        msg = f"Invalid PenFed HELOC principal curtailment row: {raw_text}"
        raise ValueError(msg)

    return total, TransactionDirection.CREDIT


def _payment_received_semantics(
    *,
    total: Decimal,
    allocations: tuple[Decimal, ...],
    raw_text: str,
) -> tuple[Decimal | None, TransactionDirection | None]:
    """Normalize received-payment totals while skipping allocation detail."""
    if total > Decimal("0"):
        if any(allocations):
            msg = f"Invalid PenFed HELOC payment received row: {raw_text}"
            raise ValueError(msg)

        return total, TransactionDirection.CREDIT

    if total < Decimal("0"):
        msg = f"Invalid PenFed HELOC payment received row: {raw_text}"
        raise ValueError(msg)

    if not any(allocations) or any(
        value < Decimal("0") for value in allocations
    ):
        msg = f"Invalid PenFed HELOC payment allocation row: {raw_text}"
        raise ValueError(msg)

    return None, None


def _returned_check_fee_semantics(  # noqa: PLR0913
    *,
    total: Decimal,
    principal: Decimal,
    interest: Decimal,
    escrow: Decimal,
    fees: Decimal,
    other: Decimal,
    raw_text: str,
) -> tuple[Decimal, TransactionDirection]:
    """Normalize one returned-check fee or matching fee reversal."""
    if (
        total != Decimal("0")
        or any((principal, interest, escrow, other))
        or fees == Decimal("0")
    ):
        msg = f"Invalid PenFed HELOC returned-check fee row: {raw_text}"
        raise ValueError(msg)

    direction = (
        TransactionDirection.DEBIT
        if fees > Decimal("0")
        else TransactionDirection.CREDIT
    )

    return abs(fees), direction


def _reversal_semantics(
    *,
    total: Decimal,
    allocations: tuple[Decimal, ...],
    raw_text: str,
) -> tuple[Decimal, TransactionDirection]:
    """Normalize an NSF/returned-check reversal of a prior credit."""
    nonzero = tuple(value for value in allocations if value != Decimal("0"))

    if (
        total != Decimal("0")
        or not nonzero
        or any(value > Decimal("0") for value in nonzero)
    ):
        msg = f"Invalid PenFed HELOC NSF reversal row: {raw_text}"
        raise ValueError(msg)

    return (
        sum((-value for value in nonzero), start=Decimal("0")),
        TransactionDirection.DEBIT,
    )


def _economic_semantics(  # noqa: PLR0913
    kind: PenFedHelocActivityKind,
    *,
    total: Decimal,
    principal: Decimal,
    interest: Decimal,
    escrow: Decimal,
    fees: Decimal,
    other: Decimal,
    raw_text: str,
) -> tuple[Decimal | None, TransactionDirection | None]:
    """Return economic amount and direction for one proven PenFed row."""
    allocations = _non_total_values(
        principal=principal,
        interest=interest,
        escrow=escrow,
        fees=fees,
        other=other,
    )

    if kind is PenFedHelocActivityKind.PRINCIPAL_CURTAILMENT:
        return _principal_curtailment_semantics(
            total=total,
            principal=principal,
            allocations=allocations,
            raw_text=raw_text,
        )

    if kind is PenFedHelocActivityKind.PAYMENT_RECEIVED:
        return _payment_received_semantics(
            total=total,
            allocations=allocations,
            raw_text=raw_text,
        )

    if kind is PenFedHelocActivityKind.RETURNED_CHECK_FEE:
        return _returned_check_fee_semantics(
            total=total,
            principal=principal,
            interest=interest,
            escrow=escrow,
            fees=fees,
            other=other,
            raw_text=raw_text,
        )

    return _reversal_semantics(
        total=total,
        allocations=allocations,
        raw_text=raw_text,
    )


def parse_activity_rows(
    text: StatementText,
) -> tuple[PenFedHelocActivityRow, ...]:
    """Parse all proven PenFed HELOC transaction-activity blocks."""
    rows: list[PenFedHelocActivityRow] = []
    in_activity = False

    for raw_line in text.text.splitlines():
        line = raw_line.strip()

        if _ACTIVITY_START_PATTERN.fullmatch(line):
            in_activity = True
            continue

        if line in _ACTIVITY_STOP_MARKERS:
            in_activity = False
            continue

        if not in_activity or not line:
            continue

        row_match = _ROW_PATTERN.fullmatch(line)

        if row_match is None:
            if _DATED_PREFIX_PATTERN.match(line):
                msg = f"Unrecognized PenFed HELOC transaction row: {line}"
                raise ValueError(msg)

            continue

        description = row_match.group("description")
        kind = _DESCRIPTION_KINDS.get(description)

        if kind is None:
            msg = f"Unsupported PenFed HELOC transaction description: {description}"  # noqa: E501
            raise ValueError(msg)

        total = to_decimal(row_match.group("total"))
        principal = to_decimal(row_match.group("principal"))
        interest = to_decimal(row_match.group("interest"))
        escrow = to_decimal(row_match.group("escrow"))
        fees = to_decimal(row_match.group("fees"))
        other = to_decimal(row_match.group("other"))

        amount, direction = _economic_semantics(
            kind,
            total=total,
            principal=principal,
            interest=interest,
            escrow=escrow,
            fees=fees,
            other=other,
            raw_text=line,
        )

        rows.append(
            PenFedHelocActivityRow(
                process_date=row_match.group("process"),
                effective_date=row_match.group("effective"),
                kind=kind,
                description=description,
                total_amount=total,
                principal_applied=principal,
                interest=interest,
                escrow=escrow,
                fees=fees,
                other=other,
                amount=amount,
                direction=direction,
                raw_text=line,
            )
        )

    return tuple(rows)
