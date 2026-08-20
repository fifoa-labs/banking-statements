"""
tests/processors/american_express/credit_card/test_identity.py

Tests for American Express credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.american_express.credit_card.identity import (  # noqa: E501
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity() -> None:
    identity = parse_identity(
        make_text(
            "American Express\n"
            "Closing Date 04/15/26 Account Ending 7-65432\n"
            "Days in Billing Period: 30\n"
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "7-65432"
    assert identity.account.last4 == "5432"
    assert identity.statement_start == date(2026, 3, 17)
    assert identity.statement_end == date(2026, 4, 15)


def test_parse_identity_accepts_compact_spacing() -> None:
    identity = parse_identity(
        make_text(
            "Closing Date04/15/26 Account Ending7-65432\n"
            "Interest Charge Calculation Days in Billing Period:31\n"
        )
    )

    assert identity.account.display_number == "7-65432"
    assert identity.account.last4 == "5432"
    assert identity.statement_start == date(2026, 3, 16)
    assert identity.statement_end == date(2026, 4, 15)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            "Closing Date 04/15/26\nDays in Billing Period: 30\n",
            "account ending was not found",
        ),
        (
            "Account Ending 7-65432\nDays in Billing Period: 30\n",
            "closing date was not found",
        ),
        (
            "Closing Date 04/15/26\nAccount Ending 7-65432\n",
            "billing period was not found",
        ),
        (
            (
                "Closing Date 04/15/26\n"
                "Account Ending 7-65432\n"
                "Days in Billing Period: 0\n"
            ),
            "billing period must be positive",
        ),
    ],
)
def test_parse_identity_rejects_missing_or_invalid_fields(
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_identity(make_text(value))
