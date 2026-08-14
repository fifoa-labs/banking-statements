"""
tests/text/test_models.py

Tests for page-aware statement text models.
"""

from __future__ import annotations

from banking_statements.text import StatementPage, StatementText


def test_statement_text_preserves_pages_and_combines_text() -> None:
    first = StatementPage(number=1, text="First page")
    second = StatementPage(number=2, text="Second page")

    statement = StatementText(pages=(first, second))

    assert statement.pages == (first, second)
    assert statement.text == "First page\nSecond page"


def test_empty_statement_text_is_empty() -> None:
    statement = StatementText(pages=())

    assert statement.text == ""
