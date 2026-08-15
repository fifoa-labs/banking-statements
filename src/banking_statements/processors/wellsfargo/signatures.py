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

WELLS_FARGO_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "Wells Fargo Bank, N.A.",
            "wellsfargo.com",
        ),
    ),
    *WELLS_FARGO_CHECKING_SIGNATURES,
)
