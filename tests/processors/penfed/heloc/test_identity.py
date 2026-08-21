"""
tests/processors/penfed/heloc/test_identity.py

Tests for PenFed HELOC identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.penfed.heloc.identity import parse_identity
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity_accepts_repeated_account_and_closing_date_forms() -> (
    None
):
    identity = parse_identity(
        make_text(
            "Home Equity Line of Credit Statement\n"
            "Statement Closing Date: March 19, 2026\n"
            "Loan Number 7000001234\n"
            "Transaction Activity (02/19/26 through 03/19/26)\n"
            "Statement Closing Date: 03/19/2026\n"
            "Account Number: 7000001234\n"
        )
    )

    assert identity.account.account_type is AccountType.LINE_OF_CREDIT
    assert identity.account.display_number == "7000001234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2026, 2, 19)
    assert identity.statement_end == date(2026, 3, 19)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            (
                "Statement Closing Date: March 19, 2026\n"
                "Transaction Activity (02/19/26 through 03/19/26)\n"
            ),
            "account number.*uniquely",
        ),
        (
            (
                "Loan Number 7000001234\n"
                "Account Number: 7000005678\n"
                "Statement Closing Date: March 19, 2026\n"
                "Transaction Activity (02/19/26 through 03/19/26)\n"
            ),
            "account number.*uniquely",
        ),
        (
            (
                "Loan Number 7000001234\n"
                "Transaction Activity (02/19/26 through 03/19/26)\n"
            ),
            "closing date.*uniquely",
        ),
        (
            "Loan Number 7000001234\nStatement Closing Date: March 19, 2026\n",
            "activity period.*uniquely",
        ),
        (
            (
                "Loan Number 7000001234\n"
                "Statement Closing Date: March 19, 2026\n"
                "Transaction Activity (03/20/26 through 03/19/26)\n"
            ),
            "starts after",
        ),
        (
            (
                "Loan Number 7000001234\n"
                "Statement Closing Date: March 20, 2026\n"
                "Transaction Activity (02/19/26 through 03/19/26)\n"
            ),
            "does not match",
        ),
    ],
)
def test_parse_identity_rejects_invalid_identity(
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_identity(make_text(value))
