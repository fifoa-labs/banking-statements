"""
tests/processors/chase/checking/test_identity.py

Tests for Chase checking statement identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.chase.checking.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for identity tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_parse_identity() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "January 1, 2026 through January 31, 2026",
                    "JPMorgan Chase Bank, N.A.",
                    "Account Number: 000000000001234",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "000000000001234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2026, 1, 1)
    assert identity.statement_end == date(2026, 1, 31)


def test_parse_identity_requires_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="Chase checking account number was not found.",  # noqa: RUF043
    ):
        parse_identity(
            make_statement_text("January 1, 2026 through January 31, 2026")
        )


def test_parse_identity_requires_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match="Chase checking statement period was not found.",  # noqa: RUF043
    ):
        parse_identity(make_statement_text("Account Number: 000000000001234"))
