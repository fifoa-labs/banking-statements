"""
tests/processors/wellsfargo/test_signatures.py

Tests for Wells Fargo institution and account-family signatures.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionDetector
from banking_statements.processors.wellsfargo import (
    WELLS_FARGO_CHECKING_SIGNATURES,
    WELLS_FARGO_CREDIT_CARD_SIGNATURES,
    WELLS_FARGO_SIGNATURES,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for signature tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_wells_fargo_signature_detects_statement() -> None:
    detector = InstitutionDetector(WELLS_FARGO_SIGNATURES)

    result = detector.detect(
        make_statement_text(
            "Wells Fargo Bank, N.A.\n"
            "Online banking available at wellsfargo.com\n"
        )
    )

    assert result == "wellsfargo"


def test_wells_fargo_college_checking_signature_detects_statement() -> None:
    detector = InstitutionDetector(WELLS_FARGO_CHECKING_SIGNATURES)

    result = detector.detect(
        make_statement_text(
            "Wells Fargo College Checking\n"
            "Transaction history\n"
            "Withdrawals/Subtractions\n"
        )
    )

    assert result == "wellsfargo"


def test_wells_fargo_everyday_checking_signature_detects_statement() -> None:
    detector = InstitutionDetector(WELLS_FARGO_CHECKING_SIGNATURES)

    result = detector.detect(
        make_statement_text(
            "Wells Fargo Everyday Checking\n"
            "Transaction history\n"
            "Withdrawals/Subtractions\n"
        )
    )

    assert result == "wellsfargo"


def test_wells_fargo_credit_card_signature_detects_statement() -> None:
    detector = InstitutionDetector(WELLS_FARGO_CREDIT_CARD_SIGNATURES)

    result = detector.detect(
        make_statement_text(
            "WELLS FARGO ACTIVE CASH VISA SIGNATURE CARD\n"
            "Account ending in 7988\n"
            "Statement Period 12/15/2023 to 01/14/2024\n"
            "Account Summary\n"
            "Transactions\n"
        )
    )

    assert result == "wellsfargo"
