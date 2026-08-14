"""
src/banking_statements/text/readers.py

Protocols for statement text extraction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from banking_statements.domain import StatementSource

    from .models import StatementText


class StatementTextReader(Protocol):
    """Contract for extracting page-aware statement text."""

    def read(self, source: StatementSource) -> StatementText:
        """Extract text from a statement source."""
        ...
