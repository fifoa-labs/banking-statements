"""
tests/processors/wellsfargo/credit_card/test_identity.py

Tests for Wells Fargo credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.wellsfargo.credit_card.identity import (
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


def test_parse_identity_uses_full_account_number_when_available() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "WELLS FARGO SAMPLE VISA CARD",
                    "Account ending in 1234",
                    "Statement Period 12/15/2023 to 01/14/2024",
                    "Account Number 1111 2222 3333 1234",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1111 2222 3333 1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2023, 12, 15)
    assert identity.statement_end == date(2024, 1, 14)


def test_parse_identity_falls_back_to_account_ending() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "WELLS FARGO SAMPLE VISA CARD",
                    "Account ending in 1234",
                    "Statement Period 12/15/2023 to 01/14/2024",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2023, 12, 15)
    assert identity.statement_end == date(2024, 1, 14)


def test_parse_identity_rejects_missing_account_ending() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo credit-card account ending was not found",
    ):
        parse_identity(
            make_statement_text(
                "Statement Period 12/15/2023 to 01/14/2024",
            )
        )


def test_parse_identity_rejects_disagreeing_account_numbers() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo credit-card account numbers do not agree",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account ending in 1234",
                        "Statement Period 12/15/2023 to 01/14/2024",
                        "Account Number 1111 2222 3333 5678",
                    )
                )
            )
        )


def test_parse_identity_rejects_missing_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo credit-card statement period was not found",
    ):
        parse_identity(
            make_statement_text(
                "Account ending in 1234",
            )
        )


def test_parse_identity_handles_end_only_statement_period() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "WELLS FARGO SAMPLE VISA CARD",
                    "Account ending in 1234",
                    "Statement Period to 05/14/2024",
                )
            )
        )
    )

    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2024, 5, 14)
    assert identity.statement_end == date(2024, 5, 14)
