"""
tests/domain/test_statements.py

Tests for normalized banking statement models.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountIdentity,
    AccountType,
    ParsedStatement,
    StatementBalanceSummary,
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


def test_statement_balance_summary_preserves_reported_values() -> None:
    balances = StatementBalanceSummary(
        opening_balance=Decimal("-10.16"),
        closing_balance=Decimal("70.56"),
    )

    assert balances.opening_balance == Decimal("-10.16")
    assert balances.closing_balance == Decimal("70.56")


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
    balances = StatementBalanceSummary(
        opening_balance=Decimal("100.00"),
        closing_balance=Decimal("125.00"),
    )

    statement = ParsedStatement(
        source=source,
        institution="sample-bank",
        account=account,
        processor="sample.monthly",
        period=period,
        balances=balances,
    )

    assert statement.source is source
    assert statement.institution == "sample-bank"
    assert statement.account is account
    assert statement.processor == "sample.monthly"
    assert statement.period is period
    assert statement.balances is balances
    assert statement.transactions == ()
