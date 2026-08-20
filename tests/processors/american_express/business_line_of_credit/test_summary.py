"""
tests/processors/american_express/business_line_of_credit/test_summary.py

Tests for American Express business line-of-credit balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.business_line_of_credit.summary import (  # noqa: E501
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "Summary of account activity\n"
            "Previous balance $1,000.00\n"
            "+ Loans/debits $200.00\n"
            "+ Costs and fees $25.00\n"
            "- Payments/credits $100.00\n"
            "New balance $1,125.00\n"
        )
    )

    assert summary.opening_balance == Decimal("1000.00")
    assert summary.closing_balance == Decimal("1125.00")


def test_parse_balance_summary_supports_reported_credit_balance() -> None:
    summary = parse_balance_summary(
        make_text("Previous balance ($25.00)\nNew balance ($10.00)\n")
    )

    assert summary.opening_balance == Decimal("-25.00")
    assert summary.closing_balance == Decimal("-10.00")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("New balance $100.00\n", "opening_balance"),
        ("Previous balance $100.00\n", "closing_balance"),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))
