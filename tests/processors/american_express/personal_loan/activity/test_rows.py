"""
tests/processors/american_express/personal_loan/activity/test_rows.py

Tests for American Express personal-loan activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.personal_loan.activity import (  # noqa: E501
    AmericanExpressPersonalLoanActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_disbursement_payment_and_interest_rows() -> None:
    rows = parse_activity_rows(
        make_text(
            "Loan Disbursements Amount\n"
            "06/01/26 SAMPLE LOAN DISBURSEMENT $10,000.00\n"
            "06/01\n"
            "Total Loan Disbursements $10,000.00\n"
            "Payments Amount\n"
            "06/26/26* SAMPLE PAYMENT -$1,200.00\n"
            "Total Payments and Credits -$1,200.00\n"
            "Fees\n"
            "Amount\n"
            "Total Fees for this Period $0.00\n"
            "Interest Charges\n"
            "Amount\n"
            "07/12/26 SAMPLE INTEREST $300.00\n"
            "Total Interest Charges for this Period $300.00\n"
        )
    )

    assert len(rows) == 3

    assert rows[0].transaction_date == "06/01/26"
    assert rows[0].description == "SAMPLE LOAN DISBURSEMENT"
    assert rows[0].amount == Decimal("10000.00")
    assert (
        rows[0].section
        is AmericanExpressPersonalLoanActivitySection.DISBURSEMENT
    )

    assert rows[1].transaction_date == "06/26/26"
    assert rows[1].description == "SAMPLE PAYMENT"
    assert rows[1].amount == Decimal("1200.00")
    assert (
        rows[1].section is AmericanExpressPersonalLoanActivitySection.PAYMENT
    )
    assert rows[1].raw_text == "06/26/26* SAMPLE PAYMENT -$1,200.00"

    assert rows[2].amount == Decimal("300.00")
    assert (
        rows[2].section is AmericanExpressPersonalLoanActivitySection.INTEREST
    )


def test_parse_activity_rows_ignores_content_outside_activity() -> None:
    assert (
        parse_activity_rows(make_text("Account Summary\n06/10/26 TEXT")) == ()
    )


def test_parse_activity_rows_ignores_blank_and_nondated_section_text() -> None:
    rows = parse_activity_rows(
        make_text(
            "Fees\n"
            "\n"
            "Amount\n"
            "Informational fee text\n"
            "Total Fees for this Period $0.00\n"
        )
    )

    assert rows == ()


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(
        ValueError,
        match="Unrecognized American Express personal-loan transaction row",
    ):
        parse_activity_rows(
            make_text("Interest Charges\n07/12/26 MALFORMED ACTIVITY\n")
        )


def test_parse_activity_rows_requires_negative_payment_amount() -> None:
    with pytest.raises(ValueError, match="payment must report a negative"):
        parse_activity_rows(
            make_text("Payments Amount\n06/26/26* SAMPLE PAYMENT $100.00\n")
        )


def test_parse_activity_rows_rejects_negative_debit_activity() -> None:
    with pytest.raises(ValueError, match="debit activity must not report"):
        parse_activity_rows(
            make_text("Interest Charges\n07/12/26 SAMPLE INTEREST -$10.00\n")
        )
