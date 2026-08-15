"""
tests/text/test_models.py

Tests for normalized banking statement text models.
"""

from __future__ import annotations

import pytest

from banking_statements.text import StatementPage, StatementText


def test_statement_page_preserves_number_and_text() -> None:
    page = StatementPage(
        number=1,
        text="Sample page text",
    )

    assert page.number == 1
    assert page.text == "Sample page text"


def test_statement_page_rejects_invalid_number() -> None:
    with pytest.raises(
        ValueError,
        match="page number must be at least 1",
    ):
        StatementPage(
            number=0,
            text="Invalid page",
        )


def test_statement_text_preserves_ordered_pages() -> None:
    first = StatementPage(
        number=1,
        text="First page",
    )
    second = StatementPage(
        number=2,
        text="Second page",
    )

    statement = StatementText(
        pages=(first, second),
    )

    assert statement.pages == (first, second)


def test_statement_text_combines_page_text_in_order() -> None:
    statement = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="First page",
            ),
            StatementPage(
                number=2,
                text="Second page",
            ),
        )
    )

    assert statement.text == "First page\nSecond page"


def test_empty_statement_text_is_empty() -> None:
    statement = StatementText(pages=())

    assert statement.text == ""
