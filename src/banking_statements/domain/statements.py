"""
src/banking_statements/domain/statements.py

Normalized banking statement models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from .evidence import StatementSource
    from .transactions import TransactionEvent


class AccountType(StrEnum):
    """Supported banking account families."""

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    """Normalized identity for the account represented by a statement."""

    account_type: AccountType
    display_number: str
    last4: str | None = None


@dataclass(frozen=True, slots=True)
class StatementPeriod:
    """Inclusive statement reporting period."""

    start: date
    end: date


@dataclass(frozen=True, slots=True)
class ParsedStatement:
    """Normalized representation of a parsed banking statement."""

    source: StatementSource
    institution: str
    account: AccountIdentity
    processor: str
    period: StatementPeriod
    transactions: tuple[TransactionEvent, ...] = ()
