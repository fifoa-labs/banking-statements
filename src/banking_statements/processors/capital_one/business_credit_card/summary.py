"""
src/banking_statements/processors/capital_one/business_credit_card/summary.py

Balance-summary parsing for supported Capital One
business credit-card statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_AMOUNT_TEXT = r"-?\s*\$[\d,]+\.\d{2}"

_PREVIOUS_BALANCE_PATTERN = re.compile(
    rf"Previous Balance\s+(?P<amount>{_AMOUNT_TEXT})",
    re.IGNORECASE,
)

_NEW_BALANCE_PATTERN = re.compile(
    rf"New Balance\s*=\s*(?P<amount>{_AMOUNT_TEXT})",
    re.IGNORECASE,
)


def _parse_amount(value: str) -> Decimal:
    """Parse one Capital One business credit-card balance amount."""
    return Decimal(value.replace("$", "").replace(",", "").replace(" ", ""))


def _parse_required_balance(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> Decimal:
    """Parse one required Capital One business-card balance field."""
    match = pattern.search(text)

    if match is None:
        msg = (
            "Capital One business credit-card summary field "
            f"{field!r} was not found."
        )
        raise ValueError(msg)

    return _parse_amount(match.group("amount"))


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported Capital One business credit-card balances."""
    return StatementBalanceSummary(
        opening_balance=_parse_required_balance(
            text.text,
            field="opening_balance",
            pattern=_PREVIOUS_BALANCE_PATTERN,
        ),
        closing_balance=_parse_required_balance(
            text.text,
            field="closing_balance",
            pattern=_NEW_BALANCE_PATTERN,
        ),
    )
