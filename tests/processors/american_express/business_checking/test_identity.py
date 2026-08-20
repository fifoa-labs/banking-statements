"""
tests/processors/american_express/business_checking/test_identity.py

Tests for American Express business-checking statement identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.american_express.business_checking.identity import (  # noqa: E501
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
                    "StatementPeriod",
                    "04/01/2023 - 04/30/2023",
                    "Business Checking Account Statement",
                    "AccountEnding *4625",
                    "AccountName General Operations",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "4625"
    assert identity.account.last4 == "4625"
    assert identity.statement_start == date(2023, 4, 1)
    assert identity.statement_end == date(2023, 4, 30)


def test_parse_identity_requires_account_ending() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking account ending was not found."  # noqa: RUF043
        ),
    ):
        parse_identity(
            make_statement_text("StatementPeriod\n04/01/2023 - 04/30/2023")
        )


def test_parse_identity_requires_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking statement period was not found."  # noqa: E501, RUF043
        ),
    ):
        parse_identity(
            make_statement_text(
                "Business Checking Account Statement\nAccountEnding *4625"
            )
        )


def test_parse_identity_current_layout() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Business Checking Account Statement",
                    (
                        "Statement Date: 04/30/2024 "
                        "Account Ending: * 4625 "
                        "Account Name: General Operations"
                    ),
                    "Beginning Balance as of 04/01/2024 $100.00",
                    "Ending Balance as of 04/30/2024 $125.00",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "4625"
    assert identity.account.last4 == "4625"
    assert identity.statement_start == date(2024, 4, 1)
    assert identity.statement_end == date(2024, 4, 30)
