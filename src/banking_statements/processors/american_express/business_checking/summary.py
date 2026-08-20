"""
src/banking_statements/processors/american_express/business_checking/summary.py

Balance-summary parsing for American Express business-checking statements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary, to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


_BALANCE_PATTERN = r"\$?(?P<amount>[\d,]+\.\d{2})\)?"

_BEGINNING_BALANCE_PATTERNS = (
    re.compile(
        r"BeginningBalance\s+\$?(?P<amount>[\d,]+\.\d{2})\)?",
    ),
    re.compile(
        r"Beginning Balance as of\s+\d{2}/\d{2}/\d{4}\s+"
        r"\$(?P<amount>[\d,]+\.\d{2})",
    ),
)

_ENDING_BALANCE_PATTERNS = (
    re.compile(
        r"EndingBalance\s+\$?(?P<amount>[\d,]+\.\d{2})\)?",
    ),
    re.compile(
        r"Ending Balance as of\s+\d{2}/\d{2}/\d{4}\s+"
        r"\$(?P<amount>[\d,]+\.\d{2})",
    ),
)


def _parse_amount(value: str) -> Decimal:
    """Parse an American Express business-checking balance amount."""
    return to_decimal(value)


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse reported American Express business-checking balances."""
    full_text = text.text

    beginning_match = next(
        (
            match
            for pattern in _BEGINNING_BALANCE_PATTERNS
            if (match := pattern.search(full_text)) is not None
        ),
        None,
    )
    if beginning_match is None:
        msg = (
            "American Express business-checking beginning balance was not "
            "found."
        )
        raise ValueError(msg)

    ending_match = next(
        (
            match
            for pattern in _ENDING_BALANCE_PATTERNS
            if (match := pattern.search(full_text)) is not None
        ),
        None,
    )
    if ending_match is None:
        msg = (
            "American Express business-checking ending balance was not found."
        )
        raise ValueError(msg)

    return StatementBalanceSummary(
        opening_balance=_parse_amount(beginning_match.group("amount")),
        closing_balance=_parse_amount(ending_match.group("amount")),
    )
