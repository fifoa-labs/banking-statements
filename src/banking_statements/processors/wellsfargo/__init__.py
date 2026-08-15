"""
src/banking_statements/processors/wellsfargo/__init__.py

Wells Fargo statement processor support.
"""

from __future__ import annotations

from .checking import WellsFargoCheckingProcessor
from .credit_card import WellsFargoCreditCardProcessor
from .signatures import (
    WELLS_FARGO_CHECKING_SIGNATURES,
    WELLS_FARGO_CREDIT_CARD_SIGNATURES,
    WELLS_FARGO_SIGNATURES,
)

__all__ = [
    "WELLS_FARGO_CHECKING_SIGNATURES",
    "WELLS_FARGO_CREDIT_CARD_SIGNATURES",
    "WELLS_FARGO_SIGNATURES",
    "WellsFargoCheckingProcessor",
    "WellsFargoCreditCardProcessor",
]
