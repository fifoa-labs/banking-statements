"""
tests/processors/wellsfargo/business_line_of_credit/test_summary.py

Tests for Wells Fargo business line-of-credit balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.business_line_of_credit.summary import (  # noqa: E501
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_text(
            "Account Summary\n"
            "Previous Balance $1,250.00\n"
            "New Balance = $1,375.25\n"
        )
    )

    assert summary.opening_balance == Decimal("1250.00")
    assert summary.closing_balance == Decimal("1375.25")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("New Balance = $1,375.25\n", "opening_balance"),
        ("Previous Balance $1,250.00\n", "closing_balance"),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))
