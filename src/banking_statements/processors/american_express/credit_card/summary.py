"""
src/banking_statements/processors/american_express/credit_card/summary.py

Balance-summary parsing for supported American Express credit-card statements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary, to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


_AMOUNT_TEXT = r"[+-]?\$?[\d,]+\.\d{2}"

_SUMMARY_PATTERNS = {
    "opening_balance": re.compile(
        rf"Previous Balance\s+"
        rf"(?P<prefix_credit>CR\s*)?"
        rf"(?P<amount>{_AMOUNT_TEXT})"
        rf"(?P<suffix_credit>\s*CR)?",
    ),
    "closing_balance": re.compile(
        rf"New Balance\s+"
        rf"(?P<prefix_credit>CR\s*)?"
        rf"(?P<amount>{_AMOUNT_TEXT})"
        rf"(?P<suffix_credit>\s*CR)?",
    ),
}


def _parse_summary_amount(
    text: str,
    field: str,
) -> Decimal:
    """Parse one required American Express balance-summary amount."""
    match = _SUMMARY_PATTERNS[field].search(text)

    if match is None:
        msg = (
            "American Express credit-card summary field "
            f"{field!r} was not found."
        )
        raise ValueError(msg)

    amount_text = match.group("amount")
    if amount_text.startswith("+"):
        amount_text = amount_text[1:]

    amount = to_decimal(amount_text)

    if (
        match.group("prefix_credit") is not None
        or match.group("suffix_credit") is not None
    ):
        return -abs(amount)

    return amount


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse reported American Express credit-card balances."""
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
