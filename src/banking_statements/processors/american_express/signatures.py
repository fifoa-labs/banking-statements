"""
src/banking_statements/processors/american_express/signatures.py

Institution detection signatures for American Express statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="american_express",
        required_markers=(
            "American Express",
            "Closing Date",
            "Account Ending",
            "Previous Balance",
            "New Charges",
        ),
    ),
)

AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="american_express",
        required_markers=(
            "Business Checking Account Statement",
            "Statement Period",
            "Account Ending",
            "Beginning Balance",
            "Ending Balance",
            "Account Activity",
        ),
    ),
    InstitutionSignature(
        institution="american_express",
        required_markers=(
            "Business Checking Account Statement",
            "StatementPeriod",
            "AccountEnding",
            "BeginningBalance",
            "EndingBalance",
            "Account Activity",
        ),
    ),
    InstitutionSignature(
        institution="american_express",
        required_markers=(
            "Business Checking Account Statement",
            "Statement Date:",
            "Account Ending:",
            "Beginning Balance as of",
            "Ending Balance as of",
            "Account Activity",
        ),
    ),
)

AMERICAN_EXPRESS_BUSINESS_LINE_OF_CREDIT_SIGNATURES = (
    InstitutionSignature(
        institution="american_express",
        required_markers=(
            "Monthly statement",
            "Statement Date",
            "For the Period",
            "Account number",
            "Summary of account activity",
            "Loans/debits",
            "Costs and fees",
            "Payments/credits",
            "Transaction Summary",
            "American Express Business Line of Credit Account",
        ),
    ),
)

AMERICAN_EXPRESS_PERSONAL_LOAN_SIGNATURES = (
    InstitutionSignature(
        institution="american_express",
        required_markers=(
            "American Express® Personal Loans",
            "Invoice Date",
            "Next Invoice Date",
            "Loan Account Ending",
            "Payment Information Account Summary",
            "Previous Outstanding Loan Balance",
            "Outstanding Loan Balance",
        ),
    ),
)

AMERICAN_EXPRESS_SIGNATURES = (
    *AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES,
    *AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES,
    *AMERICAN_EXPRESS_BUSINESS_LINE_OF_CREDIT_SIGNATURES,
    *AMERICAN_EXPRESS_PERSONAL_LOAN_SIGNATURES,
)
