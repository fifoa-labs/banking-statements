"""
tests/processors/wellsfargo/checking/test_identity.py

Tests for Wells Fargo checking identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.wellsfargo.checking.identity import (
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
            "Wells Fargo College Checking\n"
            "Activity sum mary Account number: 1234567890\n"
            "Fee period 12/14/2018 - 01/14/2019\n"
        )
    )

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "1234567890"
    assert identity.account.last4 == "7890"
    assert identity.statement_start == date(2018, 12, 14)
    assert identity.statement_end == date(2019, 1, 14)


def test_parse_identity_rejects_missing_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo checking account number was not found",
    ):
        parse_identity(
            make_statement_text(
                "Wells Fargo College Checking\n"
                "Fee period 12/14/2018 - 01/14/2019\n"
            )
        )


def test_parse_identity_rejects_missing_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo checking statement period was not found",
    ):
        parse_identity(
            make_statement_text(
                "Wells Fargo College Checking\n"
                "Activity sum mary Account number: 1234567890\n"
            )
        )


def test_parse_identity_handles_statement_period_activity_summary() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Wells Far go College Checking®",
                    "Statement p eriod activity summary Account number: 1234567890",  # noqa: E501
                    "Fee period 12/12/2020 - 01/14/2021",
                )
            )
        )
    )

    assert identity.account.display_number == "1234567890"
    assert identity.account.last4 == "7890"
    assert identity.statement_start == date(2020, 12, 12)
    assert identity.statement_end == date(2021, 1, 14)
