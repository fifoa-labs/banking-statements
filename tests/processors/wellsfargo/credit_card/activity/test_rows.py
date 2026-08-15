"""
tests/processors/wellsfargo/credit_card/activity/test_rows.py

Tests for Wells Fargo credit-card layout-aware activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.credit_card.activity.rows import (  # noqa: E501
    WellsFargoCreditCardActivityRow,
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
                text="synthetic Wells Fargo credit-card statement",
                words=words,
            ),
        )
    )


def transaction_heading(
    *,
    top: float = 10.0,
) -> tuple[StatementWord, ...]:
    """Build a transaction-history heading."""
    return (make_word("Transactions", x0=40.0, top=top),)


def activity_header(
    *,
    top: float = 20.0,
) -> tuple[StatementWord, ...]:
    """Build a credit-card activity table header."""
    return (
        make_word("Card", x0=40.0, top=top),
        make_word("Trans", x0=80.0, top=top),
        make_word("Post", x0=120.0, top=top),
        make_word("Reference", x0=160.0, top=top),
        make_word("Number", x0=220.0, top=top),
        make_word("Description", x0=280.0, top=top),
        make_word("Credits", x0=470.0, top=top),
        make_word("Charges", x0=535.0, top=top),
    )


def test_parse_activity_rows_preserves_charge_column() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
                make_word("Purchase", x0=330.0, top=30.0),
                make_word("50.00", x0=540.0, top=30.0),
            )
        )
    )

    assert rows == (
        WellsFargoCreditCardActivityRow(
            card_last4="1234",
            transaction_date="12/20",
            post_date="12/21",
            reference_number="REF001",
            description="Sample Purchase",
            credit=None,
            charge=Decimal("50.00"),
        ),
    )


def test_parse_activity_rows_preserves_credit_column() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
                make_word("Credit", x0=330.0, top=30.0),
                make_word("25.00", x0=475.0, top=30.0),
            )
        )
    )

    assert rows == (
        WellsFargoCreditCardActivityRow(
            card_last4="1234",
            transaction_date="12/20",
            post_date="12/21",
            reference_number="REF001",
            description="Sample Credit",
            credit=Decimal("25.00"),
            charge=None,
        ),
    )


def test_parse_activity_rows_parses_multiple_rows() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("First", x0=280.0, top=30.0),
                make_word("Transaction", x0=320.0, top=30.0),
                make_word("40.00", x0=540.0, top=30.0),
                make_word("1234", x0=40.0, top=40.0),
                make_word("12/22", x0=80.0, top=40.0),
                make_word("12/23", x0=120.0, top=40.0),
                make_word("REF002", x0=160.0, top=40.0),
                make_word("Second", x0=280.0, top=40.0),
                make_word("Transaction", x0=325.0, top=40.0),
                make_word("15.00", x0=475.0, top=40.0),
            )
        )
    )

    assert len(rows) == 2
    assert rows[0].charge == Decimal("40.00")
    assert rows[1].credit == Decimal("15.00")


def test_parse_activity_rows_handles_description_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
                make_word("Purchase", x0=330.0, top=30.0),
                make_word("50.00", x0=540.0, top=30.0),
                make_word("Additional", x0=280.0, top=40.0),
                make_word("detail", x0=335.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoCreditCardActivityRow(
            card_last4="1234",
            transaction_date="12/20",
            post_date="12/21",
            reference_number="REF001",
            description="Sample Purchase Additional detail",
            credit=None,
            charge=Decimal("50.00"),
        ),
    )


def test_parse_activity_rows_handles_continued_transactions_page() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                make_word("Transactions", x0=40.0, top=10.0),
                make_word("(continued", x0=105.0, top=10.0),
                make_word("from", x0=175.0, top=10.0),
                make_word("previous", x0=210.0, top=10.0),
                make_word("page)", x0=260.0, top=10.0),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
                make_word("Purchase", x0=330.0, top=30.0),
                make_word("50.00", x0=540.0, top=30.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_content_before_transactions() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                make_word("Account", x0=40.0, top=5.0),
                make_word("Summary", x0=100.0, top=5.0),
                *transaction_heading(top=20.0),
                *activity_header(top=30.0),
                make_word("1234", x0=40.0, top=40.0),
                make_word("12/20", x0=80.0, top=40.0),
                make_word("12/21", x0=120.0, top=40.0),
                make_word("REF001", x0=160.0, top=40.0),
                make_word("Sample", x0=280.0, top=40.0),
                make_word("Purchase", x0=330.0, top=40.0),
                make_word("50.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_waits_for_complete_header() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                make_word("Card", x0=40.0, top=20.0),
                make_word("Description", x0=280.0, top=20.0),
                make_word("Credits", x0=470.0, top=20.0),
                *activity_header(top=30.0),
                make_word("1234", x0=40.0, top=40.0),
                make_word("12/20", x0=80.0, top=40.0),
                make_word("12/21", x0=120.0, top=40.0),
                make_word("REF001", x0=160.0, top=40.0),
                make_word("Sample", x0=280.0, top=40.0),
                make_word("Purchase", x0=330.0, top=40.0),
                make_word("50.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_known_section_labels() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("Purchases,", x0=40.0, top=30.0),
                make_word("Balance", x0=100.0, top=30.0),
                make_word("Transfers", x0=150.0, top=30.0),
                make_word("1234", x0=40.0, top=40.0),
                make_word("12/20", x0=80.0, top=40.0),
                make_word("12/21", x0=120.0, top=40.0),
                make_word("REF001", x0=160.0, top=40.0),
                make_word("Sample", x0=280.0, top=40.0),
                make_word("Purchase", x0=330.0, top=40.0),
                make_word("50.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].description == "Sample Purchase"


def test_parse_activity_rows_ignores_pages_without_layout_words() -> None:
    rows = parse_activity_rows(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="synthetic statement",
                ),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_rejects_missing_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must contain exactly one credit or charge amount",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("1234", x0=40.0, top=30.0),
                    make_word("12/20", x0=80.0, top=30.0),
                    make_word("12/21", x0=120.0, top=30.0),
                    make_word("REF001", x0=160.0, top=30.0),
                    make_word("Sample", x0=280.0, top=30.0),
                    make_word("Purchase", x0=330.0, top=30.0),
                )
            )
        )


def test_parse_activity_rows_rejects_multiple_amounts() -> None:
    with pytest.raises(
        ValueError,
        match="must contain exactly one credit or charge amount",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("1234", x0=40.0, top=30.0),
                    make_word("12/20", x0=80.0, top=30.0),
                    make_word("12/21", x0=120.0, top=30.0),
                    make_word("REF001", x0=160.0, top=30.0),
                    make_word("Sample", x0=280.0, top=30.0),
                    make_word("Transaction", x0=330.0, top=30.0),
                    make_word("25.00", x0=475.0, top=30.0),
                    make_word("50.00", x0=540.0, top=30.0),
                )
            )
        )


def test_parse_activity_rows_ignores_noncard_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("ABCD", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_ignores_invalid_transaction_date() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("BAD", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_ignores_invalid_post_date() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("BAD", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
                make_word("Sample", x0=280.0, top=30.0),
                make_word("1234", x0=40.0, top=40.0),
                make_word("12/21", x0=80.0, top=40.0),
                make_word("12/22", x0=120.0, top=40.0),
                make_word("REF002", x0=160.0, top=40.0),
                make_word("Sample", x0=280.0, top=40.0),
                make_word("Purchase", x0=330.0, top=40.0),
                make_word("25.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1
    assert rows[0].reference_number == "REF002"
    assert rows[0].description == "Sample Purchase"
    assert rows[0].charge == Decimal("25.00")


def test_parse_activity_rows_handles_payment_without_card_number() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("Payments", x0=40.0, top=30.0),
                make_word("01/18", x0=80.0, top=40.0),
                make_word("01/18", x0=120.0, top=40.0),
                make_word("REF001", x0=160.0, top=40.0),
                make_word("Sample", x0=280.0, top=40.0),
                make_word("Payment", x0=330.0, top=40.0),
                make_word("25.00", x0=475.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoCreditCardActivityRow(
            card_last4="",
            transaction_date="01/18",
            post_date="01/18",
            reference_number="REF001",
            description="Sample Payment",
            credit=Decimal("25.00"),
            charge=None,
        ),
    )


def test_parse_activity_rows_ignores_short_card_row() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("1234", x0=40.0, top=30.0),
                make_word("12/20", x0=80.0, top=30.0),
                make_word("12/21", x0=120.0, top=30.0),
                make_word("REF001", x0=160.0, top=30.0),
            )
        )
    )

    assert rows == ()
