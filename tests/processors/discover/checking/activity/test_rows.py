"""
tests/processors/discover/checking/activity/test_rows.py

Tests for Discover checking activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.discover.checking.activity import (
    DiscoverCheckingActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_deposit_rows_and_continuation() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Apr 13 Apr 13 SAMPLE PAYROLL $ 250.00\n"
            "ADDITIONAL DETAIL\n"
            "Apr 27 Apr 27 SAMPLE DEPOSIT 9.01\n"
            "TOTAL DEPOSITS AND CREDITS $ 259.01\n"
            "Contact Us\n"
        )
    )

    assert len(rows) == 2
    assert rows[0].effective_date == "Apr 13"
    assert rows[0].posting_date == "Apr 13"
    assert rows[0].description == "SAMPLE PAYROLL ADDITIONAL DETAIL"
    assert rows[0].amount == Decimal("250.00")
    assert rows[0].section is DiscoverCheckingActivitySection.CREDIT
    assert rows[1].amount == Decimal("9.01")


@pytest.mark.parametrize(
    "section",
    [
        "Checks",
        "ATM and Debit Card Withdrawals",
        "Electronic Withdrawals",
        "Fees and Other Withdrawals",
        "Service Charges, Fees, and Other Withdrawals",
    ],
)
def test_parse_supported_debit_sections(section: str) -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            f"{section}\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Apr 10 Apr 10 SAMPLE WITHDRAWAL 25.00\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].section is DiscoverCheckingActivitySection.DEBIT


def test_parse_activity_rows_returns_empty_without_activity_section() -> None:
    assert parse_activity_rows(make_text("ACCOUNT SUMMARY\n")) == ()


def test_parse_activity_rows_rejects_header_without_supported_section() -> (
    None
):
    with pytest.raises(ValueError, match="header appeared without"):
        parse_activity_rows(
            make_text(
                "ACCOUNT ACTIVITY\nEff. Date Bus. Date Description Amount\n"
            )
        )


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(ValueError, match="Unrecognized Discover checking"):
        parse_activity_rows(
            make_text(
                "ACCOUNT ACTIVITY\n"
                "Deposits and Credits\n"
                "Eff. Date Bus. Date Description Amount\n"
                "Apr 13 MALFORMED TRANSACTION\n"
            )
        )


def test_parse_activity_rows_ignores_content_before_header() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Informational text\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Apr 13 Apr 13 SAMPLE DEPOSIT 10.00\n"
        )
    )

    assert len(rows) == 1


def test_total_resets_section() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Apr 13 Apr 13 SAMPLE DEPOSIT 10.00\n"
            "TOTAL DEPOSITS AND CREDITS $ 10.00\n"
            "Apr 14 Apr 14 NOT IN SECTION 5.00\n"
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_blank_and_pretransaction_detail() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Eff. Date Bus. Date Description Amount\n"
            "\n"
            "Informational detail before first transaction\n"
            "Apr 13 Apr 13 SAMPLE DEPOSIT 10.00\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE DEPOSIT"


def test_parse_activity_rows_across_multiple_activity_blocks() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Jun 08 Jun 08 SAMPLE DEPOSIT 250.00\n"
            "TOTAL DEPOSITS AND CREDITS $ 250.00\n"
            "Contact Us\n"
            "ACCOUNT ACTIVITY\n"
            "Electronic Withdrawals\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Jun 27 Jun 27 SAMPLE PAYMENT 40.00\n"
            "Jun 28 Jun 28 SAMPLE TRANSFER 100.00\n"
            "TOTAL ELECTRONIC WITHDRAWALS $ 140.00\n"
            "Overdraft/Returned Item Fees Summary\n"
        )
    )

    assert len(rows) == 3

    assert rows[0].description == "SAMPLE DEPOSIT"
    assert rows[0].amount == Decimal("250.00")
    assert rows[0].section is DiscoverCheckingActivitySection.CREDIT

    assert rows[1].description == "SAMPLE PAYMENT"
    assert rows[1].amount == Decimal("40.00")
    assert rows[1].section is DiscoverCheckingActivitySection.DEBIT

    assert rows[2].description == "SAMPLE TRANSFER"
    assert rows[2].amount == Decimal("100.00")
    assert rows[2].section is DiscoverCheckingActivitySection.DEBIT


def test_parse_activity_rows_reuses_header_across_sections() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Deposits and Credits\n"
            "Eff. Date Bus. Date Description Amount\n"
            "Nov 09 Nov 09 SAMPLE DEPOSIT 250.00\n"
            "TOTAL DEPOSITS AND CREDITS $ 250.00\n"
            "Electronic Withdrawals\n"
            "Nov 11 Nov 13 SAMPLE TRANSFER 125.00\n"
            "TOTAL ELECTRONIC WITHDRAWALS $ 125.00\n"
        )
    )

    assert len(rows) == 2

    assert rows[0].description == "SAMPLE DEPOSIT"
    assert rows[0].amount == Decimal("250.00")
    assert rows[0].section is DiscoverCheckingActivitySection.CREDIT

    assert rows[1].description == "SAMPLE TRANSFER"
    assert rows[1].amount == Decimal("125.00")
    assert rows[1].section is DiscoverCheckingActivitySection.DEBIT


def test_parse_activity_rows_accepts_system_date_header() -> None:
    rows = parse_activity_rows(
        make_text(
            "ACCOUNT ACTIVITY\n"
            "Electronic Withdrawals\n"
            "Eff. Date Syst. Date Description Amount\n"
            "Jan 10 Jan 12 SAMPLE PAYMENT 25.00\n"
            "TOTAL ELECTRONIC WITHDRAWALS $ 25.00\n"
        )
    )

    assert len(rows) == 1

    row = rows[0]
    assert row.effective_date == "Jan 10"
    assert row.posting_date == "Jan 12"
    assert row.description == "SAMPLE PAYMENT"
    assert row.amount == Decimal("25.00")
    assert row.section is DiscoverCheckingActivitySection.DEBIT
