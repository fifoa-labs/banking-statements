"""
tests/processors/chase/heloc/test_summary.py

Tests for Chase HELOC account-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.chase.heloc.summary import (
    parse_balance_summary,
    parse_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_summary() -> None:
    summary = parse_summary(
        make_text(
            "Previous balance $1,000.00\n"
            "Payments/credits $125.00\n"
            "Fees chrgd/advances $400.00\n"
            "Interest charged $15.25\n"
            "New balance $1,290.25\n"
        )
    )

    assert summary.balances.opening_balance == Decimal("1000.00")
    assert summary.balances.closing_balance == Decimal("1290.25")
    assert summary.payments_credits == Decimal("125.00")
    assert summary.fees_charged_advances == Decimal("400.00")
    assert summary.interest_charged == Decimal("15.25")


def test_parse_summary_accepts_parenthesized_credit_balance() -> None:
    summary = parse_balance_summary(
        make_text(
            "Previous balance ($25.00)\n"
            "Payments/credits $0.00\n"
            "Fees chrgd/advances $0.00\n"
            "Interest charged $0.00\n"
            "New balance ($25.00)\n"
        )
    )

    assert summary.opening_balance == Decimal("-25.00")
    assert summary.closing_balance == Decimal("-25.00")


@pytest.mark.parametrize(
    "missing_field",
    [
        "opening_balance",
        "payments_credits",
        "fees_charged_advances",
        "interest_charged",
        "closing_balance",
    ],
)
def test_parse_summary_requires_fields(missing_field: str) -> None:
    lines = {
        "opening_balance": "Previous balance $1,000.00",
        "payments_credits": "Payments/credits $100.00",
        "fees_charged_advances": "Fees chrgd/advances $0.00",
        "interest_charged": "Interest charged $10.00",
        "closing_balance": "New balance $910.00",
    }

    value = "\n".join(
        line for field, line in lines.items() if field != missing_field
    )

    with pytest.raises(ValueError, match=missing_field):
        parse_summary(make_text(value))
