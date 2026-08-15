"""
tests/domain/test_statements.py

Tests for normalized banking statement models.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from banking_statements.domain import (
    AccountIdentity,
    AccountType,
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)


def test_account_identity_preserves_masked_number() -> None:
    account = AccountIdentity(
        account_type=AccountType.CREDIT_CARD,
        display_number="XXXX XXXX XXXX 9062",
        last4="9062",
    )

    assert account.account_type is AccountType.CREDIT_CARD
    assert account.display_number == "XXXX XXXX XXXX 9062"
    assert account.last4 == "9062"


def test_account_types_are_stable_strings() -> None:
    assert AccountType.CHECKING.value == "checking"
    assert AccountType.SAVINGS.value == "savings"
    assert AccountType.CREDIT_CARD.value == "credit_card"


def test_parsed_statement_defaults_to_no_transactions() -> None:
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )
    account = AccountIdentity(
        account_type=AccountType.CREDIT_CARD,
        display_number="XXXX XXXX XXXX 1234",
        last4="1234",
    )
    period = StatementPeriod(
        start=date(2026, 7, 1),
        end=date(2026, 7, 31),
    )

    statement = ParsedStatement(
        source=source,
        institution="sample-bank",
        account=account,
        processor="sample.monthly",
        period=period,
    )

    assert statement.source is source
    assert statement.institution == "sample-bank"
    assert statement.account is account
    assert statement.processor == "sample.monthly"
    assert statement.period is period
    assert statement.transactions == ()
