"""
tests/processors/chase/business_credit_card/activity/test_rows.py

Tests for Chase business credit-card logical activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.chase.business_credit_card.activity import (
    ChaseBusinessCreditCardActivityRow,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(*pages: str) -> StatementText:
    """Build page-aware statement text for activity-row tests."""
    return StatementText(
        pages=tuple(
            StatementPage(number=index, text=value)
            for index, value in enumerate(pages, start=1)
        )
    )


def test_parse_signed_activity_rows() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT ACTIVITY",
                    "Date of",
                    "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                    "06/10 SAMPLE PAYMENT -125.00",
                    "06/12 SAMPLE PURCHASE 24.35",
                    "06/13 SAMPLE REFUND -8.20",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ChaseBusinessCreditCardActivityRow(
            date_text="06/10",
            description="SAMPLE PAYMENT",
            amount=Decimal("-125.00"),
            page=1,
            raw_text="06/10 SAMPLE PAYMENT -125.00",
        ),
        ChaseBusinessCreditCardActivityRow(
            date_text="06/12",
            description="SAMPLE PURCHASE",
            amount=Decimal("24.35"),
            page=1,
            raw_text="06/12 SAMPLE PURCHASE 24.35",
        ),
        ChaseBusinessCreditCardActivityRow(
            date_text="06/13",
            description="SAMPLE REFUND",
            amount=Decimal("-8.20"),
            page=1,
            raw_text="06/13 SAMPLE REFUND -8.20",
        ),
    )


def test_parse_mangled_activity_marker_and_multiple_cardholder_groups() -> (
    None
):
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "AACCCCOOUUNNTT AACCTTIIVVIITTYY",
                    "Date of",
                    "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                    "03/15 AUTOMATIC PAYMENT - THANK YOU -103.43",
                    "SAMPLE CARDHOLDER",
                    "TRANSACTIONS THIS CYCLE (CARD 1234) $103.43-",
                    "INCLUDING PAYMENTS RECEIVED",
                    "03/20 SAMPLE WIRELESS PROVIDER 45.18",
                    "SECOND CARDHOLDER",
                    "TRANSACTIONS THIS CYCLE (CARD 5678) $45.18",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert [row.description for row in rows] == [
        "AUTOMATIC PAYMENT - THANK YOU",
        "SAMPLE WIRELESS PROVIDER",
    ]
    assert [row.amount for row in rows] == [
        Decimal("-103.43"),
        Decimal("45.18"),
    ]


def test_parse_activity_across_continued_page() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT ACTIVITY",
                    "Date of",
                    "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                    "10/17 FIRST SAMPLE PURCHASE 14.32",
                )
            ),
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT ACTIVITY (CONTINUED)",
                    "Date of",
                    "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                    "10/18 SECOND SAMPLE PURCHASE 11.25",
                    "2026 Totals Year-to-Date",
                )
            ),
        )
    )

    assert len(rows) == 2
    assert rows[0].page == 1
    assert rows[1].page == 2


def test_parse_foreign_currency_continuation_and_leading_decimal() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT ACTIVITY",
                    "08/04 SAMPLE FOREIGN MERCHANT 8.81",
                    "08/05 EURO",
                    "7.60 X 1.159210526 (EXCHG RATE)",
                    "08/05 FOREIGN TRANSACTION FEE .26",
                    "2025 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows[0].continuation_lines == (
        "08/05 EURO",
        "7.60 X 1.159210526 (EXCHG RATE)",
    )
    assert rows[1].amount == Decimal("0.26")


def test_year_to_date_marker_ends_activity() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT ACTIVITY",
                    "12/14 SAMPLE PURCHASE 5.00",
                    "2026 Totals Year-to-Date",
                    "12/15 SHOULD NOT PARSE 10.00",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE PURCHASE"


def test_no_activity_returns_empty_rows() -> None:
    assert (
        parse_activity_rows(
            make_statement_text("ACCOUNT SUMMARY\nPrevious Balance $0.00")
        )
        == ()
    )


def test_unrecognized_dated_activity_row_raises() -> None:
    with pytest.raises(
        ValueError,
        match="Unrecognized Chase business credit-card transaction row",
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "ACCOUNT ACTIVITY",
                        "07/04 MALFORMED TRANSACTION ROW",
                        "2026 Totals Year-to-Date",
                    )
                )
            )
        )


def test_orphan_continuation_raises() -> None:
    with pytest.raises(
        ValueError,
        match="continuation has no transaction row",
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "ACCOUNT ACTIVITY",
                        "07/05 EUR",
                    )
                )
            )
        )


def test_orphan_exchange_rate_continuation_raises() -> None:
    with pytest.raises(
        ValueError,
        match="continuation has no transaction row",
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "ACCOUNT ACTIVITY",
                        "52,000 X 0.000047115 (EXCHG RATE)",
                    )
                )
            )
        )


def test_continuation_cannot_attach_across_activity_blocks() -> None:
    with pytest.raises(
        ValueError,
        match="continuation has no transaction row",
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "ACCOUNT ACTIVITY",
                        "07/04 SAMPLE PURCHASE 10.00",
                        "2026 Totals Year-to-Date",
                        "ACCOUNT ACTIVITY (CONTINUED)",
                        "07/05 EUR",
                    )
                )
            )
        )
