"""
src/banking_statements/processors/chase/heloc/finance.py

Finance-charge parsing for Chase home-equity line-of-credit statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import to_decimal

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_FINANCE_SECTION_MARKER = "Finance charge calculations"
_FINANCE_ROW_PATTERN = re.compile(
    r"^Purchases, Balance Transfers,\s+"
    r"\d{2}/\d{2}/\d{4}\s+-\s+\d+\s+"
    r"\d+\.\d+%\s+\d+\.\d+%\s+"
    r"(?:\(\$?[\d,]+\.\d{2}\)|\$?[\d,]+\.\d{2})\s+"
    r"(?P<charge>\$?[\d,]+\.\d{2})$",
)


def parse_finance_charges(text: StatementText) -> Decimal:
    """Return gross finance charges accrued during the statement cycle."""
    marker_position = text.text.find(_FINANCE_SECTION_MARKER)

    if marker_position < 0:
        msg = "Chase HELOC finance-charge section was not found."
        raise ValueError(msg)

    section = text.text[marker_position + len(_FINANCE_SECTION_MARKER) :]
    charges = tuple(
        to_decimal(match.group("charge"))
        for raw_line in section.splitlines()
        if (match := _FINANCE_ROW_PATTERN.fullmatch(raw_line.strip()))
        is not None
    )

    if not charges:
        msg = "Chase HELOC finance-charge rows were not found."
        raise ValueError(msg)

    return sum(charges, start=Decimal("0"))
