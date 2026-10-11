"""
tests/processors/chime/test_processor.py

Synthetic evidence for Chime account isolation and strict grammar handling.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements import api
from banking_statements.domain import AccountType, StatementSource
from banking_statements.exceptions import UnsupportedStatementError
from banking_statements.processors import (
    build_default_institution_detector,
    build_default_processor_registry,
)
from banking_statements.processors.chime import (
    ChimeCheckingProcessor,
    ChimeCreditBuilderProcessor,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText

SOURCE = StatementSource(Path("synthetic.pdf"), "synthetic")
HEADER = "TRANSACTION DATE DESCRIPTION TYPE AMOUNT"
CHECKING = """Checking Account Statement
Account number
123456781234
Statement period
February 2024 (February 01, 2024 - February 29, 2024)
Summary
Beginning balance on February 01, 2024 $15.00
Deposits $80.00
Transfers -$30.00
Ending balance on February 29, 2024 $65.00
Transactions
TRANSACTION DATE DESCRIPTION TYPE AMOUNT NET AMOUNT SETTLEMENT DATE
2/20/2024 Unknown merchant Transfer -$30.00 -$30.00 2/21/2024
2/10/2024 Sample payroll Deposit $80.00 $80.00 2/11/2024
SAMPLE EMPLOYER
Yearly Summary
Chime Member Services
"""
CARD = """Credit Builder Card Account Billing Statement
Account number Routing number (for payments)
987654325678 012345678
Statement period
February 2024 (January 30th, 2024 - February 28th, 2024)
Summary Your Payment
Previous Balance $0.00 Payment Due Date 3/20/2024
Payments/Credits $0.00 Total Due $0.00
New spending $0.00
Fees $0.00
New balance $0.00
Payments
TRANSACTION DATE DESCRIPTION TYPE AMOUNT SETTLEMENT DATE
TOTAL FOR THIS PERIOD: $0.00
Transactions
TRANSACTION DATE DESCRIPTION TYPE AMOUNT SETTLEMENT DATE
TOTAL FOR THIS PERIOD: $0.00
Fees
TRANSACTION DATE DESCRIPTION TYPE AMOUNT SETTLEMENT DATE
TOTAL FOR THIS PERIOD: $0.00
Disputed transactions
TRANSACTION DATE DESCRIPTION TYPE AMOUNT SETTLEMENT DATE
TOTAL FOR THIS PERIOD: $0.00
Chime
"""
SECURED = """Credit Builder Secured Account Billing Statement
Account number
246813579012
Statement period
February 2024 (January 30, 2024 - February 28, 2024)
Summary
Beginning balance on January 30, 2024 $30.00
Transfers -$30.00
Ending balance on February 28, 2024 $0.00
Transactions
TRANSACTION DATE DESCRIPTION TYPE AMOUNT SETTLEMENT DATE
2/02/2024 Transfer to Checking Account Transfer -$30.00 2/03/2024
TOTAL FOR THIS PERIOD: -$30.00
"""


def text(*pages: str) -> StatementText:
    return StatementText(
        tuple(
            StatementPage(index, page) for index, page in enumerate(pages, 1)
        )
    )


def test_checking_evidence_and_balances() -> None:
    document = text(CHECKING, "Error Resolution Procedures\nChime")
    processor = ChimeCheckingProcessor()
    assert processor.match(document).matched
    assert not processor.match(text("Unrelated Bancorp document")).matched
    assert build_default_institution_detector().detect(document) == "chime"
    assert (
        build_default_processor_registry().select(document).name
        == processor.name
    )
    result = processor.parse(SOURCE, document)
    assert result.account.last4 == "1234"
    assert result.period.end == date(2024, 2, 29)
    assert reconcile_statement(result).reconciled
    assert result.transactions[0].description == "Unknown merchant"
    transaction = result.transactions[1]
    assert transaction.amount == Decimal("80")
    assert transaction.description == "Sample payroll SAMPLE EMPLOYER"
    assert transaction.evidence is not None
    assert transaction.evidence.page == 1
    assert transaction.evidence.sequence == 2
    assert transaction.evidence.raw_text is not None
    assert "2/11/2024\nSAMPLE EMPLOYER" in transaction.evidence.raw_text


def test_credit_builder_keeps_accounts_separate() -> None:
    document = text(CARD, "Chime legal text", SECURED)
    processor = ChimeCreditBuilderProcessor()
    assert processor.match(document).matched
    assert not processor.match(text(CHECKING)).matched
    assert build_default_institution_detector().detect(document) == "chime"
    assert (
        build_default_processor_registry().select(document).name
        == processor.name
    )
    card = processor.parse(SOURCE, document)
    assert card.account.account_type == AccountType.CREDIT_CARD
    assert card.account.last4 == "5678"
    assert card.transactions == ()
    (secured,) = card.additional_statements
    assert secured.account.account_type == AccountType.CHECKING
    assert secured.account.last4 == "9012"
    assert secured.transactions[0].evidence is not None
    assert secured.transactions[0].evidence.page == 3
    assert card.period == secured.period
    assert reconcile_statement(card).reconciled
    assert reconcile_statement(secured).reconciled


def test_api_returns_and_flattens_both_accounts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Reader:
        def read(self, source: StatementSource) -> StatementText:
            del source
            return text(CARD, SECURED)

    path = tmp_path / "random-name.pdf"
    path.write_bytes(b"synthetic")
    monkeypatch.setattr(api, "PdfStatementTextReader", Reader)
    result = api.parse_statement(path)
    assert len(result.accounts) == 2
    assert all(
        account.reconciliation.reconciled for account in result.accounts
    )
    results = api.parse_statements(tmp_path)
    assert [account.statement.account.last4 for account in results] == [
        "5678",
        "9012",
    ]


def test_checking_continues_across_pages() -> None:
    before, after = CHECKING.split("2/10/2024", 1)
    document = text(
        before + "Page 1 of 3\n",
        HEADER + " NET AMOUNT SETTLEMENT DATE\n2/10/2024" + after,
    )
    result = ChimeCheckingProcessor().parse(SOURCE, document)
    assert len(result.transactions) == 2
    assert reconcile_statement(result).reconciled


def test_zero_activity_and_error_resolution_boundary() -> None:
    document = CHECKING.split("Transactions\n", 1)[0] + (
        "Transactions\n" + HEADER + " NET AMOUNT SETTLEMENT DATE\n\n"
        "Error Resolution Procedures\nChime"
    )
    assert (
        ChimeCheckingProcessor().parse(SOURCE, text(document)).transactions
        == ()
    )


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            "Account number\n123456781234",
            "Account number\nxxxx",
            "account number",
        ),
        ("Statement period", "Unknown period", "statement period"),
        (
            "February 01, 2024 - February 29, 2024",
            "March 01, 2024 - February 29, 2024",
            "Reversed",
        ),
        ("Beginning balance on February 01, 2024 $15.00", "", "balance"),
        ("-$30.00 -$30.00", "-$30.00 -$31.00", "net amount"),
        ("-$30.00 -$30.00", "-$30.00", "columns"),
        ("2/20/2024", "3/20/2024", "outside"),
        ("Transfer -$30.00", "Purchase -$30.00", "activity row"),
        ("2/20/2024", "BROKEN $30.00", "activity row"),
        ("Transactions\n", "Transactions\nORPHAN\n", "Orphan"),
        ("Transactions\n", "Missing\n", "Transactions section"),
        ("Yearly Summary", "", "table boundary"),
    ],
)
def test_checking_rejects_unknown_grammar(
    old: str,
    new: str,
    message: str,
) -> None:
    with pytest.raises(UnsupportedStatementError, match=message):
        ChimeCheckingProcessor().parse(
            SOURCE, text(CHECKING.replace(old, new))
        )


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            "Previous Balance $0.00",
            "Previous Balance $1.00",
            "new source evidence",
        ),
        (
            "TOTAL FOR THIS PERIOD: $0.00",
            "TOTAL FOR THIS PERIOD: $1.00",
            "activity table",
        ),
        (
            "Transactions\n" + HEADER,
            "Transactions\n2/01/2024 SAMPLE $0.00\n" + HEADER,
            "activity table",
        ),
    ],
)
def test_credit_rejects_unproven_card_activity(
    old: str,
    new: str,
    message: str,
) -> None:
    with pytest.raises(UnsupportedStatementError, match=message):
        ChimeCreditBuilderProcessor().parse(
            SOURCE,
            text(CARD.replace(old, new), SECURED),
        )


def test_credit_requires_exactly_one_secured_account() -> None:
    with pytest.raises(
        UnsupportedStatementError, match="secured account section"
    ):
        ChimeCreditBuilderProcessor().parse(SOURCE, text(CARD))
