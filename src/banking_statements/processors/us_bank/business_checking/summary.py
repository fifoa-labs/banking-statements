"""
src/banking_statements/processors/us_bank/business_checking/summary.py

Balance-summary parsing for supported U.S. Bank business checking statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_AMOUNT = r"\$\s*(?P<amount>[\d,]+\.\d{2})(?P<negative>-)?"

_BEGINNING_BALANCE_PATTERN = re.compile(
    rf"Beginning Balance on\s+[A-Z][a-z]{{2}}\s*\d{{1,2}}\s+{_AMOUNT}",
)

_ENDING_BALANCE_PATTERN = re.compile(
    rf"Ending Balance on\s+[A-Z][a-z]{{2}}\s*\d{{1,2}},\s*\d{{4}}\s+{_AMOUNT}",
)


def _parse_balance(match: re.Match[str]) -> Decimal:
    """Parse a U.S. Bank deposit-account balance including trailing minus."""
    amount = Decimal(match.group("amount").replace(",", ""))
    if match.group("negative") is not None:
        return -amount
    return amount


def _unique_balance(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> Decimal:
    """Return one uniquely reported U.S. Bank checking balance."""
    values = {_parse_balance(match) for match in pattern.finditer(text)}

    if len(values) != 1:
        msg = (
            "U.S. Bank business-checking summary field "
            f"{field!r} was not found uniquely."
        )
        raise ValueError(msg)

    return next(iter(values))


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported U.S. Bank business-checking balance checkpoints."""
    return StatementBalanceSummary(
        opening_balance=_unique_balance(
            text.text,
            field="opening_balance",
            pattern=_BEGINNING_BALANCE_PATTERN,
        ),
        closing_balance=_unique_balance(
            text.text,
            field="closing_balance",
            pattern=_ENDING_BALANCE_PATTERN,
        ),
    )
