"""
tests/processors/capital_one/checking/test_identity.py

Tests for Capital One checking identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.capital_one.checking.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_identity_monthly_statement_and_repeated_markers() -> None:
    value = (
        "STATEMENT PERIOD\nMar 1 - Mar 31, 2026\n360 Checking - 70000001234\n"
    )

    identity = parse_identity(make_text(value + value))

    assert identity.account.account_type is AccountType.CHECKING
    assert identity.account.display_number == "70000001234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2026, 3, 1)
    assert identity.statement_end == date(2026, 3, 31)


def test_parse_identity_quarterly_statement() -> None:
    identity = parse_identity(
        make_text(
            "STATEMENT PERIOD\n"
            "Apr 1 - Jun 30, 2026\n"
            "360 Checking - 70000005678\n"
        )
    )

    assert identity.statement_start == date(2026, 4, 1)
    assert identity.statement_end == date(2026, 6, 30)


def test_parse_identity_resolves_cross_year_start_date() -> None:
    identity = parse_identity(
        make_text(
            "STATEMENT PERIOD\n"
            "Dec 1 - Jan 31, 2026\n"
            "360 Checking - 70000005678\n"
        )
    )

    assert identity.statement_start == date(2025, 12, 1)
    assert identity.statement_end == date(2026, 1, 31)


def test_parse_identity_resolves_prior_year_leap_day() -> None:
    identity = parse_identity(
        make_text(
            "STATEMENT PERIOD\n"
            "Feb 29 - Jan 31, 2025\n"
            "360 Checking - 70000005678\n"
        )
    )

    assert identity.statement_start == date(2024, 2, 29)


@pytest.mark.parametrize(
    "value",
    [
        "STATEMENT PERIOD\nMar 1 - Mar 31, 2026\n",
        (
            "STATEMENT PERIOD\n"
            "Mar 1 - Mar 31, 2026\n"
            "360 Checking - 70000001234\n"
            "360 Checking - 70000005678\n"
        ),
    ],
)
def test_parse_identity_requires_unique_account_number(value: str) -> None:
    with pytest.raises(
        ValueError, match="account number was not found uniquely"
    ):
        parse_identity(make_text(value))


@pytest.mark.parametrize(
    "value",
    [
        "360 Checking - 70000001234\n",
        (
            "360 Checking - 70000001234\n"
            "STATEMENT PERIOD\nMar 1 - Mar 31, 2026\n"
            "STATEMENT PERIOD\nApr 1 - Apr 30, 2026\n"
        ),
    ],
)
def test_parse_identity_requires_unique_statement_period(value: str) -> None:
    with pytest.raises(
        ValueError, match="statement period was not found uniquely"
    ):
        parse_identity(make_text(value))


def test_parse_identity_rejects_invalid_end_date() -> None:
    with pytest.raises(ValueError, match="statement date"):
        parse_identity(
            make_text(
                "360 Checking - 70000001234\n"
                "STATEMENT PERIOD\nMar 1 - Feb 30, 2026\n"
            )
        )


def test_parse_identity_rejects_invalid_start_date() -> None:
    with pytest.raises(ValueError, match="statement date"):
        parse_identity(
            make_text(
                "360 Checking - 70000001234\n"
                "STATEMENT PERIOD\nFeb 30 - Mar 31, 2026\n"
            )
        )


def test_parse_identity_rejects_unresolvable_leap_day() -> None:
    with pytest.raises(ValueError, match="statement date"):
        parse_identity(
            make_text(
                "360 Checking - 70000001234\n"
                "STATEMENT PERIOD\nFeb 29 - Mar 31, 2023\n"
            )
        )
