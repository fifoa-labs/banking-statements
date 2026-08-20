"""
tests/processors/capital_one/credit_card/test_summary.py

Tests for Capital One credit-card balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.capital_one.credit_card.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "Account Summary\n"
            "Previous Balance $1,250.50\n"
            "New Balance = $875.25\n"
        )
    )

    assert summary.opening_balance == Decimal("1250.50")
    assert summary.closing_balance == Decimal("875.25")


def test_parse_balance_summary_supports_credit_balances() -> None:
    summary = parse_balance_summary(
        make_text("Previous Balance - $25.00\nNew Balance = -$10.50\n")
    )

    assert summary.opening_balance == Decimal("-25.00")
    assert summary.closing_balance == Decimal("-10.50")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("New Balance = $25.00\n", "opening_balance"),
        ("Previous Balance $25.00\n", "closing_balance"),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))
