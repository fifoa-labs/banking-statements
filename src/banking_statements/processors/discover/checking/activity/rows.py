"""
src/banking_statements/processors/discover/checking/activity/rows.py

Activity-row parsing for Discover checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class DiscoverCheckingActivitySection(StrEnum):
    """Supported Discover checking activity sections."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class DiscoverCheckingActivityRow:
    """One Discover checking account-activity row."""

    effective_date: str
    posting_date: str
    description: str
    amount: Decimal
    section: DiscoverCheckingActivitySection
    raw_text: str


_ACTIVITY_MARKER = "ACCOUNT ACTIVITY"
_ACTIVITY_HEADERS = frozenset(
    {
        "Eff. Date Bus. Date Description Amount",
        "Eff. Date Syst. Date Description Amount",
    }
)

_SECTION_MARKERS = {
    "Deposits and Credits": DiscoverCheckingActivitySection.CREDIT,
    "Checks": DiscoverCheckingActivitySection.DEBIT,
    "ATM and Debit Card Withdrawals": DiscoverCheckingActivitySection.DEBIT,
    "Electronic Withdrawals": DiscoverCheckingActivitySection.DEBIT,
    "Fees and Other Withdrawals": DiscoverCheckingActivitySection.DEBIT,
    "Service Charges, Fees, and Other Withdrawals": (
        DiscoverCheckingActivitySection.DEBIT
    ),
}

_TOTAL_PREFIXES = (
    "TOTAL DEPOSITS AND CREDITS",
    "TOTAL CHECKS",
    "TOTAL ATM AND DEBIT CARD WITHDRAWALS",
    "TOTAL ELECTRONIC WITHDRAWALS",
    "TOTAL FEES AND OTHER WITHDRAWALS",
    "TOTAL SERVICE CHARGES, FEES, AND OTHER WITHDRAWALS",
)

_STOP_PREFIXES = (
    "Overdraft/Returned Item Fees Summary",
    "Contact Us",
    "CONTACT US",
    "Pleasefoldontheperforationbelow",
    "Important Information",
)

_ROW_PATTERN = re.compile(
    r"^(?P<effective>[A-Z][a-z]{2} \d{1,2})\s+"
    r"(?P<posting>[A-Z][a-z]{2} \d{1,2})\s+"
    r"(?P<description>.+?)\s+"
    r"\$?\s*(?P<amount>[\d,]+\.\d{2})$",
)

_DATE_PREFIX_PATTERN = re.compile(
    r"^[A-Z][a-z]{2} \d{1,2}\b",
)


def _parse_amount(value: str) -> Decimal:
    """Parse a Discover account-activity amount."""
    return Decimal(value.replace(",", ""))


def parse_activity_rows(  # noqa: C901, PLR0912
    text: StatementText,
) -> tuple[DiscoverCheckingActivityRow, ...]:
    """Parse Discover checking account activity."""
    lines = tuple(line.strip() for line in text.text.splitlines())

    rows: list[DiscoverCheckingActivityRow] = []
    section: DiscoverCheckingActivitySection | None = None
    header_seen = False
    in_activity = False

    for line in lines:
        if not line:
            continue

        if line == _ACTIVITY_MARKER:
            in_activity = True
            section = None
            header_seen = False
            continue

        if not in_activity:
            continue

        if line.startswith(_STOP_PREFIXES):
            in_activity = False
            section = None
            header_seen = False
            continue

        discovered_section = _SECTION_MARKERS.get(line)
        if discovered_section is not None:
            section = discovered_section
            continue

        if line in _ACTIVITY_HEADERS:
            if section is None:
                msg = (
                    "Discover checking activity header appeared without "
                    "a supported activity section."
                )
                raise ValueError(msg)

            header_seen = True
            continue

        if line.startswith(_TOTAL_PREFIXES):
            section = None
            continue

        if section is None or not header_seen:
            continue

        row_match = _ROW_PATTERN.fullmatch(line)

        if row_match is not None:
            rows.append(
                DiscoverCheckingActivityRow(
                    effective_date=row_match.group("effective"),
                    posting_date=row_match.group("posting"),
                    description=row_match.group("description"),
                    amount=_parse_amount(row_match.group("amount")),
                    section=section,
                    raw_text=line,
                )
            )
            continue

        if _DATE_PREFIX_PATTERN.match(line):
            msg = f"Unrecognized Discover checking transaction row: {line}"
            raise ValueError(msg)

        if rows:
            previous = rows[-1]
            rows[-1] = replace(
                previous,
                description=f"{previous.description} {line}".strip(),
                raw_text=f"{previous.raw_text}\n{line}",
            )

    return tuple(rows)
