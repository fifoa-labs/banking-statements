"""
tests/processors/discover/checking/test_summary.py

Tests for Discover checking balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.discover.checking.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "ACCOUNT SUMMARY\n"
            "Beginning Balance ..........................$1,234.56\n"
            "Ending Balance .............................$1,534.56\n"
        )
    )

    assert summary.opening_balance == Decimal("1234.56")
    assert summary.closing_balance == Decimal("1534.56")


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            "Ending Balance .............................$100.00\n",
            "beginning balance was not found",
        ),
        (
            "Beginning Balance ..........................$100.00\n",
            "ending balance was not found",
        ),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_balance_summary(make_text(value))


def test_parse_balance_summary_ignores_adjacent_rewards_column() -> None:
    summary = parse_balance_summary(
        make_text(
            "Beginning Balance................$100.00 Rewards text +$1.00\n"
            "Ending Balance..................$125.00 Promotions +$0.00\n"
        )
    )

    assert summary.opening_balance == Decimal("100.00")
    assert summary.closing_balance == Decimal("125.00")
