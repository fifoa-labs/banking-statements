"""
src/banking_statements/processors/chase/credit_card/processor.py

Statement processor for the first supported Chase credit-card format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.processors.base import ProcessorMatch

if TYPE_CHECKING:
    from banking_statements.domain import ParsedStatement, StatementSource
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
        del source
        del text

        msg = "Chase credit-card identity parsing is not implemented."
        raise NotImplementedError(msg)
