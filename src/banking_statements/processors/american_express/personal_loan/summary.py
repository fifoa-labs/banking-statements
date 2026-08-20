"""
src/banking_statements/processors/american_express/personal_loan/summary.py

Balance-summary parsing for American Express personal-loan statements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary, to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


_AMOUNT_TEXT = r"[+-]?\$[\d,]+\.\d{2}"

_PREVIOUS_BALANCE_PATTERN = re.compile(
    rf"Previous Outstanding Loan Balance\s+(?P<amount>{_AMOUNT_TEXT})",
)

_OUTSTANDING_BALANCE_PATTERN = re.compile(
    rf"(?<!Previous )Outstanding Loan Balance\s+"
    rf"(?P<amount>{_AMOUNT_TEXT})",
)


def _parse_required_amount(
    pattern: re.Pattern[str],
    text: str,
    *,
    field: str,
) -> Decimal:
    """Parse one required American Express personal-loan balance."""
    match = pattern.search(text)
    if match is None:
        msg = (
            "American Express personal-loan summary field "
            f"{field!r} was not found."
        )
        raise ValueError(msg)

    return to_decimal(match.group("amount"))


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse American Express personal-loan balance checkpoints."""
    return StatementBalanceSummary(
        opening_balance=_parse_required_amount(
            _PREVIOUS_BALANCE_PATTERN,
            text.text,
            field="opening_balance",
        ),
        closing_balance=_parse_required_amount(
            _OUTSTANDING_BALANCE_PATTERN,
            text.text,
            field="closing_balance",
        ),
    )
