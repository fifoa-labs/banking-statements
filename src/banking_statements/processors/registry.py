"""
src/banking_statements/processors/registry.py

Deterministic selection of compatible statement processors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.exceptions import (
    AmbiguousProcessorError,
    UnsupportedStatementError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from banking_statements.text import StatementText

    from .base import StatementProcessor


class ProcessorRegistry:
    """Registry of available statement processors."""

    def __init__(self, processors: Iterable[StatementProcessor] = ()) -> None:
        self._processors = tuple(processors)

    @property
    def processors(self) -> tuple[StatementProcessor, ...]:
        """Return registered processors in registration order."""
        return self._processors

    def select(self, text: StatementText) -> StatementProcessor:
        """Select exactly one compatible processor."""
        matches = tuple(
            processor
            for processor in self._processors
            if processor.match(text).matched
        )

        if not matches:
            message = "No registered processor supports this statement."
            raise UnsupportedStatementError(message)

        if len(matches) > 1:
            names = ", ".join(processor.name for processor in matches)
            message = f"Multiple processors support this statement: {names}."
            raise AmbiguousProcessorError(message)

        return matches[0]
