"""
src/banking_statements/processors/chase/signatures.py

Institution detection signatures for Chase statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

CHASE_SIGNATURES = (
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "www.chase.com/cardhelp",
            "Account Number:",
            "Opening/Closing Date",
        ),
    ),
)
