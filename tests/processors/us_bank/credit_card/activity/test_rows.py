"""
tests/processors/us_bank/credit_card/activity/test_rows.py

Tests for U.S. Bank credit-card activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.us_bank.credit_card.activity import (
    USBankCreditCardActivitySection,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(*pages: str) -> StatementText:
    return StatementText(
        tuple(
            StatementPage(number=index, text=value)
            for index, value in enumerate(pages, start=1)
        )
    )


def test_parse_activity_rows_supports_all_sections_and_continuations() -> None:
    rows = parse_activity_rows(
        make_text(
            "\nTransactions\n"
            "Payments and Other Credits\n"
            "Post Trans\n"
            "Date Date Ref # Transaction Description Amount\n"
            "01/05 01/05 1234 SAMPLE RETURN $12.00CR\n"
            "MERCHANDISE/SERVICE RETURN\n"
            "TOTAL THIS PERIOD $12.00CR\n"
            "Purchases and Other Debits\n"
            "Post Trans\n"
            "Date Date Ref # Transaction Description Amount\n"
            "01/10 01/09 SAMPLE PURCHASE $20.00\n"
            "DEBIT ADJUSTMENT\n"
            "TOTAL THIS PERIOD $20.00",
            "Transactions\n"
            "Fees\n"
            "Post Trans\n"
            "Date Date Ref # Transaction Description Amount\n"
            "01/31 ANNUAL FEE $5.00\n"
            "01/31 REVERSAL OF ANNUAL FEE $2.00CR\n"
            "TOTAL FEES THIS PERIOD $3.00\n"
            "Interest Charged\n"
            "Post\n"
            "Date Transaction Description Amount\n"
            "01/31 INTEREST CHARGE ON PURCHASES $1.25\n"
            "TOTAL INTEREST THIS PERIOD $1.25",
        )
    )
    assert len(rows) == 5
    assert rows[0].section is USBankCreditCardActivitySection.CREDIT
    assert rows[0].direction_is_credit
    assert rows[0].raw_text.endswith("MERCHANDISE/SERVICE RETURN")
    assert rows[1].section is USBankCreditCardActivitySection.DEBIT
    assert rows[1].transaction_date == "01/09"
    assert rows[2].section is USBankCreditCardActivitySection.FEE
    assert rows[3].direction_is_credit
    assert rows[4].section is USBankCreditCardActivitySection.INTEREST
    assert rows[4].amount == Decimal("1.25")


def test_parse_activity_rows_supports_one_date_and_zero_fee() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transactions\n"
            "Purchases and Other Debits\n"
            "01/11 4567 CREDIT BALANCE REFUND $25.00\n"
            "CREDIT ADJUSTMENT\n"
            "TOTAL THIS PERIOD $25.00\n"
            "Fees\n"
            "01/31 ANNUAL MEMBERSHIP FEE $0.00\n"
            "TOTAL FEES THIS PERIOD $0.00"
        )
    )
    assert len(rows) == 2
    assert rows[0].transaction_date is None
    assert rows[0].description == "CREDIT BALANCE REFUND"
    assert rows[1].amount == Decimal("0.00")


def test_parse_activity_rows_ignores_text_outside_sections_and_stops() -> None:
    rows = parse_activity_rows(
        make_text(
            "01/01 not activity $1.00\n"
            "Fees\n"
            "01/02 SAMPLE FEE $1.00\n"
            "Interest Charge Calculation\n"
            "01/03 not activity $1.00"
        )
    )
    assert len(rows) == 1


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        parse_activity_rows(
            make_text(
                "Purchases and Other Debits\n"
                "NONDATED UNKNOWN\n"
                "01/10 malformed transaction"
            )
        )


def test_parse_activity_rows_rejects_wrong_total_label() -> None:
    with pytest.raises(ValueError, match="active section"):
        parse_activity_rows(
            make_text("Fees\n01/10 SAMPLE FEE $2.00\nTOTAL THIS PERIOD $2.00")
        )


def test_parse_activity_rows_rejects_total_mismatch() -> None:
    with pytest.raises(ValueError, match="period total"):
        parse_activity_rows(
            make_text(
                "Purchases and Other Debits\n"
                "01/10 SAMPLE PURCHASE $2.00\n"
                "TOTAL THIS PERIOD $3.00"
            )
        )


def test_parse_activity_rows_validates_credit_fee_total() -> None:
    rows = parse_activity_rows(
        make_text(
            "Fees\n01/10 REVERSAL FEE $2.00CR\nTOTAL FEES THIS PERIOD $2.00CR"
        )
    )
    assert rows[0].direction_is_credit
