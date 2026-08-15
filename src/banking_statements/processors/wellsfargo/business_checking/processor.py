"""
src/banking_statements/processors/wellsfargo/business_checking/processor.py

Statement processor for supported Wells Fargo business checking statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.base import ProcessorMatch
from banking_statements.processors.wellsfargo.signatures import (
    WELLS_FARGO_BUSINESS_CHECKING_SIGNATURES,
)

from .activity import parse_activity_rows, parse_activity_transactions
from .identity import parse_identity
from .summary import parse_balance_summary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class WellsFargoBusinessCheckingProcessor:
    """Processor for supported Wells Fargo business checking statements."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "wellsfargo.business_checking.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in WELLS_FARGO_BUSINESS_CHECKING_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched Wells Fargo business checking statement structure."
                if matched
                else (
                    "Required Wells Fargo business checking markers "
                    "were not found."
                )
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a Wells Fargo business checking statement."""
        identity = parse_identity(text)

        period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        balances = parse_balance_summary(text)
        activity_rows = parse_activity_rows(text)
        transactions = parse_activity_transactions(
            activity_rows,
            period=period,
        )

        return ParsedStatement(
            source=source,
            institution="wellsfargo",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=balances,
            transactions=transactions,
        )
