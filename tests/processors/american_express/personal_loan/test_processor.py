"""
tests/processors/american_express/personal_loan/test_processor.py

Tests for American Express personal-loan statement processing.
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
from banking_statements.processors.american_express import (
    AmericanExpressPersonalLoanProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-personal-loan.pdf"),
        sha256="a" * 64,
    )


def test_processor_name_is_stable() -> None:
    assert (
        AmericanExpressPersonalLoanProcessor().name
        == "american_express.personal_loan.v1"
    )


def test_processor_matches_supported_structure() -> None:
    result = AmericanExpressPersonalLoanProcessor().match(
        make_text(
            "American Express® Personal Loans\n"
            "Invoice Date07/12/26 Next Invoice Date08/12/26 "
            "Loan Account Ending4-12345\n"
            "Payment Information Account Summary\n"
            "Outstanding Loan Balance $9,100.00 "
            "Previous Outstanding Loan Balance $10,000.00\n"
        )
    )

    assert result.matched is True
    assert result.confidence == 100
    assert result.reason == (
        "Matched American Express personal-loan statement structure."
    )


def test_processor_rejects_unsupported_structure() -> None:
    result = AmericanExpressPersonalLoanProcessor().match(
        make_text("American Express account information")
    )

    assert result.matched is False
    assert result.confidence == 0
    assert result.reason == (
        "Required American Express personal-loan markers were not found."
    )


def test_processor_parses_and_reconciles_monthly_invoice() -> None:
    processor = AmericanExpressPersonalLoanProcessor()
    statement = processor.parse(
        make_source(),
        make_text(
            "American Express® Personal Loans p. 1/3\n"
            "Invoice Date07/12/26 Next Invoice Date08/12/26 "
            "Loan Account Ending4-12345\n"
            "Payment Information Account Summary\n"
            "Outstanding Loan Balance $9,100.00 "
            "Previous Outstanding Loan Balance $10,000.00\n"
            "Payments/Credits -$1,200.00\n"
            "Loan Disbursements +$0.00\n"
            "Interest Charges +$300.00\n"
            "Fees +$0.00\n"
            "Payments and Credits\n"
            "Payments Amount\n"
            "06/26/26* SAMPLE PAYMENT -$1,200.00\n"
            "Total Payments and Credits -$1,200.00\n"
            "Fees\n"
            "Amount\n"
            "Total Fees for this Period $0.00\n"
            "Interest Charges\n"
            "Amount\n"
            "07/12/26 SAMPLE INTEREST $300.00\n"
            "Total Interest Charges for this Period $300.00\n"
        ),
    )

    assert statement.institution == "american_express"
    assert statement.processor == processor.name
    assert statement.account.account_type is AccountType.LOAN
    assert statement.account.display_number == "4-12345"
    assert statement.account.last4 == "2345"
    assert statement.period.start == date(2026, 6, 26)
    assert statement.period.end == date(2026, 7, 12)
    assert statement.balances.opening_balance == Decimal("10000.00")
    assert statement.balances.closing_balance == Decimal("9100.00")

    assert len(statement.transactions) == 2
    assert statement.transactions[0].direction is TransactionDirection.CREDIT
    assert statement.transactions[0].amount == Decimal("1200.00")
    assert statement.transactions[1].direction is TransactionDirection.DEBIT
    assert statement.transactions[1].amount == Decimal("300.00")

    reconciliation = reconcile_statement(statement)
    assert reconciliation.reconciled is True
    assert reconciliation.difference == Decimal("0.00")


def test_processor_parses_initial_disbursement_invoice() -> None:
    statement = AmericanExpressPersonalLoanProcessor().parse(
        make_source(),
        make_text(
            "American Express® Personal Loans p. 1/3\n"
            "Invoice Date06/11/26 Next Invoice Date07/12/26 "
            "Loan Account Ending4-12345\n"
            "Payment Information Account Summary\n"
            "Outstanding Loan Balance $10,000.00 "
            "Previous Outstanding Loan Balance $0.00\n"
            "Payments/Credits -$0.00\n"
            "Loan Disbursements +$10,000.00\n"
            "Interest Charges +$0.00\n"
            "Fees +$0.00\n"
            "Loan Disbursements Amount\n"
            "06/01/26 SAMPLE LOAN DISBURSEMENT $10,000.00\n"
            "06/01\n"
            "Total Loan Disbursements $10,000.00\n"
            "Fees\n"
            "Amount\n"
            "Total Fees for this Period $0.00\n"
        ),
    )

    assert len(statement.transactions) == 1
    assert statement.transactions[0].direction is TransactionDirection.DEBIT
    assert statement.transactions[0].amount == Decimal("10000.00")
    assert reconcile_statement(statement).reconciled is True
