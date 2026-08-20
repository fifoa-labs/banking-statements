"""
src/banking_statements/processors/american_express/business_checking/activity/rows.py

Activity-row parsing for American Express business-checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

from banking_statements.domain import to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


class AmericanExpressBusinessCheckingActivitySection(StrEnum):
    """Supported American Express business-checking activity directions."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class AmericanExpressBusinessCheckingActivityRow:
    """One American Express business-checking account activity row."""

    transaction_date: str
    description: str
    amount: Decimal
    balance: Decimal
    section: AmericanExpressBusinessCheckingActivitySection
    continuation_lines: tuple[str, ...] = ()


_BEGINNING_ROW_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{4})\s+"
    r"Beginning\s*Balance\s+"
    r"\$(?P<balance>[\d,]+\.\d{2})\s*\)?$",
)

_ENDING_ROW_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{4}\s+Ending\s*Balance\s+",
)

_ROW_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<debit_open>\()?"
    r"\$?"
    r"(?P<legacy_debit_open>\()?"
    r"(?P<amount>[\d,]+\.\d{2})"
    r"(?P<debit_close>\))?\s+"
    r"\$(?P<balance>[\d,]+\.\d{2})\s*\)?$",
)

_DATE_PREFIX_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{4}\b",
)

_SECTION_PATTERN = re.compile(
    r"Account Activity\s+"
    r"Date Description Credits Debits Balance\s+"
    r"(?P<body>.*?)"
    r"(?:24/7 Account Access|\Z)",
    re.DOTALL,
)

_IGNORED_PREFIXES = ("ID:",)


def _parse_amount(value: str) -> Decimal:
    """Parse an American Express business-checking monetary amount."""
    return to_decimal(value)


def parse_activity_rows(  # noqa: C901, PLR0912
    text: StatementText,
) -> tuple[AmericanExpressBusinessCheckingActivityRow, ...]:
    """Parse American Express business-checking account activity."""
    section_match = _SECTION_PATTERN.search(text.text)

    if section_match is None:
        return ()

    rows: list[AmericanExpressBusinessCheckingActivityRow] = []
    running_balance: Decimal | None = None

    for raw_line in section_match.group("body").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        beginning_match = _BEGINNING_ROW_PATTERN.fullmatch(line)
        if beginning_match is not None:
            running_balance = _parse_amount(
                beginning_match.group("balance"),
            )
            continue

        if _ENDING_ROW_PATTERN.match(line):
            continue

        if line.startswith(_IGNORED_PREFIXES):
            continue

        if (
            rows
            and _DATE_PREFIX_PATTERN.match(line) is None
            and _BEGINNING_ROW_PATTERN.fullmatch(line) is None
        ):
            previous = rows[-1]
            rows[-1] = replace(
                previous,
                continuation_lines=(
                    *previous.continuation_lines,
                    line,
                ),
            )
            continue

        row_match = _ROW_PATTERN.fullmatch(line)
        if row_match is None:
            if _DATE_PREFIX_PATTERN.match(line):
                msg = (
                    "Unrecognized American Express business-checking "
                    f"transaction row: {line}"
                )
                raise ValueError(msg)

            continue

        if running_balance is None:
            msg = (
                "American Express business-checking beginning activity "
                "balance was not found."
            )
            raise ValueError(msg)

        amount = _parse_amount(row_match.group("amount"))
        balance = _parse_amount(row_match.group("balance"))

        is_parenthesized_debit = (
            row_match.group("debit_open") is not None
            or row_match.group("legacy_debit_open") is not None
        ) and row_match.group("debit_close") is not None

        if is_parenthesized_debit:
            if balance != running_balance - amount:
                msg = (
                    "American Express business-checking debit row does not "
                    f"reconcile with its running balance: {line}"
                )
                raise ValueError(msg)

            section = AmericanExpressBusinessCheckingActivitySection.DEBIT
        elif balance == running_balance + amount:
            section = AmericanExpressBusinessCheckingActivitySection.CREDIT
        elif balance == running_balance - amount:
            section = AmericanExpressBusinessCheckingActivitySection.DEBIT
        else:
            msg = (
                "American Express business-checking activity row does not "
                f"reconcile with its running balance: {line}"
            )
            raise ValueError(msg)

        rows.append(
            AmericanExpressBusinessCheckingActivityRow(
                transaction_date=row_match.group("date"),
                description=row_match.group("description"),
                amount=amount,
                balance=balance,
                section=section,
            )
        )

        running_balance = balance

    return tuple(rows)
