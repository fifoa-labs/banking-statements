"""
tests/text/test_models.py

Tests for normalized statement text and layout models.
"""

from __future__ import annotations

import pytest

from banking_statements.text import (
    StatementPage,
    StatementText,
    StatementWord,
)


def test_statement_page_defaults_to_no_layout_words() -> None:
    page = StatementPage(
        number=1,
        text="Sample statement text",
    )

    assert page.number == 1
    assert page.text == "Sample statement text"
    assert page.words == ()


def test_statement_page_accepts_layout_words() -> None:
    word = StatementWord(
        text="100.00",
        x0=400.0,
        x1=430.0,
        top=100.0,
        bottom=110.0,
    )

    page = StatementPage(
        number=1,
        text="100.00",
        words=(word,),
    )

    assert page.words == (word,)


def test_statement_page_rejects_invalid_page_number() -> None:
    with pytest.raises(
        ValueError,
        match="page number must be at least 1",
    ):
        StatementPage(
            number=0,
            text="Sample",
        )


def test_statement_text_combines_page_text() -> None:
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Page one",
            ),
            StatementPage(
                number=2,
                text="Page two",
            ),
        )
    )

    assert text.text == "Page one\nPage two"
