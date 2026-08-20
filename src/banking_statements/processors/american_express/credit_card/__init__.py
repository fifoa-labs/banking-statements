"""
src/banking_statements/processors/american_express/credit_card/__init__.py

American Express credit-card statement processor support.
"""

from __future__ import annotations

from .identity import AmericanExpressCreditCardIdentity, parse_identity
from .processor import AmericanExpressCreditCardProcessor
from .summary import parse_balance_summary

__all__ = [
    "AmericanExpressCreditCardIdentity",
    "AmericanExpressCreditCardProcessor",
    "parse_balance_summary",
    "parse_identity",
]
