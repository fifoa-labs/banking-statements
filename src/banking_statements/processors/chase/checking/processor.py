"""
src/banking_statements/processors/chase/checking/processor.py

Statement processor for the first supported Chase checking format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.base import ProcessorMatch
from banking_statements.processors.chase.signatures import (
    CHASE_CHECKING_SIGNATURES,
)

from .identity import parse_identity
from .summary import parse_balance_summary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class ChaseCheckingProcessor:
    """Processor for the first supported Chase checking statement format."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "chase.checking.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in CHASE_CHECKING_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched Chase checking statement structure."
                if matched
                else "Required Chase checking markers were not found."
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a Chase checking statement."""
        identity = parse_identity(text)

        _period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        _balances = parse_balance_summary(text)

        msg = "Chase checking transaction parsing is not implemented yet."
        raise NotImplementedError(msg)
