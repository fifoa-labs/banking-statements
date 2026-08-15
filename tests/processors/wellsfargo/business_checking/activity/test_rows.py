"""
tests/processors/wellsfargo/business_checking/activity/test_rows.py

Tests for Wells Fargo business checking layout-aware activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.business_checking.activity.rows import (  # noqa: E501
    WellsFargoBusinessCheckingActivityRow,
    parse_activity_rows,
)
from banking_statements.text import (
    StatementPage,
    StatementText,
    StatementWord,
)


def make_word(
    text: str,
    *,
    x0: float,
    top: float,
    width: float = 20.0,
) -> StatementWord:
    """Build positioned synthetic PDF word evidence."""
    return StatementWord(
        text=text,
        x0=x0,
        x1=x0 + width,
        top=top,
        bottom=top + 8.0,
    )


def make_statement_text(
    words: tuple[StatementWord, ...],
) -> StatementText:
    """Build single-page statement text with layout evidence."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text="synthetic Wells Fargo business checking statement",
                words=words,
            ),
        )
    )


def transaction_heading(
    *,
    top: float = 10.0,
) -> tuple[StatementWord, ...]:
    """Build a transaction-history heading."""
    return (
        make_word("Transaction", x0=40.0, top=top),
        make_word("history", x0=100.0, top=top),
    )


def activity_header(
    *,
    top: float = 20.0,
) -> tuple[StatementWord, ...]:
    """Build a business checking activity table header."""
    return (
        make_word("Date", x0=40.0, top=top),
        make_word("Number", x0=80.0, top=top),
        make_word("Description", x0=140.0, top=top),
        make_word("Credits", x0=410.0, top=top),
        make_word("Debits", x0=470.0, top=top),
        make_word("balance", x0=545.0, top=top),
    )


def test_parse_activity_rows_preserves_transaction_columns() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=30.0),
                make_word("Sample", x0=140.0, top=30.0),
                make_word("Deposit", x0=190.0, top=30.0),
                make_word("200.00", x0=420.0, top=30.0),
                make_word("1,200.00", x0=543.0, top=30.0),
                make_word("1/5", x0=40.0, top=40.0),
                make_word("Sample", x0=140.0, top=40.0),
                make_word("Payment", x0=190.0, top=40.0),
                make_word("50.00", x0=480.0, top=40.0),
                make_word("1,150.00", x0=543.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoBusinessCheckingActivityRow(
            transaction_date="12/20",
            description="Sample Deposit",
            credit=Decimal("200.00"),
            debit=None,
            balance=Decimal("1200.00"),
        ),
        WellsFargoBusinessCheckingActivityRow(
            transaction_date="1/5",
            description="Sample Payment",
            credit=None,
            debit=Decimal("50.00"),
            balance=Decimal("1150.00"),
        ),
    )


def test_parse_activity_rows_handles_missing_running_balance() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=30.0),
                make_word("Sample", x0=140.0, top=30.0),
                make_word("Deposit", x0=190.0, top=30.0),
                make_word("200.00", x0=420.0, top=30.0),
            )
        )
    )

    assert rows == (
        WellsFargoBusinessCheckingActivityRow(
            transaction_date="12/20",
            description="Sample Deposit",
            credit=Decimal("200.00"),
            debit=None,
            balance=None,
        ),
    )


def test_parse_activity_rows_handles_description_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=30.0),
                make_word("Sample", x0=140.0, top=30.0),
                make_word("Payment", x0=190.0, top=30.0),
                make_word("50.00", x0=480.0, top=30.0),
                make_word("Additional", x0=140.0, top=40.0),
                make_word("detail", x0=200.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoBusinessCheckingActivityRow(
            transaction_date="12/20",
            description="Sample Payment Additional detail",
            credit=None,
            debit=Decimal("50.00"),
            balance=None,
        ),
    )


def test_parse_activity_rows_ignores_content_before_transaction_history() -> (
    None
):
    rows = parse_activity_rows(
        make_statement_text(
            (
                make_word("Account", x0=40.0, top=5.0),
                make_word("Summary", x0=100.0, top=5.0),
                *transaction_heading(top=20.0),
                *activity_header(top=30.0),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=140.0, top=40.0),
                make_word("Deposit", x0=190.0, top=40.0),
                make_word("100.00", x0=420.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_waits_for_complete_header() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                make_word("Date", x0=40.0, top=20.0),
                make_word("Description", x0=140.0, top=20.0),
                make_word("Credits", x0=410.0, top=20.0),
                *activity_header(top=30.0),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=140.0, top=40.0),
                make_word("Deposit", x0=190.0, top=40.0),
                make_word("100.00", x0=420.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].credit == Decimal("100.00")


def test_parse_activity_rows_stops_at_section_end() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=30.0),
                make_word("Sample", x0=140.0, top=30.0),
                make_word("Deposit", x0=190.0, top=30.0),
                make_word("100.00", x0=420.0, top=30.0),
                make_word("Ending", x0=40.0, top=40.0),
                make_word("balance", x0=90.0, top=40.0),
                make_word("on", x0=140.0, top=40.0),
                make_word("1/31", x0=165.0, top=40.0),
                make_word("12/21", x0=40.0, top=50.0),
                make_word("Ignored", x0=140.0, top=50.0),
                make_word("25.00", x0=420.0, top=50.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "Sample Deposit"


def test_parse_activity_rows_ignores_nonrow_before_first_transaction() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("Informational", x0=140.0, top=30.0),
                make_word("line", x0=210.0, top=30.0),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=140.0, top=40.0),
                make_word("Deposit", x0=190.0, top=40.0),
                make_word("100.00", x0=420.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "Sample Deposit"


def test_parse_activity_rows_ignores_pages_without_layout_words() -> None:
    rows = parse_activity_rows(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="synthetic business checking statement",
                ),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_rejects_row_without_monetary_value() -> None:
    with pytest.raises(
        ValueError,
        match="transaction row contained no monetary value",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=30.0),
                    make_word("Sample", x0=140.0, top=30.0),
                    make_word("Transaction", x0=190.0, top=30.0),
                )
            )
        )


def test_parse_activity_rows_rejects_duplicate_column_values() -> None:
    with pytest.raises(
        ValueError,
        match="multiple values for the credit column",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=30.0),
                    make_word("Sample", x0=140.0, top=30.0),
                    make_word("100.00", x0=420.0, top=30.0),
                    make_word("25.00", x0=425.0, top=30.0),
                )
            )
        )


def test_parse_activity_rows_rejects_both_credit_and_debit() -> None:
    with pytest.raises(
        ValueError,
        match="contained both a credit and debit",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=30.0),
                    make_word("Sample", x0=140.0, top=30.0),
                    make_word("100.00", x0=420.0, top=30.0),
                    make_word("25.00", x0=480.0, top=30.0),
                )
            )
        )


def test_parse_activity_rows_rejects_balance_without_transaction_amount() -> (
    None
):
    with pytest.raises(
        ValueError,
        match="contained no transaction amount",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=30.0),
                    make_word("Sample", x0=140.0, top=30.0),
                    make_word("1000.00", x0=543.0, top=30.0),
                )
            )
        )
