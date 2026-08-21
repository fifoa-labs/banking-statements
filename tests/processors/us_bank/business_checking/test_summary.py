"""
tests/processors/us_bank/business_checking/test_summary.py

Tests for U.S. Bank business-checking balance parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.us_bank.business_checking.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText((StatementPage(number=1, text=value),))


def test_parse_balance_summary_supports_trailing_minus() -> None:
    result = parse_balance_summary(
        make_text(
            "Beginning Balance on Jan 1 $ 5.25-\n"
            "Ending Balance on Jan 31, 2026 $ 2.75"
        )
    )
    assert result.opening_balance == Decimal("-5.25")
    assert result.closing_balance == Decimal("2.75")


def test_parse_balance_summary_requires_unique_fields() -> None:
    with pytest.raises(ValueError, match="opening_balance"):
        parse_balance_summary(
            make_text("Ending Balance on Jan 31, 2026 $ 2.75")
        )
    with pytest.raises(ValueError, match="closing_balance"):
        parse_balance_summary(make_text("Beginning Balance on Jan 1 $ 2.75"))
    with pytest.raises(ValueError, match="opening_balance"):
        parse_balance_summary(
            make_text(
                "Beginning Balance on Jan 1 $ 1.00\n"
                "Beginning Balance on Jan 2 $ 2.00\n"
                "Ending Balance on Jan 31, 2026 $ 3.00"
            )
        )
