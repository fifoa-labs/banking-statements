"""
tests/processors/wellsfargo/business_checking/test_identity.py

Tests for Wells Fargo business checking identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.wellsfargo.business_checking.identity import (  # noqa: E501
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for identity tests."""
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
                    "Sample Business Checking",
                    (
                        "Statement period activity summary "
                        "Account number: 1234567890"
                    ),
                    "Beginning balance on 1/1 $1,000.00",
                    "Ending balance on 1/31 $1,250.00",
                    (
                        "Fee period 01/01/2024 - 01/31/2024 "
                        "Standard monthly service fee $10.00"
                    ),
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "1234567890"
    assert identity.account.last4 == "7890"
    assert identity.statement_start == date(2024, 1, 1)
    assert identity.statement_end == date(2024, 1, 31)


def test_parse_identity_rejects_missing_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo business checking account number was not found",
    ):
        parse_identity(
            make_statement_text(
                "Fee period 01/01/2024 - 01/31/2024",
            )
        )


def test_parse_identity_rejects_missing_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo business checking statement period was not found",
    ):
        parse_identity(
            make_statement_text(
                "Statement period activity summary Account number: 1234567890",
            )
        )
