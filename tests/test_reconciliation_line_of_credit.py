"""
tests/test_reconciliation_line_of_credit.py

Tests for line-of-credit statement reconciliation semantics.
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


def test_line_of_credit_reconciles_as_debt_account() -> None:
    statement = ParsedStatement(
        source=StatementSource(
            path=Path("sample.pdf"),
            sha256="0" * 64,
        ),
        institution="sample",
        account=AccountIdentity(
            account_type=AccountType.LINE_OF_CREDIT,
            display_number="1234",
            last4="1234",
        ),
        processor="sample.line_of_credit.v1",
        period=StatementPeriod(
            start=date(2026, 1, 1),
            end=date(2026, 1, 31),
        ),
        balances=StatementBalanceSummary(
            opening_balance=Decimal("1000.00"),
            closing_balance=Decimal("1315.00"),
        ),
        transactions=(
            TransactionEvent(
                date=date(2026, 1, 10),
                amount=Decimal("400.00"),
                direction=TransactionDirection.DEBIT,
                description="SAMPLE ADVANCE",
            ),
            TransactionEvent(
                date=date(2026, 1, 15),
                amount=Decimal("100.00"),
                direction=TransactionDirection.CREDIT,
                description="SAMPLE PAYMENT",
            ),
            TransactionEvent(
                date=date(2026, 1, 31),
                amount=Decimal("15.00"),
                direction=TransactionDirection.DEBIT,
                description="SAMPLE FINANCE CHARGE",
            ),
        ),
    )

    result = reconcile_statement(statement)

    assert result.expected_closing_balance == Decimal("1315.00")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True
