"""
tests/processors/capital_one/credit_card/test_identity.py

Tests for Capital One credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.capital_one.credit_card.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity_accepts_repeated_same_account_and_period() -> None:
    identity = parse_identity(
        make_text(
            "Venture X Card | Visa Infinite ending in 1234\n"
            "Dec 19, 2025 - Jan 18, 2026 | 31 days in Billing Cycle\n"
            "Account ending in 1234\n"
            "Dec 19, 2025 - Jan 18, 2026 | 31 days in Billing Cycle\n"
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2025, 12, 19)
    assert identity.statement_end == date(2026, 1, 18)
    assert identity.billing_days == 31


def test_parse_identity_requires_unique_account_ending() -> None:
    with pytest.raises(ValueError, match="account ending.*uniquely"):  # noqa: RUF043
        parse_identity(
            make_text(
                "Venture X Card | Visa Infinite ending in 1234\n"
                "Account ending in 5678\n"
                "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            )
        )


def test_parse_identity_requires_unique_statement_period() -> None:
    with pytest.raises(ValueError, match="statement period.*uniquely"):  # noqa: RUF043
        parse_identity(
            make_text("Venture X Card | Visa Infinite ending in 1234\n")
        )


def test_parse_identity_rejects_reversed_statement_period() -> None:
    with pytest.raises(ValueError, match="starts after it ends"):
        parse_identity(
            make_text(
                "Venture X Card | Visa Infinite ending in 1234\n"
                "Mar 31, 2026 - Mar 1, 2026 | 31 days in Billing Cycle\n"
            )
        )


def test_parse_identity_rejects_incorrect_billing_day_count() -> None:
    with pytest.raises(ValueError, match="day count does not match"):
        parse_identity(
            make_text(
                "Venture X Card | Visa Infinite ending in 1234\n"
                "Mar 1, 2026 - Mar 31, 2026 | 30 days in Billing Cycle\n"
            )
        )
