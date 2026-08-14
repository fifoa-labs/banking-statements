"""
src/banking_statements/__init__.py

Public package interface for banking-statements.
"""

from .domain.amounts import to_decimal
from .domain.evidence import SourceEvidence, StatementSource
from .domain.statements import ParsedStatement, StatementPeriod
from .domain.transactions import TransactionDirection, TransactionEvent
from .exceptions import (
    AmbiguousProcessorError,
    BankingStatementsError,
    UnsupportedStatementError,
)

__version__ = "0.1.0"

__all__ = [
    "AmbiguousProcessorError",
    "BankingStatementsError",
    "ParsedStatement",
    "SourceEvidence",
    "StatementPeriod",
    "StatementSource",
    "TransactionDirection",
    "TransactionEvent",
    "UnsupportedStatementError",
    "__version__",
    "to_decimal",
]
