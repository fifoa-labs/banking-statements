"""
tests/processors/wellsfargo/credit_card/test_summary.py

Tests for Wells Fargo credit-card balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.credit_card.summary import (
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
                    "Account Summary",
                    "Previous Balance $100.00",
                    "- Payments $25.00",
                    "- Other Credits $10.00",
                    "+ Purchases, Balance Transfers & $75.00",
                    "Other Charges",
                    "+ Fees Charged $5.00",
                    "+ Interest Charged $2.00",
                    "= New Balance $147.00",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("100.00")
    assert summary.closing_balance == Decimal("147.00")


def test_parse_balance_summary_handles_comma_amounts() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Summary",
                    "Previous Balance $1,250.50",
                    "= New Balance $2,345.67",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("1250.50")
    assert summary.closing_balance == Decimal("2345.67")


def test_parse_balance_summary_handles_negative_balance() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Summary",
                    "Previous Balance $25.00",
                    "= New Balance -$10.00",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("25.00")
    assert summary.closing_balance == Decimal("-10.00")


def test_parse_balance_summary_rejects_missing_previous_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Wells Fargo credit-card summary field "
            "'opening_balance' was not found"
        ),
    ):
        parse_balance_summary(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Summary",
                        "= New Balance $125.00",
                    )
                )
            )
        )


def test_parse_balance_summary_rejects_missing_new_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Wells Fargo credit-card summary field "
            "'closing_balance' was not found"
        ),
    ):
        parse_balance_summary(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Summary",
                        "Previous Balance $100.00",
                    )
                )
            )
        )
