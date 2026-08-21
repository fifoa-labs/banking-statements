"""
src/banking_statements/processors/penfed/heloc/processor.py

Statement processor for supported PenFed home-equity lines of credit.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.base import ProcessorMatch
from banking_statements.processors.penfed.signatures import (
    PENFED_HELOC_SIGNATURES,
)

from .activity import parse_activity_rows, parse_activity_transactions
from .finance import parse_finance_charges
from .identity import parse_identity
from .summary import PenFedHelocSummary, parse_summary

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.processors.penfed.heloc.activity import (
        PenFedHelocActivityRow,
    )
    from banking_statements.text import StatementText


def _activity_movement(
    rows: Sequence[PenFedHelocActivityRow],
) -> Decimal:
    """Return debt movement represented by economic activity rows."""
    movement = Decimal("0")

    for row in rows:
        if row.amount is None and row.direction is None:
            continue

        if row.amount is None or row.direction is None:
            msg = (
                "PenFed HELOC activity row has incomplete transaction "
                f"semantics: {row.description}"
            )
            raise ValueError(msg)

        movement += (
            row.amount
            if row.direction is TransactionDirection.DEBIT
            else -row.amount
        )

    return movement


def _validate_activity_summary(
    rows: Sequence[PenFedHelocActivityRow],
    *,
    summary: PenFedHelocSummary,
) -> None:
    """Require activity rows to explain non-interest summary movement."""
    reported_movement = (
        summary.advances_and_fees
        + summary.payment_and_other_credits
        + summary.debit_credit_adjustment
    )

    if _activity_movement(rows) != reported_movement:
        msg = (
            "PenFed HELOC transaction activity does not match the "
            "reported non-interest account-summary movement."
        )
        raise ValueError(msg)


class PenFedHelocProcessor:
    """Processor for supported PenFed HELOC statements."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return "penfed.heloc.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        """Determine whether the statement matches this processor."""
        matched = any(
            all(marker in text.text for marker in signature.required_markers)
            for signature in PENFED_HELOC_SIGNATURES
        )

        return ProcessorMatch(
            matched=matched,
            confidence=100 if matched else 0,
            reason=(
                "Matched PenFed HELOC statement structure."
                if matched
                else "Required PenFed HELOC markers were not found."
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a supported PenFed HELOC statement."""
        identity = parse_identity(text)
        summary = parse_summary(text)
        rows = parse_activity_rows(text)
        finance_charges, finance_raw_text = parse_finance_charges(text)

        if finance_charges != summary.interest_charges:
            msg = (
                "PenFed HELOC total finance charge does not match the "
                "reported account-summary interest charges."
            )
            raise ValueError(msg)

        _validate_activity_summary(
            rows,
            summary=summary,
        )

        period = StatementPeriod(
            start=identity.statement_start,
            end=identity.statement_end,
        )

        return ParsedStatement(
            source=source,
            institution="penfed",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=summary.balances,
            transactions=parse_activity_transactions(
                rows,
                period=period,
                source=source,
                finance_charges=finance_charges,
                finance_raw_text=finance_raw_text,
            ),
        )
