"""
tests/processors/chase/credit_card/test_identity.py

Tests for Chase credit-card statement identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.chase.credit_card.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for identity parser tests."""
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
                    "Account Number: XXXX XXXX XXXX 9062",
                    "Opening/Closing Date 03/12/26 - 04/11/26",
                    "Statement Date: 04/11/26",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "XXXX XXXX XXXX 9062"
    assert identity.account.last4 == "9062"
    assert identity.statement_start == date(2026, 3, 12)
    assert identity.statement_end == date(2026, 4, 11)
    assert identity.statement_date == date(2026, 4, 11)


def test_parse_identity_requires_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="account number was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Opening/Closing Date 03/12/26 - 04/11/26",
                        "Statement Date: 04/11/26",
                    )
                )
            )
        )


def test_parse_identity_requires_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match="statement period was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number: XXXX XXXX XXXX 9062",
                        "Statement Date: 04/11/26",
                    )
                )
            )
        )


def test_parse_identity_requires_statement_date() -> None:
    with pytest.raises(
        ValueError,
        match="statement date was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number: XXXX XXXX XXXX 9062",
                        "Opening/Closing Date 03/12/26 - 04/11/26",
                    )
                )
            )
        )


def test_parse_identity_requires_matching_closing_date() -> None:
    with pytest.raises(
        ValueError,
        match="statement date does not match the closing date",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number: XXXX XXXX XXXX 9062",
                        "Opening/Closing Date 03/12/26 - 04/11/26",
                        "Statement Date: 04/12/26",
                    )
                )
            )
        )
