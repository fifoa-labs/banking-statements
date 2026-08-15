"""
src/banking_statements/processors/chase/heloc/processor.py

Statement processor for supported Chase home-equity line-of-credit statements.
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
    CHASE_HELOC_SIGNATURES,
)

from .activity import parse_activity_rows, parse_activity_transactions
from .finance import parse_finance_charges
from .identity import parse_identity
from .summary import parse_summary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class ChaseHelocProcessor:
    """Processor for supported Chase home-equity line-of-credit statements."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "chase.heloc.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in CHASE_HELOC_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched Chase HELOC statement structure."
                if matched
                else "Required Chase HELOC markers were not found."
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a Chase HELOC statement."""
        identity = parse_identity(text)
        summary = parse_summary(text)

        period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        transactions = parse_activity_transactions(
            parse_activity_rows(text),
            period=period,
            finance_charges=parse_finance_charges(text),
        )

        return ParsedStatement(
            source=source,
            institution="chase",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=summary.balances,
            transactions=transactions,
        )
