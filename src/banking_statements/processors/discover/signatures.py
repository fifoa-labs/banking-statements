"""
src/banking_statements/processors/discover/signatures.py

Institution detection signatures for Discover statements.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionSignature

DISCOVER_CHECKING_SIGNATURES = (
    InstitutionSignature(
        institution="discover",
        required_markers=(
            "CASHBACK CHECKING",
            "Statement Period:",
            "ACCOUNT SUMMARY",
            "Beginning Balance",
            "Ending Balance",
            "DiscoverBank.com",
        ),
    ),
    InstitutionSignature(
        institution="discover",
        required_markers=(
            "CASHBACK DEBIT",
            "Statement Period:",
            "ACCOUNT SUMMARY",
            "Beginning Balance",
            "Ending Balance",
            "DiscoverBank.com",
        ),
    ),
    InstitutionSignature(
        institution="discover",
        required_markers=(
            "CASHBACK DEBIT",
            "Statement Period:",
            "ACCOUNT SUMMARY",
            "Beginning Balance",
            "Ending Balance",
            "Discover.com",
        ),
    ),
)

DISCOVER_CREDIT_CARD_SIGNATURES = (
    InstitutionSignature(
        institution="discover",
        required_markers=(
            "Discover it® Card",
            "Account number ending in",
            "Open Date:",
            "Close Date:",
            "ACCOUNT SUMMARY",
            "Transactions",
        ),
    ),
    InstitutionSignature(
        institution="discover",
        required_markers=(
            "DISCOVER IT® CARD ENDING IN",
            "AccountSummary",
            "PaymentInformation",
            "PreviousBalance",
            "NewBalance",
            "Transactions",
        ),
    ),
)

DISCOVER_SIGNATURES = (
    *DISCOVER_CHECKING_SIGNATURES,
    *DISCOVER_CREDIT_CARD_SIGNATURES,
)
