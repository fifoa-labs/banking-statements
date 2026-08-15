"""
tests/processors/wellsfargo/business_credit_card/test_summary.py

Tests for Wells Fargo business credit-card balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.business_credit_card.summary import (  # noqa: E501
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for summary tests."""
    return StatementText(pages=(StatementPage(number=1, text=text),))


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Summary",
                    "Previous Balance $500.00",
                    "Credits - $50.00",
                    "Payments - $200.00",
                    "Purchases & Other Charges + $125.00",
                    "New Balance = $375.00",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("500.00")
    assert summary.closing_balance == Decimal("375.00")


def test_parse_balance_summary_rejects_missing_previous_balance() -> None:
    with pytest.raises(
        ValueError,
        match="'opening_balance' was not found",
    ):
        parse_balance_summary(make_statement_text("New Balance = $100.00"))


def test_parse_balance_summary_rejects_missing_new_balance() -> None:
    with pytest.raises(
        ValueError,
        match="'closing_balance' was not found",
    ):
        parse_balance_summary(make_statement_text("Previous Balance $100.00"))
