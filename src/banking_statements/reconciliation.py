"""
src/banking_statements/reconciliation.py

Optional reconciliation checks for parsed banking statements.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from banking_statements.domain import (
    AccountType,
    ParsedStatement,
    TransactionDirection,
)


@dataclass(frozen=True, slots=True)
class StatementReconciliation:
    """Result of reconciling a parsed statement."""

    opening_balance: Decimal
    closing_balance: Decimal
    transaction_debits: Decimal
    transaction_credits: Decimal
    expected_closing_balance: Decimal
    difference: Decimal
    reconciled: bool


_DEBT_ACCOUNT_TYPES = frozenset(
    {
        AccountType.CREDIT_CARD,
        AccountType.LINE_OF_CREDIT,
    }
)


def reconcile_statement(
    statement: ParsedStatement,
) -> StatementReconciliation:
    """Reconcile parsed transactions against statement balances."""
    transaction_debits = sum(
        (
            transaction.amount
            for transaction in statement.transactions
            if transaction.direction is TransactionDirection.DEBIT
        ),
        start=Decimal("0"),
    )
    transaction_credits = sum(
        (
            transaction.amount
            for transaction in statement.transactions
            if transaction.direction is TransactionDirection.CREDIT
        ),
        start=Decimal("0"),
    )

    if statement.account.account_type in _DEBT_ACCOUNT_TYPES:
        expected_closing_balance = (
            statement.balances.opening_balance
            + transaction_debits
            - transaction_credits
        )
    else:
        expected_closing_balance = (
            statement.balances.opening_balance
            + transaction_credits
            - transaction_debits
        )

    difference = statement.balances.closing_balance - expected_closing_balance

    return StatementReconciliation(
        opening_balance=statement.balances.opening_balance,
        closing_balance=statement.balances.closing_balance,
        transaction_debits=transaction_debits,
        transaction_credits=transaction_credits,
        expected_closing_balance=expected_closing_balance,
        difference=difference,
        reconciled=difference == Decimal("0"),
    )
