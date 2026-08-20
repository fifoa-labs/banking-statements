"""
src/banking_statements/processors/discover/checking/summary.py

Balance-summary parsing for Discover checking statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_BEGINNING_BALANCE_PATTERN = re.compile(
    r"^Beginning Balance\s*\.{2,}\s*\$(?P<amount>[\d,]+\.\d{2})",
    re.MULTILINE,
)

_ENDING_BALANCE_PATTERN = re.compile(
    r"^Ending Balance\s*\.{2,}\s*\$(?P<amount>[\d,]+\.\d{2})",
    re.MULTILINE,
)


def _parse_amount(value: str) -> Decimal:
    """Parse a Discover checking balance amount."""
    return Decimal(value.replace(",", ""))


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported Discover checking opening and closing balances."""
    beginning_match = _BEGINNING_BALANCE_PATTERN.search(text.text)
    if beginning_match is None:
        msg = "Discover checking beginning balance was not found."
        raise ValueError(msg)

    ending_match = _ENDING_BALANCE_PATTERN.search(text.text)
    if ending_match is None:
        msg = "Discover checking ending balance was not found."
        raise ValueError(msg)

    return StatementBalanceSummary(
        opening_balance=_parse_amount(beginning_match.group("amount")),
        closing_balance=_parse_amount(ending_match.group("amount")),
    )
