"""
tests/processors/penfed/heloc/test_finance.py

Tests for PenFed HELOC finance-charge parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.penfed.heloc.finance import (
    parse_finance_charges,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_finance_charge_accepts_repeated_same_total() -> None:
    amount, raw_text = parse_finance_charges(
        make_text("Total Finance Charge $12.50\nTotal Finance Charge $12.50\n")
    )

    assert amount == Decimal("12.50")
    assert raw_text == "Total Finance Charge $12.50"


def test_parse_finance_charge_requires_total() -> None:
    with pytest.raises(ValueError, match="was not found"):
        parse_finance_charges(make_text("FINANCE CHARGES"))


def test_parse_finance_charge_requires_unique_total() -> None:
    with pytest.raises(ValueError, match="uniquely"):
        parse_finance_charges(
            make_text(
                "Total Finance Charge $12.50\nTotal Finance Charge $13.50\n"
            )
        )


def test_parse_finance_charge_rejects_negative_total() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        parse_finance_charges(make_text("Total Finance Charge -$1.00"))
