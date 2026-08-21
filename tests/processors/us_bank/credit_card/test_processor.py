"""
tests/processors/us_bank/credit_card/test_processor.py

Tests for the U.S. Bank credit-card processor.
"""

from __future__ import annotations

from pathlib import Path

from banking_statements.domain import StatementSource
from banking_statements.processors.us_bank.credit_card import (
    USBankCreditCardProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText((StatementPage(number=1, text=value),))


STATEMENT = """U.S. Bank Sample Visa Card
Cardmember Service 1-800-000-0000
Account Number: 9999 8888 7777 1234
01/01/2026 -01/31/2026
New Balance $17.00 Activity Summary
Minimum Payment Due $0.00 Previous Balance + $10.00
Payments - $5.00CR
Purchases + $12.00
New Balance = $17.00
Transactions
Payments and Other Credits
Post Trans
Date Date Ref # Transaction Description Amount
01/05 01/05 PAYMENT THANK YOU $5.00CR
TOTAL THIS PERIOD $5.00CR
Purchases and Other Debits
Post Trans
Date Date Ref # Transaction Description Amount
01/10 01/09 1234 SAMPLE PURCHASE $12.00
TOTAL THIS PERIOD $12.00
"""


def test_processor_matches_parses_and_reconciles() -> None:
    processor = USBankCreditCardProcessor()
    assert processor.name == "us_bank.credit_card.v1"
    match = processor.match(make_text(STATEMENT))
    assert match.matched
    assert match.confidence == 100

    statement = processor.parse(
        StatementSource(path=Path("sample.pdf"), sha256="synthetic"),
        make_text(STATEMENT),
    )
    assert statement.institution == "us_bank"
    assert reconcile_statement(statement).reconciled


def test_processor_matches_zero_activity_without_transactions_marker() -> None:
    text = make_text(
        "U.S. Bank Sample Visa Card\n"
        "Cardmember Service\n"
        "Account Number: 9999 8888 7777 1234\n"
        "01/01/2026 -01/31/2026\n"
        "New Balance $0.00 Activity Summary\n"
        "Previous Balance $0.00\n"
        "New Balance = $0.00"
    )
    processor_match = USBankCreditCardProcessor().match(text)
    assert processor_match.matched
    statement = USBankCreditCardProcessor().parse(
        StatementSource(path=Path("sample.pdf"), sha256="synthetic"), text
    )
    assert statement.transactions == ()


def test_processor_rejects_unrelated_text() -> None:
    match = USBankCreditCardProcessor().match(make_text("not a statement"))
    assert not match.matched
    assert match.confidence == 0
    assert "markers" in match.reason
