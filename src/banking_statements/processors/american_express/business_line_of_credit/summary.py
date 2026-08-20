"""
src/banking_statements/processors/american_express/business_line_of_credit/summary.py

Balance-summary parsing for American Express
business line-of-credit statements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary, to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


_AMOUNT_TEXT = r"(?:\(\$[\d,]+\.\d{2}\)|\$[\d,]+\.\d{2})"

_SUMMARY_PATTERNS = {
    "opening_balance": re.compile(
        rf"Previous balance\s+(?P<amount>{_AMOUNT_TEXT})",
    ),
    "closing_balance": re.compile(
        rf"New balance\s+(?P<amount>{_AMOUNT_TEXT})",
    ),
}


def _parse_summary_amount(
    text: str,
    field: str,
) -> Decimal:
    """Parse one required American Express line-of-credit balance."""
    match = _SUMMARY_PATTERNS[field].search(text)

    if match is None:
        msg = (
            "American Express business line-of-credit summary field "
            f"{field!r} was not found."
        )
        raise ValueError(msg)

    return to_decimal(match.group("amount"))


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse American Express business line-of-credit balance checkpoints."""
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
