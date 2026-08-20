"""
tests/processors/american_express/business_line_of_credit/test_identity.py

Tests for American Express business line-of-credit identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.american_express.business_line_of_credit.identity import (  # noqa: E501
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity() -> None:
    identity = parse_identity(
        make_text(
            "Monthly statement\n"
            "Statement Date 04/30/2026\n"
            "For the Period 04/01/2026 - 04/30/2026\n"
            "Account number 123456\n"
        )
    )

    assert identity.account.account_type is AccountType.LINE_OF_CREDIT
    assert identity.account.display_number == "123456"
    assert identity.account.last4 == "3456"
    assert identity.statement_start == date(2026, 4, 1)
    assert identity.statement_end == date(2026, 4, 30)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            (
                "Statement Date 04/30/2026\n"
                "For the Period 04/01/2026 - 04/30/2026\n"
            ),
            "account number was not found",
        ),
        (
            (
                "For the Period 04/01/2026 - 04/30/2026\n"
                "Account number 123456\n"
            ),
            "statement date was not found",
        ),
        (
            "Statement Date 04/30/2026\nAccount number 123456\n",
            "statement period was not found",
        ),
    ],
)
def test_parse_identity_requires_fields(value: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_identity(make_text(value))


def test_parse_identity_requires_statement_date_to_match_period_end() -> None:
    with pytest.raises(
        ValueError, match="does not match the statement period"
    ):
        parse_identity(
            make_text(
                "Statement Date 04/29/2026\n"
                "For the Period 04/01/2026 - 04/30/2026\n"
                "Account number 123456\n"
            )
        )
