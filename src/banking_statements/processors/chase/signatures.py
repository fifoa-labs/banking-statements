"""
src/banking_statements/processors/chase/signatures.py

Institution detection signatures for Chase statements.

Institution detection intentionally uses only strong, stable Chase markers.
Account-number labels are not required here because PDF text extraction can
heavily corrupt those labels even when the statement is clearly from Chase.

The opening/closing-date marker uses its stable substring because extraction
has produced both "Opening/Closing Date" and "O`pening/Closing Date".

Account-family signatures are kept in dedicated tuples so each Chase processor
can reuse only the marker sets for the statement grammar it supports.
CHASE_SIGNATURES remains the institution-level aggregate.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

CHASE_BUSINESS_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "www.chase.com/ink",
            "Revolving Credit Amount",
            "pening/Closing Date",
        ),
    ),
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "chase.com/cardhelp",
            "Revolving Credit Amount",
            "pening/Closing Date",
        ),
    ),
)

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

CHASE_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "JPMorgan Chase Bank, N.A.",
            "CHECKING SUMMARY",
            "TRANSACTION DETAIL",
        ),
    ),
)

CHASE_HELOC_SIGNATURES = (
    InstitutionSignature(
        institution="chase",
        required_markers=(
            "JPMorgan Chase Bank, N.A.",
            "Line of credit information",
            "Transaction activity",
        ),
    ),
)

CHASE_SIGNATURES = (
    *CHASE_BUSINESS_CREDIT_CARD_SIGNATURES,
    *CHASE_CREDIT_CARD_SIGNATURES,
    *CHASE_CHECKING_SIGNATURES,
    *CHASE_HELOC_SIGNATURES,
)
