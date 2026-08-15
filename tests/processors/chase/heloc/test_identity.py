"""
tests/processors/chase/heloc/test_identity.py

Tests for Chase HELOC statement identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.chase.heloc.identity import parse_identity
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity() -> None:
    identity = parse_identity(
        make_text(
            "Home EquityLine of credit Statement\n"
            "Statement Period\n"
            "01/20/2026 - 02/18/2026\n"
            "Account number 0000001234\n"
        )
    )

    assert identity.account.account_type is AccountType.LINE_OF_CREDIT
    assert identity.account.display_number == "0000001234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2026, 1, 20)
    assert identity.statement_end == date(2026, 2, 18)


def test_parse_identity_accepts_unique_unlabeled_period() -> None:
    identity = parse_identity(
        make_text(
            "Home EquityLine of credit Statement\n"
            "01/20/2026 - 02/18/2026\n"
            "Account number 0000001234\n"
        )
    )

    assert identity.statement_start == date(2026, 1, 20)
    assert identity.statement_end == date(2026, 2, 18)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            "Statement Period\n01/20/2026 - 02/18/2026\n",
            "account number was not found",
        ),
        (
            "Account number 0000001234\n",
            "statement period was not found",
        ),
        (
            (
                "Account number 0000001234\n"
                "Statement Period\n"
                "02/18/2026 - 01/20/2026\n"
            ),
            "starts after it ends",
        ),
    ],
)
def test_parse_identity_rejects_invalid_fields(
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_identity(make_text(value))
