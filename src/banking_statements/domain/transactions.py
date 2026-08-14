"""
src/banking_statements/domain/transactions.py

Generic normalized transaction models for banking statements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date
    from decimal import Decimal

    from .evidence import SourceEvidence


class TransactionDirection(StrEnum):
    """Economic direction of a banking transaction."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class TransactionEvent:
    """A normalized banking transaction."""

    date: date
    amount: Decimal
    direction: TransactionDirection
    description: str
    evidence: SourceEvidence | None = None
