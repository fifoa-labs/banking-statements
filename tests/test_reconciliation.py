"""
tests/test_reconciliation.py

Tests for optional statement reconciliation.
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
    TransactionDirection,
    TransactionEvent,
)
from banking_statements.reconciliation import reconcile_statement


def make_statement(
    *,
    opening_balance: str,
    closing_balance: str,
    transactions: tuple[TransactionEvent, ...] = (),
    account_type: AccountType = AccountType.CREDIT_CARD,
) -> ParsedStatement:
    """Build a parsed statement for reconciliation tests."""
    return ParsedStatement(
        source=StatementSource(
            path=Path("statement.pdf"),
            sha256="abc123",
        ),
        institution="sample-bank",
        account=AccountIdentity(
            account_type=account_type,
            display_number="000000000001234",
            last4="1234",
        ),
        processor="sample.credit_card",
        period=StatementPeriod(
            start=date(2026, 7, 1),
            end=date(2026, 7, 31),
        ),
        balances=StatementBalanceSummary(
            opening_balance=Decimal(opening_balance),
            closing_balance=Decimal(closing_balance),
        ),
        transactions=transactions,
    )


def test_reconcile_statement_matches_balances() -> None:
    statement = make_statement(
        opening_balance="130.92",
        closing_balance="1214.78",
        transactions=(
            TransactionEvent(
                date=date(2026, 7, 4),
                amount=Decimal("1000.00"),
                direction=TransactionDirection.DEBIT,
                description="PURCHASE ONE",
            ),
            TransactionEvent(
                date=date(2026, 7, 5),
                amount=Decimal("83.86"),
                direction=TransactionDirection.DEBIT,
                description="PURCHASE TWO",
            ),
        ),
    )

    result = reconcile_statement(statement)

    assert result.opening_balance == Decimal("130.92")
    assert result.closing_balance == Decimal("1214.78")
    assert result.transaction_debits == Decimal("1083.86")
    assert result.transaction_credits == Decimal("0")
    assert result.expected_closing_balance == Decimal("1214.78")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True


def test_reconcile_statement_reports_mismatch_without_raising() -> None:
    statement = make_statement(
        opening_balance="100.00",
        closing_balance="120.01",
        transactions=(
            TransactionEvent(
                date=date(2026, 7, 10),
                amount=Decimal("20.00"),
                direction=TransactionDirection.DEBIT,
                description="PURCHASE",
            ),
        ),
    )

    result = reconcile_statement(statement)

    assert result.expected_closing_balance == Decimal("120.00")
    assert result.difference == Decimal("0.01")
    assert result.reconciled is False


def test_reconcile_statement_accounts_for_credits() -> None:
    statement = make_statement(
        opening_balance="100.00",
        closing_balance="125.00",
        transactions=(
            TransactionEvent(
                date=date(2026, 7, 10),
                amount=Decimal("50.00"),
                direction=TransactionDirection.DEBIT,
                description="PURCHASE",
            ),
            TransactionEvent(
                date=date(2026, 7, 11),
                amount=Decimal("25.00"),
                direction=TransactionDirection.CREDIT,
                description="PAYMENT",
            ),
        ),
    )

    result = reconcile_statement(statement)

    assert result.transaction_debits == Decimal("50.00")
    assert result.transaction_credits == Decimal("25.00")
    assert result.expected_closing_balance == Decimal("125.00")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True


def test_reconcile_statement_handles_no_transactions() -> None:
    statement = make_statement(
        opening_balance="-95.90",
        closing_balance="-95.90",
    )

    result = reconcile_statement(statement)

    assert result.transaction_debits == Decimal("0")
    assert result.transaction_credits == Decimal("0")
    assert result.expected_closing_balance == Decimal("-95.90")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True


def test_reconcile_checking_statement_uses_account_balance_direction() -> None:
    statement = make_statement(
        opening_balance="1000.00",
        closing_balance="1150.00",
        account_type=AccountType.CHECKING,
        transactions=(
            TransactionEvent(
                date=date(2026, 1, 5),
                amount=Decimal("200.00"),
                direction=TransactionDirection.CREDIT,
                description="SAMPLE DEPOSIT",
            ),
            TransactionEvent(
                date=date(2026, 1, 10),
                amount=Decimal("50.00"),
                direction=TransactionDirection.DEBIT,
                description="SAMPLE PAYMENT",
            ),
        ),
    )

    result = reconcile_statement(statement)

    assert result.transaction_debits == Decimal("50.00")
    assert result.transaction_credits == Decimal("200.00")
    assert result.expected_closing_balance == Decimal("1150.00")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True
