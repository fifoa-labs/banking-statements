"""
src/banking_statements/text/models.py

Normalized text extracted from banking statement pages.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StatementPage:
    """Text extracted from one banking statement page."""

    number: int
    text: str

    def __post_init__(self) -> None:
        """Validate page numbering."""
        if self.number < 1:
            msg = "page number must be at least 1."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class StatementText:
    """Ordered text extracted from a banking statement."""

    pages: tuple[StatementPage, ...]

    @property
    def text(self) -> str:
        """Return all page text in statement order."""
        return "\n".join(page.text for page in self.pages)
