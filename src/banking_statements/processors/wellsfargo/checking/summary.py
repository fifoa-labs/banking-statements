"""
src/banking_statements/processors/wellsfargo/checking/summary.py

Balance summary parsing for supported Wells Fargo checking statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary

from .sections import extract_checking_section

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_BEGINNING_BALANCE_PATTERN = re.compile(
    r"Beginning\s+b\s*alance\s+on\s+\d{1,2}/\d{1,2}\s+"
    r"\$(?P<amount>[\d,]+\.\d{2})",
)

_ENDING_BALANCE_PATTERN = re.compile(
    r"Ending\s+bal\s*ance\s+on\s+\d{1,2}/\d{1,2}\s+"
    r"\$?(?P<amount>[\d,]+\.\d{2})",
)


def _parse_amount(value: str) -> Decimal:
    """Parse a Wells Fargo checking balance amount."""
    return Decimal(value.replace(",", ""))


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported Wells Fargo checking opening and closing balances."""
    section = extract_checking_section(text)

    beginning_match = _BEGINNING_BALANCE_PATTERN.search(section)
    if beginning_match is None:
        msg = "Wells Fargo checking beginning balance was not found."
        raise ValueError(msg)

    ending_match = _ENDING_BALANCE_PATTERN.search(section)
    if ending_match is None:
        msg = "Wells Fargo checking ending balance was not found."
        raise ValueError(msg)

    return StatementBalanceSummary(
        opening_balance=_parse_amount(beginning_match.group("amount")),
        closing_balance=_parse_amount(ending_match.group("amount")),
    )
