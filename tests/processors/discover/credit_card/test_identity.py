"""
tests/processors/discover/credit_card/test_identity.py

Tests for Discover credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.discover.credit_card.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_legacy_identity() -> None:
    identity = parse_identity(
        make_text(
            "Discover it® Card\n"
            "Account number ending in1234\n"
            "Open Date:Dec 15, 2025- Close Date:Jan 14, 2026\n"
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2025, 12, 15)
    assert identity.statement_end == date(2026, 1, 14)


def test_parse_current_identity_accepts_repeated_same_ending() -> None:
    identity = parse_identity(
        make_text(
            "DISCOVER IT® CARD ENDING IN 5678\n"
            "AccountSummary 05/10/2026 -06/09/2026 PaymentInformation\n"
            "DISCOVER IT® CARD ENDING IN5678\n"
            "OPEN TO CLOSE DATE:05/10/2026 -06/09/2026\n"
        )
    )

    assert identity.account.display_number == "5678"
    assert identity.account.last4 == "5678"
    assert identity.statement_start == date(2026, 5, 10)
    assert identity.statement_end == date(2026, 6, 9)


def test_parse_identity_accepts_open_to_close_period() -> None:
    identity = parse_identity(
        make_text(
            "DISCOVER IT® CARD ENDING IN 1234\n"
            "OPEN TO CLOSE DATE:10/05/2026 -11/04/2026\n"
        )
    )

    assert identity.statement_start == date(2026, 10, 5)
    assert identity.statement_end == date(2026, 11, 4)


def test_parse_identity_rejects_conflicting_account_endings() -> None:
    with pytest.raises(ValueError, match="not found uniquely"):
        parse_identity(
            make_text(
                "Account number ending in1234\n"
                "DISCOVER IT® CARD ENDING IN 5678\n"
                "AccountSummary 05/10/2026 -06/09/2026\n"
            )
        )


def test_parse_identity_requires_account_ending() -> None:
    with pytest.raises(ValueError, match="account ending"):
        parse_identity(make_text("AccountSummary 05/10/2026 -06/09/2026\n"))


def test_parse_identity_requires_statement_period() -> None:
    with pytest.raises(ValueError, match="statement period"):
        parse_identity(make_text("DISCOVER IT® CARD ENDING IN 1234\n"))


def test_parse_identity_rejects_reversed_statement_period() -> None:
    with pytest.raises(ValueError, match="starts after it ends"):
        parse_identity(
            make_text(
                "DISCOVER IT® CARD ENDING IN 1234\n"
                "AccountSummary 11/04/2026 -10/05/2026\n"
            )
        )
