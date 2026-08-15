"""
tests/processors/chase/heloc/test_processor.py

Tests for the Chase HELOC statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.chase import ChaseHelocProcessor
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_processor_name() -> None:
    assert ChaseHelocProcessor().name == "chase.heloc.v1"


def test_processor_match() -> None:
    processor = ChaseHelocProcessor()

    matched = processor.match(
        make_text(
            "JPMorgan Chase Bank, N.A.\n"
            "Line of credit information\n"
            "Transaction activity\n"
        )
    )
    unmatched = processor.match(make_text("Other statement"))

    assert matched.matched is True
    assert matched.confidence == 100
    assert matched.reason == "Matched Chase HELOC statement structure."
    assert unmatched.matched is False
    assert unmatched.confidence == 0
    assert unmatched.reason == "Required Chase HELOC markers were not found."


def test_processor_parses_and_reconciles_statement() -> None:
    processor = ChaseHelocProcessor()
    source = StatementSource(
        path=Path("sample.pdf"),
        sha256="0" * 64,
    )

    text = make_text(
        "JPMorgan Chase Bank, N.A.\n"
        "Home EquityLine of credit Statement\n"
        "Statement Period\n"
        "01/20/2026 - 02/18/2026\n"
        "Line of credit information\n"
        "Account number 0000001234 Previous balance $1,000.00\n"
        "Payments/credits $200.00\n"
        "Fees chrgd/advances $500.00\n"
        "Interest charged $25.00\n"
        "New balance $1,325.00\n"
        "Transaction activity\n"
        "Transaction Description Total received Principal Interest\n"
        "01/25/2026 ADDITIONAL PRINCIPAL PYMT $100.00 $100.00\n"
        "02/10/2026 PAYMENT Revolving $0.00 $40.00 $60.00\n"
        "02/10/2026 FUNDS APPLIED Revolving $100.00\n"
        "02/12/2026 BALANCE ADVANCE Revolving $0.00 ($500.00)\n"
        "Additional information\n"
        "Finance charge calculations\n"
        "Purchases, Balance Transfers, 01/20/2026 - 30 "
        "6.63000% 0.0181644% $1,000.00 $25.00\n"
        "Cash Advances - Revolving 02/18/2026\n"
    )

    statement = processor.parse(source, text)

    assert statement.institution == "chase"
    assert statement.processor == "chase.heloc.v1"
    assert statement.account.account_type is AccountType.LINE_OF_CREDIT
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 1, 20)
    assert statement.period.end == date(2026, 2, 18)
    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("1325.00")

    directions = [
        transaction.direction for transaction in statement.transactions
    ]
    assert directions == [
        TransactionDirection.CREDIT,
        TransactionDirection.CREDIT,
        TransactionDirection.DEBIT,
        TransactionDirection.DEBIT,
    ]

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")


def test_processor_parses_zero_activity_credit_balance() -> None:
    processor = ChaseHelocProcessor()
    source = StatementSource(
        path=Path("sample.pdf"),
        sha256="0" * 64,
    )

    statement = processor.parse(
        source,
        make_text(
            "JPMorgan Chase Bank, N.A.\n"
            "Statement Period\n"
            "02/19/2026 - 03/18/2026\n"
            "Line of credit information\n"
            "Account number 0000001234 Previous balance ($25.00)\n"
            "Payments/credits $0.00\n"
            "Fees chrgd/advances $0.00\n"
            "Interest charged $0.00\n"
            "New balance ($25.00)\n"
            "Transaction activity\n"
            "Additional information\n"
            "Finance charge calculations\n"
            "Purchases, Balance Transfers, 02/19/2026 - 28 "
            "6.63000% 0.0181644% ($25.00) $0.00\n"
            "Cash Advances - Revolving 03/18/2026\n"
        ),
    )

    assert statement.transactions == ()
    assert reconcile_statement(statement).reconciled is True


def test_processor_reconciles_same_cycle_interest_payment_and_undated_fee() -> (  # noqa: E501
    None
):
    processor = ChaseHelocProcessor()
    source = StatementSource(path=Path("sample.pdf"), sha256="0" * 64)

    statement = processor.parse(
        source,
        make_text(
            "JPMorgan Chase Bank, N.A.\n"
            "Home EquityLine of credit Statement\n"
            "Statement Period\n"
            "01/01/2026 - 01/31/2026\n"
            "Line of credit information\n"
            "Account number 0000001234 Previous balance $0.00\n"
            "Payments/credits $1,025.00\n"
            "Fees chrgd/advances $2,025.00\n"
            "Interest charged $25.00\n"
            "New balance $1,050.00\n"
            "Transaction activity\n"
            "Transaction Description Total received Principal Interest\n"
            "01/02/2026 INITIAL FUNDING Revolving $0.00 ($2,000.00)\n"
            "FIN CHARGE-ORIG FEE ASSES $0.00 $25.00\n"
            "01/10/2026 ADDITIONAL PRINCIPAL PYMT $1,000.00 $1,000.00\n"
            "01/15/2026 PAYMENT Revolving $0.00 $25.00\n"
            "01/15/2026 FUNDS APPLIED Revolving $25.00\n"
            "Additional information\n"
            "Finance charge calculations\n"
            "Purchases, Balance Transfers, 01/02/2026 - 14 "
            "6.63000% 0.0181644% $2,000.00 $40.00\n"
            "Cash Advances - Revolving 01/15/2026\n"
            "Purchases, Balance Transfers, 01/16/2026 - 16 "
            "6.63000% 0.0181644% $925.00 $10.00\n"
            "Cash Advances - Revolving 01/31/2026\n"
        ),
    )

    reconciliation = reconcile_statement(statement)

    assert reconciliation.transaction_debits == Decimal("2075.00")
    assert reconciliation.transaction_credits == Decimal("1025.00")
    assert reconciliation.expected_closing_balance == Decimal("1050.00")
    assert reconciliation.reconciled is True
