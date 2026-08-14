"""
tests/domain/test_transactions.py

Tests for normalized banking transactions.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from banking_statements.domain import (
    TransactionDirection,
    TransactionEvent,
)


def test_transaction_event_preserves_statement_fact() -> None:
    event = TransactionEvent(
        date=date(2026, 8, 14),
        amount=Decimal("42.17"),
        direction=TransactionDirection.DEBIT,
        description="Sample purchase",
    )

    assert event.date == date(2026, 8, 14)
    assert event.amount == Decimal("42.17")
    assert event.direction is TransactionDirection.DEBIT
    assert event.description == "Sample purchase"
    assert event.evidence is None


def test_transaction_directions_are_stable_strings() -> None:
    assert TransactionDirection.CREDIT.value == "credit"
    assert TransactionDirection.DEBIT.value == "debit"
