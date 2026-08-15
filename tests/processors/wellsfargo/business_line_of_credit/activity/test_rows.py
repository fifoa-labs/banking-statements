"""
tests/processors/wellsfargo/business_line_of_credit/activity/test_rows.py

Tests for Wells Fargo business line-of-credit layout-aware activity parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.business_line_of_credit.activity.rows import (  # noqa: E501
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText, StatementWord


def word(
    text: str,
    x0: float,
    top: float,
    *,
    width: float = 20,
) -> StatementWord:
    """Build one positioned statement word."""
    return StatementWord(
        text=text,
        x0=x0,
        x1=x0 + width,
        top=top,
        bottom=top + 10,
    )


def make_page(*words: StatementWord) -> StatementText:
    """Build one page with positioned words."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Transaction Details",
                words=words,
            ),
        )
    )


def test_parse_dated_credit_and_charge_rows() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("03/10", 20, 30),
        word("03/10", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("PAYMENT", 290, 30),
        word("200.00", 450, 30),
        word("03/12", 20, 40),
        word("03/12", 65, 40),
        word("DEF456", 110, 40),
        word("SAMPLE", 230, 40),
        word("ADVANCE", 290, 40),
        word("500.00", 520, 40),
    )

    rows = parse_activity_rows(text)

    assert len(rows) == 2
    assert rows[0].credit == Decimal("200.00")
    assert rows[0].charge is None
    assert rows[0].description == "SAMPLE PAYMENT"

    assert rows[1].credit is None
    assert rows[1].charge == Decimal("500.00")
    assert rows[1].description == "SAMPLE ADVANCE"


def test_parse_finance_charge_uses_rightmost_total() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("PERIODIC*FINANCE", 20, 30, width=100),
        word("CHARGE*", 125, 30, width=50),
        word("PURCHASES", 180, 30, width=60),
        word("$0.08", 300, 30),
        word("CASH", 340, 30),
        word("ADVANCE", 380, 30),
        word("$12.42", 440, 30),
        word("12.50", 520, 30),
    )

    rows = parse_activity_rows(text)

    assert len(rows) == 1
    assert rows[0].transaction_date is None
    assert rows[0].credit is None
    assert rows[0].charge == Decimal("12.50")
    assert rows[0].description.endswith("$12.42")


def test_continuation_line_extends_dated_description() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("03/10", 20, 30),
        word("03/10", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("10.00", 520, 30),
        word("CONTINUED", 230, 40),
        word("DESCRIPTION", 300, 40),
    )

    rows = parse_activity_rows(text)

    assert rows[0].description == "SAMPLE CONTINUED DESCRIPTION"


def test_no_transaction_details_returns_no_rows() -> None:
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Account Summary\nPrevious Balance $0.00\nNew Balance $0.00",  # noqa: E501
            ),
        )
    )

    assert parse_activity_rows(text) == ()


def test_dated_row_requires_exactly_one_activity_amount() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("03/10", 20, 30),
        word("03/10", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("10.00", 450, 30),
        word("20.00", 520, 30),
    )

    with pytest.raises(ValueError, match="exactly one"):
        parse_activity_rows(text)


def test_finance_charge_requires_amount() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("PERIODIC*FINANCE", 20, 30, width=100),
        word("CHARGE*", 125, 30, width=50),
    )

    with pytest.raises(ValueError, match="contains no amount"):
        parse_activity_rows(text)


def test_invalid_transaction_date_is_not_a_transaction_row() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("BAD", 20, 30),
        word("03/10", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("10.00", 520, 30),
    )

    assert parse_activity_rows(text) == ()


def test_invalid_post_date_is_not_a_transaction_row() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("03/10", 20, 30),
        word("BAD", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("10.00", 520, 30),
    )

    assert parse_activity_rows(text) == ()


def test_content_before_transaction_details_is_ignored() -> None:
    text = make_page(
        word("Account", 20, 5),
        word("Summary", 80, 5),
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Trans", 20, 20),
        word("Post", 65, 20),
        word("Reference", 110, 20),
        word("Number", 175, 20),
        word("Description", 230, 20),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("03/10", 20, 30),
        word("03/10", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("10.00", 520, 30),
    )

    rows = parse_activity_rows(text)

    assert len(rows) == 1


def test_parser_waits_for_complete_activity_header() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Credits", 450, 20),
        word("Informational", 230, 30),
        word("line", 310, 30),
        word("Credits", 450, 40),
        word("Charges", 520, 40),
        word("03/10", 20, 50),
        word("03/10", 65, 50),
        word("ABC123", 110, 50),
        word("SAMPLE", 230, 50),
        word("10.00", 520, 50),
    )

    rows = parse_activity_rows(text)

    assert len(rows) == 1
    assert rows[0].charge == Decimal("10.00")


def test_ignored_structure_resets_description_continuation() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("03/10", 20, 30),
        word("03/10", 65, 30),
        word("ABC123", 110, 30),
        word("SAMPLE", 230, 30),
        word("10.00", 520, 30),
        word("Wells", 20, 40),
        word("Fargo", 60, 40),
        word("News", 100, 40),
        word("Not", 230, 50),
        word("a", 265, 50),
        word("continuation", 285, 50),
    )

    rows = parse_activity_rows(text)

    assert len(rows) == 1
    assert rows[0].description == "SAMPLE"


def test_nonrow_after_finance_charge_is_not_a_continuation() -> None:
    text = make_page(
        word("Transaction", 20, 10),
        word("Details", 90, 10),
        word("Credits", 450, 20),
        word("Charges", 520, 20),
        word("PERIODIC*FINANCE", 20, 30, width=100),
        word("CHARGE*", 125, 30, width=50),
        word("PURCHASES", 180, 30, width=60),
        word("$0.00", 300, 30),
        word("CASH", 340, 30),
        word("ADVANCE", 380, 30),
        word("$12.50", 440, 30),
        word("12.50", 520, 30),
        word("Informational", 230, 40),
        word("content", 310, 40),
    )

    rows = parse_activity_rows(text)

    assert len(rows) == 1
    assert rows[0].charge == Decimal("12.50")
    assert "Informational" not in rows[0].description
