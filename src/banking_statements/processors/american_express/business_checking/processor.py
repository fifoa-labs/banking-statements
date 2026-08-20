"""
src/banking_statements/processors/american_express/business_checking/processor.py

Statement processor for American Express business-checking statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.american_express.signatures import (
    AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES,
)
from banking_statements.processors.base import ProcessorMatch

from .activity import parse_activity_rows, parse_activity_transactions
from .identity import parse_identity
from .summary import parse_balance_summary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class AmericanExpressBusinessCheckingProcessor:
    """Processor for American Express business-checking statements."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "american_express.business_checking.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched American Express business-checking statement "
                "structure."
                if matched
                else (
                    "Required American Express business-checking markers "
                    "were not found."
                )
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse an American Express business-checking statement."""
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
            institution="american_express",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=balances,
            transactions=transactions,
        )
