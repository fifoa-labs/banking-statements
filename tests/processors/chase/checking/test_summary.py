"""
tests/processors/chase/checking/test_summary.py

Tests for Chase checking statement balance parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.chase.checking.summary import (
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
                    "CHECKING SUMMARY Chase Total Checking",
                    "Beginning Balance $1,234.56",
                    "Deposits and Additions 500.00",
                    "Electronic Withdrawals -200.00",
                    "Ending Balance $1,534.56",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("1234.56")
    assert summary.closing_balance == Decimal("1534.56")


def test_parse_balance_summary_requires_beginning_balance() -> None:
    with pytest.raises(
        ValueError,
        match="Chase checking beginning balance was not found.",  # noqa: RUF043
    ):
        parse_balance_summary(make_statement_text("Ending Balance $1,534.56"))


def test_parse_balance_summary_requires_ending_balance() -> None:
    with pytest.raises(
        ValueError,
        match="Chase checking ending balance was not found.",  # noqa: RUF043
    ):
        parse_balance_summary(
            make_statement_text("Beginning Balance $1,234.56")
        )
