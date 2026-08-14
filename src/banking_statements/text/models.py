"""
src/banking_statements/text/models.py

Page-aware extracted text models for bank statements.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StatementPage:
    """Text extracted from one statement page."""

    number: int
    text: str


@dataclass(frozen=True, slots=True)
class StatementText:
    """Page-aware text extracted from a statement."""

    pages: tuple[StatementPage, ...]

    @property
    def text(self) -> str:
        """Return all page text in document order."""
        return "\n".join(page.text for page in self.pages)
