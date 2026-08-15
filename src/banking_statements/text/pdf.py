"""
src/banking_statements/text/pdf.py

PDF-backed extraction of page-aware banking statement text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pdfplumber

from banking_statements.exceptions import StatementSourceError

from .models import StatementPage, StatementText

if TYPE_CHECKING:
    from banking_statements.domain import StatementSource


class PdfStatementTextReader:
    """Extract page-aware text from banking statement PDFs."""

    def read(
        self,
        source: StatementSource,
    ) -> StatementText:
        """Extract normalized text from a PDF statement source."""
        path = source.path

        try:
            with pdfplumber.open(path) as pdf:
                pages = tuple(
                    self._extract_page(
                        page_number=index,
                        page=page,
                    )
                    for index, page in enumerate(
                        pdf.pages,
                        start=1,
                    )
                )
        except OSError as exc:
            msg = f"Could not read PDF statement source: {path}."
            raise StatementSourceError(msg) from exc

        return StatementText(pages=pages)

    def _extract_page(
        self,
        *,
        page_number: int,
        page: pdfplumber.page.Page,
    ) -> StatementPage:
        """Extract text from one PDF page."""
        text = page.extract_text()

        if text is None:
            text = ""

        return StatementPage(
            number=page_number,
            text=text,
        )
