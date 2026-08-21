"""
src/banking_statements/processors/chase/business_credit_card/processor.py

Statement processor for supported Chase business credit-card statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors.base import ProcessorMatch
from banking_statements.processors.chase.credit_card.identity import (
    parse_identity,
)
from banking_statements.processors.chase.credit_card.summary import (
    parse_balance_summary,
)
from banking_statements.processors.chase.signatures import (
    CHASE_BUSINESS_CREDIT_CARD_SIGNATURES,
)

from .activity import parse_activity_rows, parse_activity_transactions

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class ChaseBusinessCreditCardProcessor:
    """Processor for supported Chase business credit-card statements."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "chase.business_credit_card.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in CHASE_BUSINESS_CREDIT_CARD_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched Chase business credit-card statement structure."
                if matched
                else (
                    "Required Chase business credit-card markers were "
                    "not found."
                )
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a Chase business credit-card statement."""
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
            source=source,
        )

        return ParsedStatement(
            source=source,
            institution="chase",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=balances,
            transactions=transactions,
        )
