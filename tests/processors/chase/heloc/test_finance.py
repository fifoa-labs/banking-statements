"""
tests/processors/chase/heloc/test_finance.py

Tests for Chase HELOC finance-charge parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.chase.heloc.finance import (
    parse_finance_charges,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_finance_charges_sums_cycle_rows() -> None:
    charges = parse_finance_charges(
        make_text(
            "Finance charge calculations\n"
            "Type of balance Dates Days in billing Annual percentage "
            "Daily periodic rate Balance subject to Finance charges\n"
            "Purchases, Balance Transfers, 01/20/2026 - 10 "
            "6.63000% 0.0181644% $1,000.00 $18.16\n"
            "Cash Advances - Revolving 01/29/2026\n"
            "Purchases, Balance Transfers, 01/30/2026 - 5 "
            "6.63000% 0.0181644% $500.00 $4.54\n"
            "Cash Advances - Revolving 02/03/2026\n"
        )
    )

    assert charges == Decimal("22.70")


def test_parse_finance_charges_accepts_credit_balance() -> None:
    charges = parse_finance_charges(
        make_text(
            "Finance charge calculations\n"
            "Purchases, Balance Transfers, 02/01/2026 - 1 "
            "6.63000% 0.0181644% ($25.00) $0.00\n"
        )
    )

    assert charges == Decimal("0.00")


def test_parse_finance_charges_requires_section() -> None:
    with pytest.raises(ValueError, match="section was not found"):
        parse_finance_charges(make_text("Account summary"))


def test_parse_finance_charges_requires_rows() -> None:
    with pytest.raises(ValueError, match="rows were not found"):
        parse_finance_charges(make_text("Finance charge calculations"))
