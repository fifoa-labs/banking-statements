"""
src/banking_statements/processors/base.py

Protocols and matching models for statement processors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from banking_statements.domain import ParsedStatement, StatementSource
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class ProcessorMatch:
    """Result of testing a processor against statement text."""

    matched: bool
    confidence: int = 0
    reason: str = ""


class StatementProcessor(Protocol):
    """Contract implemented by statement processors."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        ...

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether this processor supports the statement."""
        ...

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a supported statement."""
        ...
