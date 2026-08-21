"""
src/banking_statements/processors/us_bank/business_checking/activity/rows.py

Logical activity-row reconstruction for U.S. Bank business checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class USBankBusinessCheckingActivitySection(StrEnum):
    """Economic activity directions reported by U.S. Bank checking."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class USBankBusinessCheckingActivityRow:
    """One reconstructed U.S. Bank business-checking activity row."""

    transaction_date: str
    description: str
    amount: Decimal
    section: USBankBusinessCheckingActivitySection
    page: int
    raw_text: str


_SECTION_MARKERS = {
    "Other Deposits": USBankBusinessCheckingActivitySection.CREDIT,
    "Other Deposits (continued)": USBankBusinessCheckingActivitySection.CREDIT,
    "Other Withdrawals": USBankBusinessCheckingActivitySection.DEBIT,
    "Other Withdrawals (continued)": (
        USBankBusinessCheckingActivitySection.DEBIT
    ),
}

_ROW_PATTERN = re.compile(
    r"^(?P<date>[A-Z][a-z]{2}\s*\d{1,2})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>\$?\s*[\d,]+\.\d{2})(?P<negative>-)?$",
)

_DATE_PREFIX_PATTERN = re.compile(r"^[A-Z][a-z]{2}\s*\d{1,2}\b")

_TOTAL_PREFIXES = (
    "Total Other Deposits",
    "Total Other Withdrawals",
)

_STOP_PREFIXES = (
    "Balance Summary",
    "ANALYSIS SERVICE CHARGE DETAIL",
)


def _parse_amount(value: str) -> Decimal:
    """Parse one unsigned U.S. Bank business-checking activity amount."""
    return Decimal(value.replace("$", "").replace(",", "").replace(" ", ""))


def _append_evidence(
    row: USBankBusinessCheckingActivityRow,
    line: str,
) -> USBankBusinessCheckingActivityRow:
    """Append a transaction continuation line to source evidence."""
    return replace(row, raw_text=f"{row.raw_text}\n{line}")


def parse_activity_rows(  # noqa: C901, PLR0912
    text: StatementText,
) -> tuple[USBankBusinessCheckingActivityRow, ...]:
    """Parse U.S. Bank business-checking deposit and withdrawal activity."""
    rows: list[USBankBusinessCheckingActivityRow] = []
    section: USBankBusinessCheckingActivitySection | None = None
    last_row_index: int | None = None

    for page in text.pages:
        section = None
        last_row_index = None

        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            discovered_section = _SECTION_MARKERS.get(line)
            if discovered_section is not None:
                section = discovered_section
                last_row_index = None
                continue

            if line.startswith(_TOTAL_PREFIXES):
                section = None
                last_row_index = None
                continue

            if line.startswith(_STOP_PREFIXES):
                section = None
                last_row_index = None
                continue

            if section is None:
                continue

            if line == "Date Description of Transaction Ref Number Amount":
                continue

            row_match = _ROW_PATTERN.fullmatch(line)
            if row_match is not None:
                amount = _parse_amount(row_match.group("amount"))
                negative = row_match.group("negative") is not None

                if section is USBankBusinessCheckingActivitySection.CREDIT:
                    if negative:
                        msg = (
                            "U.S. Bank business-checking deposit row must not "
                            f"report a trailing minus: {line}"
                        )
                        raise ValueError(msg)
                elif not negative:
                    msg = (
                        "U.S. Bank business-checking withdrawal row must "
                        f"report a trailing minus: {line}"
                    )
                    raise ValueError(msg)

                rows.append(
                    USBankBusinessCheckingActivityRow(
                        transaction_date=row_match.group("date"),
                        description=row_match.group("description"),
                        amount=amount,
                        section=section,
                        page=page.number,
                        raw_text=line,
                    )
                )
                last_row_index = len(rows) - 1
                continue

            if _DATE_PREFIX_PATTERN.match(line):
                msg = (
                    "Unrecognized U.S. Bank business-checking transaction "
                    f"row: {line}"
                )
                raise ValueError(msg)

            if last_row_index is not None:
                rows[last_row_index] = _append_evidence(
                    rows[last_row_index],
                    line,
                )

    return tuple(rows)
