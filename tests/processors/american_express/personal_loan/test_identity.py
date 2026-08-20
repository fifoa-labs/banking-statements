"""
tests/processors/american_express/personal_loan/test_identity.py

Tests for American Express personal-loan identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.american_express.personal_loan.identity import (  # noqa: E501
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity_uses_evidenced_activity_boundary() -> None:
    identity = parse_identity(
        make_text(
            "American Express® Personal Loans\n"
            "Invoice Date07/12/26 Next Invoice Date08/12/26 "
            "Loan Account Ending4-12345\n"
            "06/26/26* SAMPLE PAYMENT -$100.00\n"
            "07/12/26 SAMPLE INTEREST $10.00\n"
        )
    )

    assert identity.account.account_type is AccountType.LOAN
    assert identity.account.display_number == "4-12345"
    assert identity.account.last4 == "2345"
    assert identity.statement_start == date(2026, 6, 26)
    assert identity.statement_end == date(2026, 7, 12)


def test_parse_identity_without_activity_uses_invoice_date() -> None:
    identity = parse_identity(
        make_text(
            "Invoice Date07/12/26 Next Invoice Date08/12/26 "
            "Loan Account Ending4-12345\n"
        )
    )

    assert identity.statement_start == date(2026, 7, 12)
    assert identity.statement_end == date(2026, 7, 12)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            "Invoice Date07/12/26 Next Invoice Date08/12/26\n",
            "account ending was not found",
        ),
        (
            "Next Invoice Date08/12/26 Loan Account Ending4-12345\n",
            "invoice date was not found",
        ),
        (
            "Invoice Date07/12/26 Loan Account Ending4-12345\n",
            "next invoice date was not found",
        ),
    ],
)
def test_parse_identity_requires_fields(value: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_identity(make_text(value))


def test_parse_identity_requires_next_invoice_after_invoice() -> None:
    with pytest.raises(ValueError, match="must be after the invoice date"):
        parse_identity(
            make_text(
                "Invoice Date07/12/26 Next Invoice Date07/12/26 "
                "Loan Account Ending4-12345\n"
            )
        )


def test_parse_identity_rejects_activity_after_invoice_date() -> None:
    with pytest.raises(ValueError, match="activity starts after"):
        parse_identity(
            make_text(
                "Invoice Date07/12/26 Next Invoice Date08/12/26 "
                "Loan Account Ending4-12345\n"
                "07/13/26 SAMPLE ACTIVITY $10.00\n"
            )
        )
