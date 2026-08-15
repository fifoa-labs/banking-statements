"""
tests/processors/chase/checking/activity/test_rows.py

Tests for Chase checking transaction-detail row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.chase.checking.activity import (
    ChaseCheckingActivityRow,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for activity-row tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_parse_activity_rows() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "*start*transactiondetail",
                    "TRANSACTION DETAIL",
                    "DATE DESCRIPTION AMOUNT BALANCE",
                    "",
                    "Beginning Balance $1,000.00",
                    "01/05 SAMPLE DEPOSIT 200.00 1,200.00",
                    "01/10 SAMPLE PAYMENT -50.00 1,150.00",
                    "Ending Balance $1,150.00",
                    "*end*transactiondetail",
                )
            )
        )
    )

    assert rows == (
        ChaseCheckingActivityRow(
            transaction_date="01/05",
            description="SAMPLE DEPOSIT",
            amount=Decimal("200.00"),
            balance=Decimal("1200.00"),
        ),
        ChaseCheckingActivityRow(
            transaction_date="01/10",
            description="SAMPLE PAYMENT",
            amount=Decimal("-50.00"),
            balance=Decimal("1150.00"),
        ),
    )


def test_parse_activity_rows_across_multiple_sections() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "*start*transactiondetail",
                    "TRANSACTION DETAIL",
                    "DATE DESCRIPTION AMOUNT BALANCE",
                    "Beginning Balance $500.00",
                    "12/30 SAMPLE PAYMENT -25.00 475.00",
                    "*end*transactiondetail",
                    "*start*transactiondetail",
                    "TRANSACTION DETAIL (continued)",
                    "DATE DESCRIPTION AMOUNT BALANCE",
                    "01/02 SAMPLE DEPOSIT 100.00 575.00",
                    "Ending Balance $575.00",
                    "*end*transactiondetail",
                )
            )
        )
    )

    assert len(rows) == 2

    assert rows[0].transaction_date == "12/30"
    assert rows[0].amount == Decimal("-25.00")
    assert rows[0].balance == Decimal("475.00")

    assert rows[1].transaction_date == "01/02"
    assert rows[1].amount == Decimal("100.00")
    assert rows[1].balance == Decimal("575.00")


def test_parse_activity_rows_preserves_description() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "*start*transactiondetail",
                    "TRANSACTION DETAIL",
                    "DATE DESCRIPTION AMOUNT BALANCE",
                    (
                        "01/15 SAMPLE ACH PAYMENT PPD ID: 1234567890 "
                        "-125.75 874.25"
                    ),
                    "*end*transactiondetail",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE ACH PAYMENT PPD ID: 1234567890"


def test_parse_activity_rows_rejects_unrecognized_transaction_line() -> None:
    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "*start*transactiondetail",
                "TRANSACTION DETAIL",
                "DATE DESCRIPTION AMOUNT BALANCE",
                "01/15 THIS ROW IS MALFORMED",
                "*end*transactiondetail",
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unrecognized Chase checking transaction row:",
    ):
        parse_activity_rows(text)


def test_parse_activity_rows_returns_empty_without_transaction_sections() -> (
    None
):
    rows = parse_activity_rows(
        make_statement_text("CHECKING SUMMARY Chase Total Checking")
    )

    assert rows == ()


def test_parse_activity_rows_appends_numeric_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "*start*transactiondetail",
                    "TRANSACTION DETAIL",
                    "DATE DESCRIPTION AMOUNT BALANCE",
                    (
                        "06/06 SAMPLE ZELLE PAYMENT FROM EXAMPLE BUSINESS "
                        "895.00 5,492.68"
                    ),
                    "8304631522",
                    "*end*transactiondetail",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == (
        "SAMPLE ZELLE PAYMENT FROM EXAMPLE BUSINESS 8304631522"
    )
    assert rows[0].amount == Decimal("895.00")
    assert rows[0].balance == Decimal("5492.68")


def test_parse_activity_rows_appends_text_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "*start*transactiondetail",
                    "TRANSACTION DETAIL",
                    "DATE DESCRIPTION AMOUNT BALANCE",
                    (
                        "04/08 Returned Item Fee For An Unpaid $250.00 Item "
                        "- Details: SAMPLE -34.00 966.00"
                    ),
                    "ACH Pmt A1234 Web ID: 1234567890",
                    "*end*transactiondetail",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == (
        "Returned Item Fee For An Unpaid $250.00 Item - Details: "
        "SAMPLE ACH Pmt A1234 Web ID: 1234567890"
    )


def test_parse_activity_rows_rejects_orphan_continuation() -> None:
    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "*start*transactiondetail",
                "TRANSACTION DETAIL",
                "DATE DESCRIPTION AMOUNT BALANCE",
                "ORPHAN CONTINUATION TEXT",
                "*end*transactiondetail",
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unrecognized Chase checking transaction row:",
    ):
        parse_activity_rows(text)
