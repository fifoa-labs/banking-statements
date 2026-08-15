"""
tests/processors/wellsfargo/business_credit_card/test_identity.py

Tests for Wells Fargo business credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.wellsfargo.business_credit_card.identity import (  # noqa: E501
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
                    "SAMPLE BUSINESS CARD",
                    "CONSOLIDATED BILLING CONTROL ACCOUNT STATEMENT",
                    "Account Number 1111 2222 3333 1234",
                    "Statement Closing Date 01/27/25",
                    "Days in Billing Cycle 31",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1111 2222 3333 1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2024, 12, 28)
    assert identity.statement_end == date(2025, 1, 27)


def test_parse_identity_accepts_matching_account_ending() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number 1111 2222 3333 1234",
                    "Sample Name account ending 1234",
                    "Statement Closing Date 01/27/25",
                    "Days in Billing Cycle 31",
                )
            )
        )
    )

    assert identity.account.last4 == "1234"


def test_parse_identity_rejects_disagreeing_account_numbers() -> None:
    with pytest.raises(
        ValueError,
        match="account numbers do not agree",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number 1111 2222 3333 1234",
                        "Sample Name account ending 5678",
                        "Statement Closing Date 01/27/25",
                        "Days in Billing Cycle 31",
                    )
                )
            )
        )


def test_parse_identity_rejects_missing_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="account number was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Statement Closing Date 01/27/25",
                        "Days in Billing Cycle 31",
                    )
                )
            )
        )


def test_parse_identity_rejects_missing_closing_date() -> None:
    with pytest.raises(
        ValueError,
        match="closing date was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number 1111 2222 3333 1234",
                        "Days in Billing Cycle 31",
                    )
                )
            )
        )


def test_parse_identity_rejects_missing_billing_cycle() -> None:
    with pytest.raises(
        ValueError,
        match="billing cycle was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number 1111 2222 3333 1234",
                        "Statement Closing Date 01/27/25",
                    )
                )
            )
        )


def test_parse_identity_handles_zero_day_billing_cycle() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number 1111 2222 3333 1234",
                    "Statement Closing Date 05/27/24",
                    "Days in Billing Cycle 0",
                )
            )
        )
    )

    assert identity.statement_start == date(2024, 5, 27)
    assert identity.statement_end == date(2024, 5, 27)
