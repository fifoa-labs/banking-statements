"""
tests/processors/wellsfargo/test_signatures.py

Tests for Wells Fargo institution and account-family signatures.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionDetector
from banking_statements.processors.wellsfargo import (
    WELLS_FARGO_BUSINESS_CHECKING_SIGNATURES,
    WELLS_FARGO_BUSINESS_CREDIT_CARD_SIGNATURES,
    WELLS_FARGO_BUSINESS_LINE_OF_CREDIT_SIGNATURES,
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
            "WELLS FARGO SAMPLE VISA CARD\n"
            "Account ending in 1234\n"
            "Statement Period 12/15/2023 to 01/14/2024\n"
            "Account Summary\n"
            "Transactions\n"
        )
    )

    assert result == "wellsfargo"


def test_wells_fargo_business_checking_signature_detects_statement() -> None:
    detector = InstitutionDetector(WELLS_FARGO_BUSINESS_CHECKING_SIGNATURES)

    result = detector.detect(
        make_statement_text(
            "Sample Business Checking\n"
            "Statement period activity summary Account number: 1234567890\n"
            "Withdrawals/Debits - 250.00\n"
            "Transaction history\n"
        )
    )

    assert result == "wellsfargo"


def test_wells_fargo_business_credit_card_signature_detects_statement() -> (
    None
):
    detector = InstitutionDetector(WELLS_FARGO_BUSINESS_CREDIT_CARD_SIGNATURES)

    result = detector.detect(
        make_statement_text(
            "SAMPLE BUSINESS CARD\n"
            "CONSOLIDATED BILLING CONTROL ACCOUNT STATEMENT\n"
            "Statement Closing Date 01/27/25\n"
            "Days in Billing Cycle 31\n"
            "Account Summary\n"
        )
    )

    assert result == "wellsfargo"


def test_wells_fargo_business_line_of_credit_signature_detects_statement() -> (
    None
):
    detector = InstitutionDetector(
        WELLS_FARGO_BUSINESS_LINE_OF_CREDIT_SIGNATURES
    )

    result = detector.detect(
        make_statement_text(
            "BUSINESSLINE\n"
            "Statement Closing Date 03/22/26\n"
            "Days in Billing Cycle 31\n"
            "Credit Line $25,000\n"
            "Account Summary\n"
        )
    )

    assert result == "wellsfargo"
