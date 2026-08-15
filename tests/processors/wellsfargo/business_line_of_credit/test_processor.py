"""
tests/processors/wellsfargo/business_line_of_credit/test_processor.py

Tests for the Wells Fargo business line-of-credit statement processor.
"""

from __future__ import annotations

from pathlib import Path

from banking_statements.domain import AccountType, StatementSource
from banking_statements.processors.wellsfargo.business_line_of_credit import (
    WellsFargoBusinessLineOfCreditProcessor,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def test_processor_name() -> None:
    processor = WellsFargoBusinessLineOfCreditProcessor()

    assert processor.name == "wellsfargo.business_line_of_credit.v1"


def test_processor_match() -> None:
    processor = WellsFargoBusinessLineOfCreditProcessor()

    matched = processor.match(
        make_text(
            "BUSINESSLINE\n"
            "Statement Closing Date 03/22/26\n"
            "Days in Billing Cycle 31\n"
            "Credit Line $25,000\n"
            "Account Summary\n"
        )
    )
    unmatched = processor.match(make_text("Other statement"))

    assert matched.matched is True
    assert matched.confidence == 100
    assert unmatched.matched is False
    assert unmatched.confidence == 0


def test_processor_parses_zero_activity_statement() -> None:
    processor = WellsFargoBusinessLineOfCreditProcessor()
    source = StatementSource(
        path=Path("sample.pdf"),
        sha256="0" * 64,
    )
    text = make_text(
        "BUSINESSLINE\n"
        "Account Number 1111 2222 3333 1234\n"
        "Statement Closing Date 07/22/25\n"
        "Days in Billing Cycle 0\n"
        "Credit Line $25,000\n"
        "Account Summary\n"
        "Previous Balance $0.00\n"
        "New Balance = $0.00\n"
    )

    statement = processor.parse(source, text)

    assert statement.institution == "wellsfargo"
    assert statement.processor == processor.name
    assert statement.account.account_type is AccountType.LINE_OF_CREDIT
    assert statement.account.last4 == "1234"
    assert (
        statement.balances.opening_balance
        == statement.balances.closing_balance
    )
    assert statement.transactions == ()
