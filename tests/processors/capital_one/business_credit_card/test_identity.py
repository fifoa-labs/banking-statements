"""
tests/processors/capital_one/business_credit_card/test_identity.py

Tests for Capital One business credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.capital_one.business_credit_card.identity import (  # noqa: E501
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_legacy_spark_identity() -> None:
    identity = parse_identity(
        make_text(
            "Spark® Visa Signature Business Account Ending in 1234\n"
            "Dec. 18, 2025 - Jan. 17, 2026 | 31 days in Billing Cycle\n"
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2025, 12, 18)
    assert identity.statement_end == date(2026, 1, 17)
    assert identity.billing_days == 31


@pytest.mark.parametrize(
    "title",
    [
        "Spark Cash credit card | Visa Signature Business ending in 5678",
        "Venture X Business card | Visa Infinite Business ending in 5678",
    ],
)
def test_parse_current_business_identity(title: str) -> None:
    identity = parse_identity(
        make_text(
            f"{title}\nMar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
        )
    )

    assert identity.account.display_number == "5678"
    assert identity.account.last4 == "5678"
    assert identity.statement_start == date(2026, 3, 1)
    assert identity.statement_end == date(2026, 3, 31)


def test_parse_identity_accepts_repeated_same_title_and_period() -> None:
    value = (
        "Spark Cash credit card | Visa Signature Business ending in 1234\n"
        "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
    )

    identity = parse_identity(make_text(value + value))

    assert identity.account.last4 == "1234"


def test_parse_identity_rejects_conflicting_account_endings() -> None:
    with pytest.raises(ValueError, match="account ending.*uniquely"):  # noqa: RUF043
        parse_identity(
            make_text(
                "Spark Cash credit card | Visa Signature Business ending in 1234\n"  # noqa: E501
                "Venture X Business card | Visa Infinite Business ending in 5678\n"  # noqa: E501
                "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            )
        )


def test_parse_identity_requires_account_ending() -> None:
    with pytest.raises(ValueError, match="account ending"):
        parse_identity(
            make_text(
                "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
            )
        )


def test_parse_identity_requires_unique_statement_period() -> None:
    with pytest.raises(ValueError, match="statement period.*uniquely"):  # noqa: RUF043
        parse_identity(
            make_text(
                "Spark Cash credit card | Visa Signature Business ending in 1234\n"  # noqa: E501
            )
        )


def test_parse_identity_rejects_reversed_statement_period() -> None:
    with pytest.raises(ValueError, match="starts after it ends"):
        parse_identity(
            make_text(
                "Spark Cash credit card | Visa Signature Business ending in 1234\n"  # noqa: E501
                "Mar 31, 2026 - Mar 1, 2026 | 31 days in Billing Cycle\n"
            )
        )


def test_parse_identity_rejects_incorrect_billing_day_count() -> None:
    with pytest.raises(ValueError, match="day count does not match"):
        parse_identity(
            make_text(
                "Spark Cash credit card | Visa Signature Business ending in 1234\n"  # noqa: E501
                "Mar 1, 2026 - Mar 31, 2026 | 30 days in Billing Cycle\n"
            )
        )
