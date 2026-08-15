"""
src/banking_statements/processors/wellsfargo/business_credit_card/summary.py

Balance-summary parsing for Wells Fargo business credit-card statements.
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
        r"Previous Balance\s+"
        r"(?P<amount>[+-]?\$?[\d,]+\.\d{2})",
    ),
    "closing_balance": re.compile(
        r"New Balance\s+(?:=\s*)?"
        r"(?P<amount>[+-]?\$?[\d,]+\.\d{2})",
    ),
}


def _parse_summary_amount(
    text: str,
    field: str,
) -> Decimal:
    """Parse one required business credit-card summary amount."""
    match = _SUMMARY_PATTERNS[field].search(text)

    if match is None:
        msg = (
            "Wells Fargo business credit-card summary field "
            f"{field!r} was not found."
        )
        raise ValueError(msg)

    return to_decimal(match.group("amount"))


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse Wells Fargo business credit-card balance checkpoints."""
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
