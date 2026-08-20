"""
src/banking_statements/processors/american_express/__init__.py

American Express statement processor support.
"""

from __future__ import annotations

from .business_checking import AmericanExpressBusinessCheckingProcessor
from .business_line_of_credit import (
    AmericanExpressBusinessLineOfCreditProcessor,
)
from .credit_card import AmericanExpressCreditCardProcessor
from .personal_loan import AmericanExpressPersonalLoanProcessor
from .signatures import (
    AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES,
    AMERICAN_EXPRESS_BUSINESS_LINE_OF_CREDIT_SIGNATURES,
    AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES,
    AMERICAN_EXPRESS_PERSONAL_LOAN_SIGNATURES,
    AMERICAN_EXPRESS_SIGNATURES,
)

__all__ = [
    "AMERICAN_EXPRESS_BUSINESS_CHECKING_SIGNATURES",
    "AMERICAN_EXPRESS_BUSINESS_LINE_OF_CREDIT_SIGNATURES",
    "AMERICAN_EXPRESS_CREDIT_CARD_SIGNATURES",
    "AMERICAN_EXPRESS_PERSONAL_LOAN_SIGNATURES",
    "AMERICAN_EXPRESS_SIGNATURES",
    "AmericanExpressBusinessCheckingProcessor",
    "AmericanExpressBusinessLineOfCreditProcessor",
    "AmericanExpressCreditCardProcessor",
    "AmericanExpressPersonalLoanProcessor",
]
