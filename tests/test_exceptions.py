"""
tests/test_exceptions.py

Tests for the banking-statements exception hierarchy.
"""

from __future__ import annotations

from banking_statements.exceptions import (
    AmbiguousInstitutionError,
    AmbiguousProcessorError,
    BankingStatementsError,
    StatementSourceError,
    UnsupportedInstitutionError,
    UnsupportedStatementError,
)


def test_package_exceptions_share_base_class() -> None:
    assert issubclass(StatementSourceError, BankingStatementsError)
    assert issubclass(UnsupportedStatementError, BankingStatementsError)
    assert issubclass(AmbiguousProcessorError, BankingStatementsError)
    assert issubclass(
        UnsupportedInstitutionError,
        BankingStatementsError,
    )
    assert issubclass(
        AmbiguousInstitutionError,
        BankingStatementsError,
    )
