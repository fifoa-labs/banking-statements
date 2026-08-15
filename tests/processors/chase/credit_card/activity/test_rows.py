"""
tests/processors/chase/credit_card/activity/test_rows.py

Tests for Chase credit-card logical activity row reconstruction.
"""

from __future__ import annotations

from banking_statements.processors.chase.credit_card.activity import (
    ActivityRow,
    ActivitySection,
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


def test_parse_simple_purchase_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT ACTIVITY",
                    "Date of",
                    "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
                    "PURCHASE",
                    "03/30 RVT*Katy ISD 281-3966000 TX 8.25",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="RVT*Katy ISD 281-3966000 TX",
            amount_text="8.25",
        ),
    )


def test_parse_foreign_currency_purchase_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 Grab* A-9FNGAQLWWUVDAV HA NOI 1.66",
                    "06/18 DONG",
                    "43,680 X 0.000038003 (EXCHG RATE)",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="Grab* A-9FNGAQLWWUVDAV HA NOI",
            amount_text="1.66",
            continuation_lines=(
                "06/18 DONG",
                "43,680 X 0.000038003 (EXCHG RATE)",
            ),
        ),
    )


def test_parse_fee_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 95.00",
                    "TOTAL FEES FOR THIS PERIOD $95.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.FEES_CHARGED,
            date_text="07/01",
            description="ANNUAL MEMBERSHIP FEE",
            amount_text="95.00",
        ),
    )


def test_parse_multiple_sections() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 SAMPLE MERCHANT 1.66",
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 95.00",
                    "TOTAL FEES FOR THIS PERIOD $95.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="SAMPLE MERCHANT",
            amount_text="1.66",
        ),
        ActivityRow(
            section=ActivitySection.FEES_CHARGED,
            date_text="07/01",
            description="ANNUAL MEMBERSHIP FEE",
            amount_text="95.00",
        ),
    )


def test_ignores_blank_lines() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "",
                    "PURCHASE",
                    "",
                    "03/30 SAMPLE MERCHANT 8.25",
                    "",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="SAMPLE MERCHANT",
            amount_text="8.25",
        ),
    )


def test_ignores_text_outside_activity_sections() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT SUMMARY",
                    "03/30 THIS LOOKS LIKE A TRANSACTION 8.25",
                    "OTHER TEXT",
                )
            )
        )
    )

    assert rows == ()


def test_section_change_flushes_pending_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 SAMPLE MERCHANT 1.66",
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 95.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="SAMPLE MERCHANT",
            amount_text="1.66",
        ),
        ActivityRow(
            section=ActivitySection.FEES_CHARGED,
            date_text="07/01",
            description="ANNUAL MEMBERSHIP FEE",
            amount_text="95.00",
        ),
    )


def test_stop_marker_without_pending_row_ends_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "2026 Totals Year-to-Date",
                    "03/30 SHOULD NOT PARSE 8.25",
                )
            )
        )
    )

    assert rows == ()


def test_stop_marker_flushes_pending_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "03/30 SAMPLE MERCHANT 8.25",
                    "2026 Totals Year-to-Date",
                    "03/31 SHOULD NOT PARSE 9.25",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="SAMPLE MERCHANT",
            amount_text="8.25",
        ),
    )


def test_consecutive_transaction_rows_flush_previous_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 FIRST MERCHANT 1.66",
                    "06/18 SECOND MERCHANT 2.25",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="FIRST MERCHANT",
            amount_text="1.66",
        ),
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/18",
            description="SECOND MERCHANT",
            amount_text="2.25",
        ),
    )


def test_continuation_without_pending_row_is_ignored() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/18 DONG",
                    "43,680 X 0.000038003 (EXCHG RATE)",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == ()


def test_unknown_line_with_pending_row_is_ignored() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "03/30 SAMPLE MERCHANT 8.25",
                    "SOME UNRECOGNIZED DETAIL",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="SAMPLE MERCHANT",
            amount_text="8.25",
        ),
    )


def test_final_pending_row_is_flushed_at_end_of_text() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "03/30 SAMPLE MERCHANT 8.25",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="SAMPLE MERCHANT",
            amount_text="8.25",
        ),
    )


def test_year_to_date_marker_is_not_year_specific() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "12/20 SAMPLE MERCHANT 10.00",
                    "2031 Totals Year-to-Date",
                    "12/21 SHOULD NOT PARSE 20.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="12/20",
            description="SAMPLE MERCHANT",
            amount_text="10.00",
        ),
    )


def test_total_fees_summary_ends_activity_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 95.00",
                    "Total fees charged in 2026 $95.00",
                    "07/02 SHOULD NOT PARSE 20.00",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "ANNUAL MEMBERSHIP FEE"


def test_total_interest_summary_ends_activity_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "03/30 SAMPLE MERCHANT 8.25",
                    "Total interest charged in 2026 $0.00",
                    "03/31 SHOULD NOT PARSE 9.25",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE MERCHANT"
