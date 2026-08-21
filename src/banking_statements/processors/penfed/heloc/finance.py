"""
src/banking_statements/processors/penfed/heloc/finance.py

Finance-charge parsing for supported PenFed HELOC statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import to_decimal

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_TOTAL_FINANCE_CHARGE_PATTERN = re.compile(
    r"Total Finance Charge\s+"
    r"(?P<amount>(?:\(\$?[\d,]+\.\d{2}\)|-?\$?[\d,]+\.\d{2}))",
)


def parse_finance_charges(text: StatementText) -> tuple[Decimal, str]:
    """Return the uniquely reported PenFed period finance charge."""
    matches = tuple(_TOTAL_FINANCE_CHARGE_PATTERN.finditer(text.text))

    if not matches:
        msg = "PenFed HELOC total finance charge was not found."
        raise ValueError(msg)

    values = {to_decimal(match.group("amount")) for match in matches}

    if len(values) != 1:
        msg = "PenFed HELOC total finance charge was not found uniquely."
        raise ValueError(msg)

    amount = next(iter(values))
    raw_text = next(
        match.group(0)
        for match in matches
        if to_decimal(match.group("amount")) == amount
    )

    if amount < Decimal("0"):
        msg = "PenFed HELOC total finance charge must not be negative."
        raise ValueError(msg)

    return amount, raw_text
