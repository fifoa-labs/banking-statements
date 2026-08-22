"""
src/banking_statements/__init__.py

Public package interface for banking-statements.
"""

from importlib.metadata import version

from .api import StatementParseResult, parse_statement, parse_statements
from .domain.amounts import to_decimal
from .domain.evidence import SourceEvidence, StatementSource
from .domain.statements import ParsedStatement, StatementPeriod
from .domain.transactions import TransactionDirection, TransactionEvent
from .exceptions import (
    AmbiguousProcessorError,
    BankingStatementsError,
    UnsupportedStatementError,
)

__version__ = version("banking-statements")

__all__ = [
    "AmbiguousProcessorError",
    "BankingStatementsError",
    "ParsedStatement",
    "SourceEvidence",
    "StatementParseResult",
    "StatementPeriod",
    "StatementSource",
    "TransactionDirection",
    "TransactionEvent",
    "UnsupportedStatementError",
    "__version__",
    "parse_statement",
    "parse_statements",
    "to_decimal",
]
