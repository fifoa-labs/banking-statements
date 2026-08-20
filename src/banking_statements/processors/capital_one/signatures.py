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

CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="capital_one",
        required_markers=(
            "Spark® Visa Signature Business Account Ending in",
            "days in Billing Cycle",
            "Account Summary",
            "Date Description Amount",
            "Fees",
            "Capital One",
        ),
    ),
    InstitutionSignature(
        institution="capital_one",
        required_markers=(
            "Spark Cash credit card | Visa Signature Business ending in",
            "days in Billing Cycle",
            "Account Summary",
            "Trans Date Post Date Description Amount",
            "Fees",
            "Capital One",
        ),
    ),
    InstitutionSignature(
        institution="capital_one",
        required_markers=(
            "Venture X Business card | Visa Infinite Business ending in",
            "days in Billing Cycle",
            "Account Summary",
            "Trans Date Post Date Description Amount",
            "Fees",
            "Capital One",
        ),
    ),
)

CAPITAL_ONE_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="capital_one",
        required_markers=(
            "STATEMENT PERIOD",
            "Account Summary Cashflow Summary",
            "360 Checking - ",
            "DATE DESCRIPTION CATEGORY AMOUNT BALANCE",
            "Opening Balance",
            "Closing Balance",
            "capitalone.com",
        ),
    ),
)

CAPITAL_ONE_SIGNATURES = (
    *CAPITAL_ONE_CREDIT_CARD_SIGNATURES,
    *CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES,
    *CAPITAL_ONE_CHECKING_SIGNATURES,
)
