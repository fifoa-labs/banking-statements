"""
tests/processors/chase/credit_card/test_summary.py

Tests for Chase credit-card statement balance-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.chase.credit_card.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for summary parser tests."""
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
                    "Previous Balance -$10.16",
                    "New Balance $70.56",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("-10.16")
    assert summary.closing_balance == Decimal("70.56")


@pytest.mark.parametrize(
    "missing_line",
    [
        "Previous Balance",
        "New Balance",
    ],
)
def test_parse_balance_summary_requires_balance_fields(
    missing_line: str,
) -> None:
    lines = [
        "Previous Balance $100.00",
        "New Balance $75.00",
    ]

    text = "\n".join(
        line for line in lines if not line.startswith(missing_line)
    )

    with pytest.raises(
        ValueError,
        match="Chase credit-card summary field",
    ):
        parse_balance_summary(
            make_statement_text(text),
        )


def test_parse_balance_summary_ignores_trailing_column_text() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    (
                        "Previous Balance -$95.90 "
                        "and 1% cash back on all other purchases."
                    ),
                    "New Balance -$95.90",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("-95.90")
    assert summary.closing_balance == Decimal("-95.90")


def test_parse_balance_summary_accepts_mangled_new_balance_marker() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Previous Balance $125.00",
                    "N`ew Balance $87.40",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("125.00")
    assert summary.closing_balance == Decimal("87.40")
