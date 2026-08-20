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


_ACCOUNT_TOTAL_PATTERN = re.compile(
    r"Account Total"
    r".*?"
    r"Previous Balance\s+"
    rf"(?P<opening_prefix_credit>CR\s*)?"
    rf"(?P<opening_amount>{_AMOUNT_TEXT})"
    rf"(?P<opening_suffix_credit>\s*CR)?"
    r".*?"
    r"New Balance\s+"
    rf"(?P<closing_prefix_credit>CR\s*)?"
    rf"(?P<closing_amount>{_AMOUNT_TEXT})"
    rf"(?P<closing_suffix_credit>\s*CR)?",
    re.DOTALL,
)


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


def _parse_account_total_amount(
    match: re.Match[str],
    field: str,
) -> Decimal:
    """Parse one amount from an American Express Account Total summary."""
    amount_text = match.group(f"{field}_amount")

    if amount_text.startswith("+"):
        amount_text = amount_text[1:]

    amount = to_decimal(amount_text)

    if (
        match.group(f"{field}_prefix_credit") is not None
        or match.group(f"{field}_suffix_credit") is not None
    ):
        return -abs(amount)

    return amount


def parse_balance_summary(
    text: StatementText,
) -> StatementBalanceSummary:
    """Parse reported American Express credit-card balances."""
    account_total_match = _ACCOUNT_TOTAL_PATTERN.search(text.text)

    if account_total_match is not None:
        return StatementBalanceSummary(
            opening_balance=_parse_account_total_amount(
                account_total_match,
                "opening",
            ),
            closing_balance=_parse_account_total_amount(
                account_total_match,
                "closing",
            ),
        )

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
