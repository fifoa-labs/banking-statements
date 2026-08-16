"""
tests/processors/american_express/credit_card/activity/test_rows.py

Tests for American Express credit-card logical activity rows.
"""

from __future__ import annotations

import pytest

from banking_statements.processors.american_express.credit_card.activity import (  # noqa: E501
    AmericanExpressCreditCardActivityRow,
    AmericanExpressCreditCardActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_parse_charge_rows_with_card_context_and_continuation() -> None:
    rows = parse_activity_rows(
        make_text(
            "New Charges\n"
            "Summary\n"
            "Total New Charges $42.50\n"
            "Detail\n"
            "Card Ending 7-65432\n"
            "Amount\n"
            "03/20/26 SAMPLE MARKET $12.50\n"
            "GROCERY STORE\n"
            "Card Ending 8-76543\n"
            "03/21/26 SAMPLE HOTEL $30.00\n"
            "Fees\n"
        )
    )

    assert rows == (
        AmericanExpressCreditCardActivityRow(
            section=AmericanExpressCreditCardActivitySection.CHARGES,
            date_text="03/20/26",
            description="SAMPLE MARKET",
            amount_text="$12.50",
            card_ending="7-65432",
            continuation_lines=("GROCERY STORE",),
            raw_text="03/20/26 SAMPLE MARKET $12.50",
        ),
        AmericanExpressCreditCardActivityRow(
            section=AmericanExpressCreditCardActivitySection.CHARGES,
            date_text="03/21/26",
            description="SAMPLE HOTEL",
            amount_text="$30.00",
            card_ending="8-76543",
            raw_text="03/21/26 SAMPLE HOTEL $30.00",
        ),
    )


def test_parse_payments_and_credits() -> None:
    rows = parse_activity_rows(
        make_text(
            "Payments and Credits\n"
            "Payments Amount\n"
            "03/10/26 SAMPLE PAYMENT -$100.00\n"
            "Credits Amount\n"
            "03/12/26 SAMPLE REFUND -$25.00\n"
            "New Charges\n"
        )
    )

    assert len(rows) == 2
    assert rows[0].section is AmericanExpressCreditCardActivitySection.PAYMENTS
    assert rows[0].amount_text == "-$100.00"
    assert rows[1].section is AmericanExpressCreditCardActivitySection.CREDITS
    assert rows[1].amount_text == "-$25.00"


def test_parse_posting_date_marker() -> None:
    rows = parse_activity_rows(
        make_text(
            "New Charges\n"
            "Detail *Indicates posting date\n"
            "Card Ending7-65432\n"
            "*03/20/26 SAMPLE PURCHASE $12.00\n"
            "03/21/26* SECOND PURCHASE $8.00\n"
            "Fees\n"
        )
    )

    assert rows[0].date_is_posting is True
    assert rows[1].date_is_posting is True


def test_parse_detail_continued() -> None:
    rows = parse_activity_rows(
        make_text(
            "Detail Continued *Indicates posting date\n"
            "Card Ending7-65432\n"
            "03/20/26 SAMPLE PURCHASE $12.00\n"
            "Fees\n"
        )
    )

    assert len(rows) == 1
    assert rows[0].section is AmericanExpressCreditCardActivitySection.CHARGES


def test_parse_undated_fee_and_interest_rows() -> None:
    rows = parse_activity_rows(
        make_text(
            "Fees\n"
            "Annual Membership Fee $95.00\n"
            "Total Fees for this Period $95.00\n"
            "Interest Charged\n"
            "Interest Charge on Purchases $14.25\n"
            "Total Interest Charged for this Period $14.25\n"
        )
    )

    assert rows == (
        AmericanExpressCreditCardActivityRow(
            section=AmericanExpressCreditCardActivitySection.FEES,
            date_text=None,
            description="Annual Membership Fee",
            amount_text="$95.00",
            raw_text="Annual Membership Fee $95.00",
        ),
        AmericanExpressCreditCardActivityRow(
            section=AmericanExpressCreditCardActivitySection.INTEREST,
            date_text=None,
            description="Interest Charge on Purchases",
            amount_text="$14.25",
            raw_text="Interest Charge on Purchases $14.25",
        ),
    )


def test_parse_cr_suffix() -> None:
    rows = parse_activity_rows(
        make_text(
            "Payments and Credits\n"
            "Credits\n"
            "03/12/26 SAMPLE ADJUSTMENT $25.00 CR\n"
            "New Charges\n"
        )
    )

    assert rows[0].amount_text == "$25.00 CR"


def test_page_structure_is_not_appended_to_description() -> None:
    rows = parse_activity_rows(
        make_text(
            "New Charges\n"
            "Detail\n"
            "Card Ending7-65432\n"
            "03/20/26 SAMPLE PURCHASE $12.00\n"
            "SAMPLE PERSON Closing Date04/15/26 Account Ending7-65432\n"
            "p. 4/5\n"
            "Fees\n"
        )
    )

    assert rows[0].continuation_lines == ()


def test_parse_activity_rows_ignores_content_outside_sections() -> None:
    assert (
        parse_activity_rows(
            make_text(
                "Account Summary\n03/20/26 LOOKS LIKE TRANSACTION $12.00\n"
            )
        )
        == ()
    )


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(
        ValueError,
        match="Unrecognized American Express credit-card transaction row",
    ):
        parse_activity_rows(
            make_text("New Charges\nDetail\n03/20/26 MALFORMED TRANSACTION\n")
        )


def test_financial_section_can_run_to_end_of_text() -> None:
    rows = parse_activity_rows(
        make_text("New Charges\nDetail\n03/20/26 SAMPLE PURCHASE $12.00\n")
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_blank_lines() -> None:
    rows = parse_activity_rows(
        make_text(
            "\n"
            "New Charges\n"
            "Detail\n"
            "\n"
            "03/20/26 SAMPLE PURCHASE $12.00\n"
            "\n"
            "Fees\n"
        )
    )

    assert len(rows) == 1


def test_nontransaction_fee_text_without_pending_row_is_ignored() -> None:
    rows = parse_activity_rows(
        make_text(
            "Fees\n"
            "Informational fee explanation\n"
            "Total Fees for this Period $0.00\n"
        )
    )

    assert rows == ()


def test_parse_lodging_date_pair_as_continuation() -> None:
    rows = parse_activity_rows(
        make_text(
            "New Charges\n"
            "Detail Continued *Indicates posting date\n"
            "Card Ending7-65432\n"
            "Amount\n"
            "04/10/26 SAMPLE HOTEL $125.00\n"
            "SAMPLE CITY TX\n"
            "Arrival Date Departure Date\n"
            "04/07/26 04/10/26\n"
            "12345678\n"
            "LODGING\n"
            "04/12/26 SAMPLE MARKET $18.25\n"
            "Fees\n"
        )
    )

    assert len(rows) == 2

    assert rows[0].description == "SAMPLE HOTEL"
    assert rows[0].amount_text == "$125.00"
    assert rows[0].continuation_lines == (
        "SAMPLE CITY TX",
        "Arrival Date Departure Date",
        "04/07/26 04/10/26",
        "12345678",
        "LODGING",
    )

    assert rows[1].description == "SAMPLE MARKET"
    assert rows[1].amount_text == "$18.25"
