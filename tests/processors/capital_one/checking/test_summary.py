"""
tests/processors/capital_one/checking/test_summary.py

Tests for Capital One checking balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.capital_one.checking.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "Mar 1 Opening Balance $1,250.50\nMar 31 Closing Balance $875.25\n"
        )
    )

    assert summary.opening_balance == Decimal("1250.50")
    assert summary.closing_balance == Decimal("875.25")


def test_parse_balance_summary_supports_negative_balances() -> None:
    summary = parse_balance_summary(
        make_text(
            "Mar 1 Opening Balance -$25.00\nMar 31 Closing Balance -$10.50\n"
        )
    )

    assert summary.opening_balance == Decimal("-25.00")
    assert summary.closing_balance == Decimal("-10.50")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("Mar 31 Closing Balance $25.00\n", "opening_balance"),
        ("Mar 1 Opening Balance $25.00\n", "closing_balance"),
        (
            (
                "Mar 1 Opening Balance $25.00\n"
                "Mar 2 Opening Balance $30.00\n"
                "Mar 31 Closing Balance $30.00\n"
            ),
            "opening_balance",
        ),
    ],
)
def test_parse_balance_summary_requires_unique_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))
