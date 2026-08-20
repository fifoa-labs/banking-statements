"""
tests/processors/discover/credit_card/test_summary.py

Tests for Discover credit-card balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.discover.credit_card.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_legacy_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "ACCOUNT SUMMARY PAYMENT INFORMATION\n"
            "New Balance $125.00\n"
            "PreviousBalance $100.00\n"
        )
    )

    assert summary.opening_balance == Decimal("100.00")
    assert summary.closing_balance == Decimal("125.00")


def test_parse_current_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "PreviousBalance $1,000.00 "
            "NewBalance MinimumPayment PaymentDueDate\n"
            "NewBalance: $875.50\n"
        )
    )

    assert summary.opening_balance == Decimal("1000.00")
    assert summary.closing_balance == Decimal("875.50")


def test_parse_balance_summary_supports_credit_balances() -> None:
    summary = parse_balance_summary(
        make_text("PreviousBalance - $25.00\nNewBalance: -$10.00\n")
    )

    assert summary.opening_balance == Decimal("-25.00")
    assert summary.closing_balance == Decimal("-10.00")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("NewBalance: $25.00\n", "opening_balance"),
        ("PreviousBalance $25.00\n", "closing_balance"),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))
