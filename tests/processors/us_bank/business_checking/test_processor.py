"""
tests/processors/us_bank/business_checking/test_processor.py

Tests for the U.S. Bank business-checking processor.
"""

from __future__ import annotations

from pathlib import Path

from banking_statements.domain import StatementSource
from banking_statements.processors.us_bank.business_checking import (
    USBankBusinessCheckingProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    return StatementText((StatementPage(number=1, text=value),))


STATEMENT = """U.S. BANK SILVER - BUSINESS CHECKING
U.S. Bank National Association
Account Number: 9-876-5432-1000
Account Summary
Beginning Balance on Jan 1 $ 10.00
Other Deposits 1 5.00
Ending Balance on Jan 31, 2026 $ 15.00
Other Deposits
Date Description of Transaction Ref Number Amount
Jan 15 Sample Deposit $ 5.00
Total Other Deposits $ 5.00
"""


def test_processor_matches_parses_and_reconciles() -> None:
    processor = USBankBusinessCheckingProcessor()
    assert processor.name == "us_bank.business_checking.v1"
    match = processor.match(make_text(STATEMENT))
    assert match.matched
    assert match.confidence == 100

    statement = processor.parse(
        StatementSource(path=Path("sample.pdf"), sha256="synthetic"),
        make_text(STATEMENT),
    )
    assert statement.institution == "us_bank"
    assert reconcile_statement(statement).reconciled


def test_processor_rejects_unrelated_text() -> None:
    match = USBankBusinessCheckingProcessor().match(
        make_text("not a statement")
    )
    assert not match.matched
    assert match.confidence == 0
    assert "markers" in match.reason
