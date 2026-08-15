"""
tests/processors/wellsfargo/business_credit_card/activity/test_rows.py

Tests for Wells Fargo business credit-card layout-aware activity-row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.business_credit_card.activity.rows import (  # noqa: E501
    WellsFargoBusinessCreditCardActivityRow,
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
                text="synthetic Wells Fargo business credit-card statement",
                words=words,
            ),
        )
    )


def transaction_heading(
    *,
    top: float = 10.0,
) -> tuple[StatementWord, ...]:
    """Build the business-card transaction-detail heading."""
    return (
        make_word("Transaction", x0=40.0, top=top),
        make_word("Details", x0=100.0, top=top),
    )


def activity_header(
    *,
    top: float = 20.0,
) -> tuple[StatementWord, ...]:
    """Build the transaction table header."""
    return (
        make_word("Trans", x0=40.0, top=top),
        make_word("Post", x0=80.0, top=top),
        make_word("Reference", x0=120.0, top=top),
        make_word("Number", x0=180.0, top=top),
        make_word("Description", x0=240.0, top=top),
        make_word("Credits", x0=470.0, top=top),
        make_word("Charges", x0=535.0, top=top),
    )


def test_parse_activity_rows_preserves_charge_column() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("12/28", x0=40.0, top=30.0),
                make_word("12/29", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
                make_word("Sample", x0=240.0, top=30.0),
                make_word("Purchase", x0=290.0, top=30.0),
                make_word("100.00", x0=540.0, top=30.0),
            )
        )
    )

    assert rows == (
        WellsFargoBusinessCreditCardActivityRow(
            transaction_date="12/28",
            post_date="12/29",
            reference_number="REF001",
            description="Sample Purchase",
            credit=None,
            charge=Decimal("100.00"),
        ),
    )


def test_parse_activity_rows_preserves_credit_column() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("01/02", x0=40.0, top=30.0),
                make_word("01/02", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
                make_word("Sample", x0=240.0, top=30.0),
                make_word("Payment", x0=290.0, top=30.0),
                make_word("50.00", x0=475.0, top=30.0),
            )
        )
    )

    assert rows == (
        WellsFargoBusinessCreditCardActivityRow(
            transaction_date="01/02",
            post_date="01/02",
            reference_number="REF001",
            description="Sample Payment",
            credit=Decimal("50.00"),
            charge=None,
        ),
    )


def test_parse_activity_rows_parses_control_and_subaccount_rows() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("01/02", x0=40.0, top=30.0),
                make_word("01/02", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
                make_word("Sample", x0=240.0, top=30.0),
                make_word("Payment", x0=290.0, top=30.0),
                make_word("50.00", x0=475.0, top=30.0),
                make_word(
                    "Transaction",
                    x0=40.0,
                    top=40.0,
                ),
                make_word(
                    "Summary",
                    x0=105.0,
                    top=40.0,
                ),
                make_word("For", x0=160.0, top=40.0),
                make_word("Sample", x0=190.0, top=40.0),
                make_word(
                    "Sub",
                    x0=40.0,
                    top=50.0,
                ),
                make_word(
                    "Account",
                    x0=70.0,
                    top=50.0,
                ),
                make_word(
                    "Number",
                    x0=120.0,
                    top=50.0,
                ),
                make_word(
                    "Ending",
                    x0=170.0,
                    top=50.0,
                ),
                make_word("In", x0=215.0, top=50.0),
                make_word("5678", x0=245.0, top=50.0),
                make_word("12/28", x0=40.0, top=60.0),
                make_word("12/28", x0=80.0, top=60.0),
                make_word("REF002", x0=120.0, top=60.0),
                make_word("Sample", x0=240.0, top=60.0),
                make_word("Purchase", x0=290.0, top=60.0),
                make_word("100.00", x0=540.0, top=60.0),
            )
        )
    )

    assert len(rows) == 2
    assert rows[0].credit == Decimal("50.00")
    assert rows[1].charge == Decimal("100.00")


def test_parse_activity_rows_handles_description_continuation() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("12/28", x0=40.0, top=30.0),
                make_word("12/28", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
                make_word("Sample", x0=240.0, top=30.0),
                make_word("Purchase", x0=290.0, top=30.0),
                make_word("100.00", x0=540.0, top=30.0),
                make_word("Additional", x0=240.0, top=40.0),
                make_word("detail", x0=305.0, top=40.0),
            )
        )
    )

    assert rows == (
        WellsFargoBusinessCreditCardActivityRow(
            transaction_date="12/28",
            post_date="12/28",
            reference_number="REF001",
            description="Sample Purchase Additional detail",
            credit=None,
            charge=Decimal("100.00"),
        ),
    )


def test_parse_activity_rows_ignores_content_before_transaction_details() -> (
    None
):
    rows = parse_activity_rows(
        make_statement_text(
            (
                make_word("Account", x0=40.0, top=5.0),
                make_word("Summary", x0=100.0, top=5.0),
                *transaction_heading(top=20.0),
                *activity_header(top=30.0),
                make_word("01/02", x0=40.0, top=40.0),
                make_word("01/02", x0=80.0, top=40.0),
                make_word("REF001", x0=120.0, top=40.0),
                make_word("Sample", x0=240.0, top=40.0),
                make_word("Purchase", x0=290.0, top=40.0),
                make_word("25.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_waits_for_complete_header() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                make_word("Trans", x0=40.0, top=20.0),
                make_word("Post", x0=80.0, top=20.0),
                make_word("Credits", x0=470.0, top=20.0),
                *activity_header(top=30.0),
                make_word("01/02", x0=40.0, top=40.0),
                make_word("01/02", x0=80.0, top=40.0),
                make_word("REF001", x0=120.0, top=40.0),
                make_word("Sample", x0=240.0, top=40.0),
                make_word("Purchase", x0=290.0, top=40.0),
                make_word("25.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_structural_lines() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("Transaction", x0=40.0, top=30.0),
                make_word("Summary", x0=105.0, top=30.0),
                make_word("For", x0=160.0, top=30.0),
                make_word("Sample", x0=190.0, top=30.0),
                make_word("01/02", x0=40.0, top=40.0),
                make_word("01/02", x0=80.0, top=40.0),
                make_word("REF001", x0=120.0, top=40.0),
                make_word("Sample", x0=240.0, top=40.0),
                make_word("Purchase", x0=290.0, top=40.0),
                make_word("25.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_subaccount_heading() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("Sample", x0=40.0, top=30.0),
                make_word("/", x0=80.0, top=30.0),
                make_word("Sub", x0=100.0, top=30.0),
                make_word("Acct", x0=130.0, top=30.0),
                make_word("Ending", x0=165.0, top=30.0),
                make_word("In", x0=210.0, top=30.0),
                make_word("5678", x0=240.0, top=30.0),
                make_word("01/02", x0=40.0, top=40.0),
                make_word("01/02", x0=80.0, top=40.0),
                make_word("REF001", x0=120.0, top=40.0),
                make_word("Sample", x0=240.0, top=40.0),
                make_word("Purchase", x0=290.0, top=40.0),
                make_word("25.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_nonrow_before_first_transaction() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("Informational", x0=240.0, top=30.0),
                make_word("line", x0=310.0, top=30.0),
                make_word("01/02", x0=40.0, top=40.0),
                make_word("01/02", x0=80.0, top=40.0),
                make_word("REF001", x0=120.0, top=40.0),
                make_word("Sample", x0=240.0, top=40.0),
                make_word("Purchase", x0=290.0, top=40.0),
                make_word("25.00", x0=540.0, top=40.0),
            )
        )
    )

    assert len(rows) == 1


def test_parse_activity_rows_ignores_pages_without_layout_words() -> None:
    rows = parse_activity_rows(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="synthetic business card statement",
                ),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_ignores_short_line() -> None:
    rows = parse_activity_rows(
        make_statement_text(
            (
                *transaction_heading(),
                *activity_header(),
                make_word("01/02", x0=40.0, top=30.0),
                make_word("01/02", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
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
                make_word("BAD", x0=40.0, top=30.0),
                make_word("01/02", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
                make_word("Sample", x0=240.0, top=30.0),
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
                make_word("01/02", x0=40.0, top=30.0),
                make_word("BAD", x0=80.0, top=30.0),
                make_word("REF001", x0=120.0, top=30.0),
                make_word("Sample", x0=240.0, top=30.0),
            )
        )
    )

    assert rows == ()


def test_parse_activity_rows_rejects_missing_amount() -> None:
    with pytest.raises(
        ValueError,
        match="exactly one credit or charge amount",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("01/02", x0=40.0, top=30.0),
                    make_word("01/02", x0=80.0, top=30.0),
                    make_word("REF001", x0=120.0, top=30.0),
                    make_word("Sample", x0=240.0, top=30.0),
                    make_word("Purchase", x0=290.0, top=30.0),
                )
            )
        )


def test_parse_activity_rows_rejects_multiple_amounts() -> None:
    with pytest.raises(
        ValueError,
        match="exactly one credit or charge amount",
    ):
        parse_activity_rows(
            make_statement_text(
                (
                    *transaction_heading(),
                    *activity_header(),
                    make_word("01/02", x0=40.0, top=30.0),
                    make_word("01/02", x0=80.0, top=30.0),
                    make_word("REF001", x0=120.0, top=30.0),
                    make_word("Sample", x0=240.0, top=30.0),
                    make_word("25.00", x0=475.0, top=30.0),
                    make_word("50.00", x0=540.0, top=30.0),
                )
            )
        )
