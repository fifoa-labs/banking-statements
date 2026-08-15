"""
src/banking_statements/processors/chase/signatures.py

Institution detection signatures for Chase statements.

Institution detection intentionally uses only strong, stable Chase markers.
Account-number labels are not required here because PDF text extraction can
heavily corrupt those labels even when the statement is clearly from Chase.

The opening/closing-date marker uses its stable substring because extraction
has produced both "Opening/Closing Date" and "O`pening/Closing Date".
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

CHASE_SIGNATURES = (
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "chase.com/cardhelp",
            "pening/Closing Date",
        ),
    ),
)
