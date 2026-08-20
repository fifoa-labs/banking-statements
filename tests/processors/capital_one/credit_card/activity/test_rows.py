"""
tests/processors/capital_one/credit_card/activity/test_rows.py

Tests for Capital One credit-card logical activity rows.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.capital_one.credit_card.activity import (
    CapitalOneCreditCardActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_activity_rows_across_sections_and_foreign_detail() -> None:
    rows = parse_activity_rows(
        make_text(
            "Account Summary\n"
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
            "SAMPLE PERSON #1234: Total Transactions $50.00\n"
            "Total Transactions for This Period $50.00\n"
            "Fees\n"
            "Trans Date Post Date Description Amount\n"
            "Mar 25 Mar 25 SAMPLE MEMBERSHIP FEE $3.00\n"
            "Total Fees for This Period $3.00\n"
            "Interest Charged\n"
            "Interest Charge on Purchases $4.00\n"
            "Total Interest for This Period $4.00\n"
        )
    )

    assert len(rows) == 4

    credit, purchase, fee, interest = rows

    assert credit.transaction_date == "Mar 10"
    assert credit.posting_date == "Mar 11"
    assert credit.description == "SAMPLE PAYMENT"
    assert credit.amount == Decimal("25.00")
    assert credit.section is CapitalOneCreditCardActivitySection.CREDIT
    assert credit.card_last4 == "1234"

    assert purchase.section is CapitalOneCreditCardActivitySection.DEBIT
    assert purchase.amount == Decimal("50.00")
    assert purchase.description == "SAMPLE MARKET"
    assert purchase.raw_text == (
        "Mar 20 Mar 21 SAMPLE MARKET $50.00\n"
        "$1,250.00\n"
        "EUR\n"
        "25.000000000 Exchange Rate"
    )

    assert fee.section is CapitalOneCreditCardActivitySection.FEE
    assert fee.card_last4 is None
    assert fee.amount == Decimal("3.00")

    assert interest.section is CapitalOneCreditCardActivitySection.INTEREST
    assert interest.transaction_date is None
    assert interest.posting_date is None
    assert interest.description == "INTEREST CHARGED"
    assert interest.amount == Decimal("4.00")
    assert interest.raw_text == "Total Interest for This Period $4.00"


def test_parse_activity_rows_omits_zero_interest() -> None:
    rows = parse_activity_rows(
        make_text(
            "SAMPLE PERSON #1234: Transactions\n"
            "Mar 20 Mar 21 SAMPLE MARKET $50.00\n"
            "Total Fees for This Period $0.00\n"
            "Total Interest for This Period $0.00\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE MARKET"


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(
        ValueError,
        match="Unrecognized Capital One credit-card transaction row",
    ):
        parse_activity_rows(
            make_text(
                "SAMPLE PERSON #1234: Transactions\n"
                "Mar 20 Mar 21 MALFORMED ROW\n"
                "Total Fees for This Period $0.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )


@pytest.mark.parametrize(
    ("text", "field"),
    [
        (
            "Total Interest for This Period $0.00\n",
            "'fee'",
        ),
        (
            "Total Fees for This Period $0.00\n",
            "'interest'",
        ),
    ],
)
def test_parse_activity_rows_requires_period_totals(
    text: str,
    field: str,
) -> None:
    with pytest.raises(ValueError, match=field):
        parse_activity_rows(make_text(text))


def test_parse_activity_rows_rejects_conflicting_period_total() -> None:
    with pytest.raises(ValueError, match="'fee'.*uniquely"):  # noqa: RUF043
        parse_activity_rows(
            make_text(
                "Total Fees for This Period $0.00\n"
                "Total Fees for This Period $1.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )


def test_parse_activity_rows_requires_fee_rows_to_match_total() -> None:
    with pytest.raises(ValueError, match="fee rows do not match"):
        parse_activity_rows(
            make_text(
                "Fees\n"
                "Mar 25 Mar 25 SAMPLE FEE $3.00\n"
                "Total Fees for This Period $4.00\n"
                "Total Interest for This Period $0.00\n"
            )
        )
