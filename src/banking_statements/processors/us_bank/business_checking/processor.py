"""
src/banking_statements/processors/us_bank/business_checking/processor.py

Statement processor for supported U.S. Bank business-checking statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.base import ProcessorMatch
from banking_statements.processors.us_bank.signatures import (
    US_BANK_BUSINESS_CHECKING_SIGNATURES,
)

from .activity import parse_activity_rows, parse_activity_transactions
from .identity import parse_identity
from .summary import parse_balance_summary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class USBankBusinessCheckingProcessor:
    """Processor for supported U.S. Bank business-checking statements."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "us_bank.business_checking.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in US_BANK_BUSINESS_CHECKING_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched U.S. Bank business-checking statement structure."
                if matched
                else (
                    "Required U.S. Bank business-checking markers were not "
                    "found."
                )
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a U.S. Bank business-checking statement."""
        identity = parse_identity(text)
        period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        return ParsedStatement(
            source=source,
            institution="us_bank",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=parse_balance_summary(text),
            transactions=parse_activity_transactions(
                parse_activity_rows(text),
                period=period,
                source=source,
            ),
        )
