"""
tests/processors/capital_one/checking/activity/test_rows.py

Tests for Capital One checking logical activity rows.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.capital_one.checking.activity import (
    CapitalOneCheckingActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_activity_rows_and_running_balances() -> None:
    rows = parse_activity_rows(
        make_text(
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Mar 1 Opening Balance $100.00\n"
            "Page 1 of 2\n"
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Mar 5 SAMPLE PAYROLL Credit + $50.00 $150.00\n"
            "Mar 10 SAMPLE PAYMENT Debit - $25.00 $125.00\n"
            "Mar 31 Closing Balance $125.00\n"
            "Fees Summary\n"
        )
    )

    assert len(rows) == 2

    credit, debit = rows

    assert credit.transaction_date == "Mar 5"
    assert credit.description == "SAMPLE PAYROLL"
    assert credit.amount == Decimal("50.00")
    assert credit.balance == Decimal("150.00")
    assert credit.section is CapitalOneCheckingActivitySection.CREDIT
    assert credit.raw_text == ("Mar 5 SAMPLE PAYROLL Credit + $50.00 $150.00")

    assert debit.transaction_date == "Mar 10"
    assert debit.amount == Decimal("25.00")
    assert debit.section is CapitalOneCheckingActivitySection.DEBIT


def test_parse_wrapped_description_and_reference_evidence() -> None:
    rows = parse_activity_rows(
        make_text(
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Aug 1 Opening Balance $0.00\n"
            "Page 1 of 2\n"
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Deposit from SAMPLE FINANCIAL TRANSFER\n"
            "Aug 13 Credit + $250.00 $250.00\n"
            "ABC123DEF456GHI\n"
            "Aug 31 Closing Balance $250.00\n"
        )
    )

    assert len(rows) == 1

    row = rows[0]

    assert row.description == "Deposit from SAMPLE FINANCIAL TRANSFER"
    assert row.amount == Decimal("250.00")
    assert row.section is CapitalOneCheckingActivitySection.CREDIT
    assert row.raw_text == (
        "Deposit from SAMPLE FINANCIAL TRANSFER\n"
        "Aug 13 Credit + $250.00 $250.00\n"
        "ABC123DEF456GHI"
    )


def test_parse_activity_rows_appends_post_row_continuation() -> None:
    rows = parse_activity_rows(
        make_text(
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
            "Mar 1 Opening Balance $100.00\n"
            "Mar 5 SAMPLE TRANSFER Credit + $25.00 $125.00\n"
            "ADDITIONAL TRANSFER DETAIL\n"
            "Mar 31 Closing Balance $125.00\n"
            "capitalone.com\n"
        )
    )

    assert rows[0].description == (
        "SAMPLE TRANSFER ADDITIONAL TRANSFER DETAIL"
    )
    assert rows[0].raw_text.endswith("ADDITIONAL TRANSFER DETAIL")


def test_parse_zero_activity_statement() -> None:
    assert (
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Apr 1 Opening Balance $10.00\n"
                "Page 1 of 2\n"
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "\n"
                "Apr 30 Closing Balance $10.00\n"
                "capitalone.com\n"
            )
        )
        == ()
    )


@pytest.mark.parametrize(
    "line",
    [
        "Mar 5 SAMPLE CREDIT Credit - $25.00 $125.00",
        "Mar 5 SAMPLE DEBIT Debit + $25.00 $75.00",
    ],
)
def test_parse_activity_rows_rejects_category_sign_mismatch(
    line: str,
) -> None:
    with pytest.raises(ValueError, match="category and sign do not agree"):
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
                f"{line}\n"
                "Mar 31 Closing Balance $125.00\n"
            )
        )


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(ValueError, match="Unrecognized Capital One"):
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
                "Mar 5 MALFORMED TRANSACTION\n"
                "Mar 31 Closing Balance $100.00\n"
            )
        )


def test_parse_wrapped_row_requires_description() -> None:
    with pytest.raises(ValueError, match="did not have a description"):
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
                "Mar 5 Credit + $25.00 $125.00\n"
                "Mar 31 Closing Balance $125.00\n"
            )
        )


def test_parse_activity_rows_rejects_orphan_continuation() -> None:
    with pytest.raises(ValueError, match="orphan continuation"):
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
                "ORPHAN DETAIL\n"
                "Page 1 of 1\n"
                "Mar 31 Closing Balance $100.00\n"
            )
        )


def test_parse_activity_rows_rejects_running_balance_mismatch() -> None:
    with pytest.raises(ValueError, match="running balance"):
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
                "Mar 5 SAMPLE CREDIT Credit + $25.00 $130.00\n"
                "Mar 31 Closing Balance $130.00\n"
            )
        )


def test_parse_activity_rows_rejects_closing_balance_mismatch() -> None:
    with pytest.raises(ValueError, match="reported closing balance"):
        parse_activity_rows(
            make_text(
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
                "Mar 5 SAMPLE CREDIT Credit + $25.00 $125.00\n"
                "Mar 31 Closing Balance $130.00\n"
            )
        )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            (
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 31 Closing Balance $100.00\n"
            ),
            "opening balance",
        ),
        (
            (
                "DATE DESCRIPTION CATEGORY AMOUNT BALANCE\n"
                "Mar 1 Opening Balance $100.00\n"
            ),
            "closing balance",
        ),
    ],
)
def test_parse_activity_rows_requires_boundary_balances(
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_activity_rows(make_text(value))
