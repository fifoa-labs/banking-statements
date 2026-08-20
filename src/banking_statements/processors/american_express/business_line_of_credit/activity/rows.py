"""
src/banking_statements/processors/american_express/business_line_of_credit/activity/rows.py

Activity-row parsing for American Express business line-of-credit statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from banking_statements.domain import to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


class AmericanExpressBusinessLineOfCreditActivitySection(StrEnum):
    """Supported American Express business line-of-credit
    activity directions.
    """

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class AmericanExpressBusinessLineOfCreditActivityRow:
    """One American Express business line-of-credit transaction-summary row."""

    transaction_date: str
    reference_number: str
    description: str
    amount: Decimal
    section: AmericanExpressBusinessLineOfCreditActivitySection
    raw_text: str


_TRANSACTION_SUMMARY_MARKER = "Transaction Summary"
_TRANSACTION_HEADER = "Date Reference number Description Amount"

_ROW_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<reference>\d{10})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>\(\$[\d,]+\.\d{2}\)|-?\$[\d,]+\.\d{2})$",
)

_DATE_PREFIX_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{4}\b",
)


def _parse_amount(
    value: str,
) -> tuple[Decimal, AmericanExpressBusinessLineOfCreditActivitySection]:
    """Parse an amount and infer its statement-reported direction."""
    amount = to_decimal(value)

    if amount < 0:
        return (
            abs(amount),
            AmericanExpressBusinessLineOfCreditActivitySection.CREDIT,
        )

    return (
        amount,
        AmericanExpressBusinessLineOfCreditActivitySection.DEBIT,
    )


def parse_activity_rows(
    text: StatementText,
) -> tuple[AmericanExpressBusinessLineOfCreditActivityRow, ...]:
    """Parse the American Express business line-of-credit
    transaction summary.
    """
    lines = tuple(line.strip() for line in text.text.splitlines())

    try:
        summary_index = lines.index(_TRANSACTION_SUMMARY_MARKER)
    except ValueError:
        return ()

    header_index = next(
        (
            index
            for index in range(summary_index + 1, len(lines))
            if lines[index]
        ),
        None,
    )

    if header_index is None or lines[header_index] != _TRANSACTION_HEADER:
        msg = (
            "American Express business line-of-credit transaction header "
            "was not found."
        )
        raise ValueError(msg)

    rows: list[AmericanExpressBusinessLineOfCreditActivityRow] = []

    for line in lines[header_index + 1 :]:
        if not line:
            continue

        row_match = _ROW_PATTERN.fullmatch(line)

        if row_match is None:
            if _DATE_PREFIX_PATTERN.match(line):
                msg = (
                    "Unrecognized American Express business line-of-credit "
                    f"transaction row: {line}"
                )
                raise ValueError(msg)

            break

        amount, section = _parse_amount(row_match.group("amount"))

        rows.append(
            AmericanExpressBusinessLineOfCreditActivityRow(
                transaction_date=row_match.group("date"),
                reference_number=row_match.group("reference"),
                description=row_match.group("description"),
                amount=amount,
                section=section,
                raw_text=line,
            )
        )

    return tuple(rows)
