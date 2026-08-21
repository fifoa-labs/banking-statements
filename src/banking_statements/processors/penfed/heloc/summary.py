"""
src/banking_statements/processors/penfed/heloc/summary.py

Account-summary parsing for supported PenFed HELOC statements.
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
class PenFedHelocSummary:
    """Balance checkpoints and reported PenFed HELOC activity totals."""

    balances: StatementBalanceSummary
    advances_and_fees: Decimal
    interest_charges: Decimal
    payment_and_other_credits: Decimal
    debit_credit_adjustment: Decimal


_AMOUNT = r"(?:\(\$?[\d,]+\.\d{2}\)|-?\$?[\d,]+\.\d{2})"

_SUMMARY_PATTERNS = {
    "opening_balance": re.compile(
        rf"Previous Balance\s+(?P<amount>{_AMOUNT})",
    ),
    "advances_and_fees": re.compile(
        rf"Advances and Fees\s+(?P<amount>{_AMOUNT})",
    ),
    "interest_charges": re.compile(
        rf"Interest Charges\s+(?P<amount>{_AMOUNT})",
    ),
    "payment_and_other_credits": re.compile(
        rf"Payment and Other Credits\s+(?P<amount>{_AMOUNT})",
    ),
    "debit_credit_adjustment": re.compile(
        rf"Debit/Credit Adjustment\s+(?P<amount>{_AMOUNT})",
    ),
    "closing_balance": re.compile(
        rf"New Balance as of \d{{2}}/\d{{2}}/\d{{2}}\s+"
        rf"(?P<amount>{_AMOUNT})",
    ),
}


def _parse_required_amount(text: str, field: str) -> Decimal:
    """Parse one required PenFed HELOC summary amount."""
    matches = tuple(_SUMMARY_PATTERNS[field].finditer(text))

    if not matches:
        msg = f"PenFed HELOC summary field {field!r} was not found."
        raise ValueError(msg)

    values = {to_decimal(match.group("amount")) for match in matches}

    if len(values) != 1:
        msg = f"PenFed HELOC summary field {field!r} was not found uniquely."
        raise ValueError(msg)

    return next(iter(values))


def parse_summary(text: StatementText) -> PenFedHelocSummary:
    """Parse and validate the PenFed HELOC account summary."""
    opening_balance = _parse_required_amount(text.text, "opening_balance")
    advances_and_fees = _parse_required_amount(text.text, "advances_and_fees")
    interest_charges = _parse_required_amount(text.text, "interest_charges")
    payment_and_other_credits = _parse_required_amount(
        text.text,
        "payment_and_other_credits",
    )
    debit_credit_adjustment = _parse_required_amount(
        text.text,
        "debit_credit_adjustment",
    )
    closing_balance = _parse_required_amount(text.text, "closing_balance")

    expected_closing_balance = (
        opening_balance
        + advances_and_fees
        + interest_charges
        + payment_and_other_credits
        + debit_credit_adjustment
    )

    if expected_closing_balance != closing_balance:
        msg = "PenFed HELOC account summary does not reconcile."
        raise ValueError(msg)

    return PenFedHelocSummary(
        balances=StatementBalanceSummary(
            opening_balance=opening_balance,
            closing_balance=closing_balance,
        ),
        advances_and_fees=advances_and_fees,
        interest_charges=interest_charges,
        payment_and_other_credits=payment_and_other_credits,
        debit_credit_adjustment=debit_credit_adjustment,
    )


def parse_balance_summary(text: StatementText) -> StatementBalanceSummary:
    """Parse PenFed HELOC opening and closing balances."""
    return parse_summary(text).balances
