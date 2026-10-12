"""
tests/processors/american_express/business_checking/activity/test_rows.py

Tests for American Express business-checking activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.american_express.business_checking.activity import (  # noqa: E501
    AmericanExpressBusinessCheckingActivityRow,
    AmericanExpressBusinessCheckingActivitySection,
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


def test_parse_credit_and_debit_rows() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "04/01/2023 BeginningBalance $1,000.00)",
                    "04/05/2023 SAMPLE DEPOSIT $200.00 $1,200.00)",
                    "04/10/2023 SAMPLE PAYMENT $50.00 $1,150.00)",
                    "04/30/2023 EndingBalance $1,150.00)",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert rows == (
        AmericanExpressBusinessCheckingActivityRow(
            transaction_date="04/05/2023",
            description="SAMPLE DEPOSIT",
            amount=Decimal("200.00"),
            balance=Decimal("1200.00"),
            section=AmericanExpressBusinessCheckingActivitySection.CREDIT,
        ),
        AmericanExpressBusinessCheckingActivityRow(
            transaction_date="04/10/2023",
            description="SAMPLE PAYMENT",
            amount=Decimal("50.00"),
            balance=Decimal("1150.00"),
            section=AmericanExpressBusinessCheckingActivitySection.DEBIT,
        ),
    )


def test_parse_activity_rows_handles_interest_deposit() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "04/01/2023 BeginningBalance $3.33)",
                    "04/30/2023 Interest Deposit $0.01 $3.34)",
                    "ID: 000000000000000",
                    "04/30/2023 EndingBalance $3.34)",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 1

    assert rows[0].transaction_date == "04/30/2023"
    assert rows[0].description == "Interest Deposit"
    assert rows[0].amount == Decimal("0.01")
    assert rows[0].balance == Decimal("3.34")
    assert (
        rows[0].section
        is AmericanExpressBusinessCheckingActivitySection.CREDIT
    )


def test_parse_activity_rows_returns_empty_without_activity_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "Business Checking Account Statement\n"
            "BeginningBalance $100.00)\n"
            "EndingBalance $100.00)"
        )
    )

    assert rows == ()


def test_parse_activity_rows_requires_beginning_activity_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking beginning activity "  # noqa: RUF043
            "balance was not found."
        ),
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Activity",
                        "Date Description Credits Debits Balance",
                        "04/05/2023 SAMPLE DEPOSIT $25.00 $125.00)",
                        "24/7 Account Access | World-Class Service",
                    )
                )
            )
        )


def test_parse_activity_rows_rejects_unreconciled_running_balance() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking activity row does not "
            "reconcile with its running balance"
        ),
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Activity",
                        "Date Description Credits Debits Balance",
                        "04/01/2023 BeginningBalance $100.00)",
                        "04/05/2023 SAMPLE DEPOSIT $25.00 $150.00)",
                        "24/7 Account Access | World-Class Service",
                    )
                )
            )
        )


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Unrecognized American Express business-checking transaction row"
        ),
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Activity",
                        "Date Description Credits Debits Balance",
                        "04/01/2023 BeginningBalance $100.00)",
                        "04/05/2023 MALFORMED TRANSACTION",
                        "24/7 Account Access | World-Class Service",
                    )
                )
            )
        )


def test_parse_activity_rows_ignores_nontransaction_text() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "04/01/2023 BeginningBalance $100.00)",
                    "Informational account text",
                    "04/05/2023 SAMPLE DEPOSIT $25.00 $125.00)",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE DEPOSIT"


def test_parse_activity_rows_requires_beginning_balance_before_valid_row() -> (
    None
):
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking beginning activity "  # noqa: RUF043
            "balance was not found."
        ),
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Activity",
                        "Date Description Credits Debits Balance",
                        "04/05/2023 SAMPLE DEPOSIT $25.00 $125.00)",
                        "24/7 Account Access | World-Class Service",
                    )
                )
            )
        )


def test_parse_activity_rows_ignores_blank_lines() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "",
                    "04/01/2023 BeginningBalance $100.00)",
                    "",
                    "04/05/2023 SAMPLE DEPOSIT $25.00 $125.00)",
                    "",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE DEPOSIT"


def test_parse_activity_rows_current_layout_without_transactions() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "04/01/2024 Beginning Balance $100.00",
                    "04/30/2024 Ending Balance $100.00",
                    "Important Information",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_legacy_layout() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "08/01/2022 Beginning Balance $100.00 )",
                    "08/05/2022 SAMPLE DEPOSIT $50.00 $150.00 )",
                    "ID: 000000000000001",
                    "08/10/2022 SAMPLE PAYMENT $25.00 $125.00 )",
                    "ID: 000000000000002",
                    "08/31/2022 Ending Balance $125.00 )",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 2

    assert rows[0].amount == Decimal("50.00")
    assert rows[0].balance == Decimal("150.00")
    assert (
        rows[0].section
        is AmericanExpressBusinessCheckingActivitySection.CREDIT
    )

    assert rows[1].amount == Decimal("25.00")
    assert rows[1].balance == Decimal("125.00")
    assert (
        rows[1].section is AmericanExpressBusinessCheckingActivitySection.DEBIT
    )


@pytest.mark.parametrize("amount", ["($200.00)", "-$200.00"])
def test_parse_activity_rows_parenthesized_debit(amount: str) -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "02/01/2025 Beginning Balance $1,000.00",
                    f"02/21/2025 SAMPLE PAYMENT {amount} $800.00",
                    "02/28/2025 Ending Balance $800.00",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].amount == Decimal("200.00")
    assert rows[0].balance == Decimal("800.00")
    assert (
        rows[0].section is AmericanExpressBusinessCheckingActivitySection.DEBIT
    )


@pytest.mark.parametrize("amount", ["($200.00)", "-$200.00"])
@pytest.mark.parametrize("balance", ["900.00", "1200.00"])
def test_parse_activity_rows_rejects_unreconciled_explicit_debit(
    amount: str,
    balance: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "American Express business-checking debit row does not "
            "reconcile with its running balance"
        ),
    ):
        parse_activity_rows(
            make_statement_text(
                "\n".join(
                    (
                        "Account Activity",
                        "Date Description Credits Debits Balance",
                        "02/01/2025 Beginning Balance $1,000.00",
                        f"02/21/2025 SAMPLE PAYMENT {amount} ${balance}",
                        "24/7 Account Access | World-Class Service",
                    )
                )
            )
        )


def test_parse_activity_rows_appends_continuation_line() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "02/01/2025 Beginning Balance $1,000.00",
                    "02/05/2025 SAMPLE DEPOSIT $200.00 $1,200.00",
                    "ADDITIONAL TRANSFER DETAIL",
                    "02/28/2025 Ending Balance $1,200.00",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE DEPOSIT"
    assert rows[0].continuation_lines == ("ADDITIONAL TRANSFER DETAIL",)


def test_parse_activity_rows_legacy_parenthesized_debit() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Activity",
                    "Date Description Credits Debits Balance",
                    "09/01/2022 Beginning Balance $5,500.14 )",
                    ("09/21/2022 SAMPLE PAYMENT $(5,500.14) $0.00 )"),
                    "09/30/2022 Ending Balance $0.00 )",
                    "24/7 Account Access | World-Class Service",
                )
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].amount == Decimal("5500.14")
    assert rows[0].balance == Decimal("0.00")
    assert (
        rows[0].section is AmericanExpressBusinessCheckingActivitySection.DEBIT
    )


def test_parse_activity_rows_continues_across_pages() -> None:
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text=(
                    "Account Activity\n"
                    "Date Description Credits Debits Balance\n"
                    "08/01/2026 Beginning Balance $100.00\n"
                    "08/12/2026 SAMPLE DEPOSIT $200.00 $300.00\n"
                    "ID 000000000000001\n"
                    "08/12/2026 SAMPLE TRANSFER -$50.00 $250.00\n"
                    "TRANSFER DETAIL\n"
                    "Continued on next page\n"
                    "FOOTNOTE TEXT\n"
                    "24/7 Account Access\n"
                ),
            ),
            StatementPage(
                number=2,
                text=(
                    "SAMPLE BUSINESS\n"
                    "Statement Date: 08/31/2026\n"
                    "Date Description Credits Debits Balance\n"
                    "08/13/2026 SAMPLE PAYMENT -$25.00 $225.00\n"
                    "PAYMENT DETAIL\n"
                    "08/31/2026 Interest Deposit $1.00 $226.00\n"
                    "08/31/2026 Ending Balance $226.00\n"
                    "Accounts offered by American Express National Bank.\n"
                ),
            ),
        )
    )
    rows = parse_activity_rows(text)
    assert len(rows) == 4
    assert rows[1].continuation_lines == ("TRANSFER DETAIL",)
    assert rows[2].continuation_lines == ("PAYMENT DETAIL",)
    assert rows[3].balance == Decimal("226.00")
    assert sum(
        row.amount
        if row.section is AmericanExpressBusinessCheckingActivitySection.CREDIT
        else -row.amount
        for row in rows
    ) == Decimal("126.00")
