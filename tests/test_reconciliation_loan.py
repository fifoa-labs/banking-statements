"""
tests/test_reconciliation_loan.py

Tests for installment-loan statement reconciliation semantics.
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


def test_loan_reconciles_as_debt_account() -> None:
    statement = ParsedStatement(
        source=StatementSource(
            path=Path("sample.pdf"),
            sha256="0" * 64,
        ),
        institution="sample",
        account=AccountIdentity(
            account_type=AccountType.LOAN,
            display_number="4-12345",
            last4="2345",
        ),
        processor="sample.loan.v1",
        period=StatementPeriod(
            start=date(2026, 6, 1),
            end=date(2026, 6, 30),
        ),
        balances=StatementBalanceSummary(
            opening_balance=Decimal("10000.00"),
            closing_balance=Decimal("9100.00"),
        ),
        transactions=(
            TransactionEvent(
                date=date(2026, 6, 10),
                amount=Decimal("1200.00"),
                direction=TransactionDirection.CREDIT,
                description="SAMPLE PAYMENT",
            ),
            TransactionEvent(
                date=date(2026, 6, 30),
                amount=Decimal("300.00"),
                direction=TransactionDirection.DEBIT,
                description="SAMPLE INTEREST",
            ),
        ),
    )

    result = reconcile_statement(statement)

    assert result.expected_closing_balance == Decimal("9100.00")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True
