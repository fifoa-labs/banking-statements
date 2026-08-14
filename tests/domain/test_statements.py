"""
tests/domain/test_statements.py

Tests for normalized banking statement models.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from banking_statements.domain import (
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)


def test_parsed_statement_defaults_to_no_transactions() -> None:
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )
    period = StatementPeriod(
        start=date(2026, 7, 1),
        end=date(2026, 7, 31),
    )

    statement = ParsedStatement(
        source=source,
        institution="sample-bank",
        processor="sample.monthly",
        period=period,
    )

    assert statement.source is source
    assert statement.institution == "sample-bank"
    assert statement.processor == "sample.monthly"
    assert statement.period is period
    assert statement.transactions == ()
