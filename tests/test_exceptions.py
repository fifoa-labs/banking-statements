"""
tests/test_exceptions.py

Tests for the package exception hierarchy.
"""

from __future__ import annotations

from banking_statements.exceptions import (
    AmbiguousProcessorError,
    BankingStatementsError,
    UnsupportedStatementError,
)


def test_package_exceptions_share_base_class() -> None:
    assert issubclass(UnsupportedStatementError, BankingStatementsError)
    assert issubclass(AmbiguousProcessorError, BankingStatementsError)
