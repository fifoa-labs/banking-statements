"""
tests/processors/us_bank/business_checking/test_identity.py

Tests for U.S. Bank business-checking identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.processors.us_bank.business_checking.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText((StatementPage(number=1, text=value),))


def test_parse_identity_resolves_cross_year_period() -> None:
    identity = parse_identity(
        make_text(
            "Account Number: 9-876-5432-1000\n"
            "Beginning Balance on Dec 30 $ 10.00\n"
            "Ending Balance on Jan 2, 2026 $ 10.00"
        )
    )
    assert identity.account.last4 == "1000"
    assert identity.statement_start == date(2025, 12, 30)
    assert identity.statement_end == date(2026, 1, 2)


def test_parse_identity_accepts_leap_day_from_prior_year() -> None:
    identity = parse_identity(
        make_text(
            "Account Number: 9 876 5432 1000\n"
            "Beginning Balance on Feb 29 $ 1.00\n"
            "Ending Balance on Mar 1, 2025 $ 1.00"
        )
    )
    assert identity.statement_start == date(2024, 2, 29)


def test_parse_identity_rejects_missing_or_ambiguous_account() -> None:
    with pytest.raises(ValueError, match="account number"):
        parse_identity(
            make_text(
                "Beginning Balance on Jan 1 $ 1.00\n"
                "Ending Balance on Jan 31, 2026 $ 1.00"
            )
        )
    with pytest.raises(ValueError, match="account number"):
        parse_identity(
            make_text(
                "Account Number: 9-876-5432-1000\n"
                "Account Number: 8-765-4321-2000\n"
                "Beginning Balance on Jan 1 $ 1.00\n"
                "Ending Balance on Jan 31, 2026 $ 1.00"
            )
        )


def test_parse_identity_rejects_missing_or_ambiguous_period() -> None:
    base = "Account Number: 9-876-5432-1000\n"
    with pytest.raises(ValueError, match="statement period"):
        parse_identity(make_text(base))
    with pytest.raises(ValueError, match="statement period"):
        parse_identity(
            make_text(
                base
                + "Beginning Balance on Jan 1 $ 1.00\n"
                + "Ending Balance on Jan 31, 2026 $ 1.00\n"
                + "Beginning Balance on Feb 1 $ 1.00\n"
                + "Ending Balance on Feb 28, 2026 $ 1.00"
            )
        )


def test_parse_identity_rejects_unresolvable_start_date() -> None:
    with pytest.raises(ValueError, match="Invalid U.S. Bank"):  # noqa: RUF043
        parse_identity(
            make_text(
                "Account Number: 9-876-5432-1000\n"
                "Beginning Balance on Feb 29 $ 1.00\n"
                "Ending Balance on Jan 31, 2023 $ 1.00"
            )
        )
