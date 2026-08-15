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
                    "03/30 EXAMPLE MARKETPLACE 18.45",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="EXAMPLE MARKETPLACE",
            amount_text="18.45",
        ),
    )


def test_parse_payments_and_other_credits_rows() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PAYMENTS AND OTHER CREDITS",
                    "07/14 ONLINE PAYMENT -245.60",
                    "07/28 MERCHANT REFUND -31.25",
                    "07/27 SAMPLE STORE REFUND -48.70",
                    "PURCHASE",
                    "07/04 SAMPLE PURCHASE 27.80",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
            date_text="07/14",
            description="ONLINE PAYMENT",
            amount_text="-245.60",
        ),
        ActivityRow(
            section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
            date_text="07/28",
            description="MERCHANT REFUND",
            amount_text="-31.25",
        ),
        ActivityRow(
            section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
            date_text="07/27",
            description="SAMPLE STORE REFUND",
            amount_text="-48.70",
        ),
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="07/04",
            description="SAMPLE PURCHASE",
            amount_text="27.80",
        ),
    )


def test_parse_foreign_currency_purchase_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 EXAMPLE FOREIGN MERCHANT 2.45",
                    "06/18 TESTCUR",
                    "52,000 X 0.000047115 (EXCHG RATE)",
                    "2026 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="EXAMPLE FOREIGN MERCHANT",
            amount_text="2.45",
            continuation_lines=(
                "06/18 TESTCUR",
                "52,000 X 0.000047115 (EXCHG RATE)",
            ),
        ),
    )


def test_parse_fee_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 75.00",
                    "TOTAL FEES FOR THIS PERIOD $75.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.FEES_CHARGED,
            date_text="07/01",
            description="ANNUAL MEMBERSHIP FEE",
            amount_text="75.00",
        ),
    )


def test_parse_multiple_sections() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 SAMPLE MERCHANT 12.35",
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 75.00",
                    "TOTAL FEES FOR THIS PERIOD $75.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="SAMPLE MERCHANT",
            amount_text="12.35",
        ),
        ActivityRow(
            section=ActivitySection.FEES_CHARGED,
            date_text="07/01",
            description="ANNUAL MEMBERSHIP FEE",
            amount_text="75.00",
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
                    "03/30 SAMPLE MERCHANT 18.45",
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
            amount_text="18.45",
        ),
    )


def test_ignores_text_outside_activity_sections() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "ACCOUNT SUMMARY",
                    "03/30 THIS LOOKS LIKE A TRANSACTION 18.45",
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
                    "06/17 SAMPLE MERCHANT 12.35",
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 75.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/17",
            description="SAMPLE MERCHANT",
            amount_text="12.35",
        ),
        ActivityRow(
            section=ActivitySection.FEES_CHARGED,
            date_text="07/01",
            description="ANNUAL MEMBERSHIP FEE",
            amount_text="75.00",
        ),
    )


def test_stop_marker_without_pending_row_ends_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "2026 Totals Year-to-Date",
                    "03/30 SHOULD NOT PARSE 18.45",
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
                    "03/30 SAMPLE MERCHANT 18.45",
                    "2026 Totals Year-to-Date",
                    "03/31 SHOULD NOT PARSE 21.90",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="SAMPLE MERCHANT",
            amount_text="18.45",
        ),
    )


def test_consecutive_transaction_rows_flush_previous_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/17 FIRST MERCHANT 12.35",
                    "06/18 SECOND MERCHANT 24.80",
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
            amount_text="12.35",
        ),
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="06/18",
            description="SECOND MERCHANT",
            amount_text="24.80",
        ),
    )


def test_continuation_without_pending_row_is_ignored() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "06/18 TESTCUR",
                    "52,000 X 0.000047115 (EXCHG RATE)",
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
                    "03/30 SAMPLE MERCHANT 18.45",
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
            amount_text="18.45",
        ),
    )


def test_final_pending_row_is_flushed_at_end_of_text() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "03/30 SAMPLE MERCHANT 18.45",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="03/30",
            description="SAMPLE MERCHANT",
            amount_text="18.45",
        ),
    )


def test_year_to_date_marker_is_not_year_specific() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PURCHASE",
                    "12/20 SAMPLE MERCHANT 14.00",
                    "2031 Totals Year-to-Date",
                    "12/21 SHOULD NOT PARSE 28.00",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PURCHASE,
            date_text="12/20",
            description="SAMPLE MERCHANT",
            amount_text="14.00",
        ),
    )


def test_total_fees_summary_ends_activity_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "FEES CHARGED",
                    "07/01 ANNUAL MEMBERSHIP FEE 75.00",
                    "Total fees charged in 2026 $75.00",
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
                    "03/30 SAMPLE MERCHANT 18.45",
                    "Total interest charged in 2026 $0.00",
                    "03/31 SHOULD NOT PARSE 21.90",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE MERCHANT"


def test_parse_interest_charge_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PAYMENTS AND OTHER CREDITS",
                    "04/27 ONLINE PAYMENT -325.00",
                    "INTEREST CHARGED",
                    "05/03 PURCHASE INTEREST CHARGE 6.40",
                    "TOTAL INTEREST FOR THIS PERIOD $6.40",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
            date_text="04/27",
            description="ONLINE PAYMENT",
            amount_text="-325.00",
        ),
        ActivityRow(
            section=ActivitySection.INTEREST_CHARGED,
            date_text="05/03",
            description="PURCHASE INTEREST CHARGE",
            amount_text="6.40",
        ),
    )


def test_parse_balance_transfer_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "PAYMENTS AND OTHER CREDITS",
                    "02/24 SYNTHETIC PROMOTIONAL ADJUSTMENT -6,400.00",
                    "BALANCE TRANSFERS",
                    "02/24 SYNTHETIC PROMOTIONAL ADJUSTMENT 6,400.00",
                    "INTEREST CHARGED",
                    "02/25 PURCHASE INTEREST CHRG DEBIT ADJ 7.35",
                    "TOTAL INTEREST FOR THIS PERIOD $7.35",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.PAYMENTS_AND_OTHER_CREDITS,
            date_text="02/24",
            description="SYNTHETIC PROMOTIONAL ADJUSTMENT",
            amount_text="-6,400.00",
        ),
        ActivityRow(
            section=ActivitySection.BALANCE_TRANSFERS,
            date_text="02/24",
            description="SYNTHETIC PROMOTIONAL ADJUSTMENT",
            amount_text="6,400.00",
        ),
        ActivityRow(
            section=ActivitySection.INTEREST_CHARGED,
            date_text="02/25",
            description="PURCHASE INTEREST CHRG DEBIT ADJ",
            amount_text="7.35",
        ),
    )


def test_parse_my_chase_loan_as_balance_transfer_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "BALANCE TRANSFERS / MY CHASE LOAN",
                    "03/27 My Chase Loan TO 9999 5,500.00",
                    "2021 Totals Year-to-Date",
                )
            )
        )
    )

    assert rows == (
        ActivityRow(
            section=ActivitySection.BALANCE_TRANSFERS,
            date_text="03/27",
            description="My Chase Loan TO 9999",
            amount_text="5,500.00",
        ),
    )
