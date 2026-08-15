"""
src/banking_statements/processors/chase/credit_card/activity/rows.py

Logical account-activity row reconstruction for Chase credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class ActivityRow:
    """One reconstructed Chase credit-card activity row."""

    section: ActivitySection
    date_text: str
    description: str
    amount_text: str
    continuation_lines: tuple[str, ...] = ()


class ActivitySection(StrEnum):
    """Supported Chase credit-card activity sections."""

    PAYMENTS_AND_OTHER_CREDITS = "payments_and_other_credits"
    PURCHASE = "purchase"
    BALANCE_TRANSFERS = "balance_transfers"
    FEES_CHARGED = "fees_charged"
    INTEREST_CHARGED = "interest_charged"


_TRANSACTION_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?(?:\d[\d,]*\.\d{2}|\.\d{2}))$",
)

_FOREIGN_CURRENCY_LABEL_PATTERN = re.compile(
    r"^\d{2}/\d{2}\s+\S+$",
)

_EXCHANGE_RATE_PATTERN = re.compile(
    r"^[\d,]+\s+X\s+\d+\.\d+\s+\(EXCHG RATE\)$",
)

_YEAR_TO_DATE_PATTERN = re.compile(
    r"^\d{4} Totals Year-to-Date$",
)

_SECTION_MARKERS = {
    "PAYMENTS AND OTHER CREDITS": ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
    "PURCHASE": ActivitySection.PURCHASE,
    "BALANCE TRANSFERS": ActivitySection.BALANCE_TRANSFERS,
    "BALANCE TRANSFERS / MY CHASE LOAN": ActivitySection.BALANCE_TRANSFERS,
    "FEES CHARGED": ActivitySection.FEES_CHARGED,
    "INTEREST CHARGED": ActivitySection.INTEREST_CHARGED,
}


def _is_stop_marker(line: str) -> bool:
    """Return whether a line ends the current activity section."""
    return _YEAR_TO_DATE_PATTERN.match(line) is not None or line.startswith(
        (
            "Total fees charged in ",
            "Total interest charged in ",
            "TOTAL FEES FOR THIS PERIOD",
            "TOTAL INTEREST FOR THIS PERIOD",
        )
    )


def _append_continuation(
    row: ActivityRow,
    line: str,
) -> ActivityRow:
    """Return an activity row with one additional continuation line."""
    return ActivityRow(
        section=row.section,
        date_text=row.date_text,
        description=row.description,
        amount_text=row.amount_text,
        continuation_lines=(
            *row.continuation_lines,
            line,
        ),
    )


def parse_activity_rows(  # noqa: C901, PLR0912
    text: StatementText,
) -> tuple[ActivityRow, ...]:
    """Reconstruct Chase account-activity rows from statement text."""
    rows: list[ActivityRow] = []
    section: ActivitySection | None = None
    pending_row: ActivityRow | None = None

    for raw_line in text.text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        section_marker = _SECTION_MARKERS.get(line)
        if section_marker is not None:
            if pending_row is not None:
                rows.append(pending_row)
                pending_row = None

            section = section_marker
            continue

        if section is None:
            continue

        if _is_stop_marker(line):
            if pending_row is not None:
                rows.append(pending_row)
                pending_row = None

            section = None
            continue

        transaction_match = _TRANSACTION_PATTERN.match(line)
        if transaction_match is not None:
            if pending_row is not None:
                rows.append(pending_row)

            pending_row = ActivityRow(
                section=section,
                date_text=transaction_match.group("date"),
                description=transaction_match.group("description"),
                amount_text=transaction_match.group("amount"),
            )
            continue

        if pending_row is None:
            continue

        if _FOREIGN_CURRENCY_LABEL_PATTERN.match(line):
            pending_row = _append_continuation(
                pending_row,
                line,
            )
            continue

        if _EXCHANGE_RATE_PATTERN.match(line):
            pending_row = _append_continuation(
                pending_row,
                line,
            )

    if pending_row is not None:
        rows.append(pending_row)

    return tuple(rows)
