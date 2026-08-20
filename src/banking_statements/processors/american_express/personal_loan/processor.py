"""
src/banking_statements/processors/american_express/personal_loan/processor.py

Statement processor for American Express personal-loan statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.american_express.signatures import (
    AMERICAN_EXPRESS_PERSONAL_LOAN_SIGNATURES,
)
from banking_statements.processors.base import ProcessorMatch

from .activity import parse_activity_rows, parse_activity_transactions
from .identity import parse_identity
from .summary import parse_balance_summary

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class AmericanExpressPersonalLoanProcessor:
    """Processor for American Express personal-loan invoices."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "american_express.personal_loan.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in AMERICAN_EXPRESS_PERSONAL_LOAN_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched American Express personal-loan statement structure."
                if matched
                else (
                    "Required American Express personal-loan markers "
                    "were not found."
                )
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse an American Express personal-loan invoice."""
        identity = parse_identity(text)
        period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        return ParsedStatement(
            source=source,
            institution="american_express",
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
