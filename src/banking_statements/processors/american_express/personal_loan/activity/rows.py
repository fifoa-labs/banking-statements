"""
src/banking_statements/processors/american_express/personal_loan/activity/rows.py

Activity-row parsing for American Express personal-loan statements.
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


class AmericanExpressPersonalLoanActivitySection(StrEnum):
    """Supported American Express personal-loan activity families."""

    PAYMENT = "payment"
    DISBURSEMENT = "disbursement"
    INTEREST = "interest"
    FEE = "fee"


@dataclass(frozen=True, slots=True)
class AmericanExpressPersonalLoanActivityRow:
    """One American Express personal-loan activity row."""

    transaction_date: str
    description: str
    amount: Decimal
    section: AmericanExpressPersonalLoanActivitySection
    raw_text: str


_ROW_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{2})(?P<posting>\*)?\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?\$[\d,]+\.\d{2})$",
)

_DATE_PREFIX_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{2}\*?\b",
)

_SECTION_MARKERS = {
    "Payments Amount": AmericanExpressPersonalLoanActivitySection.PAYMENT,
    "Loan Disbursements Amount": (
        AmericanExpressPersonalLoanActivitySection.DISBURSEMENT
    ),
    "Interest Charges": AmericanExpressPersonalLoanActivitySection.INTEREST,
    "Fees": AmericanExpressPersonalLoanActivitySection.FEE,
}

_STOP_PREFIXES = (
    "Total Payments and Credits",
    "Total Loan Disbursements",
    "Total Interest Charges for this Period",
    "Total Fees for this Period",
)


def parse_activity_rows(  # noqa: C901
    text: StatementText,
) -> tuple[AmericanExpressPersonalLoanActivityRow, ...]:
    """Parse economic activity from an American Express
    personal-loan invoice.
    """
    rows: list[AmericanExpressPersonalLoanActivityRow] = []
    section: AmericanExpressPersonalLoanActivitySection | None = None

    for raw_line in text.text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        discovered_section = _SECTION_MARKERS.get(line)
        if discovered_section is not None:
            section = discovered_section
            continue

        if line.startswith(_STOP_PREFIXES):
            section = None
            continue

        if section is None:
            continue

        match = _ROW_PATTERN.fullmatch(line)
        if match is None:
            if _DATE_PREFIX_PATTERN.match(line):
                msg = (
                    "Unrecognized American Express personal-loan "
                    f"transaction row: {line}"
                )
                raise ValueError(msg)

            continue

        amount = to_decimal(match.group("amount"))

        if section is AmericanExpressPersonalLoanActivitySection.PAYMENT:
            if amount >= 0:
                msg = (
                    "American Express personal-loan payment must report "
                    f"a negative amount: {line}"
                )
                raise ValueError(msg)
            amount = abs(amount)
        elif amount < 0:
            msg = (
                "American Express personal-loan debit activity must not "
                f"report a negative amount: {line}"
            )
            raise ValueError(msg)

        rows.append(
            AmericanExpressPersonalLoanActivityRow(
                transaction_date=match.group("date"),
                description=match.group("description"),
                amount=amount,
                section=section,
                raw_text=line,
            )
        )

    return tuple(rows)
