"""
tests/processors/us_bank/credit_card/test_identity.py

Tests for U.S. Bank credit-card identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.processors.us_bank.credit_card.identity import (
    _last4,
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText((StatementPage(number=1, text=value),))


def test_parse_identity_supports_full_and_masked_accounts() -> None:
    full = parse_identity(
        make_text(
            "Account Number: 9999 8888 7777 1234\n01/02/2026 -02/03/2026"
        )
    )
    masked = parse_identity(
        make_text(
            "Account Ending in: #### #### #### 4321\n"
            "Open Date:12/10/2025 Closing Date:01/09/2026\n"
            "12/10/2025 -01/09/2026"
        )
    )
    assert full.account.last4 == "1234"
    assert full.statement_start == date(2026, 1, 2)
    assert masked.account.last4 == "4321"
    assert masked.statement_end == date(2026, 1, 9)


def test_parse_identity_supports_inline_account_label() -> None:
    identity = parse_identity(
        make_text(
            "Open Date:01/01/2026 Closing Date:01/31/2026 "
            "Account: 1111 2222 3333 4444\n"
            "01/01/2026 -01/31/2026"
        )
    )
    assert identity.account.last4 == "4444"


def test_parse_identity_rejects_missing_or_ambiguous_account() -> None:
    with pytest.raises(ValueError, match="account ending"):
        parse_identity(make_text("01/01/2026 -01/31/2026"))
    with pytest.raises(ValueError, match="account ending"):
        parse_identity(
            make_text(
                "Account Number: 1111 2222 3333 4444\n"
                "Account Number: 5555 6666 7777 8888\n"
                "01/01/2026 -01/31/2026"
            )
        )


def test_parse_identity_rejects_missing_ambiguous_or_reversed_period() -> None:
    account = "Account Number: 1111 2222 3333 4444\n"
    with pytest.raises(ValueError, match="statement period"):
        parse_identity(make_text(account))
    with pytest.raises(ValueError, match="statement period"):
        parse_identity(
            make_text(
                account + "01/01/2026 -01/31/2026\n" + "02/01/2026 -02/28/2026"
            )
        )
    with pytest.raises(ValueError, match="starts after"):
        parse_identity(make_text(account + "02/01/2026 -01/31/2026"))


def test_parse_identity_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError, match="Invalid U.S. Bank"):  # noqa: RUF043
        parse_identity(
            make_text(
                "Account Number: 1111 2222 3333 4444\n02/30/2026 -03/01/2026"
            )
        )


def test_last4_rejects_short_display() -> None:
    with pytest.raises(ValueError, match="account ending"):
        _last4("12")
