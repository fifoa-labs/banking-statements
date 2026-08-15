"""
src/banking_statements/processors/chase/checking/activity/rows.py

Transaction-detail row parsing for Chase checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class ChaseCheckingActivityRow:
    """Normalized raw row from Chase checking transaction detail."""

    transaction_date: str
    description: str
    amount: Decimal
    balance: Decimal


_ROW_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?[\d,]+\.\d{2})\s+"
    r"(?P<balance>-?[\d,]+\.\d{2})$",
)

_SECTION_PATTERN = re.compile(
    r"\*start\*transactiondetail\s*"
    r"(?P<body>.*?)"
    r"\*end\*transactiondetail",
    re.DOTALL,
)

_IGNORED_PREFIXES = (
    "TRANSACTION DETAIL",
    "DATE DESCRIPTION AMOUNT BALANCE",
    "Beginning Balance ",
    "Ending Balance ",
)


def _parse_amount(value: str) -> Decimal:
    """Parse a Chase checking monetary amount."""
    return Decimal(value.replace(",", ""))


def parse_activity_rows(
    text: StatementText,
) -> tuple[ChaseCheckingActivityRow, ...]:
    """Parse transaction-detail rows from a Chase checking statement."""
    rows: list[ChaseCheckingActivityRow] = []

    for section_match in _SECTION_PATTERN.finditer(text.text):
        body = section_match.group("body")

        for raw_line in body.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith(_IGNORED_PREFIXES):
                continue

            row_match = _ROW_PATTERN.fullmatch(line)

            if row_match is None:
                if rows:
                    previous = rows[-1]

                    rows[-1] = replace(
                        previous,
                        description=f"{previous.description} {line}",
                    )
                    continue

                msg = f"Unrecognized Chase checking transaction row: {line}"
                raise ValueError(msg)

            rows.append(
                ChaseCheckingActivityRow(
                    transaction_date=row_match.group("date"),
                    description=row_match.group("description"),
                    amount=_parse_amount(row_match.group("amount")),
                    balance=_parse_amount(row_match.group("balance")),
                )
            )

    return tuple(rows)
