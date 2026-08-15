"""
src/banking_statements/processors/wellsfargo/signatures.py

Institution detection signatures for Wells Fargo statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

WELLS_FARGO_SIGNATURES = (
    InstitutionSignature(
        institution="wellsfargo",
        required_markers=(
            "Wells Fargo Bank, N.A.",
            "wellsfargo.com",
        ),
    ),
)
