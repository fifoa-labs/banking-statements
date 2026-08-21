"""
src/banking_statements/processors/us_bank/credit_card/summary.py

Balance-summary parsing for supported U.S. Bank credit-card statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_AMOUNT_PATTERN = (
    r"(?P<sign>[+-])?\s*\$"
    r"(?P<amount>[\d,]+\.\d{2})"
    r"(?P<credit>CR)?"
)

_PREVIOUS_BALANCE_PATTERN = re.compile(
    rf"Previous Balance\s+{_AMOUNT_PATTERN}",
)

_NEW_BALANCE_PATTERN = re.compile(
    rf"New Balance(?:\s*=)?\s+{_AMOUNT_PATTERN}",
)


def _parse_balance(match: re.Match[str]) -> Decimal:
    """Parse one U.S. Bank credit-card balance including credit notation."""
    amount = Decimal(match.group("amount").replace(",", ""))
    if match.group("credit") is not None or match.group("sign") == "-":
        return -amount
    return amount


def _unique_balance(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> Decimal:
    """Return one uniquely reported U.S. Bank credit-card balance."""
    values = {_parse_balance(match) for match in pattern.finditer(text)}

    if len(values) != 1:
        msg = (
            "U.S. Bank credit-card summary field "
            f"{field!r} was not found uniquely."
        )
        raise ValueError(msg)

    return next(iter(values))


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported U.S. Bank credit-card balance checkpoints."""
    return StatementBalanceSummary(
        opening_balance=_unique_balance(
            text.text,
            field="opening_balance",
            pattern=_PREVIOUS_BALANCE_PATTERN,
        ),
        closing_balance=_unique_balance(
            text.text,
            field="closing_balance",
            pattern=_NEW_BALANCE_PATTERN,
        ),
    )
