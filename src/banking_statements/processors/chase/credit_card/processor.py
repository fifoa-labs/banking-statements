"""
src/banking_statements/processors/chase/credit_card/processor.py

Statement processor for the first supported Chase credit-card format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.base import ProcessorMatch

from .activity import (
    parse_activity_rows,
    parse_activity_transactions,
)
from .identity import parse_identity

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class ChaseCreditCardProcessor:
    """Processor for the first supported Chase credit-card statement format."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "chase.credit_card.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        markers = (
            "www.chase.com/cardhelp",
            "Account Number:",
            "Opening/Closing Date",
            "Date of",
            "Transaction Merchant Name or Transaction Description $ Amount",
        )

        matched = all(marker in text.text for marker in markers)

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched Chase credit-card statement structure."
                if matched
                else "Required Chase credit-card markers were not found."
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a Chase credit-card statement."""
        identity = parse_identity(text)

        period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        activity_rows = parse_activity_rows(text)
        transactions = parse_activity_transactions(
            activity_rows,
            period=period,
        )

        return ParsedStatement(
            source=source,
            institution="chase",
            account=identity.account,
            processor=self.name,
            period=period,
            transactions=transactions,
        )
