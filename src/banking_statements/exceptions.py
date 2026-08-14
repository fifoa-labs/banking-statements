"""
src/banking_statements/exceptions.py

Exception hierarchy for banking statement parsing.
"""


class BankingStatementsError(Exception):
    """Base exception for banking-statements."""


class UnsupportedStatementError(BankingStatementsError):
    """Raised when no processor supports a statement."""


class AmbiguousProcessorError(BankingStatementsError):
    """Raised when multiple processors claim the same statement."""
