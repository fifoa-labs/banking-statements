"""
tests/processors/penfed/heloc/test_processor.py

Tests for the PenFed HELOC statement processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements.domain import (
    AccountType,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.penfed import PenFedHelocProcessor
from banking_statements.processors.penfed.heloc.activity import (
    PenFedHelocActivityKind,
    PenFedHelocActivityRow,
)
from banking_statements.processors.penfed.heloc.processor import (
    _activity_movement,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-penfed-heloc.pdf"),
        sha256="a" * 64,
    )


def statement_text(
    *,
    interest: str = "12.50",
    payment_credit: str = "125.00",
    closing: str = "887.50",
    activity: str | None = None,
    finance: str = "12.50",
) -> str:
    """Build a complete synthetic PenFed HELOC statement."""
    activity_text = activity or (
        "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
        "$25.00 $25.00 $0.00 $0.00 $0.00 $0.00\n"
        "03/10/26 PAYMENT RECEIVED "
        "$0.00 $0.00 $100.00 $0.00 $0.00 $0.00\n"
        "03/10/26 PAYMENT RECEIVED "
        "$100.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
    )

    return (
        "Home Equity Line of Credit Statement\n"
        "Statement Closing Date: March 19, 2026\n"
        "Online: www.PenFed.org\n"
        "Loan Number 7000001234\n"
        "CURRENT ACCOUNT INFORMATION\n"
        "Previous Balance $1,000.00\n"
        "Advances and Fees $0.00\n"
        f"Interest Charges ${interest}\n"
        f"Payment and Other Credits -${payment_credit}\n"
        "Debit/Credit Adjustment $0.00\n"
        f"New Balance as of 03/19/26 ${closing}\n"
        "HELOC ACTIVITY AND FINANCE CHARGES\n"
        "Transaction Activity (02/19/26 through 03/19/26)\n"
        "Total Principal Charges/ Unapplied/\n"
        "Date Description Amount Applied Interest Escrow Fees Other\n"
        f"{activity_text}"
        "FINANCE CHARGES\n"
        f"Total Finance Charge ${finance}\n"
        "Statement Closing Date: 03/19/2026\n"
        "Account Number: 7000001234\n"
    )


def test_processor_name_and_matching() -> None:
    processor = PenFedHelocProcessor()

    assert processor.name == "penfed.heloc.v1"

    matched = processor.match(make_text(statement_text()))
    unmatched = processor.match(make_text("Other statement"))

    assert matched.matched is True
    assert matched.confidence == 100
    assert matched.reason == "Matched PenFed HELOC statement structure."
    assert unmatched.matched is False
    assert unmatched.confidence == 0
    assert unmatched.reason == "Required PenFed HELOC markers were not found."


def test_processor_parses_and_reconciles_statement() -> None:
    statement = PenFedHelocProcessor().parse(
        make_source(),
        make_text(statement_text()),
    )

    assert statement.institution == "penfed"
    assert statement.processor == "penfed.heloc.v1"
    assert statement.account.account_type is AccountType.LINE_OF_CREDIT
    assert statement.account.display_number == "7000001234"
    assert statement.account.last4 == "1234"
    assert statement.period.start == date(2026, 2, 19)
    assert statement.period.end == date(2026, 3, 19)
    assert statement.balances.opening_balance == Decimal("1000.00")
    assert statement.balances.closing_balance == Decimal("887.50")

    assert len(statement.transactions) == 3
    assert statement.transactions[0].amount == Decimal("25.00")
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[1].amount == Decimal("100.00")
    assert statement.transactions[1].direction is TransactionDirection.CREDIT
    assert statement.transactions[2].amount == Decimal("12.50")
    assert statement.transactions[2].direction is TransactionDirection.DEBIT

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")


def test_processor_reconciles_returned_check_cycle() -> None:
    activity = (
        "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
        "$25.00 $25.00 $0.00 $0.00 $0.00 $0.00\n"
        "03/10/26 PAYMENT RECEIVED "
        "$100.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
        "03/11/26 RETURNED CHECK FEE "
        "$0.00 $0.00 $0.00 $0.00 $5.00 $0.00\n"
        "03/12/26 RETURNED CHECK FEE "
        "$0.00 $0.00 $0.00 $0.00 ($5.00) $0.00\n"
        "03/12/26 NSF/RETURNED CHECK REVERSAL "
        "$0.00 ($25.00) ($100.00) $0.00 $0.00 $0.00\n"
        "03/13/26 PAYMENT RECEIVED "
        "$100.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
    )

    statement = PenFedHelocProcessor().parse(
        make_source(),
        make_text(
            statement_text(
                payment_credit="100.00",
                closing="912.50",
                activity=activity,
            )
        ),
    )

    reconciliation = reconcile_statement(statement)

    assert reconciliation.transaction_debits == Decimal("142.50")
    assert reconciliation.transaction_credits == Decimal("230.00")
    assert reconciliation.expected_closing_balance == Decimal("912.50")
    assert reconciliation.reconciled is True


def test_processor_requires_finance_total_to_match_summary() -> None:
    with pytest.raises(ValueError, match="finance charge does not match"):
        PenFedHelocProcessor().parse(
            make_source(),
            make_text(statement_text(finance="11.50")),
        )


def test_processor_requires_activity_to_match_summary() -> None:
    with pytest.raises(
        ValueError, match="transaction activity does not match"
    ):
        PenFedHelocProcessor().parse(
            make_source(),
            make_text(
                statement_text(
                    activity=(
                        "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
                        "$24.00 $24.00 $0.00 $0.00 $0.00 $0.00\n"
                        "03/10/26 PAYMENT RECEIVED "
                        "$100.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
                    )
                )
            ),
        )


def test_activity_movement_rejects_incomplete_semantics() -> None:
    row = PenFedHelocActivityRow(
        process_date="03/10/26",
        effective_date=None,
        kind=PenFedHelocActivityKind.PAYMENT_RECEIVED,
        description="PAYMENT RECEIVED",
        total_amount=Decimal("25.00"),
        principal_applied=Decimal("0.00"),
        interest=Decimal("0.00"),
        escrow=Decimal("0.00"),
        fees=Decimal("0.00"),
        other=Decimal("0.00"),
        amount=None,
        direction=TransactionDirection.CREDIT,
        raw_text="synthetic row",
    )

    with pytest.raises(ValueError, match="incomplete transaction semantics"):
        _activity_movement((row,))
