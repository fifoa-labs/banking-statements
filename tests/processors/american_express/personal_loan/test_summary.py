"""
tests/processors/american_express/personal_loan/test_summary.py

Tests for American Express personal-loan balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.personal_loan.summary import (  # noqa: E501
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "Outstanding Loan Balance $9,100.00 "
            "Previous Outstanding Loan Balance $10,000.00\n"
        )
    )

    assert summary.opening_balance == Decimal("10000.00")
    assert summary.closing_balance == Decimal("9100.00")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("Outstanding Loan Balance $9,100.00\n", "opening_balance"),
        (
            "Previous Outstanding Loan Balance $10,000.00\n",
            "closing_balance",
        ),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))
