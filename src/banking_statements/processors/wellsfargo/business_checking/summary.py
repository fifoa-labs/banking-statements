"""
src/banking_statements/processors/wellsfargo/business_checking/summary.py

Balance-summary parsing for Wells Fargo business checking statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_BEGINNING_BALANCE_PATTERN = re.compile(
    r"Beginning balance on \d{1,2}/\d{1,2}\s+"
    r"\$(?P<amount>[\d,]+\.\d{2})",
)

_ENDING_BALANCE_PATTERN = re.compile(
    r"Ending balance on \d{1,2}/\d{1,2}\s+"
    r"\$(?P<amount>[\d,]+\.\d{2})",
)


def _parse_amount(value: str) -> Decimal:
    """Parse a Wells Fargo business checking monetary amount."""
    return Decimal(value.replace(",", ""))


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse reported Wells Fargo business checking balances."""
    full_text = text.text

    beginning_match = _BEGINNING_BALANCE_PATTERN.search(full_text)
    if beginning_match is None:
        msg = "Wells Fargo business checking beginning balance was not found."
        raise ValueError(msg)

    ending_match = _ENDING_BALANCE_PATTERN.search(full_text)
    if ending_match is None:
        msg = "Wells Fargo business checking ending balance was not found."
        raise ValueError(msg)

    return StatementBalanceSummary(
        opening_balance=_parse_amount(beginning_match.group("amount")),
        closing_balance=_parse_amount(ending_match.group("amount")),
    )
