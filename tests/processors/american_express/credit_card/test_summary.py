"""
tests/processors/american_express/credit_card/test_summary.py

Tests for American Express credit-card balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.credit_card.summary import (  # noqa: E501
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
            "Previous Balance $125.25\n"
            "Payments/Credits -$50.00\n"
            "New Charges +$75.50\n"
            "New Balance $150.75\n"
        )
    )

    assert summary.opening_balance == Decimal("125.25")
    assert summary.closing_balance == Decimal("150.75")


def test_parse_balance_summary_handles_credit_balance() -> None:
    summary = parse_balance_summary(
        make_text("Previous Balance $25.00\nNew Balance $10.50 CR\n")
    )

    assert summary.opening_balance == Decimal("25.00")
    assert summary.closing_balance == Decimal("-10.50")


def test_parse_balance_summary_handles_signed_amounts() -> None:
    summary = parse_balance_summary(
        make_text("Previous Balance -$12.50\nNew Balance +$7.25\n")
    )

    assert summary.opening_balance == Decimal("-12.50")
    assert summary.closing_balance == Decimal("7.25")


@pytest.mark.parametrize(
    ("value", "field"),
    [
        ("New Balance $25.00\n", "opening_balance"),
        ("Previous Balance $25.00\n", "closing_balance"),
    ],
)
def test_parse_balance_summary_requires_fields(
    value: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_balance_summary(make_text(value))


def test_parse_balance_summary_accepts_prefix_credit_balance() -> None:
    summary = parse_balance_summary(
        make_text("Previous Balance $25.00\nNew Balance CR$12.34\n")
    )

    assert summary.opening_balance == Decimal("25.00")
    assert summary.closing_balance == Decimal("-12.34")


def test_parse_balance_summary_accepts_suffix_credit_balance() -> None:
    summary = parse_balance_summary(
        make_text("Previous Balance $25.00\nNew Balance $12.34CR\n")
    )

    assert summary.opening_balance == Decimal("25.00")
    assert summary.closing_balance == Decimal("-12.34")


def test_parse_balance_summary_prefers_account_total() -> None:
    summary = parse_balance_summary(
        make_text(
            "Account Summary\n"
            "Pay In Full Portion\n"
            "Previous Balance $500.00\n"
            "Payments/Credits -$500.00\n"
            "New Charges +$300.00\n"
            "New Balance = $300.00\n"
            "Pay Over Time Portion\n"
            "Previous Balance $400.00\n"
            "Payments/Credits -$400.00\n"
            "New Charges +$700.00\n"
            "New Balance = $700.00\n"
            "Account Total\n"
            "Minimum Payment Due Previous Balance $900.00\n"
            "Payments/Credits -$900.00\n"
            "New Charges +$1,000.00\n"
            "New Balance $1,000.00\n"
        )
    )

    assert summary.opening_balance == Decimal("900.00")
    assert summary.closing_balance == Decimal("1000.00")


def test_parse_account_total_handles_credit_balances() -> None:
    summary = parse_balance_summary(
        make_text(
            "Account Summary\n"
            "Pay In Full Portion\n"
            "Previous Balance $100.00\n"
            "New Balance $50.00\n"
            "Account Total\n"
            "Minimum Payment Due Previous Balance CR$25.00\n"
            "Payments/Credits $0.00\n"
            "New Charges $0.00\n"
            "New Balance $12.50 CR\n"
        )
    )

    assert summary.opening_balance == Decimal("-25.00")
    assert summary.closing_balance == Decimal("-12.50")


def test_parse_account_total_handles_explicit_plus_amounts() -> None:
    summary = parse_balance_summary(
        make_text(
            "Account Summary\n"
            "Pay In Full Portion\n"
            "Previous Balance $100.00\n"
            "New Balance $50.00\n"
            "Account Total\n"
            "Minimum Payment Due Previous Balance +$125.00\n"
            "Payments/Credits $0.00\n"
            "New Charges $0.00\n"
            "New Balance +$150.00\n"
        )
    )

    assert summary.opening_balance == Decimal("125.00")
    assert summary.closing_balance == Decimal("150.00")
