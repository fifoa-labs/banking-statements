"""
src/banking_statements/processors/capital_one/signatures.py

Institution detection signatures for Capital One statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

CAPITAL_ONE_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="capital_one",
        required_markers=(
            "Venture X Card | Visa Infinite ending in",
            "days in Billing Cycle",
            "Account Summary",
            "Account ending in",
            "Transactions",
            "Trans Date Post Date Description Amount",
            "Capital One",
        ),
    ),
)

CAPITAL_ONE_SIGNATURES = (*CAPITAL_ONE_CREDIT_CARD_SIGNATURES,)
