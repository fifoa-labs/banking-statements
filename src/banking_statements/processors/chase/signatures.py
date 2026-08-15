"""
src/banking_statements/processors/chase/signatures.py

Institution detection signatures for Chase statements.

Institution detection intentionally uses only strong, stable Chase markers.
Account-number labels are not required here because PDF text extraction can
heavily corrupt those labels even when the statement is clearly from Chase.

The opening/closing-date marker uses its stable substring because extraction
has produced both "Opening/Closing Date" and "O`pening/Closing Date".

Credit-card signatures are kept in a dedicated tuple so the Chase credit-card
processor can reuse the exact same marker sets without duplicating detection
logic. CHASE_SIGNATURES remains the institution-level aggregate and can later
include checking and savings signatures as those processors are added.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

CHASE_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "chase.com/cardhelp",
            "pening/Closing Date",
        ),
    ),
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "www.chase.com",
            "Credit Card Statement",
            "pening/Closing Date",
        ),
    ),
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "www.Chase.com/",
            "Credit Card Statement",
            "pening/Closing Date",
        ),
    ),
)

CHASE_SIGNATURES = (*CHASE_CREDIT_CARD_SIGNATURES,)
