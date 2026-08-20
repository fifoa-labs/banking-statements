"""
tests/processors/discover/credit_card/activity/test_rows.py

Tests for Discover credit-card logical activity-row reconstruction.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.discover.credit_card.activity import (
    DiscoverCreditCardActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_legacy_rows_with_inline_categories_and_references() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transactions\n"
            "Trans. Date Post Date\n"
            "Payments and Credits Dec 12 Dec 13 SAMPLE REFUND $ -15.00\n"
            "ABC12345678\n"
            "Dec 16 Dec 16 SAMPLE PAYMENT -85.00\n"
            "Merchandise Dec 20 Dec 21 SAMPLE MARKET $ 40.00\n"
            "REFERENCE123\n"
            "Transactions - continued\n"
            "Services Dec 22 Dec 23 SAMPLE SERVICE 10.00\n"
            "Fees TOTALFEESFORTHISPERIOD 0.00\n"
            "InterestCharged TOTALINTERESTFORTHISPERIOD 0.00\n"
        )
    )

    assert len(rows) == 4

    assert rows[0].transaction_date == "Dec 12"
    assert rows[0].posting_date == "Dec 13"
    assert rows[0].description == "SAMPLE REFUND"
    assert rows[0].amount == Decimal("15.00")
    assert rows[0].section is DiscoverCreditCardActivitySection.CREDIT
    assert rows[0].raw_text.endswith("ABC12345678")

    assert rows[1].section is DiscoverCreditCardActivitySection.CREDIT
    assert rows[1].amount == Decimal("85.00")

    assert rows[2].posting_date == "Dec 21"
    assert rows[2].section is DiscoverCreditCardActivitySection.DEBIT
    assert rows[2].amount == Decimal("40.00")
    assert rows[2].raw_text.endswith("REFERENCE123")

    assert rows[3].posting_date == "Dec 23"
    assert rows[3].section is DiscoverCreditCardActivitySection.DEBIT


def test_parse_current_rows_and_nonzero_period_totals() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transactions Cashback Bonus® Rewards\n"
            "TRANS. PREVIOUSBALANCE $0.00\n"
            "DATE PAYMENTSANDCREDITS AMOUNT\n"
            "03/10 SAMPLE PAYMENT -$25.00\n"
            "TRANS.\n"
            "DATE PURCHASES MERCHANTCATEGORY AMOUNT\n"
            "03/20 SAMPLE MARKET Grocery $50.00\n"
            "ABCDEF123456\n"
            "FeesandInterestCharged\n"
            "TOTALFEESFORTHISPERIOD $3.00\n"
            "TOTALINTERESTFORTHISPERIOD $4.00\n"
        )
    )

    assert len(rows) == 4

    assert rows[0].transaction_date == "03/10"
    assert rows[0].posting_date is None
    assert rows[0].section is DiscoverCreditCardActivitySection.CREDIT
    assert rows[0].amount == Decimal("25.00")

    assert rows[1].transaction_date == "03/20"
    assert rows[1].posting_date is None
    assert rows[1].description == "SAMPLE MARKET Grocery"
    assert rows[1].section is DiscoverCreditCardActivitySection.DEBIT
    assert rows[1].raw_text.endswith("ABCDEF123456")

    assert rows[2].posting_date is None
    assert rows[2].description == "FEES CHARGED"
    assert rows[2].amount == Decimal("3.00")
    assert rows[2].section is DiscoverCreditCardActivitySection.FEE

    assert rows[3].description == "INTEREST CHARGED"
    assert rows[3].amount == Decimal("4.00")
    assert rows[3].section is DiscoverCreditCardActivitySection.INTEREST


def test_parse_activity_rows_omits_zero_period_totals() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transactions\n"
            "Fees TOTALFEESFORTHISPERIOD 0.00\n"
            "InterestCharged TOTALINTERESTFORTHISPERIOD 0.00\n"
        )
    )

    assert rows == ()


def test_parse_activity_rows_can_return_only_period_charges() -> None:
    rows = parse_activity_rows(
        make_text(
            "No dated transaction table\n"
            "TOTALFEESFORTHISPERIOD $5.00\n"
            "TOTALINTERESTFORTHISPERIOD $7.00\n"
        )
    )

    assert len(rows) == 2
    assert rows[0].section is DiscoverCreditCardActivitySection.FEE
    assert rows[1].section is DiscoverCreditCardActivitySection.INTEREST


def test_parse_activity_rows_ignores_dated_text_outside_transactions() -> None:
    rows = parse_activity_rows(
        make_text(
            "Account Summary\n"
            "03/10 LOOKS LIKE ACTIVITY $25.00\n"
            "TOTALFEESFORTHISPERIOD $0.00\n"
            "TOTALINTERESTFORTHISPERIOD $0.00\n"
        )
    )

    assert rows == ()


@pytest.mark.parametrize(
    "line",
    [
        "Dec 12 Dec 13 MALFORMED LEGACY ROW",
        "03/10 MALFORMED CURRENT ROW",
    ],
)
def test_parse_activity_rows_rejects_malformed_dated_row(line: str) -> None:
    with pytest.raises(ValueError, match="Unrecognized Discover credit-card"):
        parse_activity_rows(
            make_text(
                "Transactions\n"
                f"{line}\n"
                "TOTALFEESFORTHISPERIOD $0.00\n"
                "TOTALINTERESTFORTHISPERIOD $0.00\n"
            )
        )


@pytest.mark.parametrize(
    ("missing_total", "message"),
    [
        (
            "TOTALFEESFORTHISPERIOD $0.00",
            "'fee'",
        ),
        (
            "TOTALINTERESTFORTHISPERIOD $0.00",
            "'interest'",
        ),
    ],
)
def test_parse_activity_rows_requires_period_totals(
    missing_total: str,
    message: str,
) -> None:
    lines = [
        "TOTALFEESFORTHISPERIOD $0.00",
        "TOTALINTERESTFORTHISPERIOD $0.00",
    ]

    with pytest.raises(ValueError, match=message):
        parse_activity_rows(
            make_text(
                "\n".join(line for line in lines if line != missing_total)
            )
        )


def test_unrecognized_reference_like_text_is_ignored() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transactions\n"
            "03/10 SAMPLE PURCHASE $25.00\n"
            "not-a-reference\n"
            "FeesandInterestCharged\n"
            "TOTALFEESFORTHISPERIOD $0.00\n"
            "TOTALINTERESTFORTHISPERIOD $0.00\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].raw_text == "03/10 SAMPLE PURCHASE $25.00"


def test_blank_lines_are_ignored() -> None:
    rows = parse_activity_rows(
        make_text(
            "\nTransactions\n\n"
            "03/10 SAMPLE PURCHASE $25.00\n\n"
            "FeesandInterestCharged\n"
            "TOTALFEESFORTHISPERIOD $0.00\n"
            "TOTALINTERESTFORTHISPERIOD $0.00\n"
        )
    )

    assert len(rows) == 1


def test_parse_current_row_ignores_adjacent_column_text_after_amount() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transactions Cashback Bonus® Rewards\n"
            "TRANS.\n"
            "DATE PURCHASES MERCHANTCATEGORY AMOUNT\n"
            "03/20 SAMPLE MARKET Grocery $50.00 REWARDS SIDEBAR TEXT\n"
            "FeesandInterestCharged\n"
            "TOTALFEESFORTHISPERIOD $0.00\n"
            "TOTALINTERESTFORTHISPERIOD $0.00\n"
        )
    )

    assert len(rows) == 1

    row = rows[0]
    assert row.transaction_date == "03/20"
    assert row.posting_date is None
    assert row.description == "SAMPLE MARKET Grocery"
    assert row.amount == Decimal("50.00")
    assert row.section is DiscoverCreditCardActivitySection.DEBIT
    assert row.raw_text.endswith("REWARDS SIDEBAR TEXT")
