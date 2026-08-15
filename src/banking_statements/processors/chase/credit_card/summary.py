"""
src/banking_statements/processors/chase/credit_card/summary.py

Statement balance-summary parsing for Chase credit-card statements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary, to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


_SUMMARY_PATTERNS = {
    "opening_balance": re.compile(
        r"^[ \t]*Previous Balance[ \t]+"
        r"(?P<amount>[+-]?\$?[\d,]+\.\d{2})(?=[ \t]|$)",
        re.MULTILINE,
    ),
    "closing_balance": re.compile(
        r"^[ \t]*N`?ew Balance[ \t]+"
        r"(?P<amount>[+-]?\$?[\d,]+\.\d{2})(?=[ \t]|$)",
        re.MULTILINE,
    ),
}


def _parse_summary_amount(
    text: str,
    field: str,
) -> Decimal:
    """Parse one required Chase account-summary amount."""
    pattern = _SUMMARY_PATTERNS[field]
    match = pattern.search(text)

    if match is None:
        msg = f"Chase credit-card summary field {field!r} was not found."
        raise ValueError(msg)

    return to_decimal(match.group("amount"))


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse balances reported by a Chase credit-card statement."""
    return StatementBalanceSummary(
        opening_balance=_parse_summary_amount(
            text.text,
            "opening_balance",
        ),
        closing_balance=_parse_summary_amount(
            text.text,
            "closing_balance",
        ),
    )
