"""
tests/text/test_pdf.py

Tests for PDF-backed banking statement text extraction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Self

import pytest

from banking_statements.domain import StatementSource
from banking_statements.exceptions import StatementSourceError
from banking_statements.text.pdf import PdfStatementTextReader


class FakePage:
    """Minimal pdfplumber page used for extraction tests."""

    def __init__(
        self,
        text: str | None,
        *,
        words: list[dict[str, object]] | None = None,
    ) -> None:
        self._text = text
        self._words = words or []

    def extract_text(self) -> str | None:
        """Return configured page text."""
        return self._text

    def extract_words(self) -> list[dict[str, object]]:
        """Return configured positioned words."""
        return self._words


class FakePdf:
    """Minimal context-managed PDF used for extraction tests."""

    def __init__(self, pages: list[FakePage]) -> None:
        self.pages = pages

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_pdf_reader_extracts_page_aware_text_and_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    fake_pdf = FakePdf(
        [
            FakePage(
                "First page",
                words=[
                    {
                        "text": "First",
                        "x0": 10.0,
                        "x1": 30.0,
                        "top": 20.0,
                        "bottom": 30.0,
                    },
                ],
            ),
            FakePage(
                "Second page",
                words=[
                    {
                        "text": "Second",
                        "x0": 11.0,
                        "x1": 40.0,
                        "top": 21.0,
                        "bottom": 31.0,
                    },
                ],
            ),
        ]
    )

    monkeypatch.setattr(
        "banking_statements.text.pdf.pdfplumber.open",
        lambda path: fake_pdf,
    )

    result = PdfStatementTextReader().read(source)

    assert len(result.pages) == 2

    assert result.pages[0].number == 1
    assert result.pages[0].text == "First page"
    assert len(result.pages[0].words) == 1
    assert result.pages[0].words[0].text == "First"
    assert result.pages[0].words[0].x0 == 10.0
    assert result.pages[0].words[0].x1 == 30.0
    assert result.pages[0].words[0].top == 20.0
    assert result.pages[0].words[0].bottom == 30.0

    assert result.pages[1].number == 2
    assert result.pages[1].text == "Second page"
    assert len(result.pages[1].words) == 1
    assert result.pages[1].words[0].text == "Second"

    assert result.text == "First page\nSecond page"


def test_pdf_reader_normalizes_missing_page_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    fake_pdf = FakePdf([FakePage(None)])

    monkeypatch.setattr(
        "banking_statements.text.pdf.pdfplumber.open",
        lambda path: fake_pdf,
    )

    result = PdfStatementTextReader().read(source)

    assert result.pages[0].text == ""
    assert result.pages[0].words == ()


def test_pdf_reader_wraps_source_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = StatementSource(
        path=Path("missing.pdf"),
        sha256="abc123",
    )

    def raise_os_error(path: Path) -> None:
        raise OSError

    monkeypatch.setattr(
        "banking_statements.text.pdf.pdfplumber.open",
        raise_os_error,
    )

    with pytest.raises(
        StatementSourceError,
        match="Could not read PDF statement source: missing.pdf",  # noqa: RUF043
    ):
        PdfStatementTextReader().read(source)
