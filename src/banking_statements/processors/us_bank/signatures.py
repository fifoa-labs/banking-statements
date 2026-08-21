"""
src/banking_statements/processors/us_bank/signatures.py

Institution detection signatures for supported U.S. Bank statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

US_BANK_BUSINESS_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="us_bank",
        required_markers=(
            "U.S. BANK SILVER - BUSINESS CHECKING",
            "U.S. Bank National Association",
            "Account Summary",
            "Beginning Balance on",
            "Ending Balance on",
        ),
    ),
)

US_BANK_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="us_bank",
        required_markers=(
            "Cardmember Service",
            "Activity Summary",
            "Previous Balance",
            "New Balance",
            "U.S. Bank",
        ),
    ),
)

US_BANK_SIGNATURES = (
    *US_BANK_BUSINESS_CHECKING_SIGNATURES,
    *US_BANK_CREDIT_CARD_SIGNATURES,
)
