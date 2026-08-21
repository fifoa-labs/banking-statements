"""
src/banking_statements/processors/chase/business_credit_card/activity/rows.py

Logical activity-row parsing for supported Chase business credit cards.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from banking_statements.domain import to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class ChaseBusinessCreditCardActivityRow:
    """One reconstructed Chase business credit-card activity row."""

    date_text: str
    description: str
    amount: Decimal
    page: int
    raw_text: str
    continuation_lines: tuple[str, ...] = ()


_TRANSACTION_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?(?:\d[\d,]*\.\d{2}|\.\d{2}))$",
)

_DATED_PREFIX_PATTERN = re.compile(r"^\d{2}/\d{2}\b")

_FOREIGN_CURRENCY_LABEL_PATTERN = re.compile(
    r"^\d{2}/\d{2}\s+\S+$",
)

_EXCHANGE_RATE_PATTERN = re.compile(
    r"^[\d,]+(?:\.\d+)?\s+X\s+\d+\.\d+\s+\(EXCHG RATE\)$",
)

_YEAR_TO_DATE_PATTERN = re.compile(
    r"^\d{4} Totals Year-to-Date$",
)

_ACTIVITY_START_MARKERS = frozenset(
    {
        "ACCOUNT ACTIVITY",
        "AACCCCOOUUNNTT AACCTTIIVVIITTYY",
        "ACCOUNT ACTIVITY (CONTINUED)",
    }
)


def _append_continuation(
    row: ChaseBusinessCreditCardActivityRow,
    line: str,
) -> ChaseBusinessCreditCardActivityRow:
    """Return an activity row with one additional continuation line."""
    return replace(
        row,
        continuation_lines=(*row.continuation_lines, line),
    )


def parse_activity_rows(
    text: StatementText,
) -> tuple[ChaseBusinessCreditCardActivityRow, ...]:
    """Parse signed rows from Chase business-card account activity."""
    rows: list[ChaseBusinessCreditCardActivityRow] = []
    in_activity = False
    continuation_row_index: int | None = None

    for page in text.pages:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if line in _ACTIVITY_START_MARKERS:
                in_activity = True
                continuation_row_index = None
                continue

            if _YEAR_TO_DATE_PATTERN.fullmatch(line):
                in_activity = False
                continuation_row_index = None
                continue

            if not in_activity or not line:
                continue

            transaction_match = _TRANSACTION_PATTERN.fullmatch(line)

            if transaction_match is not None:
                rows.append(
                    ChaseBusinessCreditCardActivityRow(
                        date_text=transaction_match.group("date"),
                        description=transaction_match.group("description"),
                        amount=to_decimal(transaction_match.group("amount")),
                        page=page.number,
                        raw_text=line,
                    )
                )
                continuation_row_index = len(rows) - 1
                continue

            if _FOREIGN_CURRENCY_LABEL_PATTERN.fullmatch(
                line
            ) or _EXCHANGE_RATE_PATTERN.fullmatch(line):
                if continuation_row_index is None:
                    msg = (
                        "Chase business credit-card continuation has no "
                        f"transaction row: {line}"
                    )
                    raise ValueError(msg)

                rows[continuation_row_index] = _append_continuation(
                    rows[continuation_row_index],
                    line,
                )
                continue

            if _DATED_PREFIX_PATTERN.match(line):
                msg = (
                    "Unrecognized Chase business credit-card transaction "
                    f"row: {line}"
                )
                raise ValueError(msg)

    return tuple(rows)
