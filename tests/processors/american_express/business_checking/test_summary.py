"""
tests/processors/american_express/business_checking/test_summary.py

Tests for American Express business-checking balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.business_checking.summary import (  # noqa: E501
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for summary tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Statement Summary as of 04/30/2023",
                    "BeginningBalance $1,234.56)",
                    "TotalDebitsThisPeriod $(200.00)",
                    "TotalCreditsThisPeriod $500.00)",
                    "EndingBalance $1,534.56)",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("1234.56")
    assert summary.closing_balance == Decimal("1534.56")


def test_parse_balance_summary_requires_beginning_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking beginning balance was not found."  # noqa: E501, RUF043
        ),
    ):
        parse_balance_summary(make_statement_text("EndingBalance $1,534.56)"))


def test_parse_balance_summary_requires_ending_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking ending balance was not found."  # noqa: RUF043
        ),
    ):
        parse_balance_summary(
            make_statement_text("BeginningBalance $1,234.56)")
        )
