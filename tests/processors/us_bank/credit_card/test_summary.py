"""
tests/processors/us_bank/credit_card/test_summary.py

Tests for U.S. Bank credit-card balance parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.us_bank.credit_card.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText((StatementPage(number=1, text=value),))


def test_parse_balance_summary_supports_positive_and_credit_balances() -> None:
    result = parse_balance_summary(
        make_text(
            "Minimum Payment Due $0.00 Previous Balance - $25.00CR\n"
            "New Balance $10.00 Activity Summary\n"
            "New Balance = $10.00"
        )
    )
    assert result.opening_balance == Decimal("-25.00")
    assert result.closing_balance == Decimal("10.00")


def test_parse_balance_summary_supports_suffix_credit() -> None:
    result = parse_balance_summary(
        make_text(
            "Previous Balance $0.00\n"
            "New Balance $4.00CR Activity Summary\n"
            "New Balance = $4.00CR"
        )
    )
    assert result.opening_balance == Decimal("0.00")
    assert result.closing_balance == Decimal("-4.00")


def test_parse_balance_summary_requires_unique_fields() -> None:
    with pytest.raises(ValueError, match="opening_balance"):
        parse_balance_summary(make_text("New Balance = $1.00"))
    with pytest.raises(ValueError, match="closing_balance"):
        parse_balance_summary(make_text("Previous Balance + $1.00"))
    with pytest.raises(ValueError, match="opening_balance"):
        parse_balance_summary(
            make_text(
                "Previous Balance + $1.00\n"
                "Previous Balance + $2.00\n"
                "New Balance = $3.00"
            )
        )
