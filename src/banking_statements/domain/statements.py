"""
src/banking_statements/domain/statements.py

Normalized bank statement models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from .evidence import StatementSource
    from .transactions import TransactionEvent


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
    processor: str
    period: StatementPeriod
    transactions: tuple[TransactionEvent, ...] = ()
