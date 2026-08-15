"""
tests/processors/wellsfargo/business_line_of_credit/test_identity.py

Tests for Wells Fargo business line-of-credit identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.wellsfargo.business_line_of_credit.identity import (  # noqa: E501
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity() -> None:
    identity = parse_identity(
        make_text(
            "BUSINESSLINE\n"
            "Account Number 1111 2222 3333 1234\n"
            "Statement Closing Date 03/22/26\n"
            "Days in Billing Cycle 31\n"
            "Sample account ending 1234\n"
        )
    )

    assert identity.account.account_type is AccountType.LINE_OF_CREDIT
    assert identity.account.display_number == "1111 2222 3333 1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2026, 2, 20)
    assert identity.statement_end == date(2026, 3, 22)


def test_parse_identity_zero_day_cycle() -> None:
    identity = parse_identity(
        make_text(
            "Account Number 1111 2222 3333 1234\n"
            "Statement Closing Date 07/22/25\n"
            "Days in Billing Cycle 0\n"
        )
    )

    assert identity.statement_start == date(2025, 7, 22)
    assert identity.statement_end == date(2025, 7, 22)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            "Statement Closing Date 03/22/26\nDays in Billing Cycle 31\n",
            "account number was not found",
        ),
        (
            (
                "Account Number 1111 2222 3333 1234\n"
                "Statement Closing Date 03/22/26\n"
                "Days in Billing Cycle 31\n"
                "Sample account ending 9999\n"
            ),
            "account numbers do not agree",
        ),
        (
            "Account Number 1111 2222 3333 1234\nDays in Billing Cycle 31\n",
            "closing date was not found",
        ),
        (
            (
                "Account Number 1111 2222 3333 1234\n"
                "Statement Closing Date 03/22/26\n"
            ),
            "billing cycle was not found",
        ),
    ],
)
def test_parse_identity_rejects_missing_or_conflicting_fields(
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_identity(make_text(value))
