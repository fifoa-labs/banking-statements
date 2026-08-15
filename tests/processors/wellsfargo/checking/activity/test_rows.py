"""
tests/processors/wellsfargo/checking/activity/test_rows.py

Tests for Wells Fargo checking layout-aware transaction-history row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.checking.activity.rows import (
    WellsFargoCheckingActivityRow,
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
                text="synthetic Wells Fargo checking statement",
                words=words,
            ),
        )
    )


def checking_heading(*, top: float = 10.0) -> tuple[StatementWord, ...]:
    """Build a Wells Fargo checking heading."""
    return (
        make_word("Wells", x0=40.0, top=top),
        make_word("Fargo", x0=70.0, top=top),
        make_word("College", x0=105.0, top=top),
        make_word("Checking", x0=150.0, top=top),
    )


def transaction_heading(*, top: float = 20.0) -> tuple[StatementWord, ...]:
    """Build a Wells Fargo transaction-history heading."""
    return (
        make_word("Transaction", x0=40.0, top=top),
        make_word("history", x0=100.0, top=top),
    )


def activity_header(*, top: float = 30.0) -> tuple[StatementWord, ...]:
    """Build the transaction-table column header."""
    return (
        make_word("Date", x0=40.0, top=top),
        make_word("Description", x0=100.0, top=top),
        make_word("Additions", x0=407.0, top=top),
        make_word("Subtractions", x0=466.0, top=top),
        make_word("balance", x0=545.0, top=top),
    )


def test_parse_activity_rows_preserves_transaction_columns() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=100.0, top=40.0),
                make_word("Payroll", x0=145.0, top=40.0),
                make_word("200.00", x0=419.0, top=40.0),
                make_word("1,200.00", x0=543.0, top=40.0),
                make_word("1/5", x0=40.0, top=50.0),
                make_word("Sample", x0=100.0, top=50.0),
                make_word("Utility", x0=145.0, top=50.0),
                make_word("50.00", x0=488.0, top=50.0),
                make_word("1,150.00", x0=543.0, top=50.0),
            )
        )
    )

    assert rows == (
        WellsFargoCheckingActivityRow(
            transaction_date="12/20",
            description="Sample Payroll",
            addition=Decimal("200.00"),
            subtraction=None,
            balance=Decimal("1200.00"),
        ),
        WellsFargoCheckingActivityRow(
            transaction_date="1/5",
            description="Sample Utility",
            addition=None,
            subtraction=Decimal("50.00"),
            balance=Decimal("1150.00"),
        ),
    )


def test_parse_activity_rows_handles_missing_running_balance() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=100.0, top=40.0),
                make_word("Deposit", x0=145.0, top=40.0),
                make_word("200.00", x0=419.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoCheckingActivityRow(
            transaction_date="12/20",
            description="Sample Deposit",
            addition=Decimal("200.00"),
            subtraction=None,
            balance=None,
        ),
    )


def test_parse_activity_rows_handles_description_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                *activity_header(),
                make_word("12/17", x0=40.0, top=40.0),
                make_word("Recurring", x0=100.0, top=40.0),
                make_word("Transfer", x0=155.0, top=40.0),
                make_word("25.00", x0=488.0, top=40.0),
                make_word("xxxxxx4321", x0=100.0, top=50.0),
            )
        )
    )

    assert rows == (
        WellsFargoCheckingActivityRow(
            transaction_date="12/17",
            description="Recurring Transfer xxxxxx4321",
            addition=None,
            subtraction=Decimal("25.00"),
            balance=None,
        ),
    )


def test_parse_activity_rows_handles_transaction_history_spacing() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                make_word("Transaction", x0=40.0, top=20.0),
                make_word("hi", x0=100.0, top=20.0),
                make_word("story", x0=120.0, top=20.0),
                make_word("(continued)", x0=155.0, top=20.0),
                *activity_header(),
                make_word("1/14", x0=40.0, top=40.0),
                make_word("Sample", x0=100.0, top=40.0),
                make_word("Card", x0=145.0, top=40.0),
                make_word("125.00", x0=488.0, top=40.0),
                make_word("900.00", x0=543.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoCheckingActivityRow(
            transaction_date="1/14",
            description="Sample Card",
            addition=None,
            subtraction=Decimal("125.00"),
            balance=Decimal("900.00"),
        ),
    )


def test_parse_activity_rows_stops_before_savings_account() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Checking", x0=100.0, top=40.0),
                make_word("Deposit", x0=150.0, top=40.0),
                make_word("200.00", x0=419.0, top=40.0),
                make_word("Wells", x0=40.0, top=60.0),
                make_word("Far", x0=70.0, top=60.0),
                make_word("go", x0=95.0, top=60.0),
                make_word("Way2Save", x0=120.0, top=60.0),
                make_word("Savings", x0=180.0, top=60.0),
                make_word("1/5", x0=40.0, top=70.0),
                make_word("Savings", x0=100.0, top=70.0),
                make_word("Deposit", x0=150.0, top=70.0),
                make_word("25.00", x0=419.0, top=70.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "Checking Deposit"


def test_parse_activity_rows_continues_across_pages() -> None:
    first_page = StatementPage(
        number=1,
        text="checking page",
        words=(
            *checking_heading(),
            *transaction_heading(),
            *activity_header(),
            make_word("12/20", x0=40.0, top=40.0),
            make_word("First", x0=100.0, top=40.0),
            make_word("Deposit", x0=145.0, top=40.0),
            make_word("100.00", x0=419.0, top=40.0),
        ),
    )

    second_page = StatementPage(
        number=2,
        text="checking continuation",
        words=(
            *transaction_heading(top=10.0),
            *activity_header(top=20.0),
            make_word("12/21", x0=40.0, top=30.0),
            make_word("Second", x0=100.0, top=30.0),
            make_word("Payment", x0=145.0, top=30.0),
            make_word("25.00", x0=488.0, top=30.0),
        ),
    )

    rows = parse_activity_rows(
        StatementText(
            pages=(
                first_page,
                second_page,
            )
        )
    )

    assert len(rows) == 2
    assert rows[0].addition == Decimal("100.00")
    assert rows[1].subtraction == Decimal("25.00")


def test_parse_activity_rows_ignores_pages_without_layout_words() -> None:
    rows = parse_activity_rows(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="Wells Fargo College Checking",
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
                    *checking_heading(),
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=40.0),
                    make_word("Sample", x0=100.0, top=40.0),
                    make_word("Transaction", x0=145.0, top=40.0),
                )
            )
        )


def test_parse_activity_rows_rejects_duplicate_column_values() -> None:
    with pytest.raises(
        ValueError,
        match="multiple values for the addition column",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *checking_heading(),
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=40.0),
                    make_word("Sample", x0=100.0, top=40.0),
                    make_word("100.00", x0=419.0, top=40.0),
                    make_word("25.00", x0=425.0, top=40.0),
                )
            )
        )


def test_parse_activity_rows_rejects_both_addition_and_subtraction() -> None:
    with pytest.raises(
        ValueError,
        match="contained both an addition and subtraction",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *checking_heading(),
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=40.0),
                    make_word("Sample", x0=100.0, top=40.0),
                    make_word("100.00", x0=419.0, top=40.0),
                    make_word("25.00", x0=488.0, top=40.0),
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
                    *checking_heading(),
                    *transaction_heading(),
                    *activity_header(),
                    make_word("12/20", x0=40.0, top=40.0),
                    make_word("Sample", x0=100.0, top=40.0),
                    make_word("1000.00", x0=543.0, top=40.0),
                )
            )
        )


def test_parse_activity_rows_ignores_content_before_checking_section() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                make_word("Unrelated", x0=40.0, top=5.0),
                make_word("content", x0=100.0, top=5.0),
                *checking_heading(top=10.0),
                *transaction_heading(top=20.0),
                *activity_header(top=30.0),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=100.0, top=40.0),
                make_word("Deposit", x0=145.0, top=40.0),
                make_word("100.00", x0=419.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_waits_for_complete_header() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                make_word("Date", x0=40.0, top=30.0),
                make_word("Description", x0=100.0, top=30.0),
                make_word("Additions", x0=407.0, top=30.0),
                *activity_header(top=40.0),
                make_word("12/20", x0=40.0, top=50.0),
                make_word("Sample", x0=100.0, top=50.0),
                make_word("Deposit", x0=145.0, top=50.0),
                make_word("100.00", x0=419.0, top=50.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].addition == Decimal("100.00")


def test_parse_activity_rows_handles_missing_activity_header() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                make_word("Date", x0=40.0, top=30.0),
                make_word("Description", x0=100.0, top=30.0),
                make_word("Additions", x0=407.0, top=30.0),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_stops_at_section_end() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                *activity_header(),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=100.0, top=40.0),
                make_word("Deposit", x0=145.0, top=40.0),
                make_word("100.00", x0=419.0, top=40.0),
                make_word("Ending", x0=40.0, top=50.0),
                make_word("balance", x0=80.0, top=50.0),
                make_word("on", x0=125.0, top=50.0),
                make_word("1/14", x0=145.0, top=50.0),
                make_word("12/21", x0=40.0, top=60.0),
                make_word("Ignored", x0=100.0, top=60.0),
                make_word("25.00", x0=419.0, top=60.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "Sample Deposit"


def test_parse_activity_rows_ignores_nonrow_before_first_transaction() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *checking_heading(),
                *transaction_heading(),
                *activity_header(),
                make_word("Informational", x0=100.0, top=40.0),
                make_word("line", x0=170.0, top=40.0),
                make_word("12/20", x0=40.0, top=50.0),
                make_word("Sample", x0=100.0, top=50.0),
                make_word("Deposit", x0=145.0, top=50.0),
                make_word("100.00", x0=419.0, top=50.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "Sample Deposit"


def test_parse_activity_rows_groups_slightly_offset_heading_words() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                make_word("Wells", x0=40.0, top=12.6),
                make_word("Fargo", x0=70.0, top=12.6),
                make_word("College", x0=105.0, top=12.6),
                make_word("Checking®", x0=150.0, top=10.0),
                *transaction_heading(top=20.0),
                *activity_header(top=30.0),
                make_word("12/20", x0=40.0, top=40.0),
                make_word("Sample", x0=100.0, top=40.0),
                make_word("Deposit", x0=145.0, top=40.0),
                make_word("100.00", x0=419.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].addition == Decimal("100.00")


def test_parse_activity_rows_handles_account_summary_before_checking_section() -> (  # noqa: E501
    None
):
    rows = parse_activity_rows(
        make_statement_text(
            (
                # Combined-account summary.
                make_word("Wells", x0=40.0, top=10.0),
                make_word("Fargo", x0=70.0, top=10.0),
                make_word("Everyday", x0=105.0, top=10.0),
                make_word("Checking", x0=160.0, top=10.0),
                make_word("Wells", x0=40.0, top=20.0),
                make_word("Fargo", x0=70.0, top=20.0),
                make_word("Way2Save", x0=105.0, top=20.0),
                make_word("Savings", x0=165.0, top=20.0),
                # Actual checking section.
                make_word("Wells", x0=40.0, top=40.0),
                make_word("Fargo", x0=70.0, top=40.0),
                make_word("Everyday", x0=105.0, top=40.0),
                make_word("Checking", x0=160.0, top=40.0),
                *transaction_heading(top=50.0),
                *activity_header(top=60.0),
                make_word("12/20", x0=40.0, top=70.0),
                make_word("Sample", x0=100.0, top=70.0),
                make_word("Deposit", x0=145.0, top=70.0),
                make_word("100.00", x0=419.0, top=70.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].addition == Decimal("100.00")
