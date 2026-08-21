"""
src/banking_statements/processors/penfed/signatures.py

Institution detection signatures for PenFed statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

PENFED_HELOC_SIGNATURES = (
    InstitutionSignature(
        institution="penfed",
        required_markers=(
            "Home Equity Line of Credit Statement",
            "Statement Closing Date:",
            "Loan Number ",
            "CURRENT ACCOUNT INFORMATION",
            "HELOC ACTIVITY AND FINANCE CHARGES",
            "Transaction Activity (",
            "FINANCE CHARGES",
            "www.PenFed.org",
        ),
    ),
)

PENFED_SIGNATURES = (*PENFED_HELOC_SIGNATURES,)
