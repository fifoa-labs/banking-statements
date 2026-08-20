"""
tests/processors/discover/checking/test_identity.py

Tests for Discover checking identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.discover.checking.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_legacy_identity_from_account_ending() -> None:
    identity = parse_identity(
        make_text(
            "CASHBACK CHECKING\n"
            "Account numberending in1234\n"
            "Statement Period: Apr 01, 2018 -Apr 30, 2018\n"
        )
    )

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2018, 4, 1)
    assert identity.statement_end == date(2018, 4, 30)


def test_parse_current_identity_prefers_full_account_number() -> None:
    identity = parse_identity(
        make_text(
            "CASHBACK DEBIT\n"
            "Account Number: 7000001234\n"
            "Statement Period: Jul 01, 2026 -Jul 31, 2026\n"
            "Deposit Slip Account number ending in1234\n"
        )
    )

    assert identity.account.display_number == "7000001234"
    assert identity.account.last4 == "1234"


def test_parse_identity_rejects_conflicting_account_endings() -> None:
    with pytest.raises(ValueError, match="account numbers do not agree"):
        parse_identity(
            make_text(
                "Account Number: 7000001234\n"
                "Account number ending in9999\n"
                "Statement Period: Jul 01, 2026 -Jul 31, 2026\n"
            )
        )


def test_parse_identity_requires_unique_account_number() -> None:
    with pytest.raises(
        ValueError, match="account number was not found uniquely"
    ):
        parse_identity(
            make_text("Statement Period: Jul 01, 2026 -Jul 31, 2026\n")
        )


def test_parse_identity_rejects_multiple_legacy_endings() -> None:
    with pytest.raises(
        ValueError, match="account number was not found uniquely"
    ):
        parse_identity(
            make_text(
                "Account number ending in1234\n"
                "Account number ending in5678\n"
                "Statement Period: Jul 01, 2026 -Jul 31, 2026\n"
            )
        )


def test_parse_identity_requires_statement_period() -> None:
    with pytest.raises(ValueError, match="statement period was not found"):
        parse_identity(make_text("Account number ending in1234\n"))


def test_parse_identity_rejects_reversed_statement_period() -> None:
    with pytest.raises(ValueError, match="starts after it ends"):
        parse_identity(
            make_text(
                "Account number ending in1234\n"
                "Statement Period: Jul 31, 2026 -Jul 01, 2026\n"
            )
        )
