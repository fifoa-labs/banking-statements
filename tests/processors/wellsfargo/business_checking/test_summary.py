"""
tests/processors/wellsfargo/business_checking/test_summary.py

Tests for Wells Fargo business checking balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.business_checking.summary import (  # noqa: E501
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for summary tests."""
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
                    "Sample Business Checking",
                    "Beginning balance on 1/1 $1,000.00",
                    "Deposits/Credits 500.00",
                    "Withdrawals/Debits - 250.00",
                    "Ending balance on 1/31 $1,250.00",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("1000.00")
    assert summary.closing_balance == Decimal("1250.00")


def test_parse_balance_summary_handles_comma_amounts() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Beginning balance on 2/1 $12,345.67",
                    "Ending balance on 2/29 $23,456.78",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("12345.67")
    assert summary.closing_balance == Decimal("23456.78")


def test_parse_balance_summary_rejects_missing_beginning_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Wells Fargo business checking beginning balance was not found"
        ),
    ):
        parse_balance_summary(
            make_statement_text(
                "Ending balance on 1/31 $1,250.00",
            )
        )


def test_parse_balance_summary_rejects_missing_ending_balance() -> None:
    with pytest.raises(
        ValueError,
        match=("Wells Fargo business checking ending balance was not found"),
    ):
        parse_balance_summary(
            make_statement_text(
                "Beginning balance on 1/1 $1,000.00",
            )
        )
