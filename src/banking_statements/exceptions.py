"""
src/banking_statements/exceptions.py

Exception hierarchy for banking statement parsing.
"""

from __future__ import annotations


class BankingStatementsError(Exception):
    """Base exception for banking-statements."""


class UnsupportedStatementError(BankingStatementsError):
    """Raised when no processor supports a statement."""


class AmbiguousProcessorError(BankingStatementsError):
    """Raised when multiple processors claim the same statement."""


class StatementSourceError(BankingStatementsError):
    """Raised when a statement source cannot be read."""


class UnsupportedInstitutionError(BankingStatementsError):
    """Raised when no known institution matches a statement."""


class AmbiguousInstitutionError(BankingStatementsError):
    """Raised when multiple institutions match a statement."""
