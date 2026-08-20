"""
src/banking_statements/processors/capital_one/__init__.py

Capital One statement processor support.
"""

from __future__ import annotations

from .business_credit_card import CapitalOneBusinessCreditCardProcessor
from .checking import CapitalOneCheckingProcessor
from .credit_card import CapitalOneCreditCardProcessor
from .signatures import (
    CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES,
    CAPITAL_ONE_CHECKING_SIGNATURES,
    CAPITAL_ONE_CREDIT_CARD_SIGNATURES,
    CAPITAL_ONE_SIGNATURES,
)

__all__ = [
    "CAPITAL_ONE_BUSINESS_CREDIT_CARD_SIGNATURES",
    "CAPITAL_ONE_CHECKING_SIGNATURES",
    "CAPITAL_ONE_CREDIT_CARD_SIGNATURES",
    "CAPITAL_ONE_SIGNATURES",
    "CapitalOneBusinessCreditCardProcessor",
    "CapitalOneCheckingProcessor",
    "CapitalOneCreditCardProcessor",
]
