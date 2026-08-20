"""
tests/processors/american_express/business_line_of_credit/activity/test_rows.py

Tests for American Express business line-of-credit activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.business_line_of_credit.activity import (  # noqa: E501
    AmericanExpressBusinessLineOfCreditActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_debit_and_parenthesized_credit_rows() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transaction Summary\n"
            "Date Reference number Description Amount\n"
            "04/10/2026 1234567890 SAMPLE ADVANCE $500.00\n"
            "04/15/2026 0987654321 SAMPLE PAYMENT ($125.00)\n"
            "1. Sample informational text\n"
        )
    )

    assert len(rows) == 2

    debit = rows[0]
    assert debit.transaction_date == "04/10/2026"
    assert debit.reference_number == "1234567890"
    assert debit.description == "SAMPLE ADVANCE"
    assert debit.amount == Decimal("500.00")
    assert (
        debit.section
        is AmericanExpressBusinessLineOfCreditActivitySection.DEBIT
    )
    assert debit.raw_text == ("04/10/2026 1234567890 SAMPLE ADVANCE $500.00")

    credit = rows[1]
    assert credit.transaction_date == "04/15/2026"
    assert credit.reference_number == "0987654321"
    assert credit.description == "SAMPLE PAYMENT"
    assert credit.amount == Decimal("125.00")
    assert (
        credit.section
        is AmericanExpressBusinessLineOfCreditActivitySection.CREDIT
    )


def test_parse_activity_rows_returns_empty_without_transaction_summary() -> (
    None
):
    assert parse_activity_rows(make_text("Account information")) == ()


def test_parse_activity_rows_requires_exact_transaction_header() -> None:
    with pytest.raises(ValueError, match="transaction header was not found"):
        parse_activity_rows(
            make_text(
                "Transaction Summary\n"
                "Date Description Amount\n"
                "04/10/2026 SAMPLE ADVANCE $500.00\n"
            )
        )


def test_parse_activity_rows_requires_header_after_summary() -> None:
    with pytest.raises(ValueError, match="transaction header was not found"):
        parse_activity_rows(make_text("Transaction Summary\n\n"))


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(
        ValueError,
        match="Unrecognized American Express business line-of-credit",
    ):
        parse_activity_rows(
            make_text(
                "Transaction Summary\n"
                "Date Reference number Description Amount\n"
                "04/10/2026 BAD SAMPLE ADVANCE $500.00\n"
            )
        )


def test_parse_activity_rows_stops_at_nontransaction_content() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transaction Summary\n"
            "Date Reference number Description Amount\n"
            "\n"
            "04/10/2026 1234567890 SAMPLE CHARGE $25.00\n"
            "Informational text\n"
            "04/11/2026 0987654321 NOT IN SECTION $30.00\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE CHARGE"


def test_parse_activity_rows_can_run_to_end_of_text() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transaction Summary\n"
            "Date Reference number Description Amount\n"
            "04/10/2026 1234567890 SAMPLE ADVANCE $500.00\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].transaction_date == "04/10/2026"
    assert rows[0].reference_number == "1234567890"
    assert rows[0].description == "SAMPLE ADVANCE"
    assert rows[0].amount == Decimal("500.00")
    assert (
        rows[0].section
        is AmericanExpressBusinessLineOfCreditActivitySection.DEBIT
    )


def test_parse_negative_credit_row() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transaction Summary\n"
            "Date Reference number Description Amount\n"
            "04/15/2026 1234567890 SAMPLE PAYMENT -$125.00\n"
        )
    )

    assert len(rows) == 1

    credit = rows[0]
    assert credit.transaction_date == "04/15/2026"
    assert credit.reference_number == "1234567890"
    assert credit.description == "SAMPLE PAYMENT"
    assert credit.amount == Decimal("125.00")
    assert (
        credit.section
        is AmericanExpressBusinessLineOfCreditActivitySection.CREDIT
    )
