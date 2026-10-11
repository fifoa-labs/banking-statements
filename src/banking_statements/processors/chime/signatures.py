"""
src/banking_statements/processors/chime/signatures.py

Chime identity requires Chime-specific document evidence, not issuer alone.
"""

from banking_statements.processors.detection import InstitutionSignature

CHECKING_TITLE = "Checking Account Statement"
CARD_TITLE = "Credit Builder Card Account Billing Statement"
SECURED_TITLE = "Credit Builder Secured Account Billing Statement"

CHIME_SIGNATURES = tuple(
    InstitutionSignature(
        institution="chime",
        required_markers=(
            title,
            "Chime",
            "Statement period",
            "Account number",
        ),
    )
    for title in (CHECKING_TITLE, CARD_TITLE)
)
