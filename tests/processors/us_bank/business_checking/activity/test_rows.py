"""
tests/processors/us_bank/business_checking/activity/test_rows.py

Tests for U.S. Bank business-checking activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.us_bank.business_checking.activity import (
    USBankBusinessCheckingActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(*pages: str) -> StatementText:
    return StatementText(
        tuple(
            StatementPage(number=index, text=value)
            for index, value in enumerate(pages, start=1)
        )
    )


def test_parse_activity_rows_supports_sections_and_continuations() -> None:
    rows = parse_activity_rows(
        make_text(
            "Other Deposits\n"
            "Date Description of Transaction Ref Number Amount\n"
            "Jan2 Opening Deposit $ 25.00\n"
            "REFERENCE TOKEN\n"
            "Total Other Deposits $ 25.00",
            "Other Withdrawals (continued)\n"
            "Date Description of Transaction Ref Number Amount\n"
            "Jan 3 Sample Transfer $ 5.00-\n"
            "Total Other Withdrawals $ 5.00-",
        )
    )
    assert len(rows) == 2
    assert rows[0].section is USBankBusinessCheckingActivitySection.CREDIT
    assert rows[0].amount == Decimal("25.00")
    assert rows[0].raw_text.endswith("REFERENCE TOKEN")
    assert rows[1].section is USBankBusinessCheckingActivitySection.DEBIT
    assert rows[1].page == 2


def test_parse_activity_rows_resets_section_at_page_boundary() -> None:
    rows = parse_activity_rows(
        make_text(
            "Other Deposits\n"
            "Date Description of Transaction Ref Number Amount\n"
            "Jan 2 Sample Deposit $ 5.00",
            "Jan 3, 2026\nOther text",
        )
    )
    assert len(rows) == 1


def test_parse_activity_rows_ignores_non_activity_and_stop_markers() -> None:
    text = make_text(
        "\nOther text\n"
        "Other Deposits\n"
        "Date Description of Transaction Ref Number Amount\n"
        "Jan 2 Sample Deposit $ 5.00\n"
        "Balance Summary\n"
        "Jan 3 Not Activity $ 1.00\n"
        "ANALYSIS SERVICE CHARGE DETAIL"
    )
    assert len(parse_activity_rows(text)) == 1


def test_parse_activity_rows_rejects_direction_sign_conflicts() -> None:
    with pytest.raises(ValueError, match="deposit row"):
        parse_activity_rows(
            make_text(
                "Other Deposits\n"
                "Date Description of Transaction Ref Number Amount\n"
                "Jan 2 Bad Deposit $ 5.00-"
            )
        )
    with pytest.raises(ValueError, match="withdrawal row"):
        parse_activity_rows(
            make_text(
                "Other Withdrawals\n"
                "Date Description of Transaction Ref Number Amount\n"
                "Jan 2 Bad Withdrawal $ 5.00"
            )
        )


def test_parse_activity_rows_rejects_unknown_dated_row() -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        parse_activity_rows(
            make_text(
                "Other Deposits\n"
                "NONDATED UNKNOWN\n"
                "Date Description of Transaction Ref Number Amount\n"
                "Jan 2 malformed transaction"
            )
        )
