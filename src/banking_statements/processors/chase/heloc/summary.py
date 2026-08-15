"""
src/banking_statements/processors/chase/heloc/summary.py

Account-summary parsing for Chase home-equity line-of-credit statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from banking_statements.domain import StatementBalanceSummary, to_decimal

if TYPE_CHECKING:
    from decimal import Decimal

    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class ChaseHelocSummary:
    """Balance checkpoints and activity totals reported by a Chase HELOC."""

    balances: StatementBalanceSummary
    payments_credits: Decimal
    fees_charged_advances: Decimal
    interest_charged: Decimal


_AMOUNT = r"(?:\([+-]?\$?[\d,]+\.\d{2}\)|[+-]?\$?[\d,]+\.\d{2})"

_SUMMARY_PATTERNS = {
    "opening_balance": re.compile(
        rf"Previous balance\s+(?P<amount>{_AMOUNT})",
        re.IGNORECASE,
    ),
    "payments_credits": re.compile(
        rf"Payments/credits\s+(?P<amount>{_AMOUNT})",
        re.IGNORECASE,
    ),
    "fees_charged_advances": re.compile(
        rf"Fees chrgd/advances\s+(?P<amount>{_AMOUNT})",
        re.IGNORECASE,
    ),
    "interest_charged": re.compile(
        rf"Interest charged\s+(?P<amount>{_AMOUNT})",
        re.IGNORECASE,
    ),
    "closing_balance": re.compile(
        rf"New balance\s*(?:1\s*)?(?P<amount>{_AMOUNT})",
        re.IGNORECASE,
    ),
}


def _parse_summary_amount(
    text: str,
    field: str,
) -> Decimal:
    """Parse one required Chase HELOC account-summary amount."""
    match = _SUMMARY_PATTERNS[field].search(text)

    if match is None:
        msg = f"Chase HELOC summary field {field!r} was not found."
        raise ValueError(msg)

    return to_decimal(match.group("amount"))


def parse_summary(text: StatementText) -> ChaseHelocSummary:
    """Parse the Chase HELOC account summary."""
    full_text = text.text

    return ChaseHelocSummary(
        balances=StatementBalanceSummary(
            opening_balance=_parse_summary_amount(
                full_text,
                "opening_balance",
            ),
            closing_balance=_parse_summary_amount(
                full_text,
                "closing_balance",
            ),
        ),
        payments_credits=_parse_summary_amount(
            full_text,
            "payments_credits",
        ),
        fees_charged_advances=_parse_summary_amount(
            full_text,
            "fees_charged_advances",
        ),
        interest_charged=_parse_summary_amount(
            full_text,
            "interest_charged",
        ),
    )


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse reported Chase HELOC opening and closing balances."""
    return parse_summary(text).balances
