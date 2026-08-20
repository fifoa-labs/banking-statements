"""
tests/processors/capital_one/business_credit_card/activity/test_rows.py

Tests for Capital One business credit-card logical activity rows.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.capital_one.business_credit_card.activity import (  # noqa: E501
    CapitalOneBusinessCreditCardActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def current_spark_prefix() -> str:
    """Return synthetic current Spark statement structure."""
    return (
        "Spark Cash credit card | Visa Signature Business ending in 1234\n"
        "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
    )


def venture_prefix() -> str:
    """Return synthetic Venture X Business statement structure."""
    return (
        "Venture X Business card | Visa Infinite Business ending in 1234\n"
        "Mar 1, 2026 - Mar 31, 2026 | 31 days in Billing Cycle\n"
    )


def test_parse_legacy_merged_column_rows() -> None:
    rows = parse_activity_rows(
        make_text(
            "Spark® Visa Signature Business Account Ending in 1234\n"
            "Mar. 1, 2026 - Mar. 31, 2026 | 31 days in Billing Cycle\n"
            "Transactions Transactions Continued\n"
            "SAMPLE PERSON #1234: Payments, Credits and Adjustments\n"
            "Date Description Amount\n"
            "Mar 10 SAMPLE PAYMENT - $25.00 Mar 20 SAMPLE MARKET $50.00\n"
            "SAMPLE PERSON #1234: Total $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Date Description Amount\n"
            "Total Fees for This Period $0.00\n"
            "Interest Charged\n"
            "Total Interest for This Period $0.00\n"
        )
    )

    assert len(rows) == 2

    credit, debit = rows

    assert credit.transaction_date == "Mar 10"
    assert credit.posting_date is None
    assert credit.description == "SAMPLE PAYMENT"
    assert credit.amount == Decimal("25.00")
    assert credit.section is CapitalOneBusinessCreditCardActivitySection.CREDIT
    assert credit.card_last4 is None
    assert credit.raw_text == "Mar 10 SAMPLE PAYMENT - $25.00"

    assert debit.transaction_date == "Mar 20"
    assert debit.description == "SAMPLE MARKET"
    assert debit.amount == Decimal("50.00")
    assert debit.section is CapitalOneBusinessCreditCardActivitySection.DEBIT


def test_parse_legacy_interest_heading_activity_start() -> None:
    rows = parse_activity_rows(
        make_text(
            "Spark® Visa Signature Business Account Ending in 1234\n"
            "Mar. 1, 2026 - Mar. 31, 2026 | 31 days in Billing Cycle\n"
            "Transactions Interest Charge Calculation\n"
            "Fees\n"
            "Date Description Amount\n"
            "Total Fees for This Period $0.00\n"
            "Total Interest for This Period $0.00\n"
        )
    )

    assert rows == ()


def test_parse_current_rows_fees_interest_and_foreign_evidence() -> None:
    rows = parse_activity_rows(
        make_text(
            current_spark_prefix() + "Transactions\n"
            "\n"
            "SAMPLE PERSON #1234: Payments, Credits and Adjustments\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 10 Mar 11 SAMPLE PAYMENT - $25.00\n"
            "SAMPLE PERSON #1234: Transactions\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 20 Mar 21 SAMPLE MARKET $50.00\n"
            "$1,250.00\n"
            "EUR\n"
            "25.000000000 Exchange Rate\n"
            "TK#: SAMPLE-TICKET\n"
            "ORIG: AAA, DEST: BBB\n"
            "ARRIVE: 03/19/26\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 25 Mar 25 SAMPLE FEE $3.00\n"
            "Total Fees for This Period $3.00\n"
            "Interest Charged\n"
            "Total Interest for This Period $4.00\n"
        )
    )

    assert len(rows) == 4

    credit, debit, fee, interest = rows

    assert credit.posting_date == "Mar 11"
    assert credit.section is CapitalOneBusinessCreditCardActivitySection.CREDIT
    assert credit.card_last4 == "1234"

    assert debit.posting_date == "Mar 21"
    assert debit.description == "SAMPLE MARKET"
    assert debit.raw_text == (
        "Mar 20 Mar 21 SAMPLE MARKET $50.00\n"
        "$1,250.00\n"
        "EUR\n"
        "25.000000000 Exchange Rate\n"
        "TK#: SAMPLE-TICKET\n"
        "ORIG: AAA, DEST: BBB\n"
        "ARRIVE: 03/19/26"
    )

    assert fee.section is CapitalOneBusinessCreditCardActivitySection.FEE
    assert fee.amount == Decimal("3.00")

    assert (
        interest.section
        is CapitalOneBusinessCreditCardActivitySection.INTEREST
    )
    assert interest.transaction_date is None
    assert interest.posting_date is None
    assert interest.amount == Decimal("4.00")
    assert interest.raw_text == "Total Interest for This Period $4.00"


def test_parse_venture_x_business_without_interest_section() -> None:
    rows = parse_activity_rows(
        make_text(
            venture_prefix() + "Transactions\n"
            "SAMPLE PERSON #1234: Transactions\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 20 Mar 21 SAMPLE PURCHASE $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 25 Mar 25 SAMPLE MEMBER FEE $95.00\n"
            "Total Fees for This Period $95.00\n"
        )
    )

    assert len(rows) == 2
    assert rows[0].section is CapitalOneBusinessCreditCardActivitySection.DEBIT
    assert rows[1].section is CapitalOneBusinessCreditCardActivitySection.FEE


def test_parse_zero_activity_without_reported_transaction_total() -> None:
    rows = parse_activity_rows(
        make_text(
            venture_prefix() + "Transactions\n"
            "SAMPLE PERSON #1234: Payments, Credits and Adjustments\n"
            "Trans Date Post Date Description Amount\n"
            "SAMPLE PERSON #1234: Transactions\n"
            "Trans Date Post Date Description Amount\n"
            "Fees\n"
            "Trans Date Post Date Description Amount\n"
            "Total Fees for This Period $0.00\n"
        )
    )

    assert rows == ()


def test_parse_current_rejects_malformed_dated_row() -> None:
    with pytest.raises(ValueError, match="transaction row"):
        parse_activity_rows(
            make_text(
                current_spark_prefix() + "Transactions\n"
                "Mar 20 Mar 21 MALFORMED ROW\n"
                "Total Transactions for This Period $0.00\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )


def test_parse_legacy_rejects_malformed_dated_segment() -> None:
    with pytest.raises(ValueError, match="legacy transaction row"):
        parse_activity_rows(
            make_text(
                "Spark® Visa Signature Business Account Ending in 1234\n"
                "Mar. 1, 2026 - Mar. 31, 2026 | 31 days in Billing Cycle\n"
                "Transactions\n"
                "Mar 20 MALFORMED ROW\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )


def test_parse_activity_requires_transaction_section() -> None:
    with pytest.raises(ValueError, match="transaction section"):
        parse_activity_rows(
            make_text(
                current_spark_prefix() + "Fees\n"
                "Total Fees for This Period $0.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )


def test_parse_activity_rejects_unknown_layout() -> None:
    with pytest.raises(ValueError, match="layout was not recognized"):
        parse_activity_rows(
            make_text(
                "Unknown Capital One business product\n"
                "Transactions\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
            )
        )


def test_nonzero_activity_requires_transaction_total() -> None:
    with pytest.raises(ValueError, match="was not reported for nonzero"):
        parse_activity_rows(
            make_text(
                venture_prefix() + "Transactions\n"
                "Mar 20 Mar 21 SAMPLE PURCHASE $50.00\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
            )
        )


def test_transaction_total_must_match_rows() -> None:
    with pytest.raises(ValueError, match="parsed transactions do not match"):
        parse_activity_rows(
            make_text(
                venture_prefix() + "Transactions\n"
                "Mar 20 Mar 21 SAMPLE PURCHASE $50.00\n"
                "Total Transactions for This Period $49.00\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
            )
        )


def test_transaction_total_must_be_unique() -> None:
    with pytest.raises(ValueError, match="'transactions'.*uniquely"):  # noqa: RUF043
        parse_activity_rows(
            make_text(
                venture_prefix() + "Transactions\n"
                "Total Transactions for This Period $0.00\n"
                "Total Transactions for This Period $1.00\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
            )
        )


def test_fee_section_is_required() -> None:
    with pytest.raises(ValueError, match="fee section"):
        parse_activity_rows(make_text(venture_prefix() + "Transactions\n"))


def test_fee_total_is_required() -> None:
    with pytest.raises(ValueError, match="activity total 'fee'"):
        parse_activity_rows(
            make_text(venture_prefix() + "Transactions\nFees\n")
        )


def test_fee_total_must_match_rows() -> None:
    with pytest.raises(ValueError, match="parsed fee rows do not match"):
        parse_activity_rows(
            make_text(
                venture_prefix() + "Transactions\n"
                "Fees\n"
                "Mar 25 Mar 25 SAMPLE FEE $3.00\n"
                "Total Fees for This Period $4.00\n"
            )
        )


def test_current_fee_row_must_be_well_formed() -> None:
    with pytest.raises(ValueError, match="fee row"):
        parse_activity_rows(
            make_text(
                venture_prefix() + "Transactions\n"
                "Fees\n"
                "Mar 25 Mar 25 MALFORMED FEE\n"
                "Total Fees for This Period $0.00\n"
            )
        )


def test_legacy_style_fee_row_is_not_guessed_for_current_product() -> None:
    with pytest.raises(ValueError, match="legacy fee row"):
        parse_activity_rows(
            make_text(
                venture_prefix() + "Transactions\n"
                "Fees\n"
                "Mar 25 SAMPLE LEGACY FEE $3.00\n"
                "Total Fees for This Period $3.00\n"
            )
        )


def test_legacy_nonzero_fee_total_fails_loudly() -> None:
    with pytest.raises(ValueError, match="legacy nonzero fee rows"):
        parse_activity_rows(
            make_text(
                "Spark® Visa Signature Business Account Ending in 1234\n"
                "Mar. 1, 2026 - Mar. 31, 2026 | 31 days in Billing Cycle\n"
                "Transactions\n"
                "Total Transactions for This Period $0.00\n"
                "Total Fees for This Period $3.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )


def test_spark_requires_interest_total() -> None:
    with pytest.raises(ValueError, match="activity total 'interest'"):
        parse_activity_rows(
            make_text(
                current_spark_prefix() + "Transactions\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
            )
        )


def test_interest_total_must_be_unique() -> None:
    with pytest.raises(ValueError, match="'interest'.*uniquely"):  # noqa: RUF043
        parse_activity_rows(
            make_text(
                current_spark_prefix() + "Transactions\n"
                "Fees\n"
                "Total Fees for This Period $0.00\n"
                "Total Interest for This Period $1.00\n"
                "Total Interest for This Period $2.00\n"
            )
        )
