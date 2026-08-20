"""
src/banking_statements/processors/capital_one/checking/summary.py

Balance-summary parsing for supported Capital One 360 checking statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
_AMOUNT_TEXT = r"-?\$[\d,]+\.\d{2}"

_OPENING_BALANCE_PATTERN = re.compile(
    rf"^{_MONTH} \d{{1,2}} Opening Balance "
    rf"(?P<amount>{_AMOUNT_TEXT})$",
    re.MULTILINE,
)

_CLOSING_BALANCE_PATTERN = re.compile(
    rf"^{_MONTH} \d{{1,2}} Closing Balance "
    rf"(?P<amount>{_AMOUNT_TEXT})$",
    re.MULTILINE,
)


def _parse_amount(value: str) -> Decimal:
    """Parse one Capital One checking balance amount."""
    return Decimal(value.replace("$", "").replace(",", ""))


def _parse_unique_balance(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> Decimal:
    """Parse one uniquely reported Capital One checking balance."""
    values = {
        _parse_amount(match.group("amount"))
        for match in pattern.finditer(text)
    }

    if len(values) != 1:
        msg = (
            "Capital One checking summary field "
            f"{field!r} was not found uniquely."
        )
        raise ValueError(msg)

    return next(iter(values))


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported Capital One checking opening and closing balances."""
    return StatementBalanceSummary(
        opening_balance=_parse_unique_balance(
            text.text,
            field="opening_balance",
            pattern=_OPENING_BALANCE_PATTERN,
        ),
        closing_balance=_parse_unique_balance(
            text.text,
            field="closing_balance",
            pattern=_CLOSING_BALANCE_PATTERN,
        ),
    )
