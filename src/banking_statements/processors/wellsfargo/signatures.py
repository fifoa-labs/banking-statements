"""
src/banking_statements/processors/wellsfargo/signatures.py

Institution and account-family detection signatures for Wells Fargo statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

WELLS_FARGO_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "College Checking",
            "Transaction history",
            "Subtractions",
        ),
    ),
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "Everyday Checking",
            "Transaction history",
            "Subtractions",
        ),
    ),
)

WELLS_FARGO_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "Account ending in",
            "Statement Period",
            "Account Summary",
            "Transactions",
        ),
    ),
)

WELLS_FARGO_BUSINESS_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "Business Checking",
            "Transaction history",
            "Withdrawals/Debits",
        ),
    ),
)

WELLS_FARGO_BUSINESS_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "CONSOLIDATED BILLING CONTROL ACCOUNT STATEMENT",
            "Statement Closing Date",
            "Days in Billing Cycle",
            "Account Summary",
        ),
    ),
)

WELLS_FARGO_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "Wells Fargo Bank, N.A.",
            "wellsfargo.com",
        ),
    ),
    *WELLS_FARGO_CHECKING_SIGNATURES,
    *WELLS_FARGO_CREDIT_CARD_SIGNATURES,
    *WELLS_FARGO_BUSINESS_CHECKING_SIGNATURES,
    *WELLS_FARGO_BUSINESS_CREDIT_CARD_SIGNATURES,
)
